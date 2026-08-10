/**
 * APP ROUTER
 * ─────────────────────────────────────────────────────────────────────
 * Minimal hash-based router. Maps a route pattern to a page module.
 * Each page module exports { topbar(params), render(container, params) }.
 *
 * To add a new page: create js/pages/yourPage.js exporting that shape,
 * then register a route below. Nothing else needs to change.
 * ─────────────────────────────────────────────────────────────────────
 */

import { renderSidebar } from './templates/sidebar.js';
import { dashboardPage } from './pages/dashboard.js';
import { importPage } from './pages/import.js';
import { repoDetailPage } from './pages/repoDetail.js';
import { chatPage } from './pages/chat.js';
import { chatListPage } from './pages/chatList.js';

const ROUTES = [
  { pattern: /^#\/$/,                page: dashboardPage,  params: () => ({}) },
  { pattern: /^#\/import$/,          page: importPage,     params: () => ({}) },
  { pattern: /^#\/chat$/,            page: chatListPage,   params: () => ({}) },
  { pattern: /^#\/repo\/([^/]+)$/,   page: repoDetailPage, params: (m) => ({ id: m[1] }) },
  { pattern: /^#\/repo\/([^/]+)\/chat$/, page: chatPage,   params: (m) => ({ id: m[1] }) },
];

function matchRoute(hash) {
  for (const route of ROUTES) {
    const match = hash.match(route.pattern);
    if (match) return { page: route.page, params: route.params(match) };
  }
  return null;
}

async function mount() {
  const hash = window.location.hash || '#/';
  const matched = matchRoute(hash) || matchRoute('#/');

  const sidebarEl = document.getElementById('sidebar');
  const topbarEl = document.getElementById('topbar');
  const contentEl = document.getElementById('content');

  sidebarEl.innerHTML = renderSidebar(hash);
  topbarEl.innerHTML = matched.page.topbar(matched.params);

  await matched.page.render(contentEl, matched.params);
}

window.addEventListener('hashchange', mount);

// Module scripts execute after the DOM is parsed, so DOMContentLoaded may
// have already fired by the time this line runs — checking readyState
// directly (instead of only listening for the event) avoids a race where
// mount() would never be called on first load.
if (document.readyState === 'loading') {
  window.addEventListener('DOMContentLoaded', mount);
} else {
  mount();
}

