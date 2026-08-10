/**
 * SIDEBAR TEMPLATE
 * ─────────────────────────────────────────────────────────────────────
 * Renders the left navigation. Pure function of (currentRoute) -> HTML string.
 * To change the nav items, edit NAV_ITEMS below.
 * To change the LOOK of the sidebar, edit css/style.css (#sidebar, .nav-item, etc).
 * ─────────────────────────────────────────────────────────────────────
 */

const NAV_ITEMS = [
  { section: 'Workspace', items: [
    { route: '#/',        label: 'Dashboard',   icon: '#' },
    { route: '#/import',  label: 'Import Repo', icon: '+' },
    { route: '#/chat',    label: 'Chat',        icon: '?' },
  ]},
  { section: 'Coming Soon', items: [
    { route: null, label: 'Code Review',    icon: '?', soon: true },
  ]},
];

export function renderSidebar(currentRoute) {
  const sections = NAV_ITEMS.map(section => `
    <div class="nav-section-label">${section.section}</div>
    ${section.items.map(item => renderNavItem(item, currentRoute)).join('')}
  `).join('');

  return `
    <div class="sidebar-logo">
      <span class="logo-icon">&gt;_</span>
      <span class="logo-text">AI Dev<br/>Assistant</span>
    </div>
    <nav class="sidebar-nav">${sections}</nav>
    <div class="sidebar-footer">v0.1 — phase 1</div>
  `;
}

function renderNavItem(item, currentRoute) {
  if (item.soon) {
    return `
      <div class="nav-item" style="opacity:0.5; cursor: default;">
        <span class="nav-cursor">&nbsp;</span>
        <span>${item.label}</span>
        <span class="nav-coming-soon">soon</span>
      </div>
    `;
  }
  const isActive = currentRoute === item.route || (item.route === '#/' && currentRoute.startsWith('#/repo/'));
  return `
    <a href="${item.route}" class="nav-item ${isActive ? 'active' : ''}">
      <span class="nav-cursor">${isActive ? '&gt;' : '&nbsp;'}</span>
      <span>${item.label}</span>
    </a>
  `;
}
