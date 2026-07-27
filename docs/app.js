const STATUS_LABELS = {
  queued: "Queued",
  running: "Running",
  failed: "Failed",
  ready_to_download: "Ready to Download",
  uploaded: "Uploaded",
};

function formatDuration(seconds) {
  if (!seconds) return "—";
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds % 60);
  return `${m}:${String(s).padStart(2, "0")}`;
}

function renderStats(records) {
  const counts = { total: records.length, ready_to_download: 0, uploaded: 0, failed: 0, running: 0 };
  for (const r of records) {
    if (r.status === "running" || r.status === "queued") counts.running++;
    else if (counts[r.status] !== undefined) counts[r.status]++;
  }
  const stats = [
    { label: "Total Videos", num: counts.total },
    { label: "Ready to Download", num: counts.ready_to_download },
    { label: "Uploaded", num: counts.uploaded },
    { label: "In Progress", num: counts.running },
    { label: "Failed", num: counts.failed },
  ];
  document.getElementById("stats").innerHTML = stats
    .map((s) => `<div class="stat"><div class="num">${s.num}</div><div class="label">${s.label}</div></div>`)
    .join("");
}

function renderCards(records) {
  const container = document.getElementById("cards");
  if (records.length === 0) {
    container.innerHTML = '<div class="empty">No videos generated yet.</div>';
    return;
  }

  const sorted = [...records].sort((a, b) => b.run_date.localeCompare(a.run_date));

  container.innerHTML = sorted
    .map((r) => {
      const thumb = r.thumbnail_path ? r.thumbnail_path : "";
      const statusBadge = `<span class="badge ${r.status}">${STATUS_LABELS[r.status] || r.status}</span>`;
      const errorLine = r.status === "failed" && r.error_message
        ? `<div class="error">${r.current_stage ? `[${r.current_stage}] ` : ""}${escapeHtml(r.error_message)}</div>`
        : "";
      const uploadedLine = r.youtube_uploaded && r.youtube_url
        ? `<a href="${r.youtube_url}" target="_blank" rel="noopener">View on YouTube</a>`
        : "";
      const runLink = r.workflow_run_url
        ? `<a href="${r.workflow_run_url}" target="_blank" rel="noopener">Run log</a>`
        : "";

      return `
        <div class="card">
          <img src="${thumb}" alt="" loading="lazy" onerror="this.style.visibility='hidden'" />
          <div>
            <div class="title">${escapeHtml(r.title || "(untitled)")}</div>
            <div class="meta">${r.run_date} · ${escapeHtml(r.theme_category || "")} · ${formatDuration(r.duration_seconds)}</div>
            ${errorLine}
          </div>
          <div class="actions">
            ${statusBadge}<br/><br/>
            ${runLink}${runLink && uploadedLine ? " · " : ""}${uploadedLine}
          </div>
        </div>`;
    })
    .join("");
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

fetch("data/videos.json")
  .then((res) => res.json())
  .then((records) => {
    renderStats(records);
    renderCards(records);
  })
  .catch((err) => {
    document.getElementById("cards").innerHTML = `<div class="empty">Failed to load status data: ${err}</div>`;
  });
