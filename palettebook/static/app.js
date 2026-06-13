/**
 * PaletteBook - frontend application logic.
 *
 * This file is strongly reviewed but nevertheless largely AI generated, so feel free to suggest improvements or optimizations.
 *
 * State model:
 *   palettes   - array of { id, name, color_count }
 *   current    - full palette object { id, name, colors: [...] } | null
 *   generated  - array of hex strings from the last generation call
 */

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------
const state = {
  /** @type {Array<{id:number, name:string, color_count:number}>} */
  palettes: [],
  /** @type {{id:number, name:string, colors:Array} | null} */
  current: null,
  /** @type {string[]} */
  generated: [],
};

// ---------------------------------------------------------------------------
// DOM refs (resolved once on DOMContentLoaded)
// ---------------------------------------------------------------------------
const $ = (id) => document.getElementById(id);

// ---------------------------------------------------------------------------
// API helpers
// ---------------------------------------------------------------------------
async function api(method, path, body) {
  const opts = {
    method,
    headers: { "Content-Type": "application/json" },
  };
  if (body !== undefined) opts.body = JSON.stringify(body);
  const res = await fetch(path, opts);
  if (res.status === 204) return null;
  const json = await res.json();
  if (!res.ok) throw new Error(json.error || `HTTP ${res.status}`);
  return json;
}

const GET = (p) => api("GET", p);
const POST = (p, b) => api("POST", p, b);
const PUT = (p, b) => api("PUT", p, b);
const DELETE = (p) => api("DELETE", p);

// ---------------------------------------------------------------------------
// Sidebar - palette list
// ---------------------------------------------------------------------------
function renderSidebar() {
  const ul = $("palette-list");
  ul.innerHTML = "";
  for (const p of state.palettes) {
    const li = document.createElement("li");
    const isActive = state.current && state.current.id === p.id;
    li.className = [
      "flex items-center justify-between px-4 py-2 cursor-pointer text-sm gap-2",
      "hover:bg-zinc-800 transition group",
      isActive ? "bg-zinc-800 text-white font-medium" : "text-zinc-300",
    ].join(" ");

    li.innerHTML = `
      <span class="truncate flex-1 select-none">${escHtml(p.name)}</span>
      <span class="text-zinc-600 text-xs shrink-0">${p.color_count}</span>
      <button data-id="${p.id}" data-action="delete-palette"
        class="opacity-0 group-hover:opacity-100 text-zinc-500 hover:text-red-400 transition text-xs
          shrink-0" title="Delete palette">✕</button>
    `;
    li.addEventListener("click", (e) => {
      const btn = e.target.closest("[data-action]");
      if (btn) return; // handled separately
      loadPalette(p.id);
    });
    ul.appendChild(li);
  }
}

// ---------------------------------------------------------------------------
// Main area rendering
// ---------------------------------------------------------------------------
function renderMain() {
  const hasPalette = state.current !== null;

  $("empty-state").classList.toggle("hidden", hasPalette);
  $("empty-state").classList.toggle("flex", !hasPalette);

  for (const id of [
    "section-palette-header",
    "section-mosaic",
    "section-swatches",
    "section-add-color",
  ]) {
    const el = $(id);
    el.classList.toggle("hidden", !hasPalette);
    if (id === "section-palette-header") {
      el.classList.toggle("flex", hasPalette);
    }
  }

  // Keep the save button in sync regardless of whether a palette is selected
  $("btn-save-generated").disabled = !hasPalette;

  if (!hasPalette) return;

  const { name, colors } = state.current;

  // Palette name input
  $("input-palette-name").value = name;
  $("palette-color-count").textContent =
    colors.length === 1 ? "1 color" : `${colors.length} colors`;

  renderMosaic(colors);
  renderSwatches(colors);
}

// ---------------------------------------------------------------------------
// Mosaic - variable-sized CSS grid
// ---------------------------------------------------------------------------
function renderMosaic(colors) {
  const container = $("mosaic");
  container.innerHTML = "";
  if (!colors.length) {
    container.style.background = "#18181b";
    return;
  }

  // Assign pseudo-random column-span widths (seeded by hex so stable per palette)
  const spans = computeSpans(colors);
  container.style.gridTemplateColumns = spans
    .map((s) => `${s}fr`)
    .join(" ");

  for (let i = 0; i < colors.length; i++) {
    const block = document.createElement("div");
    block.className = "mosaic-block";
    block.style.backgroundColor = colors[i].hex_value;
    block.title = colors[i].name
      ? `${colors[i].name} - ${colors[i].hex_value}`
      : colors[i].hex_value;
    container.appendChild(block);
  }
}

