/**
 * Supersonic Atomizer GUI — vanilla JavaScript client (P25-T05)
 *
 * Architecture boundary (architecture.md B.7.2):
 *   - All solver logic stays server-side.
 *   - This file talks to the FastAPI REST API only.
 *   - Plots arrive as base64 PNG strings embedded in JSON.
 *   - Solver status is polled every 800 ms until completion.
 */

"use strict";

// ── State ─────────────────────────────────────────────────────────────────────
let activeCaseName = null;
let currentJobId   = null;
let pollTimer      = null;
let plotData       = {};   // field → base64 PNG
let csvContent     = "";
let tableRows      = [];

// ── Utilities ─────────────────────────────────────────────────────────────────
async function apiFetch(url, options = {}) {
  const res = await fetch(url, { credentials: "same-origin", ...options });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }
  return res.status === 204 ? null : res.json();
}

function showError(el, msg) {
  el.textContent = msg;
  el.classList.remove("hidden");
}

function hideError(el) {
  el.textContent = "";
  el.classList.add("hidden");
}

function setStatus(el, msg, cls) {
  el.textContent = msg;
  el.className = "solve-status " + (cls || "");
}

// ── Tab navigation ─────────────────────────────────────────────────────────────
document.querySelectorAll(".tab-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach(s => s.classList.add("hidden"));
    btn.classList.add("active");
    const id = "tab-" + btn.dataset.tab;
    document.getElementById(id).classList.remove("hidden");
  });
});

// ── Case management ────────────────────────────────────────────────────────────
async function loadCaseList() {
  const data = await apiFetch("/api/cases/");
  const ul = document.getElementById("case-list");
  ul.innerHTML = "";
  (data.cases || []).forEach(name => {
    const li = document.createElement("li");
    li.textContent = name;
    if (name === activeCaseName) li.classList.add("active");
    li.addEventListener("click", () => selectCase(name));
    ul.appendChild(li);
  });
}

async function selectCase(name) {
  activeCaseName = name;
  document.getElementById("active-case-label").textContent = `Active: ${name}`;
  document.querySelectorAll(".case-list li").forEach(li => {
    li.classList.toggle("active", li.textContent === name);
  });
  // Load the case config into the forms
  try {
    const cfg = await apiFetch(`/api/cases/${encodeURIComponent(name)}`);
    populateConditionsForm(cfg);
    populateGridForm(cfg);
  } catch (e) {
    console.warn("Failed to load case config:", e);
  }
}

