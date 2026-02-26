"""
ai_analyzer.py
AI analysis engine for student performance.
Classifies students into grade bands, performance labels,
and generates AI-powered insight summaries.
"""

from typing import List, Dict, Any
import statistics


# ── Grade Bands ─────────────────────────────────────────────────────────────

BANDS = [
    {"key": "below_40",  "label": "Below 40%",  "emoji": "🔴",  "color": "#ff4d4d",  "min": 0,   "max": 40},
    {"key": "40_50",     "label": "40% – 50%",  "emoji": "🟠",  "color": "#ff8c00",  "min": 40,  "max": 50},
    {"key": "50_60",     "label": "50% – 60%",  "emoji": "🟡",  "color": "#ffd700",  "min": 50,  "max": 60},
    {"key": "60_80",     "label": "60% – 80%",  "emoji": "🟢",  "color": "#00c853",  "min": 60,  "max": 80},
    {"key": "above_80",  "label": "80% & Above","emoji": "🌟",  "color": "#7c4dff",  "min": 80,  "max": 101},
]


def get_band(percentage: float) -> Dict:
    """Return the grade band dict for a given percentage."""
    for band in BANDS:
        if band["min"] <= percentage < band["max"]:
            return band
    return BANDS[-1]  # fallback: 80%+


# ── Performance Labels ───────────────────────────────────────────────────────

def get_performance_label(percentage: float) -> str:
    """Return a textual AI performance label for a given percentage."""
    if percentage < 40:
        return "Poor"
    elif percentage < 60:
        return "Average"
    elif percentage < 80:
        return "Best"
    else:
        return "Excellent"


def get_performance_color(label: str) -> str:
    """Return a hex color for a performance label."""
    return {
        "Poor":      "#ff4d4d",
        "Average":   "#ffaa00",
        "Best":      "#00c853",
        "Excellent": "#7c4dff",
    }.get(label, "#888888")


# ── Per-Student AI Insights ─────────────────────────────────────────────────

def generate_student_insight(name: str, subjects: List[Dict]) -> str:
    """
    Generate a natural-language AI insight string for a student
    across all their subjects.
    """
    if not subjects:
        return f"{name} has no recorded data."

    percentages = [s["percentage"] for s in subjects]
    avg = round(statistics.mean(percentages), 1)

    best = max(subjects, key=lambda s: s["percentage"])
    worst = min(subjects, key=lambda s: s["percentage"])

    label = get_performance_label(avg)
    insight_parts = []

    if label == "Excellent":
        insight_parts.append(
            f"🌟 {name.title()} demonstrates outstanding overall performance with an average of {avg}%."
        )
    elif label == "Best":
        insight_parts.append(
            f"✅ {name.title()} shows good overall performance with an average of {avg}%."
        )
    elif label == "Average":
        insight_parts.append(
            f"⚠️ {name.title()} has a moderate overall average of {avg}% and can improve further."
        )
    else:
        insight_parts.append(
            f"🚨 {name.title()} is below expectations with an average of {avg}% and needs immediate attention."
        )

    if best["subject"] != worst["subject"]:
        insight_parts.append(
            f"Strongest in **{best['subject']}** ({best['percentage']}%), "
            f"weakest in **{worst['subject']}** ({worst['percentage']}%)."
        )

    struggling = [s for s in subjects if s["percentage"] < 40]
    if struggling:
        subj_list = ", ".join(s["subject"] for s in struggling)
        insight_parts.append(f"❗ Failing in: {subj_list}.")

    return " ".join(insight_parts)


# ── Aggregated Analytics ────────────────────────────────────────────────────

