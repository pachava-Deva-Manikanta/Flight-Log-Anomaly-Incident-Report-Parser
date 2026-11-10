/**
 * AEROTRIAGE ENTERPRISE JAVASCRIPT ENGINE
 * Handles Stepped Workflow, Reporter Telemetry, Neural Urgency Classification,
 * Dynamic SVG Gauge Animation, and Real-time Incident Audit Logging.
 */

// Helper selector
const $ = (id) => document.getElementById(id);

// System Constants & Guidance Directives
const URGENCY_CONFIG = {
    "Immediate Safety Hazard": {
        key: "hazard",
        icon: "🚨",
        title: "Immediate Safety Hazard",
        directive: "CRITICAL SAFETY DIRECTIVE: Stop flight operations immediately. Ground aircraft and notify Chief Inspector and Flight Dispatch within 30 minutes."
    },
    "Ground Aircraft": {
        key: "ground",
        icon: "⛔",
        title: "Ground Aircraft (AOG)",
        directive: "AIRCRAFT ON GROUND (AOG): Defect rectification is mandatory prior to departure. Aircraft cannot be released for line service under MEL."
    },
    "Routine": {
        key: "routine",
        icon: "✅",
        title: "Routine Maintenance",
        directive: "ROUTINE DEFECT: Defect may be logged and deferred per Minimum Equipment List (MEL). Aircraft is safe and approved for revenue service."
    }
};

// Current Session State
const state = {
    reporter: {
        name: "Capt. Alex Vance",
        badge_id: "AME-7492",
        role: "Line Maintenance Engineer",
        station: "JFK / Terminal 4",
        aircraft_reg: "N789AA (B737-800)",
        flight_number: "AA-1042"
    },
    step: 1,
    incidentHistory: []
};

// ============================================================================
// 1. UTC ZULU CLOCK & TELEMETRY
// ============================================================================
// function updateZuluClock() {
//     const now = new Date();
//     const utcHours = String(now.getUTCHours()).padStart(2, "0");
//     const utcMinutes = String(now.getUTCMinutes()).padStart(2, "0");
//     const utcSeconds = String(now.getUTCSeconds()).padStart(2, "0");
//     $("zuluTime").textContent = `${utcHours}:${utcMinutes}:${utcSeconds} UTC`;
// }
// IST CLOCK & TELEMETRY
function updateZuluClock() {
    const el = document.getElementById("zuluTime") || document.getElementById("zulutime");
    if (!el) return;

    const now = new Date();
    const istTime = new Intl.DateTimeFormat("en-IN", {
        timeZone: "Asia/Kolkata",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hour12: false
    }).format(now);

    el.textContent = `${istTime} IST`;
}

async function fetchTelemetry() {
    try {
        const [healthRes, modelRes] = await Promise.all([
            fetch("/health"),
            fetch("/model-info")
        ]);

        if (healthRes.ok && modelRes.ok) {
            const modelData = await modelRes.json();
            const modelName = modelData.best_model || "Active ML Model";
            $("modelStatusText").textContent = `Model: ${modelName}`;
        } else {
            $("modelStatusText").textContent = "Telemetry Offline";
        }
    } catch (err) {
        $("modelStatusText").textContent = "Offline Mode";
    }
}

