const STATUS_LABELS = {
  queued: "Queued",
  running: "Running",
  failed: "Failed",
  ready_to_download: "Ready to Download",
  uploaded: "Uploaded",
};

// Only these reach a CSS class name; anything else falls back to a safe default.
const KNOWN_STATUSES = new Set(Object.keys(STATUS_LABELS));

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str == null ? "" : String(str);
  return div.innerHTML;
}

// Values interpolated into href/src need URL validation, not just HTML
// escaping — youtube_url arrives from a workflow input, so treat it as
// untrusted and reject anything that isn't a plain http(s) URL.
function safeUrl(value) {
  if (!value) return null;
  try {
    const url = new URL(value, window.location.href);
    return url.protocol === "https:" || url.protocol === "http:" ? url.href : null;
  } catch {
    return null;
  }
}

function formatDuration(seconds) {
  if (!seconds) return "—";
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds % 60);
  return `${m}:${String(s).padStart(2, "0")}`;
}

function formatCost(cost) {
  return typeof cost === "number" && cost > 0 ? `$${cost.toFixed(2)}` : "—";
}

function renderStats(records) {
  const counts = { total: records.length, ready_to_download: 0, uploaded: 0, failed: 0, running: 0 };
  let totalCost = 0;
  for (const r of records) {
    if (r.status === "running" || r.status === "queued") counts.running++;
    else if (counts[r.status] !== undefined) counts[r.status]++;
    if (typeof r.cost_estimate_usd === "number") totalCost += r.cost_estimate_usd;
  }
  const stats = [
    { label: "Total Videos", num: counts.total },
    { label: "Ready to Download", num: counts.ready_to_download },
    { label: "Uploaded", num: counts.uploaded },
    { label: "In Progress", num: counts.running },
    { label: "Failed", num: counts.failed },
    { label: "Est. Spend", num: `$${totalCost.toFixed(2)}` },
  ];
  document.getElementById("stats").innerHTML = stats
    .map((s) => `<div class="stat"><div class="num">${escapeHtml(s.num)}</div><div class="label">${escapeHtml(s.label)}</div></div>`)
    .join("");
}

function renderCards(records) {
  const container = document.getElementById("cards");
  if (records.length === 0) {
    container.innerHTML = '<div class="empty">No videos generated yet.</div>';
    return;
  }

  const sorted = [...records].sort((a, b) => String(b.run_date).localeCompare(String(a.run_date)));

  container.innerHTML = sorted
    .map((r) => {
      const statusClass = KNOWN_STATUSES.has(r.status) ? r.status : "queued";
      const statusLabel = STATUS_LABELS[r.status] || r.status;
      const statusBadge = `<span class="badge ${statusClass}">${escapeHtml(statusLabel)}</span>`;

      const thumb = safeUrl(r.thumbnail_path);
      const thumbTag = thumb
        ? `<img src="${escapeHtml(thumb)}" alt="" loading="lazy" onerror="this.style.visibility='hidden'" />`
        : `<div class="thumb-placeholder"></div>`;

      const errorLine =
        r.status === "failed" && r.error_message
          ? `<div class="error">${r.current_stage ? `[${escapeHtml(r.current_stage)}] ` : ""}${escapeHtml(r.error_message)}</div>`
          : "";

      const ytUrl = r.youtube_uploaded ? safeUrl(r.youtube_url) : null;
      const uploadedLink = ytUrl
        ? `<a href="${escapeHtml(ytUrl)}" target="_blank" rel="noopener noreferrer">View on YouTube</a>`
        : "";

      const runUrl = safeUrl(r.workflow_run_url);
      const runLink = runUrl
        ? `<a href="${escapeHtml(runUrl)}" target="_blank" rel="noopener noreferrer">Run log</a>`
        : "";

      const meta = [r.run_date, r.theme_category, formatDuration(r.duration_seconds), formatCost(r.cost_estimate_usd)]
        .filter(Boolean)
        .map((part) => escapeHtml(part))
        .join(" · ");

      return `
        <div class="card">
          ${thumbTag}
          <div>
            <div class="title">${escapeHtml(r.title || "(untitled)")}</div>
            <div class="meta">${meta}</div>
            ${errorLine}
          </div>
          <div class="actions">
            ${statusBadge}<br/><br/>
            ${runLink}${runLink && uploadedLink ? " · " : ""}${uploadedLink}
          </div>
        </div>`;
    })
    .join("");
}

fetch("data/videos.json")
  .then((res) => {
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  })
  .then((records) => {
    renderStats(records);
    renderCards(records);
  })
  .catch((err) => {
    document.getElementById("cards").innerHTML =
      `<div class="empty">Failed to load status data: ${escapeHtml(err.message)}</div>`;
  });