def analyze_all(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Run full AI analysis on all student-subject records.

    Returns:
    {
      "students": [
         {
           "name": ...,
           "subjects": [
             { subject, internal_marks, external_marks, total_marks, percentage,
               band, band_color, band_emoji, performance_label, performance_color }
           ],
           "overall_avg": ...,
           "overall_band": ...,
           "overall_label": ...,
           "insight": ...,
         }
       ],
      "bands": {
         "below_40": { "label":..., "color":..., "emoji":..., "students": [...] },
         ...
      },
      "subject_summary": {
         "Java Programming": { avg, min, max, count,
           band_counts: {below_40: N, 40_50: N, ...},
           label_counts: {Poor: N, Average: N, Best: N, Excellent: N}
         },
         ...
      },
      "class_overview": {
         "total_students": N,
         "total_subjects": N,
         "class_avg": ...,
         "best_subject": ...,
         "weakest_subject": ...,
      }
    }
    """

    # ── Group records by student ──
    student_map: Dict[str, List[Dict]] = {}
    for rec in records:
        name = rec["name"]
        if name not in student_map:
            student_map[name] = []

        band = get_band(rec["percentage"])
        label = get_performance_label(rec["percentage"])
        student_map[name].append({
            **rec,
            "band":              band["key"],
            "band_label":        band["label"],
            "band_color":        band["color"],
            "band_emoji":        band["emoji"],
            "performance_label": label,
            "performance_color": get_performance_color(label),
        })

    # ── Build student list ──
    students_out = []
    for name, subj_list in sorted(student_map.items()):
        percentages = [s["percentage"] for s in subj_list]
        overall_avg = round(statistics.mean(percentages), 2)
        overall_band = get_band(overall_avg)
        overall_label = get_performance_label(overall_avg)
        insight = generate_student_insight(name, subj_list)
        students_out.append({
            "name": name,
            "subjects": subj_list,
            "overall_avg": overall_avg,
            "overall_band": overall_band["key"],
            "overall_band_label": overall_band["label"],
            "overall_band_color": overall_band["color"],
            "overall_label": overall_label,
            "insight": insight,
        })

    # ── Grade band buckets (overall percentage per student) ──
    bands_out = {b["key"]: {**b, "students": []} for b in BANDS}
    for student in students_out:
        band_key = student["overall_band"]
        bands_out[band_key]["students"].append({
            "name": student["name"],
            "overall_avg": student["overall_avg"],
            "overall_label": student["overall_label"],
        })

    # ── Subject-level summary ──
    subject_map: Dict[str, List[float]] = {}
    subject_band_counts: Dict[str, Dict[str, int]] = {}
    subject_label_counts: Dict[str, Dict[str, int]] = {}

    for rec in records:
        subj = rec["subject"]
        pct = rec["percentage"]
        band_key = get_band(pct)["key"]
        label = get_performance_label(pct)

        subject_map.setdefault(subj, []).append(pct)
        subject_band_counts.setdefault(subj, {b["key"]: 0 for b in BANDS})
        subject_label_counts.setdefault(subj, {"Poor": 0, "Average": 0, "Best": 0, "Excellent": 0})

        subject_band_counts[subj][band_key] += 1
        subject_label_counts[subj][label] += 1

    subject_summary = {}
    for subj, pcts in subject_map.items():
        avg = round(statistics.mean(pcts), 2)
        subject_summary[subj] = {
            "avg": avg,
            "min": round(min(pcts), 2),
            "max": round(max(pcts), 2),
            "count": len(pcts),
            "band_counts": subject_band_counts[subj],
            "label_counts": subject_label_counts[subj],
        }

    # ── Class overview ──
    all_pcts = [r["percentage"] for r in records]
    class_avg = round(statistics.mean(all_pcts), 2) if all_pcts else 0
    best_subj = max(subject_summary, key=lambda s: subject_summary[s]["avg"]) if subject_summary else ""
    weak_subj = min(subject_summary, key=lambda s: subject_summary[s]["avg"]) if subject_summary else ""

    class_overview = {
        "total_students": len(student_map),
        "total_subjects": len(subject_summary),
        "class_avg": class_avg,
        "best_subject": best_subj,
        "weakest_subject": weak_subj,
    }

    return {
        "students":       students_out,
        "bands":          bands_out,
        "subject_summary": subject_summary,
        "class_overview": class_overview,
    }
