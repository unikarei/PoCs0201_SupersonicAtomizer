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
let projectTreeData = [];
let currentJobId   = null;
let pollTimer      = null;
let plotData       = {};   // field → base64 PNG
let csvContent     = "";
let tableRows      = [];
let lastPlotFields = [];
let lastRunCount = 0;
let lastDiagnostics = null;
const MULTI_VALUE_SPLIT_RE = /[\s,;，、]+/;
const expandedProjects = new Set();
let contextMenuTarget = { type: "root" };
let draggedCaseRef = null;
let sidebarResizeState = null;
let rightSidebarResizeState = null;
const caseChatHistories = new Map();
const caseChatThreads = new Map();
let activeChatThreadId = null;
let chatVoiceRecognition = null;
let chatVoiceListening = false;
const MIN_LEFT_PANEL_WIDTH = 180;
const MAX_LEFT_PANEL_WIDTH = 520;
const MIN_RIGHT_PANEL_WIDTH = 280;

// ── Unit conversion state ──────────────────────────────────────────────────
// Loaded from /api/units/groups — keyed by group name.
// Each group: { [unitLabel]: { scale: number, offset: number } }
let unitGroupSpecs = {};
let caseSelectionToken = 0;

// Maps input field name → unit group name for inline unit selectors.
const INPUT_FIELD_UNIT_GROUP = {
  // Boundary Conditions
  Pt_in:  "pressure",
  Tt_in:  "temperature",
  Ps_out: "pressure",
  inlet_wetness: "dimensionless",
  // Droplet Injection
  droplet_velocity_in: "velocity",
  liquid_jet_diameter: "diameter",
  liquid_velocity: "velocity",
  liquid_density: "density",
  liquid_viscosity: "viscosity",
  liquid_mass_flow_rate: "mass_flow",
  water_mass_flow_rate: "mass_flow",
  water_mass_flow_rate_percent: "dimensionless",
  // Breakup Parameters
  khrt_liquid_density: "density",
  khrt_liquid_viscosity: "viscosity",
  primary_breakup_coefficient: "dimensionless",
  critical_weber_number: "dimensionless",
  breakup_factor_mean: "dimensionless",
  breakup_factor_max: "dimensionless",
  khrt_B0: "dimensionless",
  khrt_B1: "dimensionless",
  khrt_Crt: "dimensionless",
  // Droplet Size
  droplet_diameter_mean_in: "diameter",
  droplet_diameter_max_in:  "diameter",
  tab_reduction_fraction: "dimensionless",
  tab_spring_k: "spring_constant",
  tab_damping_c: "damping",
  tab_breakup_threshold: "dimensionless",
  // Grid
  x_start: "length",
  x_end:   "length",
  // Note: fields with no matching group (mass flow, viscosity, surface_tension, 
  // and dimensionless numbers) are not converted.
};

// Client-side cache mapping "project/case" -> last_result payload
let caseResultCache = new Map();
// Tracks which case reference has finished config-form population.
let caseConfigReadyRef = null;

/**
 * Convert a single SI value to the given display unit.
 * Formula: display = si * scale + offset
 */
function siToDisplay(siValue, group, unitLabel) {
  const spec = (unitGroupSpecs[group] || {})[unitLabel];
  if (!spec) return siValue;
  return siValue * spec.scale + spec.offset;
}

/**
 * Convert a single display value back to SI.
 * Formula: si = (display - offset) / scale
 */
function displayToSi(displayValue, group, unitLabel) {
  const spec = (unitGroupSpecs[group] || {})[unitLabel];
  if (!spec) return displayValue;
  return (displayValue - spec.offset) / spec.scale;
}

/**
 * Convert a multi-token string of SI values to display unit string.
 * Tokens may be separated by spaces, commas, semicolons, etc.
 */
function convertSiStringToDisplay(rawSiString, group, unitLabel) {
  if (rawSiString === null || rawSiString === undefined || String(rawSiString).trim() === "") {
    return String(rawSiString ?? "");
  }
  const tokens = String(rawSiString).trim().split(MULTI_VALUE_SPLIT_RE).filter(Boolean);
  if (tokens.length === 0) return "";
  return tokens.map(t => {
    const v = Number(t);
    if (Number.isNaN(v)) return t;
    return String(siToDisplay(v, group, unitLabel));
  }).join(" ");
}

/**
 * Convert a multi-token string of display values back to SI values string.
 */
function convertDisplayStringToSi(rawDisplayString, group, unitLabel) {
  if (rawDisplayString === null || rawDisplayString === undefined || String(rawDisplayString).trim() === "") {
    return String(rawDisplayString ?? "");
  }
  const tokens = String(rawDisplayString).trim().split(MULTI_VALUE_SPLIT_RE).filter(Boolean);
  if (tokens.length === 0) return "";
  return tokens.map(t => {
    const v = Number(t);
    if (Number.isNaN(v)) return t;
    return String(displayToSi(v, group, unitLabel));
  }).join(" ");
}

/**
 * Return the currently selected unit label for a given BC input field.
 * Falls back to "Pa" for pressure, "K" for temperature if selector not found.
 */
function getInputUnitLabel(fieldName) {
  const sel = document.getElementById("unit-in-" + fieldName);
  return sel ? sel.value : null;
}


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

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#39;");
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

function formatReportValue(value) {
  if (value === null || value === undefined || value === "") return "-";
  if (Array.isArray(value)) return value.join(", ");
  return String(value);
}

function clamp(value, minValue, maxValue) {
  return Math.min(maxValue, Math.max(minValue, value));
}

function formatPlotFieldLabel(field) {
  if (field === "area_profile") return "Area Profile";
  if (field === "pressure") return "Static Pressure";
  return String(field).replace(/_/g, " ");
}

function setLeftPanelWidth(widthPx) {
  const nextWidth = clamp(widthPx, MIN_LEFT_PANEL_WIDTH, MAX_LEFT_PANEL_WIDTH);
  document.documentElement.style.setProperty("--left-panel-width", `${nextWidth}px`);
}

function setRightPanelWidth(widthPx) {
  // Allow the right chat panel to expand up to nearly the full viewport width
  // while still preserving the left panel minimum. This removes the previous
  // hard cap so users can make the chat as wide as they need.
  const viewportWidth = document.documentElement.clientWidth || window.innerWidth;
  const maxAllowed = Math.max(MIN_RIGHT_PANEL_WIDTH, viewportWidth - MIN_LEFT_PANEL_WIDTH - 40);
  const nextWidth = clamp(widthPx, MIN_RIGHT_PANEL_WIDTH, maxAllowed);
  document.documentElement.style.setProperty("--right-panel-width", `${nextWidth}px`);
}

function endSidebarResize() {
  if (!sidebarResizeState) return;
  sidebarResizeState = null;
  document.body.classList.remove("sidebar-resizing");
}

function handleSidebarResizeMove(event) {
  if (!sidebarResizeState) return;
  const width = sidebarResizeState.startWidth + (event.clientX - sidebarResizeState.startX);
  setLeftPanelWidth(width);
}

function initializeSidebarResizeHandle() {
  const handle = document.getElementById("left-panel-resize-handle");
  const panel = document.querySelector(".left-panel");
  if (!handle || !panel) return;

  handle.addEventListener("mousedown", event => {
    sidebarResizeState = {
      startX: event.clientX,
      startWidth: panel.getBoundingClientRect().width,
    };
    document.body.classList.add("sidebar-resizing");
    event.preventDefault();
  });

  document.addEventListener("mousemove", handleSidebarResizeMove);
  document.addEventListener("mouseup", endSidebarResize);
  document.addEventListener("mouseleave", endSidebarResize);
}

function endRightSidebarResize() {
  if (!rightSidebarResizeState) return;
  rightSidebarResizeState = null;
  document.body.classList.remove("chat-sidebar-resizing");
}

function handleRightSidebarResizeMove(event) {
  if (!rightSidebarResizeState) return;
  const width = rightSidebarResizeState.startWidth + (rightSidebarResizeState.startX - event.clientX);
  setRightPanelWidth(width);
}

function initializeRightSidebarResizeHandle() {
  const handle = document.getElementById("right-panel-resize-handle");
  const panel = document.querySelector(".chat-panel");
  if (!handle || !panel) return;

  handle.addEventListener("mousedown", event => {
    rightSidebarResizeState = {
      startX: event.clientX,
      startWidth: panel.getBoundingClientRect().width,
    };
    document.body.classList.add("chat-sidebar-resizing");
    event.preventDefault();
  });

  document.addEventListener("mousemove", handleRightSidebarResizeMove);
  document.addEventListener("mouseup", endRightSidebarResize);
  document.addEventListener("mouseleave", endRightSidebarResize);
}

