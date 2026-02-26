/**
 * app.js — Student AI Analyzer Frontend
 * Fetches data from the Flask backend and renders:
 *   1. Stats overview cards
 *   2. Grade Band sections (Below 40 / 40-50 / 50-60 / 60-80 / 80+)
 *   3. AI Performance table with labels per subject
 *   4. Class subject summary cards
 */

const API = "http://localhost:5000/api";

const BANDS = [
    { key: "below_40", label: "Below 40%", emoji: "🔴", color: "#ff4d4d" },
    { key: "40_50", label: "40% – 50%", emoji: "🟠", color: "#ff8c00" },
    { key: "50_60", label: "50% – 60%", emoji: "🟡", color: "#f59e0b" },
    { key: "60_80", label: "60% – 80%", emoji: "🟢", color: "#10b981" },
    { key: "above_80", label: "80% & Above", emoji: "🌟", color: "#7c4dff" },
];

const LABEL_CONFIG = {
    Poor: { color: "#ff4d4d", emoji: "🔴" },
    Average: { color: "#f59e0b", emoji: "🟡" },
    Best: { color: "#10b981", emoji: "🟢" },
    Excellent: { color: "#7c4dff", emoji: "⭐" },
};

// State
let _analysis = null;
let _subjects = [];
let _currentSubject = "";
let _searchQuery = "";
let _activeTab = "bands";

// ── Init ──────────────────────────────────────────────────────────────────────
window.addEventListener("DOMContentLoaded", init);

function initTheme() {
    const savedTheme = localStorage.getItem("theme") || "light";
    if (savedTheme === "dark") {
        document.body.classList.add("dark-mode");
    }
}

async function init() {
    initTheme();
    try {
        const [analysis, subjects] = await Promise.all([
            fetchJSON(`${API}/analysis`),
            fetchJSON(`${API}/subjects`),
        ]);
        _analysis = analysis;
        _subjects = subjects;
        populateSubjectFilter(subjects);
        renderAll();
        hideLoading();
        showToast(
            `✅ Loaded ${analysis.class_overview.total_students} students across` +
            ` ${analysis.class_overview.total_subjects} subjects`
        );
    } catch (err) {
        hideLoading();
        showToast("❌ Cannot connect to backend. Is the server running on port 5000?", 6000);
        console.error(err);
    }
}

async function fetchJSON(url) {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
}

// ── Controls ──────────────────────────────────────────────────────────────────
function populateSubjectFilter(subjects) {
    const sel = document.getElementById("subjectFilter");
    sel.innerHTML = `<option value="">All Subjects</option>`;
    subjects.forEach(s => {
        sel.innerHTML += `<option value="${s}">${s}</option>`;
    });
}

document.getElementById("subjectFilter").addEventListener("change", e => {
    _currentSubject = e.target.value;
    renderAll();
});

document.getElementById("searchInput").addEventListener("input", e => {
    _searchQuery = e.target.value.trim().toLowerCase();
    renderAll();
});

document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
        _activeTab = btn.dataset.tab;
        document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        document.querySelectorAll(".section").forEach(s => s.classList.remove("active"));
        document.getElementById(`section-${_activeTab}`)?.classList.add("active");
    });
});

document.getElementById("themeToggle").addEventListener("click", () => {
    const isDark = document.body.classList.toggle("dark-mode");
    localStorage.setItem("theme", isDark ? "dark" : "light");
});

// ── Master Render ─────────────────────────────────────────────────────────────
function renderAll() {
    if (!_analysis) return;
    renderStats();
    renderBands();
    renderPerformanceTable();
    renderClassSummary();
}

// ── Stats Row ─────────────────────────────────────────────────────────────────
function renderStats() {
    const ov = _analysis.class_overview;
    const students = getFilteredStudents();
    const avgPct = students.length
        ? (students.reduce((s, st) => s + st.overall_avg, 0) / students.length).toFixed(1)
        : 0;

    document.getElementById("stat-students").textContent = students.length;
    document.getElementById("stat-subjects").textContent = ov.total_subjects;
    document.getElementById("stat-avg").textContent = avgPct + "%";
    document.getElementById("stat-best").textContent = ov.best_subject || "—";
    document.getElementById("stat-weak").textContent = ov.weakest_subject || "—";
    document.getElementById("stat-poor").textContent = students.filter(s => s.overall_label === "Poor").length;
    document.getElementById("stat-excellent").textContent = students.filter(s => s.overall_label === "Excellent").length;
}