document.getElementById("btn-new-case").addEventListener("click", async () => {
  const nameInput = document.getElementById("new-case-name");
  const name = nameInput.value.trim();
  const errEl = document.getElementById("case-error");
  if (!name) { showError(errEl, "Enter a case name."); return; }
  hideError(errEl);
  try {
    await apiFetch("/api/cases/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    });
    nameInput.value = "";
    await loadCaseList();
    await selectCase(name);
  } catch (e) {
    showError(errEl, e.message);
  }
});

document.getElementById("btn-refresh-cases").addEventListener("click", loadCaseList);

// ── Conditions form ─────────────────────────────────────────────────────────
function populateConditionsForm(cfg) {
  const f = document.getElementById("conditions-form");
  const bc = cfg.boundary_conditions || {};
  const fl = cfg.fluid || {};
  const di = cfg.droplet_injection || {};
  const ms = cfg.models || cfg.model_selection || {};

  setFieldValue(f, "working_fluid", fl.working_fluid || "air");
  setFieldValue(f, "inlet_wetness", fl.inlet_wetness ?? "");
  setFieldValue(f, "Pt_in", bc.Pt_in ?? "");
  setFieldValue(f, "Tt_in", bc.Tt_in ?? "");
  setFieldValue(f, "Ps_out", bc.Ps_out ?? "");
  setFieldValue(f, "droplet_velocity_in", di.droplet_velocity_in ?? "");
  setFieldValue(f, "droplet_diameter_mean_in", di.droplet_diameter_mean_in ?? "");
  setFieldValue(f, "droplet_diameter_max_in", di.droplet_diameter_max_in ?? "");
  setFieldValue(f, "critical_weber_number", ms.critical_weber_number ?? "");
  setFieldValue(f, "breakup_factor_mean", ms.breakup_factor_mean ?? "");
  setFieldValue(f, "breakup_factor_max", ms.breakup_factor_max ?? "");
}

function setFieldValue(form, name, value) {
  const el = form.elements[name];
  if (el) el.value = value;
}

function readConditionsForm() {
  const f = document.getElementById("conditions-form");
  const fl = f.elements.working_fluid.value;
  const wetness = parseFloat(f.elements.inlet_wetness.value);
  const cfg = {
    fluid: { working_fluid: fl },
    boundary_conditions: {
      Pt_in:  parseFloat(f.elements.Pt_in.value),
      Tt_in:  parseFloat(f.elements.Tt_in.value),
      Ps_out: parseFloat(f.elements.Ps_out.value),
    },
    droplet_injection: {
      droplet_velocity_in:      parseFloat(f.elements.droplet_velocity_in.value),
      droplet_diameter_mean_in: parseFloat(f.elements.droplet_diameter_mean_in.value),
      droplet_diameter_max_in:  parseFloat(f.elements.droplet_diameter_max_in.value),
    },
    models: {
      breakup_model:         "weber_critical",
      critical_weber_number: parseFloat(f.elements.critical_weber_number.value),
      breakup_factor_mean:   parseFloat(f.elements.breakup_factor_mean.value),
      breakup_factor_max:    parseFloat(f.elements.breakup_factor_max.value),
    },
  };
  if (!isNaN(wetness)) cfg.fluid.inlet_wetness = wetness;
  return cfg;
}

document.getElementById("btn-save-conditions").addEventListener("click", async () => {
  if (!activeCaseName) { alert("Select or create a case first."); return; }
  const statusEl = document.getElementById("conditions-status");
  try {
    const condCfg = readConditionsForm();
    // Merge with existing grid config
    const existing = await apiFetch(`/api/cases/${encodeURIComponent(activeCaseName)}`);
    const merged = { ...existing, ...condCfg };
    await apiFetch(`/api/cases/${encodeURIComponent(activeCaseName)}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(merged),
    });
    statusEl.textContent = "✓ Saved";
    setTimeout(() => { statusEl.textContent = ""; }, 2000);
  } catch (e) {
    statusEl.textContent = "Error: " + e.message;
    statusEl.style.color = "#c62828";
  }
});

// ── Grid form ───────────────────────────────────────────────────────────────
function populateGridForm(cfg) {
  const f = document.getElementById("grid-form");
  const geo = cfg.geometry || {};
  setFieldValue(f, "x_start", geo.x_start ?? 0);
  setFieldValue(f, "x_end", geo.x_end ?? 0.1);
  setFieldValue(f, "n_cells", geo.n_cells ?? 100);

  const tbody = document.getElementById("area-table-body");
  tbody.innerHTML = "";
  const areaDist = geo.area_distribution || {};
  const xs = areaDist.x || [];
  const As = areaDist.A || [];
  if (xs.length === 0) {
    addAreaRow(0.0, 1e-4);
    addAreaRow(0.05, 6e-5);
    addAreaRow(0.1, 5e-5);
  } else {
    xs.forEach((x, i) => addAreaRow(x, As[i] ?? ""));
  }
  updateAreaPreview();
}

function addAreaRow(x, A) {
  const tbody = document.getElementById("area-table-body");
  const tr = document.createElement("tr");
  tr.innerHTML = `
    <td><input type="number" step="any" value="${x ?? ""}" class="area-x-input" /></td>
    <td><input type="number" step="any" value="${A ?? ""}" class="area-A-input" /></td>
    <td><button class="del-row-btn" title="Delete row">✕</button></td>
  `;
  tr.querySelector(".del-row-btn").addEventListener("click", () => {
    tr.remove();
    updateAreaPreview();
  });
  tr.querySelectorAll("input").forEach(inp => inp.addEventListener("input", updateAreaPreview));
  tbody.appendChild(tr);
}

document.getElementById("btn-add-area-row").addEventListener("click", () => {
  addAreaRow("", "");
  updateAreaPreview();
});

function readAreaTable() {
  const xs = [], As = [];
  document.querySelectorAll("#area-table-body tr").forEach(tr => {
    const xVal = parseFloat(tr.querySelector(".area-x-input").value);
    const AVal = parseFloat(tr.querySelector(".area-A-input").value);
    if (!isNaN(xVal) && !isNaN(AVal)) { xs.push(xVal); As.push(AVal); }
  });
  return { x: xs, A: As };
}

function updateAreaPreview() {
  const errEl = document.getElementById("area-table-error");
  const { x, A } = readAreaTable();
  if (x.length < 2) { hideError(errEl); drawAreaPreview([], []); return; }
  const invalid = A.some(a => a <= 0);
  if (invalid) { showError(errEl, "Area values must be positive."); }
  else { hideError(errEl); }
  drawAreaPreview(x, A);
}

function drawAreaPreview(xs, As) {
  const canvas = document.getElementById("area-preview-canvas");
  const ctx = canvas.getContext("2d");
  const W = canvas.width, H = canvas.height;
  ctx.clearRect(0, 0, W, H);
  if (xs.length < 2) return;

  const pad = 30;
  const xMin = Math.min(...xs), xMax = Math.max(...xs);
  const AMin = Math.min(...As), AMax = Math.max(...As);
  const xRange = xMax - xMin || 1, ARange = AMax - AMin || 1;

  const toCanvasX = x => pad + (x - xMin) / xRange * (W - 2 * pad);
  const toCanvasY = A => (H - pad) - (A - AMin) / ARange * (H - 2 * pad);

  ctx.beginPath();
  ctx.strokeStyle = "#3a78b5";
  ctx.lineWidth = 2;
  ctx.moveTo(toCanvasX(xs[0]), toCanvasY(As[0]));
  for (let i = 1; i < xs.length; i++) ctx.lineTo(toCanvasX(xs[i]), toCanvasY(As[i]));
  ctx.stroke();

  // Axes labels
  ctx.fillStyle = "#666";
  ctx.font = "11px system-ui";
  ctx.textAlign = "center";
  ctx.fillText(`x = ${xMin.toExponential(2)}`, toCanvasX(xMin), H - 4);
  ctx.fillText(`x = ${xMax.toExponential(2)}`, toCanvasX(xMax), H - 4);
  ctx.textAlign = "right";
  ctx.fillText(`A = ${AMax.toExponential(2)}`, pad - 2, toCanvasY(AMax) + 4);
}

function readGridForm() {
  const f = document.getElementById("grid-form");
  const area = readAreaTable();
  return {
    geometry: {
      x_start: parseFloat(f.elements.x_start.value),
      x_end:   parseFloat(f.elements.x_end.value),
      n_cells: parseInt(f.elements.n_cells.value, 10),
      area_distribution: { type: "table", ...area },
    },
  };
}

document.getElementById("btn-save-grid").addEventListener("click", async () => {
  if (!activeCaseName) { alert("Select or create a case first."); return; }
  const statusEl = document.getElementById("grid-status");
  try {
    const gridCfg = readGridForm();
    const existing = await apiFetch(`/api/cases/${encodeURIComponent(activeCaseName)}`);
    const merged = { ...existing, ...gridCfg };
    await apiFetch(`/api/cases/${encodeURIComponent(activeCaseName)}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(merged),
    });
    statusEl.textContent = "✓ Saved";
    setTimeout(() => { statusEl.textContent = ""; }, 2000);
  } catch (e) {
    statusEl.textContent = "Error: " + e.message;
    statusEl.style.color = "#c62828";
  }
});