// ── Tab navigation ─────────────────────────────────────────────────────────────
document.querySelectorAll(".tab-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach(s => s.classList.add("hidden"));
    btn.classList.add("active");
    const id = "tab-" + btn.dataset.tab;
    document.getElementById(id).classList.remove("hidden");

    // Requirement P34-T09: when Graph/Table/Report is opened for a selected
    // case, refresh from server-side last_result which can be disk-backed.
    const isPostTab = ["post-graphs", "post-table", "post-report"].includes(btn.dataset.tab);
    if (isPostTab && activeProjectName && activeCaseName) {
      void (async () => {
        try {
          await refreshLastResultForCase(activeProjectName, activeCaseName, { preferFiles: "1", cache: true });
        } catch (e) {
          console.debug("Post-tab refresh from last_result failed:", e && e.message ? e.message : e);
        }
      })();
    }
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

function getActiveCaseRef() {
  if (!activeCaseName) return null;
  return `${getActiveProjectName()}/${activeCaseName}`;
}

function markCaseConfigReady(caseRef) {
  caseConfigReadyRef = caseRef || null;
}

function isCaseConfigReady(caseRef) {
  if (!caseRef) return false;
  return caseConfigReadyRef === caseRef;
}

function rerenderReportIfCaseConfigReady(caseRef = null) {
  const resolvedRef = caseRef || getActiveCaseRef();
  if (!resolvedRef) return;
  if (!isCaseConfigReady(resolvedRef)) return;
  renderReport();
}

function getCaseChatHistory() {
  const caseRef = getActiveCaseRef();
  if (!caseRef || !activeChatThreadId) return [];
  return caseChatHistories.get(`${caseRef}::${activeChatThreadId}`) || [];
}

function setCaseChatHistory(messages) {
  const caseRef = getActiveCaseRef();
  if (!caseRef || !activeChatThreadId) return;
  caseChatHistories.set(`${caseRef}::${activeChatThreadId}`, messages);
}

function getCaseThreadList() {
  const caseRef = getActiveCaseRef();
  if (!caseRef) return [];
  return caseChatThreads.get(caseRef) || [];
}

function setCaseThreadList(threads) {
  const caseRef = getActiveCaseRef();
  if (!caseRef) return;
  caseChatThreads.set(caseRef, Array.isArray(threads) ? threads : []);
}

function renderChatThreadList() {
  const container = document.getElementById("chat-thread-list");
  if (!container) return;
  container.innerHTML = "";

  if (!activeCaseName) {
    container.innerHTML = '<div class="chat-thread-empty">Select a case to see chat history.</div>';
    return;
  }

  const threads = getCaseThreadList();
  if (threads.length === 0) {
    container.innerHTML = '<div class="chat-thread-empty">No chat history yet.</div>';
    return;
  }

  threads.forEach(thread => {
    const row = document.createElement("div");
    row.className = `chat-thread-item ${thread.id === activeChatThreadId ? "active" : ""}`;
    row.title = thread.title || "Chat";
    row.addEventListener("click", async () => {
      activeChatThreadId = thread.id;
      await loadActiveThreadHistory();
      updateChatPanelState();
    });

    const title = document.createElement("div");
    title.className = "chat-thread-title";
    title.textContent = thread.title || "New chat";
    row.appendChild(title);

    const renameBtn = document.createElement("button");
    renameBtn.type = "button";
    renameBtn.className = "chat-thread-meta-btn";
    renameBtn.title = "Rename";
    renameBtn.textContent = "✎";
    renameBtn.addEventListener("click", async event => {
      event.stopPropagation();
      const nextTitle = window.prompt("Rename chat", thread.title || "");
      if (!nextTitle) return;
      try {
        await apiFetch(`/api/chat/threads/${encodeURIComponent(thread.id)}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            project_name: getActiveProjectName(),
            case_name: activeCaseName,
            title: nextTitle,
          }),
        });
        await loadChatThreadsForActiveCase({ keepCurrent: true });
      } catch (error) {
        setChatStatus(`Rename failed: ${error.message}`, true);
      }
    });
    row.appendChild(renameBtn);

    const deleteBtn = document.createElement("button");
    deleteBtn.type = "button";
    deleteBtn.className = "chat-thread-meta-btn";
    deleteBtn.title = "Delete";
    deleteBtn.textContent = "🗑";
    deleteBtn.addEventListener("click", async event => {
      event.stopPropagation();
      if (!window.confirm("Delete this chat history?")) return;
      try {
        await apiFetch(
          `/api/chat/threads/${encodeURIComponent(thread.id)}?project_name=${encodeURIComponent(getActiveProjectName())}&case_name=${encodeURIComponent(activeCaseName)}`,
          { method: "DELETE" },
        );
        const caseRef = getActiveCaseRef();
        if (caseRef) {
          caseChatHistories.delete(`${caseRef}::${thread.id}`);
        }
        if (activeChatThreadId === thread.id) {
          activeChatThreadId = null;
        }
        await loadChatThreadsForActiveCase({ keepCurrent: false });
      } catch (error) {
        setChatStatus(`Delete failed: ${error.message}`, true);
      }
    });
    row.appendChild(deleteBtn);

    container.appendChild(row);
  });
}

async function loadActiveThreadHistory() {
  if (!activeCaseName || !activeChatThreadId) return;
  const caseRef = getActiveCaseRef();
  if (!caseRef) return;
  const cacheKey = `${caseRef}::${activeChatThreadId}`;
  if (caseChatHistories.has(cacheKey)) return;

  const detail = await apiFetch(
    `/api/chat/threads/${encodeURIComponent(activeChatThreadId)}?project_name=${encodeURIComponent(getActiveProjectName())}&case_name=${encodeURIComponent(activeCaseName)}`,
  );
  caseChatHistories.set(cacheKey, detail.messages || []);
}

async function loadChatThreadsForActiveCase({ keepCurrent = true } = {}) {
  if (!activeCaseName) {
    activeChatThreadId = null;
    renderChatThreadList();
    renderChatHistory();
    return;
  }

  const payload = await apiFetch(
    `/api/chat/threads?project_name=${encodeURIComponent(getActiveProjectName())}&case_name=${encodeURIComponent(activeCaseName)}`,
  );
  setCaseThreadList(payload.threads || []);
  const threads = getCaseThreadList();

  const stillExists = keepCurrent && activeChatThreadId && threads.some(thread => thread.id === activeChatThreadId);
  if (!stillExists) {
    activeChatThreadId = threads.length > 0 ? threads[0].id : null;
  }

  if (activeChatThreadId) {
    await loadActiveThreadHistory();
  }
  renderChatThreadList();
  renderChatHistory();
}

async function createNewChatThread(initialTitle = "New chat") {
  if (!activeCaseName) return;
  const created = await apiFetch("/api/chat/threads", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      project_name: getActiveProjectName(),
      case_name: activeCaseName,
      title: initialTitle,
    }),
  });
  activeChatThreadId = created.id;
  setCaseThreadList([created, ...getCaseThreadList().filter(thread => thread.id !== created.id)]);
  setCaseChatHistory(created.messages || []);
  renderChatThreadList();
  renderChatHistory();
}

function setChatStatus(message, isError = false) {
  const statusEl = document.getElementById("chat-status");
  if (!statusEl) return;
  statusEl.textContent = message || "";
  statusEl.style.color = isError ? "#b91c1c" : "#64748b";
}

function renderChatHistory() {
  const container = document.getElementById("chat-messages");
  if (!container) return;
  container.innerHTML = "";

  if (!activeCaseName) {
    container.innerHTML = '<div class="chat-empty">Select a case to discuss it with the assistant.</div>';
    return;
  }

  if (!activeChatThreadId) {
    container.innerHTML = '<div class="chat-empty">Create a new chat or select history from the left panel.</div>';
    return;
  }

  const history = getCaseChatHistory();
  if (history.length === 0) {
    container.innerHTML = '<div class="chat-empty">Ask about the selected case configuration or the latest solve result.</div>';
    return;
  }

  history.forEach(message => {
    const row = document.createElement("div");
    row.className = `chat-message ${message.role}`;
    const bubble = document.createElement("div");
    bubble.className = "chat-bubble";
    bubble.textContent = message.content;
    row.appendChild(bubble);
    container.appendChild(row);
  });
  container.scrollTop = container.scrollHeight;
}

function updateChatPanelState() {
  const caseLabel = document.getElementById("chat-case-label");
  const input = document.getElementById("chat-input");
  const sendButton = document.getElementById("btn-send-chat");
  const voiceButton = document.getElementById("btn-chat-voice");
  const clearButton = document.getElementById("btn-clear-chat");
  const newThreadButton = document.getElementById("btn-new-chat-thread");
  const hasCase = Boolean(activeCaseName);

  if (caseLabel) {
    caseLabel.textContent = hasCase
      ? `${getActiveProjectName()} / ${activeCaseName}`
      : "No case selected";
  }
  if (input) input.disabled = !hasCase;
  if (sendButton) sendButton.disabled = !hasCase;
  if (clearButton) clearButton.disabled = !hasCase || !activeChatThreadId;
  if (newThreadButton) newThreadButton.disabled = !hasCase;
  if (voiceButton) voiceButton.disabled = !hasCase || !chatVoiceRecognition;
  renderChatThreadList();
  renderChatHistory();
}

function normalizeChatMessagesForApi(messages) {
  return messages
    .filter(message => message.role === "user" || message.role === "assistant")
    .map(message => ({ role: message.role, content: message.content }));
}

function appendChatSystemMessage(content) {
  const history = getCaseChatHistory();
  setCaseChatHistory([...history, { role: "system", content }]);
  renderChatHistory();
}

function formatProposalDiff(diffRows) {
  if (!Array.isArray(diffRows) || diffRows.length === 0) {
    return "(no diff rows)";
  }
  return diffRows
    .map(row => `${row.path}: ${JSON.stringify(row.before)} -> ${JSON.stringify(row.after)}`)
    .join("\n");
}

function parseCfgProposeCommand(commandText) {
  const stripped = commandText.replace("/cfg-propose", "").trim();
  if (!stripped) {
    throw new Error("Usage: /cfg-propose dotted.path=value [dotted.path=value ...]");
  }
  const parts = stripped.split(/\s+/).filter(Boolean);
  const changes = parts.map(part => {
    const eqIdx = part.indexOf("=");
    if (eqIdx < 1) {
      throw new Error(`Invalid token: ${part}`);
    }
    const path = part.slice(0, eqIdx).trim();
    const rawValue = part.slice(eqIdx + 1).trim();
    if (!path || rawValue.length === 0) {
      throw new Error(`Invalid token: ${part}`);
    }
    const asNumber = Number(rawValue);
    const value = Number.isFinite(asNumber) ? asNumber : rawValue;
    return { path, value };
  });
  return changes;
}

async function handleChatConfigCommand(text) {
  if (!text.startsWith("/cfg-")) return false;
  if (!activeCaseName) throw new Error("Select a case first.");

  if (text.startsWith("/cfg-propose")) {
    const changes = parseCfgProposeCommand(text);
    const response = await apiFetch("/api/chat/config-changes/proposals", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        project_name: getActiveProjectName(),
        case_name: activeCaseName,
        pattern: 4,
        changes,
      }),
    });
    const proposalId = response.proposal_id || "(none)";
    appendChatSystemMessage(
      `Config proposal created: ${proposalId}\n${formatProposalDiff(response.diff)}\nApprove with: /cfg-apply ${proposalId}`
    );
    return true;
  }

  if (text.startsWith("/cfg-apply")) {
    const proposalId = text.replace("/cfg-apply", "").trim();
    if (!proposalId) throw new Error("Usage: /cfg-apply <proposal_id>");
    const response = await apiFetch(`/api/chat/config-changes/proposals/${encodeURIComponent(proposalId)}/apply`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        project_name: getActiveProjectName(),
        case_name: activeCaseName,
        approved_by_user: true,
      }),
    });
    appendChatSystemMessage(
      `Config proposal applied: ${proposalId}\n${formatProposalDiff(response.diff)}\nConfirm with: /cfg-confirm ${proposalId}`
    );
    return true;
  }

  if (text.startsWith("/cfg-confirm")) {
    const proposalId = text.replace("/cfg-confirm", "").trim();
    if (!proposalId) throw new Error("Usage: /cfg-confirm <proposal_id>");
    await apiFetch(`/api/chat/config-changes/proposals/${encodeURIComponent(proposalId)}/confirm`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        project_name: getActiveProjectName(),
        case_name: activeCaseName,
        confirmed_by_user: true,
      }),
    });
    appendChatSystemMessage(`Config proposal confirmed: ${proposalId}`);
    return true;
  }

  if (text.startsWith("/cfg-reject")) {
    const proposalId = text.replace("/cfg-reject", "").trim();
    if (!proposalId) throw new Error("Usage: /cfg-reject <proposal_id>");
    await apiFetch(`/api/chat/config-changes/proposals/${encodeURIComponent(proposalId)}/reject`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        project_name: getActiveProjectName(),
        case_name: activeCaseName,
        rejected_by_user: true,
      }),
    });
    appendChatSystemMessage(`Config proposal rejected: ${proposalId}`);
    return true;
  }

  throw new Error("Unknown /cfg command.");
}

async function submitChatMessage() {
  if (!activeCaseName) return;
  const input = document.getElementById("chat-input");
  if (!input) return;
  const text = input.value.trim();
  if (!text) return;

  if (!activeChatThreadId) {
    await createNewChatThread(text.slice(0, 48));
  }

  const history = getCaseChatHistory();
  const userMessage = { role: "user", content: text };
  setCaseChatHistory([...history, userMessage]);
  renderChatHistory();

  try {
    const handled = await handleChatConfigCommand(text);
    if (handled) {
      input.value = "";
      setChatStatus("");
      return;
    }
  } catch (error) {
    setCaseChatHistory([...getCaseChatHistory(), { role: "system", content: error.message }]);
    renderChatHistory();
    input.value = "";
    setChatStatus("Config command failed.", true);
    return;
  }

  const pendingMessage = { role: "assistant", content: "Thinking..." };
  setCaseChatHistory([...history, userMessage, pendingMessage]);
  renderChatHistory();
  setChatStatus("Sending message...");
  input.value = "";

  try {
    const headers = { "Content-Type": "application/json" };
    const llmSel = document.getElementById("chat-llm-sel");
    if (llmSel && llmSel.value) headers["X-LLM-MODEL"] = llmSel.value;
    const response = await apiFetch("/api/chat/messages", {
      method: "POST",
      headers,
      body: JSON.stringify({
        project_name: getActiveProjectName(),
        case_name: activeCaseName,
        thread_id: activeChatThreadId,
        messages: normalizeChatMessagesForApi([...history, userMessage]),
      }),
    });
    if (response.thread_id) {
      activeChatThreadId = response.thread_id;
    }
    setCaseChatHistory([...history, userMessage, response.reply]);
    await loadChatThreadsForActiveCase({ keepCurrent: true });
    setChatStatus("");
  } catch (error) {
    setCaseChatHistory([...history, userMessage, { role: "system", content: error.message }]);
    setChatStatus("Chat request failed.", true);
  }
  renderChatHistory();
}

async function clearActiveCaseChat() {
  const caseRef = getActiveCaseRef();
  if (!caseRef || !activeChatThreadId) return;
  caseChatHistories.set(`${caseRef}::${activeChatThreadId}`, []);
  try {
    await apiFetch(`/api/chat/threads/${encodeURIComponent(activeChatThreadId)}/messages`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        project_name: getActiveProjectName(),
        case_name: activeCaseName,
        messages: [],
      }),
    });
    await loadChatThreadsForActiveCase({ keepCurrent: true });
  } catch (error) {
    setChatStatus(`Clear failed: ${error.message}`, true);
  }
  setChatStatus("");
  renderChatHistory();
}

// ── Chat inner tab (チャット / 要約) ────────────────────────────────────────

function switchChatInnerTab(tabName) {
  document.querySelectorAll(".chat-inner-tab-btn").forEach(btn => {
    const isActive = btn.dataset.innerTab === tabName;
    btn.classList.toggle("active", isActive);
    btn.setAttribute("aria-selected", String(isActive));
  });
  document.querySelectorAll(".chat-inner-tab-content").forEach(pane => {
    const show = pane.id === `chat-inner-tab-${tabName}`;
    pane.style.display = show ? "flex" : "none";
  });
}

function setSummaryStatus(text, isError = false) {
  const el = document.getElementById("summary-status");
  if (!el) return;
  el.textContent = text;
  el.classList.toggle("error", isError);
}

async function generateSummary(refinePrompt = null) {
  if (!activeCaseName || !activeChatThreadId) {
    setSummaryStatus("ケースとチャットスレッドを選択してください。", true);
    return;
  }
  const maxCharsEl = document.getElementById("summary-max-chars");
  const maxChars = maxCharsEl ? parseInt(maxCharsEl.value, 10) : 300;
  const displayEl = document.getElementById("summary-display");
  if (displayEl) displayEl.innerHTML = "<p class='summary-loading'>生成中...</p>";
  setSummaryStatus("要約を生成中...");

  try {
    const headers = { "Content-Type": "application/json" };
    const llmSel = document.getElementById("chat-llm-sel");
    if (llmSel && llmSel.value) headers["X-LLM-MODEL"] = llmSel.value;
    const payload = {
      project_name: getActiveProjectName(),
      case_name: activeCaseName,
      thread_id: activeChatThreadId,
      max_chars: maxChars,
    };
    if (refinePrompt) payload.refine_prompt = refinePrompt;
    const response = await apiFetch("/api/chat/summary", {
      method: "POST",
      headers,
      body: JSON.stringify(payload),
    });
    const summaryText = (response && response.summary) ? response.summary : "";
    if (displayEl) {
      if (summaryText) {
        displayEl.textContent = summaryText;
      } else {
        displayEl.innerHTML = "<p class='summary-empty'>要約が返されませんでした。</p>";
      }
    }
    setSummaryStatus("");
  } catch (error) {
    if (displayEl) displayEl.innerHTML = `<p class='summary-error'>エラー: ${error.message}</p>`;
    setSummaryStatus(`要約の生成に失敗しました: ${error.message}`, true);
  }
}

function initializeSummaryTab() {
  // Set initial display states via style.display (avoids CSS class specificity conflicts).
  switchChatInnerTab("conversation");

  document.querySelectorAll(".chat-inner-tab-btn").forEach(btn => {
    btn.addEventListener("click", () => switchChatInnerTab(btn.dataset.innerTab));
  });

  const genBtn = document.getElementById("btn-generate-summary");
  if (genBtn) {
    genBtn.addEventListener("click", () => void generateSummary());
  }

  const refineForm = document.getElementById("summary-refine-form");
  if (refineForm) {
    refineForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const refineInput = document.getElementById("summary-refine-input");
      const refineText = refineInput ? refineInput.value.trim() : "";
      await generateSummary(refineText || null);
      if (refineInput) refineInput.value = "";
    });
  }
}

function initializeChatVoiceInput() {
  const voiceButton = document.getElementById("btn-chat-voice");
  const input = document.getElementById("chat-input");
  if (!voiceButton || !input) return;

  const RecognitionCtor = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!RecognitionCtor) {
    voiceButton.textContent = "Voice unavailable";
    voiceButton.disabled = true;
    return;
  }

  chatVoiceRecognition = new RecognitionCtor();
  chatVoiceRecognition.lang = "ja-JP";
  chatVoiceRecognition.interimResults = false;
  chatVoiceRecognition.maxAlternatives = 1;

  chatVoiceRecognition.addEventListener("result", event => {
    const transcript = Array.from(event.results)
      .map(result => result[0]?.transcript || "")
      .join(" ")
      .trim();
    if (!transcript) return;
    input.value = input.value ? `${input.value.trim()} ${transcript}` : transcript;
    setChatStatus("Voice input added.");
  });
  chatVoiceRecognition.addEventListener("end", () => {
    chatVoiceListening = false;
    voiceButton.classList.remove("listening");
    voiceButton.textContent = "Voice";
  });
  chatVoiceRecognition.addEventListener("error", event => {
    chatVoiceListening = false;
    voiceButton.classList.remove("listening");
    voiceButton.textContent = "Voice";
    setChatStatus(`Voice input failed: ${event.error}`, true);
  });

  voiceButton.addEventListener("click", () => {
    if (!chatVoiceRecognition || voiceButton.disabled) return;
    if (chatVoiceListening) {
      chatVoiceRecognition.stop();
      return;
    }
    try {
      chatVoiceRecognition.start();
      chatVoiceListening = true;
      voiceButton.classList.add("listening");
      voiceButton.textContent = "Listening...";
      setChatStatus("Listening for voice input...");
    } catch (error) {
      setChatStatus(`Voice input failed: ${error.message}`, true);
    }
  });
}

// Chat LLM selector persistence and helper
function loadChatLlmSelection() {
  const sel = document.getElementById("chat-llm-sel");
  if (!sel) return;
  const saved = localStorage.getItem("chat_llm_model") || "";
  sel.value = saved;
  sel.addEventListener("change", () => {
    try { localStorage.setItem("chat_llm_model", sel.value || ""); } catch (_e) {}
  });
}

// Initialize the chat LLM settings dialog and its controls (open/close/save)
function initializeChatLlmDialog() {
  const btn = document.getElementById("btn-chat-llm-settings");
  const dlg = document.getElementById("chat-llm-dialog");
  const closeBtn = document.getElementById("chat-llm-close");
  const saveBtn = document.getElementById("chat-llm-save");
  const cancelBtn = document.getElementById("chat-llm-cancel");
  const sel = document.getElementById("chat-llm-sel");
  if (!btn || !dlg) return;

  btn.addEventListener("click", () => {
    try {
      if (sel) sel.value = localStorage.getItem("chat_llm_model") || "";
      dlg.showModal();
    } catch (e) {
      // Fallback for browsers without <dialog>
      dlg.classList.remove("hidden");
    }
  });

  const closeDialog = () => {
    try { dlg.close(); } catch (_) { dlg.classList.add("hidden"); }
  };

  if (closeBtn) closeBtn.addEventListener("click", closeDialog);
  if (cancelBtn) cancelBtn.addEventListener("click", closeDialog);

  if (saveBtn) saveBtn.addEventListener("click", () => {
    const statusEl = document.getElementById("chat-llm-status");
    try {
      if (sel) localStorage.setItem("chat_llm_model", sel.value || "");
      if (statusEl) { statusEl.textContent = "✓ Saved"; }
      showToast("LLM selection saved");
      setTimeout(() => { if (statusEl) statusEl.textContent = ""; }, 1500);
      closeDialog();
    } catch (e) {
      if (statusEl) statusEl.textContent = "Error: " + e.message;
    }
  });
}

function getCaseErrorElement() {
  return document.getElementById("case-error");
}

function clearCaseError() {
  const errEl = getCaseErrorElement();
  if (errEl) hideError(errEl);
}

function showCaseErrorMessage(message) {
  const errEl = getCaseErrorElement();
  if (errEl) showError(errEl, message);
}

function findProjectRecord(projectName) {
  return projectTreeData.find(project => project.name === projectName) || null;
}

function closeTreeContextMenu() {
  const menu = document.getElementById("tree-context-menu");
  if (!menu) return;
  menu.classList.add("hidden");
  menu.replaceChildren();
}

function clearTreeDropTargets() {
  document.querySelectorAll(".tree-row.drop-target").forEach(row => row.classList.remove("drop-target"));
}

function getContextMenuActions(target) {
  if (target.type === "case") {
    return [
      { id: "rename-case", label: "Rename case" },
      { id: "duplicate-case", label: "Duplicate case" },
      { id: "export-case", label: "Export YAML" },
      { id: "delete-case", label: "Delete case" },
    ];
  }
  if (target.type === "project") {
    return [
      { id: "new-case", label: "New case" },
      { id: "rename-project", label: "Rename project" },
      { id: "export-project", label: "Export project" },
      { id: "delete-project", label: "Delete project" },
      { id: "refresh-tree", label: "Refresh tree" },
    ];
  }
  return [
    { id: "new-project", label: "New project" },
    { id: "refresh-tree", label: "Refresh tree" },
  ];
}

function positionTreeContextMenu(menu, x, y) {
  const padding = 8;
  const { innerWidth, innerHeight } = window;
  const rect = menu.getBoundingClientRect();
  const nextLeft = Math.min(x, innerWidth - rect.width - padding);
  const nextTop = Math.min(y, innerHeight - rect.height - padding);
  menu.style.left = `${Math.max(padding, nextLeft)}px`;
  menu.style.top = `${Math.max(padding, nextTop)}px`;
}

function openTreeContextMenu(x, y, target) {
  const menu = document.getElementById("tree-context-menu");
  if (!menu) return;
  contextMenuTarget = target;
  menu.replaceChildren();

  getContextMenuActions(target).forEach(action => {
    const button = document.createElement("button");
    button.type = "button";
    button.dataset.action = action.id;
    button.textContent = action.label;
    menu.appendChild(button);
  });

  menu.classList.remove("hidden");
  positionTreeContextMenu(menu, x, y);
}

function renderProjectCaseTree() {
  const tree = document.getElementById("project-case-tree");
  if (!tree) return;
  tree.replaceChildren();

  if (!projectTreeData.length) {
    const empty = document.createElement("li");
    empty.className = "tree-empty";
    empty.textContent = "No projects yet. Right-click here to create one.";
    tree.appendChild(empty);
    return;
  }

  projectTreeData.forEach(project => {
    const projectItem = document.createElement("li");
    projectItem.className = "tree-node";
    projectItem.setAttribute("role", "treeitem");

    const projectRow = document.createElement("div");
    projectRow.className = "tree-row project-row";
    projectRow.dataset.treeType = "project";
    projectRow.dataset.projectName = project.name;
    if (activeProjectName === project.name && !activeCaseName) {
      projectRow.classList.add("active");
    }

    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "tree-toggle";
    if (project.cases.length > 0) {
      toggle.textContent = expandedProjects.has(project.name) ? "-" : "+";
      toggle.setAttribute("aria-label", expandedProjects.has(project.name) ? "Collapse project" : "Expand project");
      toggle.addEventListener("click", event => {
        event.stopPropagation();
        if (expandedProjects.has(project.name)) {
          expandedProjects.delete(project.name);
        } else {
          expandedProjects.add(project.name);
        }
        renderProjectCaseTree();
      });
    } else {
      toggle.disabled = true;
      toggle.classList.add("tree-toggle-placeholder");
      toggle.textContent = "";
    }
    projectRow.appendChild(toggle);

    const projectBadge = document.createElement("span");
    projectBadge.className = "tree-badge";
    projectBadge.textContent = "PRJ";
    projectRow.appendChild(projectBadge);

    const projectLabel = document.createElement("span");
    projectLabel.className = "tree-label";
    projectLabel.textContent = project.name;
    projectRow.appendChild(projectLabel);
    projectRow.addEventListener("click", () => selectProject(project.name));
    projectRow.addEventListener("dragover", event => {
      if (!draggedCaseRef || draggedCaseRef.projectName === project.name) return;
      event.preventDefault();
      clearTreeDropTargets();
      projectRow.classList.add("drop-target");
    });
    projectRow.addEventListener("dragleave", event => {
      if (event.currentTarget !== projectRow) return;
      projectRow.classList.remove("drop-target");
    });
    projectRow.addEventListener("drop", event => {
      if (!draggedCaseRef || draggedCaseRef.projectName === project.name) return;
      event.preventDefault();
      projectRow.classList.remove("drop-target");
      void moveCaseToProject(draggedCaseRef.projectName, draggedCaseRef.caseName, project.name);
    });
    projectRow.addEventListener("contextmenu", event => {
      event.preventDefault();
      selectProject(project.name, { preserveCase: true });
      openTreeContextMenu(event.clientX, event.clientY, { type: "project", projectName: project.name });
    });
    projectItem.appendChild(projectRow);

    if (project.cases.length > 0 && expandedProjects.has(project.name)) {
      const childList = document.createElement("ul");
      childList.className = "tree-children";
      childList.setAttribute("role", "group");
      project.cases.forEach(caseName => {
        const caseItem = document.createElement("li");
        caseItem.className = "tree-node";
        caseItem.setAttribute("role", "treeitem");

        const caseRow = document.createElement("div");
        caseRow.className = "tree-row case-row";
        caseRow.dataset.treeType = "case";
        caseRow.dataset.projectName = project.name;
        caseRow.dataset.caseName = caseName;
        if (activeProjectName === project.name && activeCaseName === caseName) {
          caseRow.classList.add("active");
        }

        const spacer = document.createElement("span");
        spacer.className = "tree-toggle-placeholder";
        caseRow.appendChild(spacer);

        const caseBadge = document.createElement("span");
        caseBadge.className = "tree-badge";
        caseBadge.textContent = "CASE";
        caseRow.appendChild(caseBadge);

        const caseLabel = document.createElement("span");
        caseLabel.className = "tree-label";
        caseLabel.textContent = caseName;
        caseRow.appendChild(caseLabel);
        caseRow.draggable = true;

        caseRow.addEventListener("click", () => {
          void selectCase(project.name, caseName);
        });
        caseRow.addEventListener("dragstart", event => {
          draggedCaseRef = { projectName: project.name, caseName };
          caseRow.classList.add("dragging");
          if (event.dataTransfer) {
            event.dataTransfer.effectAllowed = "move";
            event.dataTransfer.setData("text/plain", `${project.name}/${caseName}`);
          }
        });
        caseRow.addEventListener("dragend", () => {
          draggedCaseRef = null;
          caseRow.classList.remove("dragging");
          clearTreeDropTargets();
        });
        caseRow.addEventListener("contextmenu", event => {
          event.preventDefault();
          activeProjectName = project.name;
          activeCaseName = caseName;
          updateActiveCaseLabel();
          renderProjectCaseTree();
          openTreeContextMenu(event.clientX, event.clientY, {
            type: "case",
            projectName: project.name,
            caseName,
          });
        });

        caseItem.appendChild(caseRow);
        childList.appendChild(caseItem);
      });
      projectItem.appendChild(childList);
    }

    tree.appendChild(projectItem);
  });
}

function updateCaseActionButtons() {
  renderProjectCaseTree();
}

function updateProjectActionButtons() {
  renderProjectCaseTree();
}

function updateActiveCaseLabel() {
  const label = document.getElementById("active-case-label");
  if (!activeProjectName && !activeCaseName) {
    label.textContent = "No case selected";
    updateChatPanelState();
    return;
  }
  if (!activeCaseName) {
    label.textContent = `Active project: ${getActiveProjectName()}`;
    updateChatPanelState();
    return;
  }
  label.textContent = `Active: ${getActiveProjectName()} / ${activeCaseName}`;
  updateChatPanelState();
}

function selectProject(projectName, { preserveCase = false } = {}) {
  const shouldPreserveCase = preserveCase && activeProjectName === projectName && Boolean(activeCaseName);
  activeProjectName = projectName;
  if (!shouldPreserveCase) {
    activeCaseName = null;
  }
  expandedProjects.add(projectName);
  updateActiveCaseLabel();
  renderProjectCaseTree();
}

async function loadProjectTree(preferredProjectName = null) {
  const data = await apiFetch("/api/cases/projects/");
  const projects = data.projects || [];
  defaultProjectName = data.default_project || "default";

  if (projects.length === 0) {
    projectTreeData = [];
    activeProjectName = null;
    activeCaseName = null;
    updateActiveCaseLabel();
    renderProjectCaseTree();
    return;
  }

  const nextProject = preferredProjectName && projects.includes(preferredProjectName)
    ? preferredProjectName
    : (activeProjectName && projects.includes(activeProjectName) ? activeProjectName : projects[0]);

  const casesByProject = await Promise.all(projects.map(async projectName => {
    const response = await apiFetch(`${projectCasesBaseUrl(projectName)}/`);
    return {
      name: projectName,
      cases: response.cases || [],
    };
  }));

  projectTreeData = casesByProject;
  activeProjectName = nextProject;
  expandedProjects.add(nextProject);

  const activeProjectCases = findProjectRecord(nextProject)?.cases || [];
  if (!activeCaseName || !activeProjectCases.includes(activeCaseName)) {
    activeCaseName = null;
  }

  updateActiveCaseLabel();
  renderProjectCaseTree();
}

async function loadProjectList(preferredProjectName = null) {
  await loadProjectTree(preferredProjectName);
}

async function loadCaseList(projectName = getActiveProjectName()) {
  await loadProjectTree(projectName);
}

async function selectCase(projectName, name) {
  const selectionToken = ++caseSelectionToken;
  activeProjectName = projectName;
  activeCaseName = name;
  markCaseConfigReady(null);
  activeChatThreadId = null;
  expandedProjects.add(projectName);
  updateActiveCaseLabel();
  renderProjectCaseTree();
  try {
    await loadChatThreadsForActiveCase({ keepCurrent: false });
    if (selectionToken !== caseSelectionToken) return;
  } catch (error) {
    setChatStatus(`Failed loading chat history: ${error.message}`, true);
  }
  // Optimise responsiveness: show cached result immediately if available and
  // fetch the latest result in the background. Load case config concurrently.
  const caseRef = `${projectName}/${name}`;

  // If we have a cached result for this case, render it immediately.
  if (caseResultCache.has(caseRef)) {
    const cached = caseResultCache.get(caseRef);
    applyLastResultToUI(cached, caseRef);
  } else {
    // No cache: clear post-tab content and show loading placeholders so UI responds fast.
    plotData = {};
    tableRows = [];
    csvContent = "";
    lastPlotFields = [];
    lastRunCount = 0;
    lastDiagnostics = null;
    renderPlots([]);
    renderTable([]);
    renderReport();
    const dlBtn = document.getElementById("btn-download-csv");
    if (dlBtn) dlBtn.disabled = true;
  }

  // Start fetching case config.
  // Try project-scoped case load first; fall back to legacy flat-case endpoint
  const cfgPromise = (async () => {
    try {
      return await apiFetch(projectCaseUrl(projectName, name));
    } catch (e) {
      console.debug(`Project-scoped config not found for ${projectName}/${name}, trying legacy path.`);
    }
    try {
      return await apiFetch(`/api/cases/${encodeURIComponent(name)}`);
    } catch (e) {
      console.warn("Failed to load case config from both project and legacy endpoints:", e);
      return null;
    }
  })();
  // Await config so forms are populated when available. After config load
  // we may fetch last_result only when the server indicates one exists.
  try {
    const cfg = await cfgPromise;
    if (selectionToken !== caseSelectionToken) return;
    if (cfg) {
      await tryPopulateCaseConfig(cfg);
      if (selectionToken !== caseSelectionToken) return;
      markCaseConfigReady(caseRef);
      // Ensure report uses freshly populated form values on the first click.
      rerenderReportIfCaseConfigReady(caseRef);
    }

    // If we already have a cached result, we rendered it earlier. Otherwise
    // only request /last_result when the server indicates a run exists
    // (avoid noisy 404s for fresh cases with no runs).
    if (!caseResultCache.has(caseRef)) {
      const hasResult = cfg && cfg.has_result;
      if (hasResult) {
        try {
          const preferFiles = document.querySelector('#tab-graphs') && !document.querySelector('#tab-graphs').classList.contains('hidden') ? '1' : '0';
          await refreshLastResultForCase(projectName, name, {
            preferFiles,
            cache: true,
            expectedSelectionToken: selectionToken,
          });
        } catch (e) {
          console.debug(`Failed fetching last_result for ${caseRef}:`, e && e.message ? e.message : e);
        }
      }
    }
  } catch (e) {
    console.warn("Failed to populate case forms:", e);
  }
}


async function tryPopulateCaseConfig(cfg) {
  try {
    populateConditionsForm(cfg);
  } catch (err) {
    console.error("populateConditionsForm failed:", err);
    // Send debug log to server for diagnosis
    try {
      await fetch('/api/debug/log', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: 'populateConditionsForm failure', details: String(err) }),
      });
    } catch (e) {
      // ignore
    }
    // Best-effort: populate only boundary conditions and fluid to avoid blanks
    try {
      const bc = cfg.boundary_conditions || {};
      const fl = cfg.fluid || {};
      const f = document.getElementById('conditions-form');
      if (f) {
        setFieldValue(f, 'Pt_in', convertSiStringToDisplay(String(bc.Pt_in ?? ''), 'pressure', getInputUnitLabel('Pt_in') || 'Pa'));
        setFieldValue(f, 'Tt_in', convertSiStringToDisplay(String(bc.Tt_in ?? ''), 'temperature', getInputUnitLabel('Tt_in') || 'K'));
        setFieldValue(f, 'Ps_out', convertSiStringToDisplay(String(bc.Ps_out ?? ''), 'pressure', getInputUnitLabel('Ps_out') || 'Pa'));
        setFieldValue(f, 'working_fluid', fl.working_fluid || 'air');
      }
    } catch (e2) {
      // swallow secondary errors
      console.error('fallback population failed', e2);
    }
  }

  try {
    populateGridForm(cfg);
  } catch (err) {
    console.error('populateGridForm failed:', err);
    try {
      await fetch('/api/debug/log', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: 'populateGridForm failure', details: String(err) }),
      });
    } catch (e) {
      // ignore
    }
  }
}


/**
 * Apply a last_result payload to global UI state and render
 */
function applyLastResultToUI(last, caseRef) {
  plotData = last.plots || {};
  tableRows = last.table_rows || [];
  csvContent = last.csv || "";
  const fields = last.plot_fields || Object.keys(plotData);
  lastPlotFields = fields;
  lastRunCount = last.run_count || 1;
  lastDiagnostics = last.diagnostics || null;
  renderPlots(fields);
  renderTable(tableRows);
  // Report summary depends on loaded case-config forms; defer until ready.
  rerenderReportIfCaseConfigReady(caseRef);
  const dlBtn = document.getElementById("btn-download-csv");
  if (dlBtn) dlBtn.disabled = !csvContent;
}

async function refreshLastResultForCase(
  projectName,
  caseName,
  {
    preferFiles = "1",
    cache = true,
    expectedSelectionToken = null,
  } = {},
) {
  const last = await apiFetch(`${projectCaseUrl(projectName, caseName)}/last_result?prefer_files=${preferFiles}`);
  if (!last) return null;
  if (expectedSelectionToken !== null && expectedSelectionToken !== caseSelectionToken) return null;
  const caseRef = `${projectName}/${caseName}`;
  if (cache) caseResultCache.set(caseRef, last);
  applyLastResultToUI(last, caseRef);
  return last;
}

async function createProject(projectName) {
  clearCaseError();
  await apiFetch("/api/cases/projects/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name: projectName }),
  });
  await loadProjectTree(projectName);
}

async function createProjectInteractive() {
  const projectName = window.prompt("New project name", "");
  if (!projectName || !projectName.trim()) return;
  try {
    await createProject(projectName.trim());
  } catch (e) {
    showCaseErrorMessage(e.message);
  }
}

async function createCase(projectName, caseName) {
  clearCaseError();
  await apiFetch(`${projectCasesBaseUrl(projectName)}/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name: caseName }),
  });
  await loadProjectTree(projectName);
  await selectCase(projectName, caseName);
}

async function createCaseInteractive(projectName) {
  if (!projectName) {
    showCaseErrorMessage("Create or select a project first.");
    return;
  }
  const caseName = window.prompt("New case name", "");
  if (!caseName || !caseName.trim()) return;
  try {
    await createCase(projectName, caseName.trim());
  } catch (e) {
    showCaseErrorMessage(e.message);
  }
}

async function renameProjectInteractive(projectName) {
  if (!projectName) {
    showCaseErrorMessage("Select a project first.");
    return;
  }
  const newName = window.prompt("New project name", projectName);
  if (!newName || !newName.trim() || newName.trim() === projectName) return;
  clearCaseError();
  try {
    const result = await apiFetch(`/api/cases/projects/${encodeURIComponent(projectName)}/rename`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ new_name: newName.trim() }),
    });
    activeProjectName = result.name || newName.trim();
    expandedProjects.add(activeProjectName);
    await loadProjectTree(activeProjectName);
    if (activeCaseName) {
      await selectCase(activeProjectName, activeCaseName);
    }
  } catch (e) {
    showCaseErrorMessage(e.message);
  }
}