/**
 * Compute relative column span weights for the mosaic.
 * Uses a deterministic pseudo-random approach so the layout is stable.
 *
 * @param {Array} colors
 * @returns {number[]}
 */
function computeSpans(colors) {
  return colors.map((c, i) => {
    // Simple deterministic hash of the hex string + index
    let seed = i * 31;
    for (const ch of c.hex_value) seed = (seed * 37 + ch.charCodeAt(0)) & 0xffff;
    // Weight in range [1, 3]
    return 1 + (seed % 200) / 100;
  });
}

// ---------------------------------------------------------------------------
// Color swatches
// ---------------------------------------------------------------------------
function renderSwatches(colors) {
  const list = $("swatch-list");
  list.innerHTML = "";
  for (const color of colors) {
    list.appendChild(buildSwatch(color));
  }
}

function buildSwatch(color, opts = {}) {
  const wrap = document.createElement("div");
  wrap.className =
    "swatch group relative flex flex-col items-center gap-1";

  const box = document.createElement("div");
  box.className =
    "w-14 h-14 rounded-lg border border-zinc-700 cursor-pointer swatch-box transition-transform hover:scale-105";
  box.style.backgroundColor = color.hex_value || color;
  box.title = "Click to copy hex";
  box.addEventListener("click", () =>
    copyToClipboard(color.hex_value || color)
  );

  const label = document.createElement("span");
  label.className = "text-xs text-zinc-400 font-mono select-all";
  label.textContent = color.hex_value || color;

  if (color.name) {
    const nameEl = document.createElement("span");
    nameEl.className = "text-xs text-zinc-500 max-w-14 truncate text-center";
    nameEl.textContent = color.name;
    wrap.append(box, label, nameEl);
  } else {
    wrap.append(box, label);
  }

  if (!opts.noDelete) {
    const del = document.createElement("button");
    del.className =
      "absolute -top-1 -right-1 w-4 h-4 rounded-full bg-zinc-700 text-zinc-300" +
      " text-xs opacity-0 group-hover:opacity-100 hover:bg-red-600 hover:text-white transition flex items-center justify-center";
    del.textContent = "✕";
    del.title = "Remove color";
    del.addEventListener("click", () => deleteColor(color.id));
    wrap.appendChild(del);
  }

  return wrap;
}

// ---------------------------------------------------------------------------
// Conversion result display
// ---------------------------------------------------------------------------
function renderConvertResult(formats) {
  const container = $("convert-result");
  container.innerHTML = "";
  container.classList.remove("hidden");
  for (const [fmt, val] of Object.entries(formats)) {
    const chip = document.createElement("div");
    chip.className =
      "flex-1 min-w-max bg-zinc-800 border border-zinc-700 rounded px-2 py-1 text-xs font-mono" +
      " cursor-pointer hover:border-indigo-500 transition flex flex-col gap-0.5";
    chip.innerHTML = `<span class="text-zinc-500 text-[10px] uppercase">${escHtml(fmt)}</span>
                      <span class="text-zinc-200">${escHtml(val)}</span>`;
    chip.title = "Click to copy";
    chip.addEventListener("click", () => copyToClipboard(val));
    container.appendChild(chip);
  }
}

// ---------------------------------------------------------------------------
// Generated palette display
// ---------------------------------------------------------------------------
function renderGenerated(hexList) {
  state.generated = hexList;
  const list = $("gen-swatch-list");
  list.innerHTML = "";
  for (const hex of hexList) {
    list.appendChild(buildSwatch({ hex_value: hex }, { noDelete: true }));
  }
  $("gen-results").classList.remove("hidden");
}

// ---------------------------------------------------------------------------
// API actions
// ---------------------------------------------------------------------------
async function loadPalettes() {
  state.palettes = await GET("/api/palettes/");
  renderSidebar();
}

async function loadPalette(id) {
  state.current = await GET(`/api/palettes/${id}`);
  renderSidebar();
  renderMain();
}