// ── Solve tab ───────────────────────────────────────────────────────────────
const btnRun       = document.getElementById("btn-run");
const solveStatus  = document.getElementById("solve-status");
const solveProgress = document.getElementById("solve-progress");

btnRun.addEventListener("click", async () => {
  if (!activeCaseName) { alert("Select or create a case first."); return; }
  btnRun.disabled = true;
  solveProgress.classList.remove("hidden");
  setStatus(solveStatus, "Starting simulation…");

  try {
    const data = await apiFetch("/api/simulation/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ case_name: activeCaseName }),
    });
    currentJobId = data.job_id;
    startPolling(currentJobId);
  } catch (e) {
    onRunFailed("Failed to start simulation: " + e.message);
  }
});

function startPolling(jobId) {
  if (pollTimer) clearInterval(pollTimer);
  pollTimer = setInterval(async () => {
    try {
      const data = await apiFetch(`/api/simulation/status/${encodeURIComponent(jobId)}`);
      if (data.status === "completed") {
        clearInterval(pollTimer);
        pollTimer = null;
        await onRunCompleted(jobId);
      } else if (data.status === "failed") {
        clearInterval(pollTimer);
        pollTimer = null;
        onRunFailed("Simulation failed: " + (data.error || "unknown error"));
      } else {
        setStatus(solveStatus, "Solver running…");
      }
    } catch (e) {
      clearInterval(pollTimer);
      pollTimer = null;
      onRunFailed("Status poll error: " + e.message);
    }
  }, 800);
}

async function onRunCompleted(jobId) {
  solveProgress.classList.add("hidden");
  setStatus(solveStatus, "✓ Simulation completed successfully.", "success");
  btnRun.disabled = false;

  try {
    const data = await apiFetch(`/api/simulation/result/${encodeURIComponent(jobId)}`);
    plotData   = data.plots || {};
    tableRows  = data.table_rows || [];
    csvContent = data.csv || "";
    const fields = data.plot_fields || Object.keys(plotData);
    renderPlots(fields);
    renderTable(tableRows);
    document.getElementById("btn-download-csv").disabled = false;
  } catch (e) {
    setStatus(solveStatus, "Run completed but failed to fetch results: " + e.message, "failure");
  }
}