async function deleteProjectInteractive(projectName) {
  if (!projectName) {
    showCaseErrorMessage("Select a project first.");
    return;
  }
  if (!window.confirm(`Delete project ${projectName} and all contained cases?`)) return;
  clearCaseError();
  try {
    await apiFetch(`/api/cases/projects/${encodeURIComponent(projectName)}`, { method: "DELETE" });
    expandedProjects.delete(projectName);
    if (activeProjectName === projectName) {
      activeProjectName = null;
      activeCaseName = null;
    }
    updateActiveCaseLabel();
    await loadProjectTree();
  } catch (e) {
    showCaseErrorMessage(e.message);
  }
}

async function exportProjectInteractive(projectName) {
  if (!projectName) {
    showCaseErrorMessage("Select a project first.");
    return;
  }
  clearCaseError();
  try {
    const archiveBlob = await apiFetchBlob(`/api/cases/projects/${encodeURIComponent(projectName)}/export`);
    const url = URL.createObjectURL(archiveBlob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${projectName}.zip`;
    anchor.click();
    URL.revokeObjectURL(url);
  } catch (e) {
    showCaseErrorMessage(e.message);
  }
}

async function renameCaseInteractive(projectName, caseName) {
  if (!projectName || !caseName) {
    showCaseErrorMessage("Select a case first.");
    return;
  }
  const newName = window.prompt("New case name", caseName);
  if (!newName || !newName.trim() || newName.trim() === caseName) return;
  clearCaseError();
  try {
    const result = await apiFetch(`${projectCaseUrl(projectName, caseName)}/rename`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ new_name: newName.trim() }),
    });
    activeCaseName = null;
    await loadProjectTree(result.project || projectName);
    await selectCase(result.project || projectName, result.name || newName.trim());
  } catch (e) {
    showCaseErrorMessage(e.message);
  }
}

async function duplicateCaseInteractive(projectName, caseName) {
  if (!projectName || !caseName) {
    showCaseErrorMessage("Select a case first.");
    return;
  }
  const newName = window.prompt("New case name", `${caseName}_copy`);
  if (!newName || !newName.trim()) return;
  clearCaseError();
  try {
    const result = await apiFetch(`${projectCaseUrl(projectName, caseName)}/duplicate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ new_name: newName.trim() }),
    });
    await loadProjectTree(result.project || projectName);
    await selectCase(result.project || projectName, result.name || newName.trim());
  } catch (e) {
    showCaseErrorMessage(e.message);
  }
}

