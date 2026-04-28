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
const MULTI_VALUE_SPLIT_RE = /[\s,;，、]+/;

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

function splitNumericTokens(rawValue) {
  if (rawValue === null || rawValue === undefined) return [];
  const text = String(rawValue).trim();
  if (!text) return [];
  return text.split(MULTI_VALUE_SPLIT_RE).filter(Boolean);
}

function parseSingleNumericValue(rawValue, label, { optional = false } = {}) {
  const tokens = splitNumericTokens(rawValue);
  if (tokens.length === 0) {
    if (optional) return null;
    throw new Error(`${label} is required.`);
  }
  // Allow multiple tokens in the input but when saving a case use the first
  // numeric token. The UI still encourages using the Solve button for
  // multi-value sweeps. This avoids blocking users who accidentally click
  // Save after entering a sweep list.
  if (tokens.length > 1) {
    console.warn(`${label}: multiple values provided; saving will use the first value (${tokens[0]}). Use Solve to run a sweep.`);
  }
  const value = Number(tokens[0]);
  if (Number.isNaN(value)) {
    throw new Error(`${label} must be numeric.`);
  }
  return value;
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
    // Try to load the most recent completed simulation result for this case
    try {
      const last = await apiFetch(`/api/cases/${encodeURIComponent(name)}/last_result`);
      plotData = last.plots || {};
      tableRows = last.table_rows || [];
      csvContent = last.csv || "";
      const fields = last.plot_fields || Object.keys(plotData);
      renderPlots(fields);
      renderTable(tableRows);
      document.getElementById("btn-download-csv").disabled = !csvContent;
    } catch (_e) {
      // No previous result for this case — clear any existing post-tab content
      plotData = {};
      tableRows = [];
      csvContent = "";
      renderPlots([]);
      renderTable([]);
      document.getElementById("btn-download-csv").disabled = true;
    }
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

// Default values for each breakup model — kept in sync with config/defaults.py
const MODEL_DEFAULTS = {
  weber_critical: {
    critical_weber_number: 12,
    breakup_factor_mean:   0.5,
    breakup_factor_max:    0.5,
  },
  bag_stripping: {
    critical_weber_number: 12,
  },
  khrt: {
    khrt_B0:          0.61,
    khrt_B1:          40.0,
    khrt_Crt:         0.1,
    liquid_density:   998.2,
    liquid_viscosity: 1.002e-3,
  },
};

// Fill any empty numeric field in the conditions-form with a default value.
function applyModelDefaults(model) {
  const f = document.getElementById("conditions-form");
  const defaults = MODEL_DEFAULTS[model] || {};
  for (const [fieldName, defaultVal] of Object.entries(defaults)) {
    const el = f.elements[fieldName];
    if (!el) continue;
    if (el.value.trim() === "") {
      el.value = defaultVal;
    }
  }
}

function updateBreakupModelState(model) {
  const weberRow  = document.getElementById("breakup-critical-weber-row");
  const weberSection = document.getElementById("breakup-params-weber");
  const khrtSection  = document.getElementById("breakup-params-khrt");
  if (model === "khrt") {
    weberRow.classList.add("hidden");
    weberSection.classList.add("hidden");
    khrtSection.classList.remove("hidden");
  } else if (model === "bag_stripping") {
    weberRow.classList.remove("hidden");
    weberSection.classList.add("hidden");
    khrtSection.classList.add("hidden");
  } else {
    // weber_critical
    weberRow.classList.remove("hidden");
    weberSection.classList.remove("hidden");
    khrtSection.classList.add("hidden");
  }
  applyModelDefaults(model);
}

function showBreakupModelHelp() {
  const dialog = document.getElementById("breakup-model-help-dialog");
  if (!dialog) return;
  if (typeof dialog.showModal === "function") {
    if (!dialog.open) {
      dialog.showModal();
    }
    return;
  }
  dialog.setAttribute("open", "open");
}

function closeBreakupModelHelp() {
  const dialog = document.getElementById("breakup-model-help-dialog");
  if (!dialog) return;
  if (typeof dialog.close === "function") {
    if (dialog.open) {
      dialog.close();
    }
    return;
  }
  dialog.removeAttribute("open");
}

function initializeBreakupHelpDialog() {
  const openButton = document.getElementById("breakup-model-help-btn");
  const closeButton = document.getElementById("breakup-model-help-close");
  const dialog = document.getElementById("breakup-model-help-dialog");
  if (!openButton || !closeButton || !dialog) return;

  openButton.addEventListener("click", showBreakupModelHelp);
  closeButton.addEventListener("click", closeBreakupModelHelp);

  dialog.addEventListener("cancel", event => {
    event.preventDefault();
    closeBreakupModelHelp();
  });

  dialog.addEventListener("click", event => {
    const rect = dialog.getBoundingClientRect();
    const clickedBackdrop =
      event.clientX < rect.left ||
      event.clientX > rect.right ||
      event.clientY < rect.top ||
      event.clientY > rect.bottom;
    if (clickedBackdrop) {
      closeBreakupModelHelp();
    }
  });
}

function updateInletWetnessState(fluidValue) {
  const f = document.getElementById("conditions-form");
  const input = f.elements.inlet_wetness;
  if (!input) return;
  const isSteam = (fluidValue || "").toLowerCase() === "steam";
  input.disabled = !isSteam;
  if (!isSteam) input.value = "";
}

function populateConditionsForm(cfg) {
  const f = document.getElementById("conditions-form");
  const bc = cfg.boundary_conditions || {};
  const fl = cfg.fluid || {};
  const di = cfg.droplet_injection || {};
  const ms = cfg.models || cfg.model_selection || {};

  const workingFluid = fl.working_fluid || "air";
  setFieldValue(f, "working_fluid", workingFluid);
  updateInletWetnessState(workingFluid);
  setFieldValue(f, "inlet_wetness", fl.inlet_wetness ?? "");
  setFieldValue(f, "Pt_in", bc.Pt_in ?? "");
  setFieldValue(f, "Tt_in", bc.Tt_in ?? "");
  setFieldValue(f, "Ps_out", bc.Ps_out ?? "");
  setFieldValue(f, "droplet_velocity_in", di.droplet_velocity_in ?? "");
  setFieldValue(f, "water_mass_flow_rate", di.water_mass_flow_rate ?? "");
  setFieldValue(f, "water_mass_flow_rate_percent", di.water_mass_flow_rate_percent ?? "");
  const hasKgPerS = di.water_mass_flow_rate !== undefined && di.water_mass_flow_rate !== null && String(di.water_mass_flow_rate) !== "";
  const hasPercent = di.water_mass_flow_rate_percent !== undefined && di.water_mass_flow_rate_percent !== null && String(di.water_mass_flow_rate_percent) !== "";
  setFieldValue(
    f,
    "water_mass_flow_mode",
    hasPercent && !hasKgPerS ? "percent" : "kg_per_s"
  );
  setFieldValue(f, "droplet_diameter_mean_in", di.droplet_diameter_mean_in ?? "");
  setFieldValue(f, "droplet_diameter_max_in", di.droplet_diameter_max_in ?? "");
  setFieldValue(f, "coupling_mode", ms.coupling_mode ?? "one_way");
  const breakupModel = ms.breakup_model || "weber_critical";
  setFieldValue(f, "breakup_model", breakupModel);
  updateBreakupModelState(breakupModel);
  // Use stored values when present; fall back to model defaults so fields are
  // never blank after selecting a model.
  const wd = MODEL_DEFAULTS.weber_critical;
  const kd = MODEL_DEFAULTS.khrt;
  setFieldValue(f, "critical_weber_number", ms.critical_weber_number ?? wd.critical_weber_number);
  setFieldValue(f, "breakup_factor_mean",   ms.breakup_factor_mean   ?? wd.breakup_factor_mean);
  setFieldValue(f, "breakup_factor_max",    ms.breakup_factor_max    ?? wd.breakup_factor_max);
  setFieldValue(f, "khrt_B0",          ms.khrt_B0          ?? kd.khrt_B0);
  setFieldValue(f, "khrt_B1",          ms.khrt_B1          ?? kd.khrt_B1);
  setFieldValue(f, "khrt_Crt",         ms.khrt_Crt         ?? kd.khrt_Crt);
  setFieldValue(f, "liquid_density",   ms.liquid_density   ?? kd.liquid_density);
  setFieldValue(f, "liquid_viscosity", ms.liquid_viscosity ?? kd.liquid_viscosity);
}

function setFieldValue(form, name, value) {
  const el = form.elements[name];
  if (!el) return;
  if (Array.isArray(value)) {
    // display arrays as space-separated tokens for readability
    el.value = value.join(" ");
  } else {
    el.value = value;
  }
}

function mergeCaseConfigs(baseCfg = {}, overrideCfg = {}) {
  // Preserve existing nested sections (e.g., droplet_injection.water_mass_flow_rate)
  // when override payloads only include a subset of fields.
  return {
    ...baseCfg,
    ...overrideCfg,
    fluid: {
      ...(baseCfg.fluid || {}),
      ...(overrideCfg.fluid || {}),
    },
    boundary_conditions: {
      ...(baseCfg.boundary_conditions || {}),
      ...(overrideCfg.boundary_conditions || {}),
    },
    droplet_injection: {
      ...(baseCfg.droplet_injection || {}),
      ...(overrideCfg.droplet_injection || {}),
    },
    models: {
      ...(baseCfg.models || {}),
      ...(overrideCfg.models || {}),
    },
    geometry: {
      ...(baseCfg.geometry || {}),
      ...(overrideCfg.geometry || {}),
    },
    outputs: {
      ...(baseCfg.outputs || {}),
      ...(overrideCfg.outputs || {}),
    },
  };
}

function assertTwoWayMassFlowRequirement(cfg) {
  const couplingMode = cfg?.models?.coupling_mode;
  if (couplingMode !== "two_way_approx" && couplingMode !== "two_way_coupled") {
    return;
  }
  const mfr = cfg?.droplet_injection?.water_mass_flow_rate;
  const mfrPercent = cfg?.droplet_injection?.water_mass_flow_rate_percent;
  const hasMfr = !(mfr === undefined || mfr === null || String(mfr).trim() === "");
  const hasPercent = !(mfrPercent === undefined || mfrPercent === null || String(mfrPercent).trim() === "");
  if (!hasMfr && !hasPercent) {
    throw new Error(
      "Water mass flow is required for two-way modes. Provide either [kg/s] or [% of gas mass flow]."
    );
  }
}


function parseNumericOrList(rawValue, label, { optional = false } = {}) {
  // Accept a space/comma/semicolon separated list or a single numeric value.
  // Returns a Number if single token, or an Array<Number> if multiple tokens,
  // or null if optional and empty.
  if (rawValue === null || rawValue === undefined) {
    if (optional) return null;
    throw new Error(`${label} is required.`);
  }
  const tokens = splitNumericTokens(rawValue);
  if (tokens.length === 0) {
    if (optional) return null;
    throw new Error(`${label} is required.`);
  }
  const nums = tokens.map(t => {
    const v = Number(t);
    if (Number.isNaN(v)) throw new Error(`${label} must be numeric.`);
    return v;
  });
  return nums.length === 1 ? nums[0] : nums;
}

function readConditionsFormForRun() {
  const f = document.getElementById("conditions-form");
  const fl = f.elements.working_fluid.value;
  const couplingMode = f.elements.coupling_mode.value;
  const cfg = {
    fluid: { working_fluid: fl },
    boundary_conditions: {
      Pt_in:  parseNumericOrList(f.elements.Pt_in.value, "Inlet total pressure P₀ [Pa]"),
      Tt_in:  parseNumericOrList(f.elements.Tt_in.value, "Inlet total temperature T₀ [K]"),
      Ps_out: parseNumericOrList(f.elements.Ps_out.value, "Outlet static pressure P₂ [Pa]"),
    },
    droplet_injection: {
      droplet_velocity_in:      parseNumericOrList(f.elements.droplet_velocity_in.value, "Initial droplet velocity [m/s]"),
      droplet_diameter_mean_in: parseNumericOrList(f.elements.droplet_diameter_mean_in.value, "Mean droplet diameter [m]"),
      droplet_diameter_max_in:  parseNumericOrList(f.elements.droplet_diameter_max_in.value, "Maximum droplet diameter [m]"),
    },
    models: {
      coupling_mode:         couplingMode,
      breakup_model:         f.elements.breakup_model.value,
      critical_weber_number: parseNumericOrList(f.elements.critical_weber_number.value, "Critical Weber number", { optional: true }),
      breakup_factor_mean:   parseNumericOrList(f.elements.breakup_factor_mean.value, "Breakup factor — mean diameter", { optional: true }),
      breakup_factor_max:    parseNumericOrList(f.elements.breakup_factor_max.value, "Breakup factor — maximum diameter", { optional: true }),
      khrt_B0:               parseNumericOrList(f.elements.khrt_B0.value, "KH wavelength coefficient B₀", { optional: true }),
      khrt_B1:               parseNumericOrList(f.elements.khrt_B1.value, "KH breakup time coefficient B₁", { optional: true }),
      khrt_Crt:              parseNumericOrList(f.elements.khrt_Crt.value, "RT wavelength coefficient C_RT", { optional: true }),
      liquid_density:        parseNumericOrList(f.elements.liquid_density.value, "Liquid density [kg/m³]", { optional: true }),
      liquid_viscosity:      parseNumericOrList(f.elements.liquid_viscosity.value, "Liquid viscosity [Pa·s]", { optional: true }),
    },
  };
  const wetness = parseNumericOrList(f.elements.inlet_wetness.value, "Inlet wetness", { optional: true });
  cfg.fluid.inlet_wetness = wetness === null ? null : wetness;
  const waterMassFlowMode = f.elements.water_mass_flow_mode.value;
  const waterMassFlowRate = parseNumericOrList(f.elements.water_mass_flow_rate.value, "Water mass flow rate [kg/s]", { optional: true });
  const waterMassFlowRatePercent = parseNumericOrList(f.elements.water_mass_flow_rate_percent.value, "Water mass flow rate [% of gas]", { optional: true });
  if (waterMassFlowMode === "percent") {
    cfg.droplet_injection.water_mass_flow_rate = null;
    if (waterMassFlowRatePercent !== null) {
      cfg.droplet_injection.water_mass_flow_rate_percent = waterMassFlowRatePercent;
    }
  } else {
    cfg.droplet_injection.water_mass_flow_rate_percent = null;
    if (waterMassFlowRate !== null) {
      cfg.droplet_injection.water_mass_flow_rate = waterMassFlowRate;
    }
  }
  return cfg;
}

function readConditionsFormForSave() {
  const f = document.getElementById("conditions-form");
  const couplingMode = f.elements.coupling_mode.value;
  const cfg = {
    fluid: { working_fluid: f.elements.working_fluid.value },
    boundary_conditions: {
      Pt_in: parseNumericOrList(f.elements.Pt_in.value, "Inlet total pressure P₀ [Pa]"),
      Tt_in: parseNumericOrList(f.elements.Tt_in.value, "Inlet total temperature T₀ [K]"),
      Ps_out: parseNumericOrList(f.elements.Ps_out.value, "Outlet static pressure P₂ [Pa]"),
    },
    droplet_injection: {
      droplet_velocity_in: parseNumericOrList(f.elements.droplet_velocity_in.value, "Initial droplet velocity [m/s]"),
      droplet_diameter_mean_in: parseNumericOrList(f.elements.droplet_diameter_mean_in.value, "Mean droplet diameter [m]"),
      droplet_diameter_max_in: parseNumericOrList(f.elements.droplet_diameter_max_in.value, "Maximum droplet diameter [m]"),
    },
    models: {
      coupling_mode: couplingMode,
      breakup_model: f.elements.breakup_model.value,
      critical_weber_number: parseNumericOrList(f.elements.critical_weber_number.value, "Critical Weber number", { optional: true }),
      breakup_factor_mean: parseNumericOrList(f.elements.breakup_factor_mean.value, "Breakup factor — mean diameter", { optional: true }),
      breakup_factor_max: parseNumericOrList(f.elements.breakup_factor_max.value, "Breakup factor — maximum diameter", { optional: true }),
      khrt_B0: parseNumericOrList(f.elements.khrt_B0.value, "KH wavelength coefficient B₀", { optional: true }),
      khrt_B1: parseNumericOrList(f.elements.khrt_B1.value, "KH breakup time coefficient B₁", { optional: true }),
      khrt_Crt: parseNumericOrList(f.elements.khrt_Crt.value, "RT wavelength coefficient C_RT", { optional: true }),
      liquid_density: parseNumericOrList(f.elements.liquid_density.value, "Liquid density [kg/m³]", { optional: true }),
      liquid_viscosity: parseNumericOrList(f.elements.liquid_viscosity.value, "Liquid viscosity [Pa·s]", { optional: true }),
    },
  };
  const wetness = parseNumericOrList(f.elements.inlet_wetness.value, "Inlet wetness", { optional: true });
  cfg.fluid.inlet_wetness = wetness; // null when cleared — overrides stale base value in merge
  const waterMassFlowMode = f.elements.water_mass_flow_mode.value;
  const waterMassFlowRate = parseNumericOrList(
    f.elements.water_mass_flow_rate.value,
    "Water mass flow rate [kg/s]",
    { optional: true },
  );
  const waterMassFlowRatePercent = parseNumericOrList(
    f.elements.water_mass_flow_rate_percent.value,
    "Water mass flow rate [% of gas]",
    { optional: true },
  );
  if (waterMassFlowMode === "percent") {
    cfg.droplet_injection.water_mass_flow_rate = null;
    if (waterMassFlowRatePercent !== null) {
      cfg.droplet_injection.water_mass_flow_rate_percent = waterMassFlowRatePercent;
    }
  } else {
    cfg.droplet_injection.water_mass_flow_rate_percent = null;
    if (waterMassFlowRate !== null) {
      cfg.droplet_injection.water_mass_flow_rate = waterMassFlowRate;
    }
  }
  return cfg;
}

async function buildRunConfigSnapshot() {
  const current = { ...readConditionsFormForRun(), ...readGridForm() };
  try {
    const existing = await apiFetch(`/api/cases/${encodeURIComponent(activeCaseName)}`);
    const merged = mergeCaseConfigs(existing, current);
    assertTwoWayMassFlowRequirement(merged);
    return merged;
  } catch (_e) {
    assertTwoWayMassFlowRequirement(current);
    return current;
  }
}

document.getElementById("btn-save-conditions").addEventListener("click", async () => {
  if (!activeCaseName) { alert("Select or create a case first."); return; }
  const statusEl = document.getElementById("conditions-status");
  try {
    const condCfg = readConditionsFormForSave();
    // Merge with existing grid config
    const existing = await apiFetch(`/api/cases/${encodeURIComponent(activeCaseName)}`);
    const merged = mergeCaseConfigs(existing, condCfg);
    await apiFetch(`/api/cases/${encodeURIComponent(activeCaseName)}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(merged),
    });
    statusEl.textContent = "✓ Saved";
    statusEl.style.color = "";
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
  // Support both current key (n_cells) and legacy key (num_cells).
  setFieldValue(f, "n_cells", geo.n_cells ?? geo.num_cells ?? 100);

  const tbody = document.getElementById("area-table-body");
  tbody.innerHTML = "";

  // Resolve area data from either the current schema (area_distribution) or the
  // legacy schema (area_table: [{x, A}, ...]).
  let xs = [];
  let As = [];
  const areaDist = geo.area_distribution;
  if (areaDist && Array.isArray(areaDist.x) && areaDist.x.length > 0) {
    xs = areaDist.x;
    As = areaDist.A || [];
  } else if (Array.isArray(geo.area_table) && geo.area_table.length > 0) {
    // Legacy format: [{x: ..., A: ...}, ...]
    geo.area_table.forEach(row => {
      xs.push(row.x);
      As.push(row.A);
    });
  }

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
  const xStart = parseFloat(f.elements.x_start.value);
  const xEnd = parseFloat(f.elements.x_end.value);
  // Ensure area table endpoints include x_start and x_end. If the user
  // provided a table that doesn't include them, prepend/append entries
  // copying the nearest A value so the solver receives matching endpoints.
  const xs = Array.isArray(area.x) ? area.x.slice() : [];
  const As = Array.isArray(area.A) ? area.A.slice() : [];
  const epsilon = 1e-12;
  if (xs.length === 0) {
    xs.push(xStart, xEnd);
    As.push(1e-4, 1e-4);
  } else {
    if (Math.abs(xs[0] - xStart) > epsilon) {
      const firstA = (As.length > 0 ? As[0] : 1e-4);
      xs.unshift(xStart);
      As.unshift(firstA);
    }
    if (Math.abs(xs[xs.length - 1] - xEnd) > epsilon) {
      const lastA = (As.length > 0 ? As[As.length - 1] : 1e-4);
      xs.push(xEnd);
      As.push(lastA);
    }
  }

  return {
    geometry: {
      x_start: xStart,
      x_end:   xEnd,
      n_cells: parseInt(f.elements.n_cells.value, 10),
      area_distribution: { type: "table", x: xs, A: As },
    },
  };
}

document.getElementById("btn-save-grid").addEventListener("click", async () => {
  if (!activeCaseName) { alert("Select or create a case first."); return; }
  const statusEl = document.getElementById("grid-status");
  try {
    const gridCfg = readGridForm();
    const existing = await apiFetch(`/api/cases/${encodeURIComponent(activeCaseName)}`);
    const merged = mergeCaseConfigs(existing, gridCfg);
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
    const runConfig = await buildRunConfigSnapshot();
    const data = await apiFetch("/api/simulation/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ case_name: activeCaseName, config: runConfig }),
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
  btnRun.disabled = false;

  try {
    const data = await apiFetch(`/api/simulation/result/${encodeURIComponent(jobId)}`);
    plotData   = data.plots || {};
    tableRows  = data.table_rows || [];
    csvContent = data.csv || "";
    const fields = data.plot_fields || Object.keys(plotData);
    const runCount = data.run_count || 1;
    const statusMessage = runCount > 1
      ? `✓ Simulation sweep completed successfully (${runCount} runs).`
      : "✓ Simulation completed successfully.";
    setStatus(solveStatus, statusMessage, "success");
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

initializeBreakupHelpDialog();

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
