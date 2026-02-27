import os
import openpyxl

wb = openpyxl.load_workbook("backend/excel_files/IT13 OOSE.xlsx", data_only=True)
ws = wb["CO Int. Attn"]
count = 0
for row in ws.iter_rows(values_only=True):
    if isinstance(row[0], int):
        count += 1
        if count > 100:
            print(f"Row {count}: {row[:3]}")

print(f"Total internal int rows: {count}")
wb.close()