async function deleteCaseInteractive(projectName, caseName) {
  if (!projectName || !caseName) {
    showCaseErrorMessage("Select a case first.");
    return;
  }
  if (!window.confirm(`Delete case ${projectName} / ${caseName}?`)) return;
  clearCaseError();
  try {
    await apiFetch(projectCaseUrl(projectName, caseName), { method: "DELETE" });
    if (activeProjectName === projectName && activeCaseName === caseName) {
      activeCaseName = null;
    }
    updateActiveCaseLabel();
    await loadProjectTree(projectName);
  } catch (e) {
    showCaseErrorMessage(e.message);
  }
}

async function exportCaseInteractive(projectName, caseName) {
  if (!projectName || !caseName) {
    showCaseErrorMessage("Select a case first.");
    return;
  }
  clearCaseError();
  try {
    const yamlText = await apiFetchText(`${projectCaseUrl(projectName, caseName)}/export`);
    const blob = new Blob([yamlText], { type: "application/x-yaml" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${projectName}_${caseName}.yaml`;
    anchor.click();
    URL.revokeObjectURL(url);
  } catch (e) {
    showCaseErrorMessage(e.message);
  }
}

async function moveCaseToProject(sourceProjectName, caseName, targetProjectName) {
  if (!sourceProjectName || !caseName || !targetProjectName || sourceProjectName === targetProjectName) {
    return;
  }
  clearCaseError();
  try {
    const result = await apiFetch(`${projectCaseUrl(sourceProjectName, caseName)}/rename`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ new_name: caseName, target_project: targetProjectName }),
    });
    expandedProjects.add(targetProjectName);
    await loadProjectTree(targetProjectName);
    if (activeProjectName === sourceProjectName && activeCaseName === caseName) {
      await selectCase(result.project || targetProjectName, result.name || caseName);
    }
  } catch (e) {
    showCaseErrorMessage(e.message);
  } finally {
    draggedCaseRef = null;
    clearTreeDropTargets();
  }
}

async function executeTreeContextAction(actionId) {
  const target = contextMenuTarget;
  closeTreeContextMenu();
  if (actionId === "new-project") {
    await createProjectInteractive();
    return;
  }
  if (actionId === "refresh-tree") {
    await loadProjectTree(activeProjectName);
    return;
  }
  if (actionId === "new-case") {
    await createCaseInteractive(target.projectName || getActiveProjectName());
    return;
  }
  if (actionId === "rename-project") {
    await renameProjectInteractive(target.projectName || getActiveProjectName());
    return;
  }
  if (actionId === "delete-project") {
    await deleteProjectInteractive(target.projectName || getActiveProjectName());
    return;
  }
  if (actionId === "export-project") {
    await exportProjectInteractive(target.projectName || getActiveProjectName());
    return;
  }
  if (actionId === "rename-case") {
    await renameCaseInteractive(target.projectName || getActiveProjectName(), target.caseName || activeCaseName);
    return;
  }
  if (actionId === "duplicate-case") {
    await duplicateCaseInteractive(target.projectName || getActiveProjectName(), target.caseName || activeCaseName);
    return;
  }
  if (actionId === "delete-case") {
    await deleteCaseInteractive(target.projectName || getActiveProjectName(), target.caseName || activeCaseName);
    return;
  }
  if (actionId === "export-case") {
    await exportCaseInteractive(target.projectName || getActiveProjectName(), target.caseName || activeCaseName);
  }
}

const treeShell = document.getElementById("project-tree-shell");
if (treeShell) {
  treeShell.addEventListener("contextmenu", event => {
    if (event.target.closest(".tree-row")) return;
    event.preventDefault();
    openTreeContextMenu(event.clientX, event.clientY, { type: "root" });
  });
}

const treeContextMenu = document.getElementById("tree-context-menu");
if (treeContextMenu) {
  treeContextMenu.addEventListener("click", event => {
    const button = event.target.closest("button[data-action]");
    if (!button) return;
    void executeTreeContextAction(button.dataset.action);
  });
}

document.addEventListener("click", event => {
  if (event.target.closest("#tree-context-menu")) return;
  closeTreeContextMenu();
});

document.addEventListener("keydown", event => {
  if (event.key === "Escape") closeTreeContextMenu();
});

window.addEventListener("resize", closeTreeContextMenu);

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
  setFieldValue(f, "inlet_wetness", convertSiStringToDisplay(fl.inlet_wetness ?? "", "dimensionless", getInputUnitLabel("inlet_wetness")));
  // BC fields: convert from SI (stored) to current display unit
  setFieldValue(f, "Pt_in",  convertSiStringToDisplay(String(bc.Pt_in  ?? ""), "pressure",    getInputUnitLabel("Pt_in")  || "Pa"));
  setFieldValue(f, "Tt_in",  convertSiStringToDisplay(String(bc.Tt_in  ?? ""), "temperature", getInputUnitLabel("Tt_in")  || "K"));
  setFieldValue(f, "Ps_out", convertSiStringToDisplay(String(bc.Ps_out ?? ""), "pressure",    getInputUnitLabel("Ps_out") || "Pa"));
  setFieldValue(f, "droplet_velocity_in", di.droplet_velocity_in ?? "");
  setFieldValue(f, "injection_mode", di.injection_mode ?? "droplet_injection");
  updateInjectionModeState(di.injection_mode ?? "droplet_injection");
  setFieldValue(f, "liquid_material", di.liquid_material ?? "water");
  updateLiquidMaterialState(di.liquid_material ?? "water");
  setSelectedInputBasis(f, di.input_basis ?? "diameter_based");
  setFieldValue(f, "liquid_jet_diameter", convertSiStringToDisplay(di.liquid_jet_diameter ?? "", "diameter", getInputUnitLabel("liquid_jet_diameter")));
  setFieldValue(f, "liquid_mass_flow_rate", convertSiStringToDisplay(di.liquid_mass_flow_rate ?? "", "mass_flow", getInputUnitLabel("liquid_mass_flow_rate")));
  setFieldValue(f, "liquid_velocity", convertSiStringToDisplay(di.liquid_velocity ?? "", "velocity", getInputUnitLabel("liquid_velocity")));
  setFieldValue(f, "liquid_density", convertSiStringToDisplay(di.liquid_density ?? "", "density", getInputUnitLabel("liquid_density")));
  updateLiquidJetInputModeUI();
  recomputeLiquidJetDerivedField();
  setFieldValue(f, "liquid_viscosity", convertSiStringToDisplay(di.liquid_viscosity ?? "", "viscosity", getInputUnitLabel("liquid_viscosity")));
  setFieldValue(f, "surface_tension", convertSiStringToDisplay(di.surface_tension ?? "", "surface_tension", getInputUnitLabel("surface_tension")));
  setFieldValue(f, "primary_breakup_model", di.primary_breakup_model ?? "empirical");
  setFieldValue(f, "primary_breakup_coefficient", convertSiStringToDisplay(di.primary_breakup_coefficient ?? "", "dimensionless", getInputUnitLabel("primary_breakup_coefficient")));
  setFieldValue(f, "initial_SMD_model", di.initial_SMD_model ?? "fraction_of_jet");
  setFieldValue(f, "water_mass_flow_rate", convertSiStringToDisplay(di.water_mass_flow_rate ?? "", "mass_flow", getInputUnitLabel("water_mass_flow_rate")));
  setFieldValue(f, "water_mass_flow_rate_percent", convertSiStringToDisplay(di.water_mass_flow_rate_percent ?? "", "dimensionless", getInputUnitLabel("water_mass_flow_rate_percent")));
  const hasKgPerS = di.water_mass_flow_rate !== undefined && di.water_mass_flow_rate !== null && String(di.water_mass_flow_rate) !== "";
  const hasPercent = di.water_mass_flow_rate_percent !== undefined && di.water_mass_flow_rate_percent !== null && String(di.water_mass_flow_rate_percent) !== "";
  setFieldValue(
    f,
    "water_mass_flow_mode",
    hasPercent && !hasKgPerS ? "percent" : "kg_per_s"
  );
  updateWaterMassFlowSectionUI();
  setFieldValue(f, "droplet_diameter_mean_in", convertSiStringToDisplay(di.droplet_diameter_mean_in ?? "", "diameter", getInputUnitLabel("droplet_diameter_mean_in")));
  setFieldValue(f, "droplet_diameter_max_in",  convertSiStringToDisplay(di.droplet_diameter_max_in  ?? "", "diameter", getInputUnitLabel("droplet_diameter_max_in")));
  setFieldValue(f, "coupling_mode", ms.coupling_mode ?? "one_way");
  const breakupModel = ms.breakup_model || "weber_critical";
  setFieldValue(f, "breakup_model", breakupModel);
  updateBreakupModelState(breakupModel);
  // Use stored values when present; fall back to model defaults so fields are
  // never blank after selecting a model.
  const wd = MODEL_DEFAULTS.weber_critical;
  const kd = MODEL_DEFAULTS.khrt;
  setFieldValue(f, "critical_weber_number", convertSiStringToDisplay(ms.critical_weber_number ?? wd.critical_weber_number, "dimensionless", getInputUnitLabel("critical_weber_number")));
  setFieldValue(f, "breakup_factor_mean",   convertSiStringToDisplay(ms.breakup_factor_mean   ?? wd.breakup_factor_mean, "dimensionless", getInputUnitLabel("breakup_factor_mean")));
  setFieldValue(f, "breakup_factor_max",    convertSiStringToDisplay(ms.breakup_factor_max    ?? wd.breakup_factor_max, "dimensionless", getInputUnitLabel("breakup_factor_max")));
  setFieldValue(f, "khrt_B0",          convertSiStringToDisplay(ms.khrt_B0          ?? kd.khrt_B0, "dimensionless", getInputUnitLabel("khrt_B0")));
  setFieldValue(f, "khrt_B1",          convertSiStringToDisplay(ms.khrt_B1          ?? kd.khrt_B1, "dimensionless", getInputUnitLabel("khrt_B1")));
  setFieldValue(f, "khrt_Crt",         convertSiStringToDisplay(ms.khrt_Crt         ?? kd.khrt_Crt, "dimensionless", getInputUnitLabel("khrt_Crt")));
  setFieldValue(f, "liquid_density",   convertSiStringToDisplay(ms.liquid_density   ?? kd.liquid_density, "density", getInputUnitLabel("liquid_density")));
  setFieldValue(f, "liquid_viscosity", convertSiStringToDisplay(ms.liquid_viscosity ?? kd.liquid_viscosity, "viscosity", getInputUnitLabel("liquid_viscosity")));
  setFieldValue(f, "khrt_liquid_density",   convertSiStringToDisplay(ms.liquid_density   ?? kd.liquid_density, "density", getInputUnitLabel("khrt_liquid_density")));
  setFieldValue(f, "khrt_liquid_viscosity", convertSiStringToDisplay(ms.liquid_viscosity ?? kd.liquid_viscosity, "viscosity", getInputUnitLabel("khrt_liquid_viscosity")));
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

/**
 * Like parseNumericOrList but first converts the value from the field's
 * currently-selected display unit back to SI.
 */
function parseBcValueSi(rawValue, fieldName, label, opts = {}) {
  const unitLabel = getInputUnitLabel(fieldName);
  const group     = INPUT_FIELD_UNIT_GROUP[fieldName];
  const siStr = (unitLabel && group)
    ? convertDisplayStringToSi(rawValue, group, unitLabel)
    : rawValue;
  return parseNumericOrList(siStr, label, opts);
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
      Pt_in:  parseBcValueSi(f.elements.Pt_in.value,  "Pt_in",  "Inlet total pressure P₀"),
      Tt_in:  parseBcValueSi(f.elements.Tt_in.value,  "Tt_in",  "Inlet total temperature T₀"),
      Ps_out: parseBcValueSi(f.elements.Ps_out.value, "Ps_out", "Outlet static pressure P₂"),
    },
    droplet_injection: {
      droplet_velocity_in:      isLiquidJet ? null : parseBcValueSi(f.elements.droplet_velocity_in.value, "droplet_velocity_in", "Initial droplet velocity"),
      injection_mode:           injectionMode,
      input_basis:              getSelectedInputBasis(f),
      liquid_material:          (f.elements.liquid_material && f.elements.liquid_material.value) || "water",
      liquid_jet_diameter:      parseBcValueSi(f.elements.liquid_jet_diameter?.value, "liquid_jet_diameter", "Liquid-jet diameter", { optional: true }),
      liquid_mass_flow_rate:    parseBcValueSi(f.elements.liquid_mass_flow_rate?.value, "liquid_mass_flow_rate", "Liquid mass flow rate", { optional: true }),
      liquid_velocity:          parseBcValueSi(f.elements.liquid_velocity?.value, "liquid_velocity", "Liquid velocity", { optional: true }),
      liquid_density:           parseBcValueSi(f.elements.liquid_density?.value, "liquid_density", "Liquid density", { optional: true }),
      liquid_viscosity:         parseBcValueSi(f.elements.liquid_viscosity?.value, "liquid_viscosity", "Liquid viscosity", { optional: true }),
      surface_tension:          parseBcValueSi(f.elements.surface_tension?.value, "surface_tension", "Surface tension", { optional: true }),
      primary_breakup_model:    (f.elements.primary_breakup_model && f.elements.primary_breakup_model.value) || null,
      primary_breakup_coefficient: parseBcValueSi(f.elements.primary_breakup_coefficient?.value, "primary_breakup_coefficient", "Primary breakup coefficient", { optional: true }),
      initial_SMD_model:        (f.elements.initial_SMD_model && f.elements.initial_SMD_model.value) || null,
      droplet_diameter_mean_in: isLiquidJet ? null : parseBcValueSi(f.elements.droplet_diameter_mean_in.value, "droplet_diameter_mean_in", "Mean droplet diameter"),
      droplet_diameter_max_in:  isLiquidJet ? null : parseBcValueSi(f.elements.droplet_diameter_max_in.value,  "droplet_diameter_max_in",  "Maximum droplet diameter"),
    },
    models: {
      coupling_mode:         couplingMode,
      breakup_model:         f.elements.breakup_model.value,
      critical_weber_number: parseBcValueSi(f.elements.critical_weber_number.value, "critical_weber_number", "Critical Weber number", { optional: true }),
      breakup_factor_mean:   parseBcValueSi(f.elements.breakup_factor_mean.value, "breakup_factor_mean", "Breakup factor — mean diameter", { optional: true }),
      breakup_factor_max:    parseBcValueSi(f.elements.breakup_factor_max.value, "breakup_factor_max", "Breakup factor — maximum diameter", { optional: true }),
      khrt_B0:               parseBcValueSi(f.elements.khrt_B0.value, "khrt_B0", "KH wavelength coefficient B₀", { optional: true }),
      khrt_B1:               parseBcValueSi(f.elements.khrt_B1.value, "khrt_B1", "KH breakup time coefficient B₁", { optional: true }),
      khrt_Crt:              parseBcValueSi(f.elements.khrt_Crt.value, "khrt_Crt", "RT wavelength coefficient C_RT", { optional: true }),
      liquid_density:        parseBcValueSi(f.elements.khrt_liquid_density?.value, "khrt_liquid_density", "Liquid density (KH-RT)", { optional: true }),
      liquid_viscosity:      parseBcValueSi(f.elements.khrt_liquid_viscosity?.value, "khrt_liquid_viscosity", "Liquid viscosity (KH-RT)", { optional: true }),
    },
  };
  const wetness = parseBcValueSi(f.elements.inlet_wetness.value, "inlet_wetness", "Inlet wetness", { optional: true });
  cfg.fluid.inlet_wetness = wetness === null ? null : wetness;
  const waterMassFlowMode = f.elements.water_mass_flow_mode.value;
  const waterMassFlowRate = parseBcValueSi(f.elements.water_mass_flow_rate.value, "water_mass_flow_rate", "Water mass flow rate", { optional: true });
  const waterMassFlowRatePercent = parseBcValueSi(f.elements.water_mass_flow_rate_percent.value, "water_mass_flow_rate_percent", "Water mass flow rate percent", { optional: true });
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
      Pt_in:  parseBcValueSi(f.elements.Pt_in.value,  "Pt_in",  "Inlet total pressure P₀"),
      Tt_in:  parseBcValueSi(f.elements.Tt_in.value,  "Tt_in",  "Inlet total temperature T₀"),
      Ps_out: parseBcValueSi(f.elements.Ps_out.value, "Ps_out", "Outlet static pressure P₂"),
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
      droplet_diameter_mean_in: isLiquidJet ? null : parseBcValueSi(f.elements.droplet_diameter_mean_in.value, "droplet_diameter_mean_in", "Mean droplet diameter"),
      droplet_diameter_max_in:  isLiquidJet ? null : parseBcValueSi(f.elements.droplet_diameter_max_in.value,  "droplet_diameter_max_in",  "Maximum droplet diameter"),
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
    rerenderReportIfCaseConfigReady();
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
  // Grid fields: convert from SI (stored) to current display unit
  setFieldValue(f, "x_start", convertSiStringToDisplay(String(geo.x_start ?? 0), "length", getInputUnitLabel("x_start") || "m"));
  setFieldValue(f, "x_end", convertSiStringToDisplay(String(geo.x_end ?? 0.1), "length", getInputUnitLabel("x_end") || "m"));
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

  const padLeft = 54;
  const padRight = 18;
  const padTop = 28;
  const padBottom = 42;
  const xMin = Math.min(...xs), xMax = Math.max(...xs);
  const AMin = Math.min(...As), AMax = Math.max(...As);
  const xRange = xMax - xMin || 1, ARange = AMax - AMin || 1;

  const toCanvasX = x => padLeft + (x - xMin) / xRange * (W - padLeft - padRight);
  const toCanvasY = A => (H - padBottom) - (A - AMin) / ARange * (H - padTop - padBottom);

  ctx.strokeStyle = "#d9e2ec";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(padLeft, padTop);
  ctx.lineTo(padLeft, H - padBottom);
  ctx.lineTo(W - padRight, H - padBottom);
  ctx.stroke();

  ctx.beginPath();
  ctx.strokeStyle = "#3a78b5";
  ctx.lineWidth = 2;
  ctx.moveTo(toCanvasX(xs[0]), toCanvasY(As[0]));
  for (let i = 1; i < xs.length; i++) ctx.lineTo(toCanvasX(xs[i]), toCanvasY(As[i]));
  ctx.stroke();

  ctx.fillStyle = "#334155";
  ctx.font = "600 12px system-ui";
  ctx.textAlign = "center";
  ctx.fillText("x vs Area", W / 2, 16);

  ctx.fillStyle = "#666";
  ctx.font = "11px system-ui";
  ctx.textAlign = "center";
  ctx.fillText(`x min ${xMin.toExponential(2)}`, toCanvasX(xMin), H - 18);
  ctx.fillText(`x max ${xMax.toExponential(2)}`, toCanvasX(xMax), H - 18);
  ctx.fillText("x [m]", W / 2, H - 6);
  ctx.textAlign = "right";
  ctx.fillText(`A max ${AMax.toExponential(2)}`, padLeft - 4, toCanvasY(AMax) + 4);
  ctx.fillText(`A min ${AMin.toExponential(2)}`, padLeft - 4, toCanvasY(AMin) + 4);

  ctx.save();
  ctx.translate(14, H / 2);
  ctx.rotate(-Math.PI / 2);
  ctx.textAlign = "center";
  ctx.fillText("Area [m²]", 0, 0);
  ctx.restore();
}

function readGridForm() {
  const f = document.getElementById("grid-form");
  const area = readAreaTable();
  // Convert from display unit back to SI
  const xStartDisplay = f.elements.x_start.value;
  const xEndDisplay = f.elements.x_end.value;
  const xStart = parseFloat(convertDisplayStringToSi(String(xStartDisplay), "length", getInputUnitLabel("x_start") || "m"));
  const xEnd = parseFloat(convertDisplayStringToSi(String(xEndDisplay), "length", getInputUnitLabel("x_end") || "m"));
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
    rerenderReportIfCaseConfigReady();
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
    lastPlotFields = fields;
    lastRunCount = data.run_count || 1;
    lastDiagnostics = data.diagnostics || null;
    const runCount = data.run_count || 1;
    const statusMessage = runCount > 1
      ? `✓ Simulation sweep completed successfully (${runCount} runs).`
      : "✓ Simulation completed successfully.";
    setStatus(solveStatus, statusMessage, "success");
    const caseRef = getActiveCaseRef();
    if (caseRef) {
      caseResultCache.set(caseRef, {
        plots: plotData,
        table_rows: tableRows,
        csv: csvContent,
        plot_fields: fields,
        run_count: runCount,
        diagnostics: lastDiagnostics,
      });
      applyLastResultToUI(caseResultCache.get(caseRef), caseRef);
    }
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
    label.appendChild(document.createTextNode(" " + formatPlotFieldLabel(field)));
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
    const title = document.createElement("div");
    title.className = "plot-card-title";
    title.textContent = formatPlotFieldLabel(field);
    const img = document.createElement("img");
    img.src = "data:image/png;base64," + b64;
    img.alt = field;
    card.appendChild(title);
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
    // Display 'pressure' as 'Static pressure' in table headers
    th.textContent = (h === "pressure") ? "Static pressure" : h;
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

function collectSummaryConditions() {
  const conditionsForm = document.getElementById("conditions-form");
  if (!conditionsForm) return [];
  return [
    `Project / Case: ${formatReportValue(activeProjectName || defaultProjectName)} / ${formatReportValue(activeCaseName)}`,
    `Working fluid: ${formatReportValue(conditionsForm.elements.working_fluid?.value)}`,
    `Inlet total pressure P0 [${getInputUnitLabel("Pt_in") || "Pa"}]: ${formatReportValue(conditionsForm.elements.Pt_in?.value)}`,
    `Inlet total temperature T0 [${getInputUnitLabel("Tt_in") || "K"}]: ${formatReportValue(conditionsForm.elements.Tt_in?.value)}`,
    `Outlet static pressure P2 [${getInputUnitLabel("Ps_out") || "Pa"}]: ${formatReportValue(conditionsForm.elements.Ps_out?.value)}`,
    `Injection mode: ${formatReportValue(conditionsForm.elements.injection_mode?.value)}`,
    `Breakup model: ${formatReportValue(conditionsForm.elements.breakup_model?.value)}`,
    `Coupling mode: ${formatReportValue(conditionsForm.elements.coupling_mode?.value)}`,
  ];
}

function collectGridSummary() {
  const gridForm = document.getElementById("grid-form");
  const areaRows = Array.from(document.querySelectorAll("#area-table-body tr")).length;
  if (!gridForm) return [];
  return [
    `x start [${getInputUnitLabel("x_start") || "m"}]: ${formatReportValue(gridForm.elements.x_start?.value)}`,
    `x end [${getInputUnitLabel("x_end") || "m"}]: ${formatReportValue(gridForm.elements.x_end?.value)}`,
    `Number of cells: ${formatReportValue(gridForm.elements.n_cells?.value)}`,
    `Area table points: ${areaRows}`,
  ];
}

function buildReportList(items) {
  return `<ul class="report-list">${items.map(item => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`;
}

function buildReportTable(rows) {
  if (!rows || rows.length === 0) {
    return '<div class="report-empty">No table rows are available for the latest result.</div>';
  }
  const headers = Object.keys(rows[0]);
  const previewRows = rows.slice(0, 12);
  const headHtml = headers.map(header => `<th>${escapeHtml(header)}</th>`).join("");
  const bodyHtml = previewRows.map(row => {
    const cells = headers.map(header => `<td>${escapeHtml(typeof row[header] === "number" ? row[header].toPrecision(5) : String(row[header]))}</td>`).join("");
    return `<tr>${cells}</tr>`;
  }).join("");
  const note = rows.length > previewRows.length
    ? `<div class="report-note">Showing first ${previewRows.length} of ${rows.length} rows. See the Table tab for the full dataset.</div>`
    : `<div class="report-note">${rows.length} rows included from the latest result.</div>`;
  return `<div class="report-table-wrapper"><table class="report-table"><thead><tr>${headHtml}</tr></thead><tbody>${bodyHtml}</tbody></table></div>${note}`;
}

function buildReportGraphs(fields) {
  const availableFields = (fields || []).filter(field => plotData[field]);
  if (availableFields.length === 0) {
    return '<div class="report-empty">No graphs are available for the latest result.</div>';
  }
  return `<div class="report-graph-grid">${availableFields
    .map(field => `<article class="report-graph-card"><h5>${escapeHtml(formatPlotFieldLabel(field))}</h5><img src="data:image/png;base64,${plotData[field]}" alt="${escapeHtml(field)}" /></article>`)
    .join("")}</div>`;
}

function collectDiscussionPoints() {
  const diagnosticsMessages = Array.isArray(lastDiagnostics?.messages) ? lastDiagnostics.messages : [];
  const points = [
    `Completed runs in latest solve: ${lastRunCount || 0}.`,
    `Graphs generated: ${lastPlotFields.length}.`,
    `Tabulated result rows available: ${tableRows.length}.`,
  ];
  if (diagnosticsMessages.length > 0) {
    points.push(`Diagnostics messages reported: ${diagnosticsMessages.length}. Review solver diagnostics alongside graph and table trends.`);
  } else {
    points.push("No additional diagnostics messages were returned with the latest result payload.");
  }
  return points;
}

function collectConclusionPoints() {
  return [
    `The latest solve has been summarized into this report for ${formatReportValue(activeCaseName)}.`,
    "Use Graph and Table sections for quantitative inspection, then refine the case settings if further iteration is required.",
  ];
}

function renderReport() {
  const container = document.getElementById("report-content");
  if (!container) return;
  if (!activeCaseName || tableRows.length === 0) {
    container.innerHTML = '<div class="report-empty">Run Solve to generate a report.</div>';
    return;
  }

  const sections = [
    { title: "1. Summary Conditions", body: buildReportList(collectSummaryConditions()) },
    { title: "2. Grid", body: buildReportList(collectGridSummary()) },
    {
      title: "3. Graph",
      body: `${buildReportList([
        `Graph fields generated: ${lastPlotFields.length}`,
        `Latest solve run count: ${lastRunCount || 1}`,
      ])}${buildReportGraphs(lastPlotFields)}`,
    },
    {
      title: "4. Table",
      body: `${buildReportList([
        `Table row count: ${tableRows.length}`,
        `CSV export ready: ${csvContent ? "yes" : "no"}`,
      ])}${buildReportTable(tableRows)}`,
    },
    { title: "5. Discussion", body: buildReportList(collectDiscussionPoints()) },
    { title: "6. Conclusion", body: buildReportList(collectConclusionPoints()) },
  ];

  container.innerHTML = sections
    .map(section => `<section class="report-section"><h4>${escapeHtml(section.title)}</h4>${section.body}</section>`)
    .join("");
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

document.getElementById("chat-form").addEventListener("submit", async event => {
  event.preventDefault();
  await submitChatMessage();
});

document.getElementById("btn-clear-chat").addEventListener("click", () => {
  void clearActiveCaseChat();
});

document.getElementById("btn-new-chat-thread").addEventListener("click", async () => {
  try {
    await createNewChatThread("New chat");
    updateChatPanelState();
  } catch (error) {
    setChatStatus(`Failed creating chat: ${error.message}`, true);
  }
});

document.getElementById("chat-input").addEventListener("keydown", async event => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    await submitChatMessage();
  }
});

// ── Settings tab: unit preferences ────────────────────────────────────────
async function loadUnitGroups() {
  try {
    console.log("Starting loadUnitGroups...");
    const groups  = await apiFetch("/api/units/groups");
    const current = await apiFetch("/api/units/preferences");
    console.log("Unit groups loaded:", groups);
    console.log("Current preferences:", current);

    // Store specs for client-side conversion
    unitGroupSpecs = groups;

    // Settings tab removed — unit-group controls are provided via Graph dialog

    // ── Inline input-field unit selectors ────────────────────────────────
    const selectors = document.querySelectorAll(".unit-input-sel");
    console.log(`Found ${selectors.length} unit-input-sel elements`);
    
    selectors.forEach((sel, idx) => {
      const group = sel.dataset.group;
      const fieldName = sel.dataset.field;
      console.log(`[${idx}] Processing selector for field '${fieldName}' (group '${group}')`);
      
      // Skip if no unit group (dimensionless or special)
      if (!group || !groups[group]) {
        console.log(`  → Skipping (no group or group not in API response)`);
        sel.style.display = "none";
        return;
      }
      
      sel.innerHTML = "";
      const optionLabels = Object.keys(groups[group]);
      console.log(`  → Adding ${optionLabels.length} options: ${optionLabels.join(", ")}`);
      optionLabels.forEach(opt => {
        const option = document.createElement("option");
        option.value = opt;
        option.textContent = opt;
        if (opt === current[group]) option.selected = true;
        sel.appendChild(option);
      });
      sel.style.display = "";  // Ensure visible if there are options

      // When unit changes: convert the currently-displayed value
      sel.addEventListener("change", () => {
        const input = document.querySelector(`[name="${fieldName}"]`);
        if (!input || (input.value && input.value.trim ? input.value.trim() === "" : input.value === "")) return;
        const prevUnit = sel._prevUnit || sel.value;
        const newUnit  = sel.value;
        if (prevUnit === newUnit) return;
        // Convert displayed value: prevUnit-display → SI → newUnit-display
        const siStr = convertDisplayStringToSi(String(input.value), group, prevUnit);
        input.value = convertSiStringToDisplay(siStr, group, newUnit);
        sel._prevUnit = newUnit;
      });
      sel._prevUnit = sel.value;

      // Convert the default field value from SI to the preferred display unit.
      // The HTML default values are always in SI.
      const input = document.querySelector(`[name="${fieldName}"]`);
      if (input && (input.value && input.value.trim ? input.value.trim() !== "" : input.value !== "")) {
        const prefUnit = current[group];
        if (prefUnit) {
          input.value = convertSiStringToDisplay(String(input.value), group, prefUnit);
        }
      }
    });

  } catch (e) {
    console.error("Failed to load unit groups:", e);
  }
}

// Small transient toast for user feedback
function showToast(message, timeout = 2500) {
  try {
    const toast = document.createElement("div");
    toast.className = "temp-toast";
    toast.textContent = message;
    toast.style.position = "fixed";
    toast.style.right = "16px";
    toast.style.bottom = "16px";
    toast.style.background = "#222";
    toast.style.color = "#fff";
    toast.style.padding = "8px 12px";
    toast.style.borderRadius = "6px";
    toast.style.boxShadow = "0 2px 8px rgba(0,0,0,0.3)";
    toast.style.zIndex = 2000;
    document.body.appendChild(toast);
    setTimeout(() => { toast.style.opacity = "0"; }, timeout - 400);
    setTimeout(() => { try { document.body.removeChild(toast); } catch (_e) {} }, timeout);
  } catch (e) {
    console.warn("showToast failed", e);
  }
}

const btnSaveUnits = document.getElementById("btn-save-units");
if (btnSaveUnits) {
  btnSaveUnits.addEventListener("click", async () => {
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
      if (statusEl) {
        statusEl.textContent = "✓ Units applied (re-run to update plots)";
        setTimeout(() => { statusEl.textContent = ""; }, 3000);
      }
    } catch (e) {
      if (statusEl) statusEl.textContent = "Error: " + e.message;
    }
  });
}

// ── Graph settings dialog and per-unit Apply handlers ────────────────────
async function openGraphSettingsDialog() {
  try {
    const groups = unitGroupSpecs || await apiFetch("/api/units/groups");
    const current = await apiFetch("/api/units/preferences");
    const container = document.getElementById("graph-unit-group-controls");
    if (!container) return;
    container.innerHTML = "";
    Object.entries(groups).forEach(([group, options]) => {
      const row = document.createElement("div");
      row.className = "unit-group-row";
      const label = document.createElement("label");
      label.textContent = group;
      const sel = document.createElement("select");
      sel.dataset.group = group;
      Object.keys(options).forEach(opt => {
        const o = document.createElement("option");
        o.value = opt;
        o.textContent = opt;
        if (opt === current[group]) o.selected = true;
        sel.appendChild(o);
      });
      const applyBtn = document.createElement("button");
      applyBtn.type = "button";
      applyBtn.className = "mini-apply-btn";
      applyBtn.textContent = "Apply";
      applyBtn.addEventListener("click", async () => {
        const statusEl = document.getElementById("graph-units-status");
        try {
          const payload = {};
          payload[group] = sel.value;
          await apiFetch("/api/units/preferences", {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
          });
          statusEl.textContent = "✓ Units applied, updating plots...";
          // Reload last_result for active case to regenerate plots with new units
          if (activeProjectName && activeCaseName) {
            await refreshLastResultForCase(activeProjectName, activeCaseName, { preferFiles: "1", cache: true });
          }
          statusEl.textContent = "✓ Units applied";
          // Close dialog and show success toast
          try { dialog.close(); } catch (_e) { dialog.classList.add("hidden"); }
          showToast("Units applied");
          setTimeout(() => { statusEl.textContent = ""; }, 2500);
        } catch (e) {
          statusEl.textContent = "Error: " + e.message;
        }
      });
      row.appendChild(label);
      row.appendChild(sel);
      row.appendChild(applyBtn);
      container.appendChild(row);
    });
    const dialog = document.getElementById("graph-settings-dialog");
    if (!dialog) return;
    if (typeof dialog.showModal === "function") {
      dialog.showModal();
    } else {
      dialog.classList.remove("hidden");
    }
  } catch (e) {
    console.error("openGraphSettingsDialog failed", e);
  }
}

document.getElementById("graphs-settings-btn").addEventListener("click", async () => {
  await openGraphSettingsDialog();
});

document.getElementById("graph-settings-close").addEventListener("click", () => {
  const dialog = document.getElementById("graph-settings-dialog");
  if (!dialog) return;
  try { dialog.close(); } catch (_e) { dialog.classList.add("hidden"); }
});

document.getElementById("graph-settings-apply-all").addEventListener("click", async () => {
  const statusEl = document.getElementById("graph-units-status");
  const container = document.getElementById("graph-unit-group-controls");
  if (!container) return;
  const updates = {};
  container.querySelectorAll("select").forEach(sel => { updates[sel.dataset.group] = sel.value; });
  try {
    await apiFetch("/api/units/preferences", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(updates),
    });
    statusEl.textContent = "✓ Units applied, updating plots...";
    if (activeProjectName && activeCaseName) {
      await refreshLastResultForCase(activeProjectName, activeCaseName, { preferFiles: "1", cache: true });
    }
    statusEl.textContent = "✓ Units applied";
    // Close dialog and show success toast
    try { document.getElementById("graph-settings-dialog")?.close(); } catch (_e) { document.getElementById("graph-settings-dialog")?.classList.add("hidden"); }
    showToast("Units applied");
    setTimeout(() => { statusEl.textContent = ""; }, 2500);
  } catch (e) {
    statusEl.textContent = "Error: " + e.message;
  }
});

// ── Initialisation ─────────────────────────────────────────────────────────
async function init() {
  console.log("init() starting...");
  initializeSidebarResizeHandle();
  initializeRightSidebarResizeHandle();
  initializeChatVoiceInput();
  initializeSummaryTab();
  console.log("About to loadProjectList...");
  await loadProjectList();
  console.log("About to loadUnitGroups...");
  await loadUnitGroups();
  console.log("About to loadChatLlmSelection...");
  loadChatLlmSelection();
  console.log("About to initializeChatLlmDialog...");
  initializeChatLlmDialog();
  console.log("About to updateChatPanelState...");
  updateChatPanelState();
  console.log("init() complete!");
}

// Wait for DOM to be fully loaded before initializing
if (document.readyState === "loading") {
  console.log("Document still loading, waiting for DOMContentLoaded...");
  document.addEventListener("DOMContentLoaded", () => {
    console.log("DOMContentLoaded fired, calling init...");
    init().catch(err => console.error("init() error:", err));
  });
} else {
  console.log("Document already loaded, calling init immediately...");
  init().catch(err => console.error("init() error:", err));
}
