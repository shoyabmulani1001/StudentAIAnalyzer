"""
excel_reader.py
Reads all Excel subject files from the excel_files/ directory.
Extracts student internal (CO Int. Attn) and external (CO Ext. Attn) marks,
merges them, and returns structured student-subject records.
"""

import os
import openpyxl
from typing import List, Dict, Any


EXCEL_DIR = os.path.join(os.path.dirname(__file__), "excel_files")

# Sheet names to look for
INT_SHEET = "CO Int. Attn"
EXT_SHEET = "CO Ext. Attn"
DETAILS_SHEET = "SubjectDetails"

# Max marks
INT_MAX = 25
EXT_MAX = 50
TOTAL_MAX = 75


def _get_subject_name(wb: openpyxl.Workbook, filename: str) -> str:
    """Extract subject name from SubjectDetails sheet, fallback to filename."""
    try:
        ws = wb[DETAILS_SHEET]
        for row in ws.iter_rows(min_row=1, max_row=30, values_only=True):
            if row[0] and str(row[0]).strip().lower().startswith("subject"):
                val = row[1] if len(row) > 1 else None
                if val:
                    return str(val).strip()
    except Exception:
        pass
    # Fallback: strip extension from filename
    name = os.path.splitext(filename)[0]
    # Remove prefix like "IT11 " or "OC11 "
    parts = name.split(" ", 1)
    return parts[1] if len(parts) > 1 else name


def _find_total_col(ws) -> tuple:
    """
    Dynamically find the column index of 'Total Marks Obtained' and whether
    the internal score is out of 100 (needs scaling to 25) or already out of 25.
    Returns (col_index, raw_max) where raw_max is 100 or 25.
    """
    for row in ws.iter_rows(max_row=15, values_only=True):
        for idx, cell in enumerate(row):
            if cell and isinstance(cell, str) and "total marks obtained" in cell.lower():
                # Determine max from header text e.g. "(25)" or "(100)"
                raw_max = 25
                import re
                m = re.search(r"\((\d+)\)", cell)
                if m:
                    raw_max = int(m.group(1))
                return idx, raw_max
    return None, 25


def _read_internal(ws) -> Dict[str, Dict]:
    """
    Parse CO Int. Attn sheet.
    Dynamically detects the 'Total Marks Obtained' column.
    The column stores scores out of 100 (Combined Assessment) which get
    scaled to 25 (the internal weightage) when raw_max == 100.
    Returns dict keyed by normalized student name -> {seat_no, internal_marks}
    """
    total_col, raw_max = _find_total_col(ws)
    students = {}
    data_started = False

    for row in ws.iter_rows(values_only=True):
        if not data_started:
            if row[0] in ("Sr. No", "Sr.No"):
                data_started = True
                continue
            elif isinstance(row[0], int) and row[0] == 1:
                data_started = True
                # Fall through — process this row
            else:
                continue

        if row[0] is None:
            continue
        try:
            sr = int(row[0])
        except (ValueError, TypeError):
            continue

        name = str(row[2]).strip().upper() if row[2] else None
        seat_no = str(row[1]).strip() if row[1] else None

        internal = None
        # Try detected column first, then scan nearby cols
        search_cols = ([total_col] if total_col is not None else []) + [20, 23, 19, 21, 22, 24]
        for col_idx in search_cols:
            if col_idx is not None and col_idx < len(row) and row[col_idx] is not None:
                try:
                    val = float(row[col_idx])
                    if val > raw_max:
                        # Skip values out of range
                        continue
                    internal = val
                    break
                except (ValueError, TypeError):
                    pass

        if internal is not None:
            # Scale to out-of-25 if raw_max is 100
            scaled = round((internal / raw_max) * 25, 2) if raw_max != 25 else round(internal, 2)
        else:
            scaled = None

        if name and scaled is not None:
            students[name] = {
                "seat_no": seat_no,
                "internal_marks": scaled,
            }

    return students


def _read_external(ws) -> Dict[str, Dict]:
    """
    Parse CO Ext. Attn sheet.
    Columns (0-indexed):
      0=Roll No, 1=Seat No, 2=Name, 3=Marks (out of 50)
    Data rows start where col[0] is an integer roll number.
    Returns dict keyed by normalized student name -> {seat_no, external_marks}
    """
    students = {}
    for row in ws.iter_rows(values_only=True):
        if row[0] is None:
            continue
        try:
            roll = int(row[0])
        except (ValueError, TypeError):
            continue

        name = str(row[2]).strip().upper() if row[2] else None
        seat_no = str(row[1]).strip() if row[1] else None

        # External marks at col index 3
        external = None
        if len(row) > 3 and row[3] is not None:
            try:
                external = float(row[3])
            except (ValueError, TypeError):
                pass

        if name and external is not None:
            students[name] = {
                "seat_no": seat_no,
                "external_marks": round(external, 2),
            }

    return students


def read_all_files() -> List[Dict[str, Any]]:
    """
    Read all Excel files from excel_files/ directory.
    Returns a flat list of student-subject records:
    [
      {
        "name": "JOHN DOE",
        "seat_no": "23101",
        "subject": "Java Programming",
        "internal_marks": 18.0,    # out of 25
        "external_marks": 35.0,    # out of 50
        "total_marks": 53.0,       # out of 75
        "percentage": 70.67,
        "file": "IT11 Java Programming.xlsx"
      },
      ...
    ]
    """
    records = []
    files = sorted(f for f in os.listdir(EXCEL_DIR) if f.endswith(".xlsx"))

    for filename in files:
        filepath = os.path.join(EXCEL_DIR, filename)
        try:
            wb = openpyxl.load_workbook(filepath, data_only=True)
        except Exception as e:
            print(f"[WARN] Could not open {filename}: {e}")
            continue

        subject = _get_subject_name(wb, filename)

        # Check sheets exist
        if INT_SHEET not in wb.sheetnames or EXT_SHEET not in wb.sheetnames:
            print(f"[WARN] Missing sheets in {filename}: {wb.sheetnames}")
            continue

        internal_data = _read_internal(wb[INT_SHEET])
        external_data = _read_external(wb[EXT_SHEET])

        # Merge by student name (both sheets should have the same students)
        all_names = set(internal_data.keys()) | set(external_data.keys())

        for name in all_names:
            int_info = internal_data.get(name, {})
            ext_info = external_data.get(name, {})

            internal = int_info.get("internal_marks")
            external = ext_info.get("external_marks")
            seat_no = int_info.get("seat_no") or ext_info.get("seat_no")

            if internal is None and external is None:
                continue

            # Use 0 if one is missing (absent in that component)
            internal = internal if internal is not None else 0.0
            external = external if external is not None else 0.0

            total = internal + external
            percentage = round((total / TOTAL_MAX) * 100, 2)

            records.append({
                "name": name,
                "seat_no": seat_no,
                "subject": subject,
                "internal_marks": internal,
                "external_marks": external,
                "total_marks": total,
                "percentage": percentage,
                "file": filename,
            })

        wb.close()

    return records


def get_all_students(records: List[Dict]) -> List[str]:
    """Return sorted list of unique student names."""
    return sorted(set(r["name"] for r in records))


def get_all_subjects(records: List[Dict]) -> List[str]:
    """Return sorted list of unique subject names."""
    return sorted(set(r["subject"] for r in records))
