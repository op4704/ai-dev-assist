/**
 * TOPBAR TEMPLATE
 * ─────────────────────────────────────────────────────────────────────
 * Renders the top breadcrumb bar. Each page provides its own breadcrumb
 * trail and optional action buttons (e.g. "Import Repository" button).
 * ─────────────────────────────────────────────────────────────────────
 */

export function renderTopbar({ crumbs = [], actionsHtml = '' }) {
  const crumbHtml = crumbs
    .map((c, i) => {
      const isLast = i === crumbs.length - 1;
      const sep = i > 0 ? '<span>/</span>' : '';
      return `${sep}<span class="${isLast ? 'crumb-active' : ''}">${c}</span>`;
    })
    .join('');

  return `
    <div class="topbar-breadcrumb">${crumbHtml}</div>
    <div class="topbar-actions">${actionsHtml}</div>
  `;
}