async function createPalette() {
  const index = state.palettes.length + 1;
  const name = `Palette ${index}`;
  const palette = await POST("/api/palettes/", { name });
  await loadPalettes();
  await loadPalette(palette.id);
}

async function deletePalette(id) {
  if (!confirm("Delete this palette and all its colors?")) return;
  await DELETE(`/api/palettes/${id}`);
  if (state.current && state.current.id === id) state.current = null;
  await loadPalettes();
  renderMain();
}

async function renamePalette(id, newName) {
  state.current = await PUT(`/api/palettes/${id}`, { name: newName });
  await loadPalettes();
  renderMain();
}

async function addColor(value, name) {
  if (!state.current) return;
  await POST(`/api/palettes/${state.current.id}/colors`, { value, name });
  await loadPalette(state.current.id);
}

async function deleteColor(colorId) {
  if (!state.current) return;
  await DELETE(`/api/palettes/${state.current.id}/colors/${colorId}`);
  await loadPalette(state.current.id);
}

async function saveGeneratedToPalette() {
  if (!state.current) {
    showError("Select or create a palette first, then save.");
    return;
  }
  if (!state.generated.length) return;
  for (const hex of state.generated) {
    await POST(`/api/palettes/${state.current.id}/colors`, { value: hex });
  }
  await loadPalette(state.current.id);
  $("gen-results").classList.add("hidden");
  state.generated = [];
}

async function saveGeneratedToNewPalette() {
  if (!state.generated.length) return;
  const index = state.palettes.length + 1;
  const name = `Palette ${index}`;
  const palette = await POST("/api/palettes/", { name });
  for (const hex of state.generated) {
    await POST(`/api/palettes/${palette.id}/colors`, { value: hex });
  }
  await loadPalettes();
  await loadPalette(palette.id);
  $("gen-results").classList.add("hidden");
  state.generated = [];
}

async function convertColor(value) {
  const result = await POST("/api/convert", { value });
  renderConvertResult(result);
  return result;
}

async function generatePalette(algorithm, baseColor, count) {
  const result = await POST("/api/generate", {
    algorithm,
    base_color: baseColor || null,
    count,
  });
  renderGenerated(result.colors);
}

/**
 * Upload a CSV/TSV file to the import endpoint, reload the palette list,
 * and show a summary toast.
 *
 * @param {File} file
 */
async function importPaletteFile(file) {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch("/api/import", { method: "POST", body: formData });
  const json = await res.json();
  if (!res.ok) throw new Error(json.error || `HTTP ${res.status}`);

  await loadPalettes();

  // Auto-select the first imported palette
  if (json.palettes && json.palettes.length > 0) {
    await loadPalette(json.palettes[0].id);
  }

  const parts = [];
  if (json.created_palettes) parts.push(`${json.created_palettes} palette(s) created`);
  if (json.reused_palettes) parts.push(`${json.reused_palettes} existing palette(s) updated`);
  parts.push(`${json.added_colors} color(s) added`);
  if (json.skipped_rows) parts.push(`${json.skipped_rows} row(s) skipped`);
  showToast(parts.join(" · "));
}

// ---------------------------------------------------------------------------
// Live color preview while typing
// ---------------------------------------------------------------------------
function updateAddPreview(value) {
  const preview = $("add-color-preview");
  try {
    // Use a dummy element to test if the browser accepts the colour
    const div = document.createElement("div");
    document.body.appendChild(div);
    div.style.color = value;
    const valid = div.style.color !== "";
    document.body.removeChild(div);
    if (valid) {
      preview.style.backgroundColor = value;
      return;
    }
  } catch (_) {
    // fall through
  }
  preview.style.backgroundColor = "#27272a";
}

// ---------------------------------------------------------------------------
// Format-aware placeholder
// ---------------------------------------------------------------------------
const FORMAT_PLACEHOLDERS = {
  hex: "#ff5733",
  rgb: "rgb(255, 87, 51)",
  hsl: "hsl(11, 100%, 60%)",
  hsv: "hsv(11, 80%, 100%)",
  forza: "forza(0.0306, 0.8, 1.0)",
};

// ---------------------------------------------------------------------------
// Utilities
// ---------------------------------------------------------------------------
function escHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function copyToClipboard(text) {
  navigator.clipboard.writeText(text).then(() => showToast(text));
}

