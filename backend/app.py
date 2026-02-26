"""
app.py — Student AI Analyzer Flask REST API

Endpoints:
  GET /                        → serves frontend dashboard
  GET /api/subjects            → list of subject names
  GET /api/students            → all student-subject records (?subject= filter)
  GET /api/analysis            → full AI analysis payload
  GET /api/analysis/bands      → grade band buckets (?subject= filter)
  GET /api/analysis/performance→ per-student performance labels & insights
  GET /api/analysis/class      → class-wide subject summary
  GET /api/health              → health check
"""

import os
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from excel_reader import read_all_files, get_all_subjects, get_all_students
from ai_analyzer  import analyze_all, BANDS

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
CORS(app)

# ── Load & analyse once at startup ────────────────────────────────────────────
print("[INFO] Loading Excel files...")
_records  = read_all_files()
print(f"[INFO] Loaded {len(_records)} student-subject records.")
_analysis = analyze_all(_records)
print("[INFO] AI analysis complete.")


# ── Frontend ──────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


# ── Helper ────────────────────────────────────────────────────────────────────
def _filter_records(subject: str = None):
    if subject:
        return [r for r in _records if r["subject"].lower() == subject.lower()]
    return _records


# ── API Routes ────────────────────────────────────────────────────────────────
@app.route("/api/subjects", methods=["GET"])
def subjects():
    return jsonify(get_all_subjects(_records))


@app.route("/api/students", methods=["GET"])
def students():
    subject = request.args.get("subject")
    return jsonify(_filter_records(subject))


@app.route("/api/analysis", methods=["GET"])
def analysis():
    return jsonify(_analysis)


@app.route("/api/analysis/bands", methods=["GET"])
def bands():
    subject = request.args.get("subject")
    if subject:
        return jsonify(analyze_all(_filter_records(subject))["bands"])
    return jsonify(_analysis["bands"])


@app.route("/api/analysis/performance", methods=["GET"])
def performance():
    subject_filter = request.args.get("subject", "").strip().lower()
    result = []
    for student in _analysis["students"]:
        subjs = student["subjects"]
        if subject_filter:
            subjs = [s for s in subjs if s["subject"].lower() == subject_filter]
        if not subjs:
            continue
        result.append({
            "name":              student["name"],
            "overall_avg":       student["overall_avg"],
            "overall_label":     student["overall_label"],
            "overall_band_color":student["overall_band_color"],
            "insight":           student["insight"],
            "subjects": [
                {
                    "subject":           s["subject"],
                    "percentage":        s["percentage"],
                    "internal_marks":    s["internal_marks"],
                    "external_marks":    s["external_marks"],
                    "total_marks":       s["total_marks"],
                    "performance_label": s["performance_label"],
                    "performance_color": s["performance_color"],
                    "band_label":        s["band_label"],
                    "band_emoji":        s["band_emoji"],
                }
                for s in subjs
            ],
        })
    return jsonify(result)


@app.route("/api/analysis/class", methods=["GET"])
def class_summary():
    return jsonify({
        "overview":        _analysis["class_overview"],
        "subject_summary": _analysis["subject_summary"],
        "bands_meta":      BANDS,
    })


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "records": len(_records)})


if __name__ == "__main__":
    app.run(debug=True, port=5000, host="0.0.0.0")
