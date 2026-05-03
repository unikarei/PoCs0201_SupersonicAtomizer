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
let activeProjectName = null;
let activeCaseName = null;
let defaultProjectName = "default";
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

async function apiFetchText(url, options = {}) {
  const res = await fetch(url, { credentials: "same-origin", ...options });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }
  return res.text();
}

async function apiFetchBlob(url, options = {}) {
  const res = await fetch(url, { credentials: "same-origin", ...options });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }
  return res.blob();
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
function getActiveProjectName() {
  return activeProjectName || defaultProjectName || "default";
}

function projectCasesBaseUrl(projectName) {
  return `/api/cases/projects/${encodeURIComponent(projectName)}/cases`;
}

function projectCaseUrl(projectName, caseName) {
  return `${projectCasesBaseUrl(projectName)}/${encodeURIComponent(caseName)}`;
}

function updateActiveCaseLabel() {
  const label = document.getElementById("active-case-label");
  if (!activeProjectName && !activeCaseName) {
    label.textContent = "No case selected";
    return;
  }
  if (!activeCaseName) {
    label.textContent = `Active project: ${getActiveProjectName()}`;
    return;
  }
  label.textContent = `Active: ${getActiveProjectName()} / ${activeCaseName}`;
}

function updateCaseActionButtons() {
  const hasCase = Boolean(activeCaseName);
  ["btn-rename-case", "btn-duplicate-case", "btn-delete-case", "btn-export-case"].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.disabled = !hasCase;
  });
}

function updateProjectActionButtons() {
  const hasProject = Boolean(activeProjectName);
  ["btn-rename-project", "btn-delete-project", "btn-export-project"].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.disabled = !hasProject;
  });
}

async function loadProjectList(preferredProjectName = null) {
  const data = await apiFetch("/api/cases/projects/");
  const select = document.getElementById("project-select");
  const projects = data.projects || [];
  defaultProjectName = data.default_project || "default";
  select.innerHTML = "";

  projects.forEach(projectName => {
    const option = document.createElement("option");
    option.value = projectName;
    option.textContent = projectName;
    select.appendChild(option);
  });

  if (projects.length === 0) {
    activeProjectName = null;
    activeCaseName = null;
    document.getElementById("case-list").innerHTML = "";
    updateActiveCaseLabel();
    updateCaseActionButtons();
    updateProjectActionButtons();
    return;
  }

  const nextProject = preferredProjectName && projects.includes(preferredProjectName)
    ? preferredProjectName
    : (activeProjectName && projects.includes(activeProjectName) ? activeProjectName : projects[0]);
  select.value = nextProject;
  activeProjectName = nextProject;
  updateActiveCaseLabel();
  updateCaseActionButtons();
  updateProjectActionButtons();
  await loadCaseList(nextProject);
}

async function loadCaseList(projectName = getActiveProjectName()) {
  if (!projectName) {
    document.getElementById("case-list").innerHTML = "";
    activeCaseName = null;
    updateActiveCaseLabel();
    updateCaseActionButtons();
    return;
  }
  const data = await apiFetch(`${projectCasesBaseUrl(projectName)}/`);
  const ul = document.getElementById("case-list");
  ul.innerHTML = "";
  (data.cases || []).forEach(name => {
    const li = document.createElement("li");
    li.textContent = name;
    if (name === activeCaseName && projectName === activeProjectName) li.classList.add("active");
    li.addEventListener("click", () => selectCase(projectName, name));
    ul.appendChild(li);
  });

  if (!(data.cases || []).includes(activeCaseName) || projectName !== activeProjectName) {
    activeProjectName = projectName;
    activeCaseName = null;
    updateActiveCaseLabel();
  }
  updateCaseActionButtons();
}