function showToast(msg) {
  const t = document.createElement("div");
  t.textContent = `Copied: ${msg}`;
  t.className =
    "fixed bottom-5 right-5 bg-zinc-800 border border-zinc-700 text-zinc-200" +
    " text-sm px-4 py-2 rounded shadow-lg transition-opacity duration-300";
  document.body.appendChild(t);
  setTimeout(() => {
    t.style.opacity = "0";
    setTimeout(() => t.remove(), 350);
  }, 1800);
}

function showError(msg) {
  showToast(`⚠ ${msg}`);
}

// ---------------------------------------------------------------------------
// Event wiring
// ---------------------------------------------------------------------------
document.addEventListener("DOMContentLoaded", async () => {
  // New palette
  $("btn-new-palette").addEventListener("click", createPalette);

  // Import CSV / TSV
  $("input-import-file").addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    // Reset so the same file can be re-imported if needed
    e.target.value = "";
    try {
      await importPaletteFile(file);
    } catch (err) {
      showError(err.message);
    }
  });

  // Delete palette (delegated from sidebar)
  $("palette-list").addEventListener("click", (e) => {
    const btn = e.target.closest("[data-action='delete-palette']");
    if (btn) {
      e.stopPropagation();
      deletePalette(Number(btn.dataset.id));
    }
  });

  // Rename palette on blur / Enter
  const nameInput = $("input-palette-name");
  let _lastPaletteName = "";
  nameInput.addEventListener("focus", () => {
    _lastPaletteName = nameInput.value;
  });
  const commitRename = () => {
    const v = nameInput.value.trim();
    if (v && v !== _lastPaletteName && state.current) {
      renamePalette(state.current.id, v).catch((e) => showError(e.message));
    }
  };
  nameInput.addEventListener("blur", commitRename);
  nameInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") { e.preventDefault(); commitRename(); nameInput.blur(); }
  });

  // Format picker changes placeholder
  $("input-format").addEventListener("change", () => {
    const fmt = $("input-format").value;
    $("input-color-value").placeholder = FORMAT_PLACEHOLDERS[fmt] || "#ff5733";
  });

  // Live preview while typing color value
  $("input-color-value").addEventListener("input", () => {
    updateAddPreview($("input-color-value").value.trim());
  });

  // Add color
  $("btn-add-color").addEventListener("click", async () => {
    const value = $("input-color-value").value.trim();
    const name = $("input-color-name").value.trim();
    if (!value) return;
    if (!state.current) { showError("Select or create a palette first."); return; }
    try {
      await addColor(value, name);
      $("input-color-value").value = "";
      $("input-color-name").value = "";
      $("add-color-preview").style.backgroundColor = "#27272a";
      $("convert-result").classList.add("hidden");
    } catch (e) {
      showError(e.message);
    }
  });

  // Convert
  $("btn-convert").addEventListener("click", async () => {
    const value = $("input-color-value").value.trim();
    if (!value) return;
    try {
      await convertColor(value);
    } catch (e) {
      showError(e.message);
    }
  });

  // Generate
  $("btn-generate").addEventListener("click", async () => {
    const algorithm = $("gen-algorithm").value;
    const baseColor = $("gen-base-color").value.trim();
    const count = parseInt($("gen-count").value, 10) || 6;
    try {
      await generatePalette(algorithm, baseColor, count);
    } catch (e) {
      showError(e.message);
    }
  });

  // Random shortcut
  $("btn-random").addEventListener("click", async () => {
    const baseColor = $("gen-base-color").value.trim();
    const count = parseInt($("gen-count").value, 10) || 6;
    try {
      await generatePalette("random", baseColor || null, count);
    } catch (e) {
      showError(e.message);
    }
  });

  // Save generated to current palette
  $("btn-save-generated").addEventListener("click", async () => {
    try {
      await saveGeneratedToPalette();
    } catch (e) {
      showError(e.message);
    }
  });

  // Save generated to a brand-new palette
  $("btn-save-generated-new").addEventListener("click", async () => {
    try {
      await saveGeneratedToNewPalette();
    } catch (e) {
      showError(e.message);
    }
  });

  // Enter key submits add-color form
  $("input-color-value").addEventListener("keydown", (e) => {
    if (e.key === "Enter") $("btn-add-color").click();
  });

  // Initial data load
  await loadPalettes();
  renderMain();
});
