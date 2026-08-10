/**
 * COMPONENTS TEMPLATE
 * ─────────────────────────────────────────────────────────────────────
 * Small, reusable HTML-string generators shared across pages.
 * Keep these dumb — they take data, return HTML, nothing else.
 * ─────────────────────────────────────────────────────────────────────
 */

export function statusBadge(status) {
  const labels = {
    ready: 'Ready', failed: 'Failed', pending: 'Pending',
    cloning: 'Cloning', processing: 'Processing',
  };
  return `<span class="badge badge--${status}">${labels[status] || status}</span>`;
}

export function emptyState({ icon = '[ ]', title, desc, actionHtml = '' }) {
  return `
    <div class="empty-state">
      <div class="empty-icon">${icon}</div>
      <div class="empty-title">${title}</div>
      <div class="empty-desc">${desc}</div>
      ${actionHtml}
    </div>
  `;
}

export function banner(type, title, body) {
  return `
    <div class="banner banner--${type}">
      <div class="banner-title">${title}</div>
      <div class="banner-body">${body}</div>
    </div>
  `;
}

export function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function timeAgo(isoString) {
  const diff = (Date.now() - new Date(isoString + 'Z')) / 1000;
  if (diff < 60) return 'just now';
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

/** Escapes text inserted into HTML templates to avoid accidental markup injection from repo names/paths. */
export function esc(str) {
  const div = document.createElement('div');
  div.textContent = str ?? '';
  return div.innerHTML;
}