// ============================================================================
// 2. REPORTER MANAGEMENT & STEPPER
// ============================================================================
function getInitials(name) {
    if (!name) return "RP";
    const parts = name.trim().split(" ");
    if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

function updateReporterRibbon() {
    $("ribbonAvatar").textContent = getInitials(state.reporter.name);
    $("ribbonName").textContent = state.reporter.name;
    $("ribbonBadge").textContent = `ID: ${state.reporter.badge_id}`;
    $("ribbonRole").textContent = state.reporter.role;
    $("ribbonStation").textContent = state.reporter.station || "N/A";
    $("ribbonAircraft").textContent = state.reporter.aircraft_reg || "N/A";
    $("ribbonFlight").textContent = state.reporter.flight_number || "N/A";
}

function setStep(stepNumber) {
    state.step = stepNumber;

    const stepNode1 = $("stepNode1");
    const stepNode2 = $("stepNode2");
    const stepNode3 = $("stepNode3");
    const connector = $("stepConnector");

    if (stepNumber === 1) {
        stepNode1.className = "step-node active";
        stepNode2.className = "step-node";
        stepNode3.className = "step-node";
        connector.classList.remove("filled");

        $("reporterCard").style.display = "block";
        $("reporterRibbon").style.display = "none";
    } else if (stepNumber >= 2) {
        stepNode1.className = "step-node completed";
        stepNode2.className = "step-node active";
        connector.classList.add("filled");

        $("reporterCard").style.display = "none";
        $("reporterRibbon").style.display = "flex";
        updateReporterRibbon();

        if (stepNumber === 3) {
            stepNode3.className = "step-node completed";
        }
    }
}

function saveReporterProfile(e) {
    if (e) e.preventDefault();

    const name = $("reporterName").value.trim();
    const badge_id = $("badgeId").value.trim();

    if (!name || !badge_id) {
        alert("Please provide reporter name and badge ID.");
        return;
    }

    state.reporter = {
        name,
        badge_id,
        role: $("reporterRole").value,
        station: $("station").value.trim() || "N/A",
        aircraft_reg: $("aircraftReg").value.trim() || "N/A",
        flight_number: $("flightNumber").value.trim() || "N/A"
    };

    setStep(2);
    $("description").focus();
}

function populatePreset(type) {
    if (type === "engineer") {
        $("reporterName").value = "Capt. Alex Vance";
        $("badgeId").value = "AME-7492";
        $("reporterRole").value = "Line Maintenance Engineer";
        $("station").value = "JFK / Terminal 4";
        $("aircraftReg").value = "N789AA (B737-800)";
        $("flightNumber").value = "AA-1042";
    } else if (type === "pilot") {
        $("reporterName").value = "Capt. Sarah Lindqvist";
        $("badgeId").value = "ATP-9941";
        $("reporterRole").value = "Captain / Pilot in Command";
        $("station").value = "ORD / Terminal 3";
        $("aircraftReg").value = "N512UA (A320)";
        $("flightNumber").value = "UA-419";
    }
}

// ============================================================================
// 3. DEFECT DIAGNOSTICS & CHAR COUNTER
// ============================================================================
function updateCharCounter() {
    const len = $("description").value.length;
    $("charCounter").textContent = `${len} / 1000`;
}

function handleScenarioChip(e) {
    const chip = e.target.closest(".chip");
    if (!chip) return;

    const comp = chip.dataset.comp;
    const desc = chip.dataset.desc;

    if (comp) $("component").value = comp;
    if (desc) $("description").value = desc;

    updateCharCounter();
    $("description").focus();
}

function clearForm() {
    $("component").value = "";
    $("description").value = "";
    updateCharCounter();
    $("resultCard").style.display = "none";
}

// ============================================================================
// 4. NEURAL CLASSIFICATION & TRIAGE ENGINE
// ============================================================================
async function runClassification() {
    const description = $("description").value.trim();
    const component = $("component").value.trim();

    if (!description) {
        $("description").focus();
        alert("Please enter a defect description from the technical log.");
        return;
    }

    const btn = $("classifyBtn");
    btn.disabled = true;
    btn.classList.add("btn-loading");

    const payload = {
        description: description,
        component: component,
        reporter_name: state.reporter.name,
        badge_id: state.reporter.badge_id,
        role: state.reporter.role,
        station: state.reporter.station,
        aircraft_reg: state.reporter.aircraft_reg,
        flight_number: state.reporter.flight_number
    };

    try {
        const response = await fetch("/predict", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Server returned ${response.status}`);
        }

        const data = await response.json();
        renderResult(data);
        fetchIncidentHistory();
        setStep(3);
    } catch (err) {
        console.error("Classification failure:", err);
        alert(`Classification Error: ${err.message}`);
    } finally {
        btn.disabled = false;
        btn.classList.remove("btn-loading");
    }
}

// ============================================================================
// 5. RESULT RENDERING & SVG GAUGE
// ============================================================================
function renderResult(data) {
    const card = $("resultCard");
    const urgency = data.urgency;
    const config = URGENCY_CONFIG[urgency] || {
        key: "hazard",
        icon: "⚠️",
        title: urgency,
        directive: "Follow standard operational safety guidelines."
    };

    // Urgency level theme
    card.dataset.urgency = config.key;
    $("urgencyIcon").textContent = config.icon;
    $("urgencyTitle").textContent = config.title;
    $("actionDirective").textContent = config.directive;

    // Metadata & Ticket details
    $("ticketId").textContent = `#${data.ticket_id || "AERO-REC"}`;
    $("ticketTime").textContent = data.timestamp || new Date().toISOString();
    $("ticketReporter").innerHTML = `Logged by: <strong>${data.reporter?.name || state.reporter.name}</strong> (${data.reporter?.badge_id || state.reporter.badge_id})`;

    // Circular Gauge Animation (Circumference of r=50 is 2 * PI * 50 = ~314.16)
    const circumference = 314.16;
    const confidencePct = (data.confidence * 100);
    const gaugeCircle = $("gaugeCircle");

    gaugeCircle.style.strokeDashoffset = circumference;
    requestAnimationFrame(() => {
        const offset = circumference - (confidencePct / 100) * circumference;
        gaugeCircle.style.strokeDashoffset = offset;
    });

    animateCountUp($("confidenceValue"), confidencePct);

    // Confidence badge label
    const confBadge = $("confidenceBadge");
    if (data.low_confidence) {
        confBadge.textContent = "⚠️ Low Confidence — Manual Review Recommended";
        confBadge.style.color = "#fbbf24";
    } else {
        confBadge.textContent = "High Model Certainty";
        confBadge.style.color = "#94a3b8";
    }

    // Multi-Class Probability Bars
    renderProbabilityBars(data.probabilities, urgency);

    // Keywords chips
    renderKeywordChips(data.keywords);

    // Cleaned Text
    $("cleanedText").textContent = data.cleaned_text || "(No text preserved after preprocessing)";

    // Make visible and scroll
    card.style.display = "block";
    card.scrollIntoView({ behavior: "smooth", block: "start" });
}

function animateCountUp(element, target) {
    const duration = 1000;
    const start = performance.now();

    function step(now) {
        const elapsed = now - start;
        const progress = Math.min(elapsed / duration, 1);
        const easeOut = 1 - Math.pow(1 - progress, 3);
        const current = (target * easeOut).toFixed(1);
        element.textContent = `${current}%`;

        if (progress < 1) {
            requestAnimationFrame(step);
        }
    }
    requestAnimationFrame(step);
}

function renderProbabilityBars(probabilities, predictedClass) {
    const list = $("probList");
    list.innerHTML = "";

    if (!probabilities) return;

    // Sort descending by percentage
    const sorted = Object.entries(probabilities).sort((a, b) => b[1] - a[1]);

    sorted.forEach(([label, prob]) => {
        const pct = (prob * 100).toFixed(1);
        const isTop = label === predictedClass;
        const classKey = (URGENCY_CONFIG[label]?.key) || "routine";

        const row = document.createElement("div");
        row.className = `prob-row ${isTop ? "top" : ""}`;
        row.innerHTML = `
            <div class="prob-label-row">
                <span class="prob-name">${label} ${isTop ? "★" : ""}</span>
                <span class="prob-percent">${pct}%</span>
            </div>
            <div class="prob-track">
                <div class="prob-bar ${classKey}" style="width: 0%" data-target-width="${pct}%"></div>
            </div>
        `;
        list.appendChild(row);
    });

    // Animate bars on next frame
    requestAnimationFrame(() => {
        setTimeout(() => {
            document.querySelectorAll(".prob-bar").forEach(bar => {
                bar.style.width = bar.dataset.targetWidth;
            });
        }, 50);
    });
}

function renderKeywordChips(keywords) {
    const container = $("keywordChips");
    container.innerHTML = "";

    if (!keywords || keywords.length === 0) {
        container.innerHTML = '<span style="font-size: 12px; color: var(--text-muted);">No trained vocabulary tokens detected.</span>';
        return;
    }

    keywords.forEach(word => {
        const tag = document.createElement("span");
        tag.className = "keyword-tag";
        tag.textContent = word;
        container.appendChild(tag);
    });
}

// ============================================================================
// 6. INCIDENT REGISTRY & AUDIT MODAL
// ============================================================================
async function fetchIncidentHistory() {
    try {
        const res = await fetch("/incidents");
        if (res.ok) {
            const data = await res.json();
            state.incidentHistory = data.incidents || [];
            $("historyCount").textContent = state.incidentHistory.length;
            renderHistoryTable();
        }
    } catch (err) {
        console.warn("Could not fetch incidents history:", err);
    }
}

function renderHistoryTable() {
    const tbody = $("historyTableBody");
    tbody.innerHTML = "";

    if (state.incidentHistory.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="empty-table">No incidents recorded yet in this session.</td></tr>';
        return;
    }

    state.incidentHistory.forEach(item => {
        const urgencyKey = URGENCY_CONFIG[item.urgency]?.key || "routine";
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td><strong>#${item.ticket_id}</strong></td>
            <td>${item.timestamp}</td>
            <td>${item.reporter?.name || "N/A"}<br><small style="color: var(--text-muted);">${item.reporter?.badge_id || ""}</small></td>
            <td>${item.reporter?.aircraft_reg || "N/A"}</td>
            <td>${item.component}</td>
            <td><span class="table-badge ${urgencyKey}">${item.urgency}</span></td>
            <td><strong>${(item.confidence * 100).toFixed(1)}%</strong></td>
        `;
        tbody.appendChild(tr);
    });
}

async function clearIncidentRegistry() {
    if (!confirm("Are you sure you want to clear the incident registry?")) return;
    try {
        await fetch("/incidents", { method: "DELETE" });
        fetchIncidentHistory();
    } catch (err) {
        alert("Failed to clear registry");
    }
}

// ============================================================================
// 7. EVENT LISTENERS INITIALIZATION
// ============================================================================
document.addEventListener("DOMContentLoaded", () => {
    // 1. Clock & Telemetry
    try {
        updateZuluClock();
        setInterval(updateZuluClock, 1000);
    } catch (err) {
        console.error("Clock initialization error:", err);
    }

    try {
        fetchTelemetry();
        fetchIncidentHistory();
    } catch (err) {
        console.error("Telemetry error:", err);
    }

    // 2. Step 1: Reporter Form & Presets
    $("reporterForm")?.addEventListener("submit", saveReporterProfile);
    $("editReporterBtn")?.addEventListener("click", () => setStep(1));
    $("presetEngineer")?.addEventListener("click", () => populatePreset("engineer"));
    $("presetPilot")?.addEventListener("click", () => populatePreset("pilot"));

    // 3. Step 2: Diagnostics & Scenario Chips
    $("description")?.addEventListener("input", updateCharCounter);
    document.querySelector(".scenario-chips")?.addEventListener("click", handleScenarioChip);
    $("clearFormBtn")?.addEventListener("click", clearForm);
    $("classifyBtn")?.addEventListener("click", runClassification);

    // Keyboard shortcut (Ctrl+Enter or Cmd+Enter to classify)
    $("description")?.addEventListener("keydown", (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
            runClassification();
        }
    });

    // 4. Result Actions
    $("printReportBtn")?.addEventListener("click", () => window.print());
    $("logAnotherBtn")?.addEventListener("click", () => {
        $("description").value = "";
        $("component").value = "";
        updateCharCounter();
        $("resultCard").style.display = "none";
        setStep(2);
        $("defectCard")?.scrollIntoView({ behavior: "smooth" });
        $("description")?.focus();
    });

    // 5. History Modal
    $("openHistoryBtn")?.addEventListener("click", () => {
        renderHistoryTable();
        $("historyModal").style.display = "flex";
    });
    $("closeHistoryBtn")?.addEventListener("click", () => {
        $("historyModal").style.display = "none";
    });
    $("clearHistoryBtn")?.addEventListener("click", clearIncidentRegistry);
    $("historyModal")?.addEventListener("click", (e) => {
        if (e.target === $("historyModal")) {
            $("historyModal").style.display = "none";
        }
    });

    // Start on Step 1
    try {
        setStep(1);
    } catch (err) {
        console.error("setStep error:", err);
    }
});