async function selectCase(projectName, name) {
  activeProjectName = projectName;
  activeCaseName = name;
  updateActiveCaseLabel();
  updateCaseActionButtons();
  document.querySelectorAll(".case-list li").forEach(li => {
    li.classList.toggle("active", li.textContent === name);
  });
  // Load the case config into the forms
  try {
    const cfg = await apiFetch(projectCaseUrl(projectName, name));
    populateConditionsForm(cfg);
    populateGridForm(cfg);
    // Try to load the most recent completed simulation result for this case
    try {
      const last = await apiFetch(`${projectCaseUrl(projectName, name)}/last_result`);
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

document.getElementById("project-select").addEventListener("change", async (ev) => {
  activeProjectName = ev.target.value || null;
  activeCaseName = null;
  updateActiveCaseLabel();
  updateProjectActionButtons();
  await loadCaseList(activeProjectName);
});

document.getElementById("btn-new-project").addEventListener("click", async () => {
  const nameInput = document.getElementById("new-project-name");
  const name = nameInput.value.trim();
  const errEl = document.getElementById("case-error");
  if (!name) { showError(errEl, "Enter a project name."); return; }
  hideError(errEl);
  try {
    await apiFetch("/api/cases/projects/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    });
    nameInput.value = "";
    await loadProjectList(name);
  } catch (e) {
    showError(errEl, e.message);
  }
});

document.getElementById("btn-new-case").addEventListener("click", async () => {
  const nameInput = document.getElementById("new-case-name");
  const name = nameInput.value.trim();
  const errEl = document.getElementById("case-error");
  if (!name) { showError(errEl, "Enter a case name."); return; }
  if (!getActiveProjectName()) { showError(errEl, "Create or select a project first."); return; }
  hideError(errEl);
  try {
    await apiFetch(`${projectCasesBaseUrl(getActiveProjectName())}/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    });
    nameInput.value = "";
    await loadCaseList(getActiveProjectName());
    await selectCase(getActiveProjectName(), name);
  } catch (e) {
    showError(errEl, e.message);
  }
});

document.getElementById("btn-refresh-cases").addEventListener("click", async () => {
  await loadProjectList(activeProjectName);
});

document.getElementById("btn-rename-project").addEventListener("click", async () => {
  const projectName = getActiveProjectName();
  if (!projectName) { alert("Select a project first."); return; }
  const newName = window.prompt("New project name", projectName);
  if (!newName || !newName.trim() || newName.trim() === projectName) return;
  const errEl = document.getElementById("case-error");
  hideError(errEl);
  try {
    const result = await apiFetch(`/api/cases/projects/${encodeURIComponent(projectName)}/rename`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ new_name: newName.trim() }),
    });
    activeProjectName = result.name || newName.trim();
    updateActiveCaseLabel();
    await loadProjectList(activeProjectName);
    if (activeCaseName) {
      await selectCase(activeProjectName, activeCaseName);
    }
  } catch (e) {
    showError(errEl, e.message);
  }
});

document.getElementById("btn-delete-project").addEventListener("click", async () => {
  const projectName = getActiveProjectName();
  if (!projectName) { alert("Select a project first."); return; }
  if (!window.confirm(`Delete project ${projectName} and all contained cases?`)) return;
  const errEl = document.getElementById("case-error");
  hideError(errEl);
  try {
    await apiFetch(`/api/cases/projects/${encodeURIComponent(projectName)}`, { method: "DELETE" });
    activeProjectName = null;
    activeCaseName = null;
    updateActiveCaseLabel();
    updateCaseActionButtons();
    updateProjectActionButtons();
    await loadProjectList();
  } catch (e) {
    showError(errEl, e.message);
  }
});

document.getElementById("btn-export-project").addEventListener("click", async () => {
  const projectName = getActiveProjectName();
  if (!projectName) { alert("Select a project first."); return; }
  const errEl = document.getElementById("case-error");
  hideError(errEl);
  try {
    const archiveBlob = await apiFetchBlob(`/api/cases/projects/${encodeURIComponent(projectName)}/export`);
    const url = URL.createObjectURL(archiveBlob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${projectName}.zip`;
    a.click();
    URL.revokeObjectURL(url);
  } catch (e) {
    showError(errEl, e.message);
  }
});

document.getElementById("btn-duplicate-case").addEventListener("click", async () => {
  if (!activeCaseName) { alert("Select a case first."); return; }
  const newName = window.prompt("New case name", `${activeCaseName}_copy`);
  if (!newName || !newName.trim()) return;
  const errEl = document.getElementById("case-error");
  hideError(errEl);
  try {
    const result = await apiFetch(`${projectCaseUrl(getActiveProjectName(), activeCaseName)}/duplicate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ new_name: newName.trim() }),
    });
    await loadCaseList(getActiveProjectName());
    await selectCase(result.project || getActiveProjectName(), result.name || newName.trim());
  } catch (e) {
    showError(errEl, e.message);
  }
});

document.getElementById("btn-rename-case").addEventListener("click", async () => {
  if (!activeCaseName) { alert("Select a case first."); return; }
  const oldCaseName = activeCaseName;
  const projectName = getActiveProjectName();
  const newName = window.prompt("New case name", oldCaseName);
  if (!newName || !newName.trim() || newName.trim() === oldCaseName) return;
  const errEl = document.getElementById("case-error");
  hideError(errEl);
  try {
    const result = await apiFetch(`${projectCaseUrl(projectName, oldCaseName)}/rename`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ new_name: newName.trim() }),
    });
    activeCaseName = null;
    await loadCaseList(result.project || projectName);
    await selectCase(result.project || projectName, result.name || newName.trim());
  } catch (e) {
    showError(errEl, e.message);
  }
});

document.getElementById("btn-delete-case").addEventListener("click", async () => {
  if (!activeCaseName) { alert("Select a case first."); return; }
  const caseName = activeCaseName;
  const projectName = getActiveProjectName();
  if (!window.confirm(`Delete case ${projectName} / ${caseName}?`)) return;
  const errEl = document.getElementById("case-error");
  hideError(errEl);
  try {
    await apiFetch(projectCaseUrl(projectName, caseName), { method: "DELETE" });
    activeCaseName = null;
    updateActiveCaseLabel();
    updateCaseActionButtons();
    await loadCaseList(projectName);
  } catch (e) {
    showError(errEl, e.message);
  }
});

document.getElementById("btn-export-case").addEventListener("click", async () => {
  if (!activeCaseName) { alert("Select a case first."); return; }
  const errEl = document.getElementById("case-error");
  hideError(errEl);
  try {
    const projectName = getActiveProjectName();
    const yamlText = await apiFetchText(`${projectCaseUrl(projectName, activeCaseName)}/export`);
    const blob = new Blob([yamlText], { type: "application/x-yaml" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${projectName}_${activeCaseName}.yaml`;
    a.click();
    URL.revokeObjectURL(url);
  } catch (e) {
    showError(errEl, e.message);
  }
});

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
  tab: {
    critical_weber_number: 12,
    tab_reduction_fraction: 0.5,
    tab_spring_k: 0.001,
    tab_damping_c: 1.0e-6,
    tab_breakup_threshold: 1.0,
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
  const tabSection   = document.getElementById("breakup-params-tab");
  if (model === "khrt") {
    weberRow.classList.add("hidden");
    weberSection.classList.add("hidden");
    khrtSection.classList.remove("hidden");
    tabSection.classList.add("hidden");
  } else if (model === "bag_stripping") {
    weberRow.classList.remove("hidden");
    weberSection.classList.add("hidden");
    khrtSection.classList.add("hidden");
    tabSection.classList.add("hidden");
  } else if (model === "tab") {
    // Show critical Weber and TAB-specific params
    weberRow.classList.remove("hidden");
    weberSection.classList.add("hidden");
    khrtSection.classList.add("hidden");
    tabSection.classList.remove("hidden");
    // fill defaults for new tab fields
    setFieldValue(f, "tab_spring_k", MODEL_DEFAULTS.tab.tab_spring_k);
    setFieldValue(f, "tab_damping_c", MODEL_DEFAULTS.tab.tab_damping_c);
    setFieldValue(f, "tab_breakup_threshold", MODEL_DEFAULTS.tab.tab_breakup_threshold);
  } else {
    // weber_critical
    weberRow.classList.remove("hidden");
    weberSection.classList.remove("hidden");
    khrtSection.classList.add("hidden");
    tabSection.classList.add("hidden");
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
  const row = document.getElementById("inlet-wetness-row");
  const f = document.getElementById("conditions-form");
  const input = f && f.elements.inlet_wetness;
  const isSteam = (fluidValue || "").toLowerCase() === "steam";
  if (row) row.classList.toggle("hidden", !isSteam);
  if (input && !isSteam) input.value = "";
}

function updateWaterMassFlowSectionUI() {
  const f = document.getElementById("conditions-form");
  if (!f) return;
  const injectionMode = (f.elements.injection_mode?.value || "droplet_injection").toLowerCase();
  const section = document.getElementById("water-mass-flow-section");
  if (!section) return;
  if (injectionMode === "liquid_jet_injection") {
    section.classList.add("hidden");
    return;
  }
  section.classList.remove("hidden");
  const mode = f.elements.water_mass_flow_mode?.value || "kg_per_s";
  const kgRow = document.getElementById("water-mass-flow-kgps-row");
  const pctRow = document.getElementById("water-mass-flow-percent-row");
  if (kgRow) kgRow.classList.toggle("hidden", mode === "percent");
  if (pctRow) pctRow.classList.toggle("hidden", mode !== "percent");
}

function updateDropletInitialConditionUI() {
  const f = document.getElementById("conditions-form");
  if (!f) return;
  const isLiquidJet = (f.elements.injection_mode?.value || "droplet_injection").toLowerCase() === "liquid_jet_injection";
  const sectionIds = ["droplet-initial-conditions-section", "droplet-size-section"];
  sectionIds.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.classList.toggle("hidden", isLiquidJet);
  });
}

const WATER_DENSITY_KG_PER_M3 = 998.2;
const PI = Math.PI;

function hasNonEmptyValue(value) {
  return !(value === undefined || value === null || String(value).trim() === "");
}

function tryParsePositiveScalar(value) {
  if (Array.isArray(value)) {
    if (value.length !== 1) return null;
    return tryParsePositiveScalar(value[0]);
  }
  if (!hasNonEmptyValue(value)) return null;
  const tokens = splitNumericTokens(value);
  if (tokens.length === 0) return null;
  if (tokens.length > 1) return null;
  const parsed = Number(tokens[0]);
  if (Number.isNaN(parsed) || parsed <= 0) return null;
  return parsed;
}

function formatCalculatedValue(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return "";
  if (Math.abs(value) >= 1.0e-3 && Math.abs(value) < 1.0e3) {
    return value.toPrecision(8).replace(/0+$/, "").replace(/\.$/, "");
  }
  return value.toExponential(6);
}

function getSelectedInputBasis(form) {
  const basisControl = form.elements.input_basis;
  if (!basisControl) return "diameter_based";
  if (typeof basisControl.value === "string" && basisControl.value) {
    return basisControl.value;
  }
  return "diameter_based";
}

function setSelectedInputBasis(form, basis) {
  const basisControl = form.elements.input_basis;
  if (!basisControl) return;
  const normalized = basis === "mass_flow_based" ? "mass_flow_based" : "diameter_based";
  if (typeof basisControl.value === "string") {
    basisControl.value = normalized;
    return;
  }
  Array.from(basisControl).forEach(el => {
    el.checked = el.value === normalized;
  });
}

function updateLiquidMaterialState(materialValue) {
  const densityInput = document.getElementById("liquid-density-input");
  if (!densityInput) return;
  const material = (materialValue || "water").toLowerCase();
  const isWater = material === "water";
  densityInput.readOnly = isWater;
  if (isWater) {
    densityInput.value = String(WATER_DENSITY_KG_PER_M3);
  }
}

function updateLiquidJetInputModeUI() {
  const f = document.getElementById("conditions-form");
  if (!f) return;
  const mode = (f.elements.injection_mode?.value || "droplet_injection").toLowerCase();
  const basis = getSelectedInputBasis(f);

  const diameterInput = document.getElementById("liquid-jet-diameter-input");
  const massFlowInput = document.getElementById("liquid-mass-flow-input");
  const diameterLabel = document.getElementById("liquid-jet-diameter-label");
  const massFlowLabel = document.getElementById("liquid-mass-flow-label");
  const noteEl = document.getElementById("liquid-jet-calc-note");
  if (!diameterInput || !massFlowInput || !diameterLabel || !massFlowLabel || !noteEl) return;

  if (mode !== "liquid_jet_injection") {
    diameterInput.readOnly = false;
    massFlowInput.readOnly = false;
    noteEl.classList.add("hidden");
    noteEl.textContent = "";
    diameterLabel.firstChild.textContent = "Liquid-jet diameter [m]";
    massFlowLabel.firstChild.textContent = "Liquid mass flow rate [kg/s]";
    return;
  }

  if (basis === "mass_flow_based") {
    diameterInput.readOnly = true;
    massFlowInput.readOnly = false;
    diameterLabel.firstChild.textContent = "Calculated liquid-jet diameter [m]";
    massFlowLabel.firstChild.textContent = "Liquid mass flow rate [kg/s]";
    noteEl.textContent = "Mass-flow-based: diameter is calculated from mass flow rate, liquid velocity, and liquid density.";
  } else {
    diameterInput.readOnly = false;
    massFlowInput.readOnly = true;
    diameterLabel.firstChild.textContent = "Liquid-jet diameter [m]";
    massFlowLabel.firstChild.textContent = "Calculated liquid mass flow rate [kg/s]";
    noteEl.textContent = "Diameter-based: mass flow rate is calculated from jet diameter, liquid velocity, and liquid density.";
  }
  noteEl.classList.remove("hidden");
}

function recomputeLiquidJetDerivedField() {
  const f = document.getElementById("conditions-form");
  if (!f) return;
  const mode = (f.elements.injection_mode?.value || "droplet_injection").toLowerCase();
  if (mode !== "liquid_jet_injection") return;

  const basis = getSelectedInputBasis(f);
  const diameterInput = document.getElementById("liquid-jet-diameter-input");
  const massFlowInput = document.getElementById("liquid-mass-flow-input");
  const velocityInput = document.getElementById("liquid-velocity-input");
  const densityInput = document.getElementById("liquid-density-input");
  if (!diameterInput || !massFlowInput || !velocityInput || !densityInput) return;

  const rho = tryParsePositiveScalar(densityInput.value);
  const u = tryParsePositiveScalar(velocityInput.value);
  if (rho === null || u === null) {
    if (basis === "mass_flow_based") {
      diameterInput.value = "";
    } else {
      massFlowInput.value = "";
    }
    return;
  }

  if (basis === "mass_flow_based") {
    const mDot = tryParsePositiveScalar(massFlowInput.value);
    if (mDot === null) {
      diameterInput.value = "";
      return;
    }
    const d = Math.sqrt((4.0 * mDot) / (PI * rho * u));
    diameterInput.value = formatCalculatedValue(d);
    return;
  }

  const d = tryParsePositiveScalar(diameterInput.value);
  if (d === null) {
    massFlowInput.value = "";
    return;
  }
  const mDot = rho * (PI * d * d / 4.0) * u;
  massFlowInput.value = formatCalculatedValue(mDot);
}

function normalizeLiquidJetConfig(cfg) {
  const di = cfg?.droplet_injection;
  if (!di || typeof di !== "object") return cfg;
  const mode = (di.injection_mode || "droplet_injection").toLowerCase();
  if (mode !== "liquid_jet_injection") return cfg;

  di.droplet_velocity_in = null;
  di.droplet_diameter_mean_in = null;
  di.droplet_diameter_max_in = null;
  di.water_mass_flow_rate = null;
  di.water_mass_flow_rate_percent = null;

  di.liquid_material = di.liquid_material || "water";
  di.input_basis = di.input_basis || "diameter_based";
  if ((di.liquid_material || "").toLowerCase() === "water" && !hasNonEmptyValue(di.liquid_density)) {
    di.liquid_density = WATER_DENSITY_KG_PER_M3;
  }

  const rho = tryParsePositiveScalar(di.liquid_density);
  const u = tryParsePositiveScalar(di.liquid_velocity);
  const basis = (di.input_basis || "diameter_based").toLowerCase();
  if (rho === null || u === null) return cfg;

  if (basis === "mass_flow_based") {
    const mDot = tryParsePositiveScalar(di.liquid_mass_flow_rate);
    if (mDot !== null) {
      di.liquid_jet_diameter = Math.sqrt((4.0 * mDot) / (PI * rho * u));
    }
  } else {
    const d = tryParsePositiveScalar(di.liquid_jet_diameter);
    if (d !== null) {
      di.liquid_mass_flow_rate = rho * (PI * d * d / 4.0) * u;
    }
  }
  return cfg;
}

function updateInjectionModeState(mode) {
  const jetSection = document.getElementById("liquid-jet-params");
  if (!jetSection) return;
  if ((mode || "").toLowerCase() === "liquid_jet_injection") {
    jetSection.classList.remove("hidden");
  } else {
    jetSection.classList.add("hidden");
  }
  updateDropletInitialConditionUI();
  updateWaterMassFlowSectionUI();
  updateLiquidJetInputModeUI();
  recomputeLiquidJetDerivedField();
}

function assertLiquidJetRequirement(cfg) {
  const mode = cfg?.droplet_injection?.injection_mode || "droplet_injection";
  if ((mode || "").toLowerCase() !== "liquid_jet_injection") return;
  const di = cfg.droplet_injection || {};
  const missing = [];
  const basis = (di.input_basis || "diameter_based").toLowerCase();
  if (!hasNonEmptyValue(di.liquid_velocity)) missing.push("liquid_velocity");
  if (!hasNonEmptyValue(di.liquid_density)) missing.push("liquid_density");
  if (basis === "mass_flow_based") {
    if (!hasNonEmptyValue(di.liquid_mass_flow_rate)) missing.push("liquid_mass_flow_rate");
  } else if (!hasNonEmptyValue(di.liquid_jet_diameter)) {
    missing.push("liquid_jet_diameter");
  }
  if (missing.length) {
    throw new Error(`Liquid-jet injection requires fields: ${missing.join(", ")}`);
  }
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
  setFieldValue(f, "injection_mode", di.injection_mode ?? "droplet_injection");
  updateInjectionModeState(di.injection_mode ?? "droplet_injection");
  setFieldValue(f, "liquid_material", di.liquid_material ?? "water");
  updateLiquidMaterialState(di.liquid_material ?? "water");
  setSelectedInputBasis(f, di.input_basis ?? "diameter_based");
  setFieldValue(f, "liquid_jet_diameter", di.liquid_jet_diameter ?? "");
  setFieldValue(f, "liquid_mass_flow_rate", di.liquid_mass_flow_rate ?? "");
  setFieldValue(f, "liquid_velocity", di.liquid_velocity ?? "");
  setFieldValue(f, "liquid_density", di.liquid_density ?? "");
  updateLiquidJetInputModeUI();
  recomputeLiquidJetDerivedField();
  setFieldValue(f, "liquid_viscosity", di.liquid_viscosity ?? "");
  setFieldValue(f, "surface_tension", di.surface_tension ?? "");
  setFieldValue(f, "primary_breakup_model", di.primary_breakup_model ?? "empirical");
  setFieldValue(f, "primary_breakup_coefficient", di.primary_breakup_coefficient ?? "");
  setFieldValue(f, "initial_SMD_model", di.initial_SMD_model ?? "fraction_of_jet");
  setFieldValue(f, "water_mass_flow_rate", di.water_mass_flow_rate ?? "");
  setFieldValue(f, "water_mass_flow_rate_percent", di.water_mass_flow_rate_percent ?? "");
  const hasKgPerS = di.water_mass_flow_rate !== undefined && di.water_mass_flow_rate !== null && String(di.water_mass_flow_rate) !== "";
  const hasPercent = di.water_mass_flow_rate_percent !== undefined && di.water_mass_flow_rate_percent !== null && String(di.water_mass_flow_rate_percent) !== "";
  setFieldValue(
    f,
    "water_mass_flow_mode",
    hasPercent && !hasKgPerS ? "percent" : "kg_per_s"
  );
  updateWaterMassFlowSectionUI();
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
  setFieldValue(f, "khrt_liquid_density",   ms.liquid_density   ?? kd.liquid_density);
  setFieldValue(f, "khrt_liquid_viscosity", ms.liquid_viscosity ?? kd.liquid_viscosity);
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
  const injectionMode = (f.elements.injection_mode && f.elements.injection_mode.value) || "droplet_injection";
  const isLiquidJet = injectionMode === "liquid_jet_injection";
  const cfg = {
    fluid: { working_fluid: fl },
    boundary_conditions: {
      Pt_in:  parseNumericOrList(f.elements.Pt_in.value, "Inlet total pressure P₀ [Pa]"),
      Tt_in:  parseNumericOrList(f.elements.Tt_in.value, "Inlet total temperature T₀ [K]"),
      Ps_out: parseNumericOrList(f.elements.Ps_out.value, "Outlet static pressure P₂ [Pa]"),
    },
    droplet_injection: {
      droplet_velocity_in:      isLiquidJet ? null : parseNumericOrList(f.elements.droplet_velocity_in.value, "Initial droplet velocity [m/s]"),
      injection_mode:           injectionMode,
      input_basis:              getSelectedInputBasis(f),
      liquid_material:          (f.elements.liquid_material && f.elements.liquid_material.value) || "water",
      liquid_jet_diameter:      parseNumericOrList(f.elements.liquid_jet_diameter?.value, "Liquid-jet diameter [m]", { optional: true }),
      liquid_mass_flow_rate:    parseNumericOrList(f.elements.liquid_mass_flow_rate?.value, "Liquid mass flow rate [kg/s]", { optional: true }),
      liquid_velocity:          parseNumericOrList(f.elements.liquid_velocity?.value, "Liquid velocity [m/s]", { optional: true }),
      liquid_density:           parseNumericOrList(f.elements.liquid_density?.value, "Liquid density [kg/m³]", { optional: true }),
      liquid_viscosity:         parseNumericOrList(f.elements.liquid_viscosity?.value, "Liquid viscosity [Pa·s]", { optional: true }),
      surface_tension:          parseNumericOrList(f.elements.surface_tension?.value, "Surface tension [N/m]", { optional: true }),
      primary_breakup_model:    (f.elements.primary_breakup_model && f.elements.primary_breakup_model.value) || null,
      primary_breakup_coefficient: parseNumericOrList(f.elements.primary_breakup_coefficient?.value, "Primary breakup coefficient", { optional: true }),
      initial_SMD_model:        (f.elements.initial_SMD_model && f.elements.initial_SMD_model.value) || null,
      droplet_diameter_mean_in: isLiquidJet ? null : parseNumericOrList(f.elements.droplet_diameter_mean_in.value, "Mean droplet diameter [m]"),
      droplet_diameter_max_in:  isLiquidJet ? null : parseNumericOrList(f.elements.droplet_diameter_max_in.value, "Maximum droplet diameter [m]"),
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
      liquid_density:        parseNumericOrList(f.elements.khrt_liquid_density?.value, "Liquid density [kg/m³] (KH-RT)", { optional: true }),
      liquid_viscosity:      parseNumericOrList(f.elements.khrt_liquid_viscosity?.value, "Liquid viscosity [Pa·s] (KH-RT)", { optional: true }),
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
  const injectionMode = (f.elements.injection_mode && f.elements.injection_mode.value) || "droplet_injection";
  const isLiquidJet = injectionMode === "liquid_jet_injection";
  const cfg = {
    fluid: { working_fluid: f.elements.working_fluid.value },
    boundary_conditions: {
      Pt_in: parseNumericOrList(f.elements.Pt_in.value, "Inlet total pressure P₀ [Pa]"),
      Tt_in: parseNumericOrList(f.elements.Tt_in.value, "Inlet total temperature T₀ [K]"),
      Ps_out: parseNumericOrList(f.elements.Ps_out.value, "Outlet static pressure P₂ [Pa]"),
    },
    droplet_injection: {
      droplet_velocity_in: isLiquidJet ? null : parseNumericOrList(f.elements.droplet_velocity_in.value, "Initial droplet velocity [m/s]"),
      injection_mode:       injectionMode,
      input_basis:          getSelectedInputBasis(f),
      liquid_material:      (f.elements.liquid_material && f.elements.liquid_material.value) || "water",
      liquid_jet_diameter:  parseNumericOrList(f.elements.liquid_jet_diameter?.value, "Liquid-jet diameter [m]", { optional: true }),
      liquid_mass_flow_rate: parseNumericOrList(f.elements.liquid_mass_flow_rate?.value, "Liquid mass flow rate [kg/s]", { optional: true }),
      liquid_velocity:      parseNumericOrList(f.elements.liquid_velocity?.value, "Liquid velocity [m/s]", { optional: true }),
      liquid_density:       parseNumericOrList(f.elements.liquid_density?.value, "Liquid density [kg/m³]", { optional: true }),
      liquid_viscosity:     parseNumericOrList(f.elements.liquid_viscosity?.value, "Liquid viscosity [Pa·s]", { optional: true }),
      surface_tension:      parseNumericOrList(f.elements.surface_tension?.value, "Surface tension [N/m]", { optional: true }),
      primary_breakup_model: (f.elements.primary_breakup_model && f.elements.primary_breakup_model.value) || null,
      primary_breakup_coefficient: parseNumericOrList(f.elements.primary_breakup_coefficient?.value, "Primary breakup coefficient", { optional: true }),
      initial_SMD_model:    (f.elements.initial_SMD_model && f.elements.initial_SMD_model.value) || null,
      droplet_diameter_mean_in: isLiquidJet ? null : parseNumericOrList(f.elements.droplet_diameter_mean_in.value, "Mean droplet diameter [m]"),
      droplet_diameter_max_in: isLiquidJet ? null : parseNumericOrList(f.elements.droplet_diameter_max_in.value, "Maximum droplet diameter [m]"),
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
      liquid_density: parseNumericOrList(f.elements.khrt_liquid_density?.value, "Liquid density [kg/m³] (KH-RT)", { optional: true }),
      liquid_viscosity: parseNumericOrList(f.elements.khrt_liquid_viscosity?.value, "Liquid viscosity [Pa·s] (KH-RT)", { optional: true }),
      tab_reduction_fraction: parseNumericOrList(f.elements.tab_reduction_fraction.value, "TAB reduction fraction", { optional: true }),
      tab_spring_k: parseNumericOrList(f.elements.tab_spring_k.value, "TAB spring constant (k)", { optional: true }),
      tab_damping_c: parseNumericOrList(f.elements.tab_damping_c.value, "TAB damping (c)", { optional: true }),
      tab_breakup_threshold: parseNumericOrList(f.elements.tab_breakup_threshold.value, "TAB breakup threshold", { optional: true }),
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
  const current = normalizeLiquidJetConfig({ ...readConditionsFormForRun(), ...readGridForm() });
  try {
    const existing = await apiFetch(projectCaseUrl(getActiveProjectName(), activeCaseName));
    const merged = normalizeLiquidJetConfig(mergeCaseConfigs(existing, current));
    assertTwoWayMassFlowRequirement(merged);
    assertLiquidJetRequirement(merged);
    return merged;
  } catch (_e) {
    assertTwoWayMassFlowRequirement(current);
    assertLiquidJetRequirement(current);
    return current;
  }
}

document.getElementById("btn-save-conditions").addEventListener("click", async () => {
  if (!activeCaseName) { alert("Select or create a case first."); return; }
  const statusEl = document.getElementById("conditions-status");
  try {
    const condCfg = normalizeLiquidJetConfig(readConditionsFormForSave());
    // Merge with existing grid config
    const existing = await apiFetch(projectCaseUrl(getActiveProjectName(), activeCaseName));
    const merged = normalizeLiquidJetConfig(mergeCaseConfigs(existing, condCfg));
    // Validate liquid-jet requirements on save as well
    assertLiquidJetRequirement(merged);
    await apiFetch(projectCaseUrl(getActiveProjectName(), activeCaseName), {
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
    const existing = await apiFetch(projectCaseUrl(getActiveProjectName(), activeCaseName));
    const merged = mergeCaseConfigs(existing, gridCfg);
    await apiFetch(projectCaseUrl(getActiveProjectName(), activeCaseName), {
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
      body: JSON.stringify({ project_name: getActiveProjectName(), case_name: activeCaseName, config: runConfig }),
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
    // Extract primary-breakup metrics from diagnostics messages if present
    try {
      const summaryEl = document.getElementById("primary-breakup-summary");
      const contentEl = document.getElementById("primary-breakup-content");
      if (!contentEl || !summaryEl) return;
      const diag = data.diagnostics || data.diagnostics || {};
      const messages = Array.isArray(diag?.messages) ? diag.messages : (diag?.messages || []);
      const keys = ["primary_breakup_length", "generated_mean_diameter", "generated_maximum_diameter", "weber_at_breakup"];
      const found = {};
      messages.forEach(m => {
        if (typeof m !== "string") return;
        keys.forEach(k => {
          if (m.startsWith(k + "=")) {
            found[k] = m.split("=")[1];
          }
        });
      });
      if (Object.keys(found).length === 0) {
        contentEl.textContent = "No primary-breakup metrics reported.";
        summaryEl.classList.add("hidden");
      } else {
        const lines = keys.filter(k => found[k]).map(k => `${k.replace(/_/g, ' ')}: ${found[k]}`);
        contentEl.innerHTML = lines.map(l => `<div>${l}</div>`).join("");
        summaryEl.classList.remove("hidden");
      }
    } catch (err) {
      console.warn("Failed to parse primary-breakup diagnostics:", err);
    }
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
// Wire injection-mode selector show/hide behavior
const injSelect = document.getElementById("injection-mode-select");
if (injSelect) {
  injSelect.addEventListener("change", (ev) => updateInjectionModeState(ev.target.value));
}

const liquidMaterialSelect = document.getElementById("liquid-material-select");
if (liquidMaterialSelect) {
  liquidMaterialSelect.addEventListener("change", (ev) => {
    updateLiquidMaterialState(ev.target.value);
    recomputeLiquidJetDerivedField();
  });
}

document.querySelectorAll("input[name='input_basis']").forEach(el => {
  el.addEventListener("change", () => {
    updateLiquidJetInputModeUI();
    recomputeLiquidJetDerivedField();
  });
});

["liquid-jet-diameter-input", "liquid-mass-flow-input", "liquid-velocity-input", "liquid-density-input"].forEach(id => {
  const el = document.getElementById(id);
  if (!el) return;
  el.addEventListener("input", recomputeLiquidJetDerivedField);
});

const waterMassFlowModeSelect = document.getElementById("water-mass-flow-mode-select");
if (waterMassFlowModeSelect) {
  waterMassFlowModeSelect.addEventListener("change", updateWaterMassFlowSectionUI);
}

updateLiquidMaterialState(liquidMaterialSelect?.value || "water");
updateLiquidJetInputModeUI();
recomputeLiquidJetDerivedField();
updateWaterMassFlowSectionUI();
updateInletWetnessState(document.getElementById("conditions-form")?.elements.working_fluid?.value || "air");

if (injSelect) {
  updateInjectionModeState(injSelect.value);
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
  const projectPrefix = activeProjectName ? `${activeProjectName}_` : "";
  a.download = `${projectPrefix}${activeCaseName || "result"}.csv`;
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
  await loadProjectList();
  await loadUnitGroups();
})();