function onRunFailed(msg) {
  solveProgress.classList.add("hidden");
  setStatus(solveStatus, msg, "failure");
  btnRun.disabled = false;
}

// ── Post tab 1: Graphs ─────────────────────────────────────────────────────
function renderPlots(fields) {
  // Build checkboxes
  const cbContainer = document.getElementById("plot-checkboxes");
  cbContainer.innerHTML = "";
  fields.forEach(field => {
    const label = document.createElement("label");
    const cb = document.createElement("input");
    cb.type = "checkbox";
    cb.checked = true;
    cb.dataset.field = field;
    cb.addEventListener("change", refreshVisiblePlots);
    label.appendChild(cb);
    label.appendChild(document.createTextNode(" " + field.replace(/_/g, " ")));
    cbContainer.appendChild(label);
  });
  refreshVisiblePlots();
}

function refreshVisiblePlots() {
  const container = document.getElementById("plot-container");
  container.innerHTML = "";
  document.querySelectorAll("#plot-checkboxes input[type=checkbox]").forEach(cb => {
    if (!cb.checked) return;
    const field = cb.dataset.field;
    const b64 = plotData[field];
    if (!b64) return;
    const card = document.createElement("div");
    card.className = "plot-card";
    const img = document.createElement("img");
    img.src = "data:image/png;base64," + b64;
    img.alt = field;
    card.appendChild(img);
    container.appendChild(card);
  });
}

// ── Post tab 2: Table ──────────────────────────────────────────────────────
function renderTable(rows) {
  const thead = document.getElementById("result-table-head");
  const tbody = document.getElementById("result-table-body");
  thead.innerHTML = "";
  tbody.innerHTML = "";
  if (!rows || rows.length === 0) return;

  const headers = Object.keys(rows[0]);
  const trHead = document.createElement("tr");
  headers.forEach(h => {
    const th = document.createElement("th");
    th.textContent = h;
    trHead.appendChild(th);
  });
  thead.appendChild(trHead);

  rows.forEach(row => {
    const tr = document.createElement("tr");
    headers.forEach(h => {
      const td = document.createElement("td");
      const val = row[h];
      td.textContent = (typeof val === "number") ? val.toPrecision(5) : String(val);
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
}

document.getElementById("btn-download-csv").addEventListener("click", () => {
  if (!csvContent) return;
  const blob = new Blob([csvContent], { type: "text/csv" });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement("a");
  a.href     = url;
  a.download = (activeCaseName || "result") + ".csv";
  a.click();
  URL.revokeObjectURL(url);
});

// ── Settings tab: unit preferences ────────────────────────────────────────
async function loadUnitGroups() {
  try {
    const groups  = await apiFetch("/api/units/groups");
    const current = await apiFetch("/api/units/preferences");
    const container = document.getElementById("unit-group-controls");
    container.innerHTML = "";
    Object.entries(groups).forEach(([group, options]) => {
      const row = document.createElement("div");
      row.className = "unit-group-row";
      const label = document.createElement("label");
      label.textContent = group;
      const sel = document.createElement("select");
      sel.id = "unit-sel-" + group;
      sel.dataset.group = group;
      options.forEach(opt => {
        const option = document.createElement("option");
        option.value = opt;
        option.textContent = opt;
        if (opt === current[group]) option.selected = true;
        sel.appendChild(option);
      });
      row.appendChild(label);
      row.appendChild(sel);
      container.appendChild(row);
    });
  } catch (e) {
    console.warn("Failed to load unit groups:", e);
  }
}

document.getElementById("btn-save-units").addEventListener("click", async () => {
  const updates = {};
  document.querySelectorAll("[id^='unit-sel-']").forEach(sel => {
    updates[sel.dataset.group] = sel.value;
  });
  const statusEl = document.getElementById("units-status");
  try {
    await apiFetch("/api/units/preferences", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(updates),
    });
    statusEl.textContent = "✓ Units applied (re-run to update plots)";
    setTimeout(() => { statusEl.textContent = ""; }, 3000);
  } catch (e) {
    statusEl.textContent = "Error: " + e.message;
  }
});

// ── Initialisation ─────────────────────────────────────────────────────────
(async function init() {
  await loadCaseList();
  await loadUnitGroups();
})();