// ── Grade Bands ───────────────────────────────────────────────────────────────
function renderBands() {
    const container = document.getElementById("bands-container");
    container.innerHTML = "";
    const students = getFilteredStudents();
    const total = students.length || 1;

    BANDS.forEach((band, i) => {
        const bandStudents = students.filter(s => s.overall_band === band.key);
        const pct = Math.round((bandStudents.length / total) * 100);

        const card = document.createElement("div");
        card.className = "band-card";
        card.style.animationDelay = `${i * 0.06}s`;
        card.innerHTML = `
      <div class="band-header" style="border-top: 3px solid ${band.color}">
        <span class="band-emoji">${band.emoji}</span>
        <span class="band-label-text" style="color:${band.color}">${band.label}</span>
        <span class="band-count">${bandStudents.length} students · ${pct}%</span>
      </div>
      <div class="band-bar">
        <div class="band-bar-fill" style="width:0%;background:${band.color}" data-width="${pct}"></div>
      </div>
      <div class="band-students">
        ${bandStudents.length === 0
                ? `<div class="no-data">No students in this band</div>`
                : bandStudents.map(s => studentRow(s, band.color)).join("")
            }
      </div>`;
        container.appendChild(card);
        setTimeout(() => {
            card.querySelector(".band-bar-fill").style.width = pct + "%";
        }, 100);
    });
}

function studentRow(student, color) {
    const initials = student.name.split(" ").slice(0, 2).map(w => w[0]).join("");
    return `<div class="band-student-row">
    <div class="student-avatar" style="background:${color}22;color:${color}">${initials}</div>
    <div class="student-name">${toTitleCase(student.name)}</div>
    <div class="student-pct" style="color:${color}">${student.overall_avg}%</div>
  </div>`;
}

// ── Performance Table ─────────────────────────────────────────────────────────
function renderPerformanceTable() {
    const tbody = document.getElementById("perf-tbody");
    const thead = document.getElementById("perf-thead");
    const students = getFilteredStudents();
    const subjects = _currentSubject ? [_currentSubject] : _subjects;

    thead.innerHTML = `
    <tr>
      <th>#</th>
      <th>Student Name</th>
      <th>Overall %</th>
      <th>Overall Rank</th>
      ${subjects.map(s => `<th title="${s}">${shortSubject(s)}</th>`).join("")}
      <th>AI Insight</th>
    </tr>`;

    tbody.innerHTML = "";
    if (!students.length) {
        tbody.innerHTML = `<tr><td colspan="${subjects.length + 5}" class="no-data">No students found</td></tr>`;
        return;
    }

    [...students].sort((a, b) => b.overall_avg - a.overall_avg).forEach((student, idx) => {
        const subjMap = {};
        student.subjects.forEach(s => { subjMap[s.subject] = s; });
        const labelCfg = LABEL_CONFIG[student.overall_label] || {};

        const row = document.createElement("tr");
        row.innerHTML = `
      <td style="color:var(--text-muted)">${idx + 1}</td>
      <td style="font-weight:600">${toTitleCase(student.name)}</td>
      <td style="font-weight:700;color:${student.overall_band_color}">${student.overall_avg}%</td>
      <td><span class="perf-badge" style="background:${labelCfg.color}22;color:${labelCfg.color}">
        ${labelCfg.emoji} ${student.overall_label}
      </span></td>
      ${subjects.map(subj => {
            const s = subjMap[subj];
            if (!s) return `<td style="color:var(--text-muted)">—</td>`;
            const lc = LABEL_CONFIG[s.performance_label] || {};
            return `<td>
          <span class="perf-badge" style="background:${lc.color}22;color:${lc.color};font-size:10px">
            ${lc.emoji} ${s.performance_label}
          </span>
          <div style="font-size:11px;color:var(--text-muted);margin-top:2px">${s.percentage}%</div>
        </td>`;
        }).join("")}
      <td><div class="insight-box">${student.insight}</div></td>`;
        tbody.appendChild(row);
    });
}

// ── Class Summary ─────────────────────────────────────────────────────────────
function renderClassSummary() {
    const container = document.getElementById("summary-container");
    container.innerHTML = "";
    const summary = _analysis.subject_summary;
    const subjects = _currentSubject ? [_currentSubject] : Object.keys(summary);

    subjects.forEach((subj, i) => {
        const data = summary[subj];
        if (!data) return;
        const total = data.count || 1;
        const card = document.createElement("div");
        card.className = "subject-card";
        card.style.animationDelay = `${i * 0.07}s`;

        const bandRows = BANDS.map(b => {
            const cnt = data.band_counts[b.key] || 0;
            const w = Math.round((cnt / total) * 100);
            return `<div class="mini-bar-row">
        <div class="mini-bar-label">${b.emoji} ${b.label}</div>
        <div class="mini-bar-track">
          <div class="mini-bar-fill" style="width:0%;background:${b.color}" data-w="${w}"></div>
        </div>
        <div class="mini-bar-count">${cnt}</div>
      </div>`;
        }).join("");

        const labelRows = Object.entries(data.label_counts).map(([lbl, cnt]) => {
            const lc = LABEL_CONFIG[lbl] || {};
            return `<span class="perf-badge" style="background:${lc.color}22;color:${lc.color};margin:2px">
        ${lc.emoji} ${lbl}: ${cnt}
      </span>`;
        }).join("");

        card.innerHTML = `
      <div class="subject-card-name">📘 ${subj}</div>
      <div class="subject-stats">
        <div class="subj-stat">
          <div class="subj-stat-val" style="color:#7c4dff">${data.avg}%</div>
          <div class="subj-stat-lbl">Avg</div>
        </div>
        <div class="subj-stat">
          <div class="subj-stat-val" style="color:#10b981">${data.max}%</div>
          <div class="subj-stat-lbl">Max</div>
        </div>
        <div class="subj-stat">
          <div class="subj-stat-val" style="color:#ff4d4d">${data.min}%</div>
          <div class="subj-stat-lbl">Min</div>
        </div>
        <div class="subj-stat">
          <div class="subj-stat-val">${data.count}</div>
          <div class="subj-stat-lbl">Students</div>
        </div>
      </div>
      <div class="mini-bars">${bandRows}</div>
      <div style="margin-top:12px;display:flex;flex-wrap:wrap;gap:4px">${labelRows}</div>`;

        container.appendChild(card);
        setTimeout(() => {
            card.querySelectorAll(".mini-bar-fill").forEach(el => {
                el.style.width = el.dataset.w + "%";
            });
        }, 150 + i * 60);
    });
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function getFilteredStudents() {
    if (!_analysis) return [];
    let students = _analysis.students;

    if (_currentSubject) {
        students = students
            .map(s => ({ ...s, subjects: s.subjects.filter(sub => sub.subject === _currentSubject) }))
            .filter(s => s.subjects.length > 0)
            .map(s => {
                const pct = s.subjects[0].percentage;
                const band = getBandKey(pct);
                return { ...s, overall_avg: pct, overall_band: band.key, overall_band_color: band.color, overall_label: getLabelName(pct) };
            });
    }

    if (_searchQuery) {
        students = students.filter(s =>
            s.name.toLowerCase().includes(_searchQuery) ||
            (s.seat_no && s.seat_no.includes(_searchQuery))
        );
    }
    return students;
}

function getBandKey(pct) {
    if (pct < 40) return { key: "below_40", color: "#ff4d4d" };
    if (pct < 50) return { key: "40_50", color: "#ff8c00" };
    if (pct < 60) return { key: "50_60", color: "#f59e0b" };
    if (pct < 80) return { key: "60_80", color: "#10b981" };
    return { key: "above_80", color: "#7c4dff" };
}

function getLabelName(pct) {
    if (pct < 40) return "Poor";
    if (pct < 60) return "Average";
    if (pct < 80) return "Best";
    return "Excellent";
}

function shortSubject(s) {
    const words = s.split(" ");
    if (words.length <= 2) return s;
    return words.slice(0, 2).join(" ") + "…";
}

function toTitleCase(str) {
    return str.toLowerCase().replace(/\b\w/g, c => c.toUpperCase());
}

function hideLoading() {
    document.getElementById("loadingOverlay").classList.add("hidden");
}

function showToast(msg, duration = 3500) {
    const el = document.getElementById("toast");
    el.textContent = msg;
    el.classList.add("show");
    setTimeout(() => el.classList.remove("show"), duration);
}
