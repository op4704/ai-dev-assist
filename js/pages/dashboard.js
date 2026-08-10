/**
 * DASHBOARD PAGE
 * ─────────────────────────────────────────────────────────────────────
 * Route: #/
 * Shows stat summary + list of imported repositories.
 * ─────────────────────────────────────────────────────────────────────
 */

import { api } from '../api/client.js';
import { renderTopbar } from '../templates/topbar.js';
import { statusBadge, emptyState, esc } from '../templates/components.js';

export const dashboardPage = {
  topbar() {
    return renderTopbar({
      crumbs: ['Dashboard'],
      actionsHtml: `<a href="#/import" class="btn btn-primary">+ Import Repository</a>`,
    });
  },

  async render(container) {
    container.innerHTML = `<div class="loading-screen"><span class="blink">_</span></div>`;

    let repos = [];
    try {
      repos = await api.getRepositories();
    } catch (err) {
      container.innerHTML = `<div class="banner banner--error"><div class="banner-title">Failed to load repositories</div><div class="banner-body">${esc(err.message)}</div></div>`;
      return;
    }

    const ready = repos.filter(r => r.status === 'ready').length;
    const totalFiles = repos.reduce((sum, r) => sum + (r.total_files || 0), 0);

    container.innerHTML = `
      <div class="page-header">
        <div class="page-title">Dashboard</div>
        <div class="page-subtitle">Overview of your imported repositories</div>
      </div>

      <div class="stat-grid">
        <div class="stat-card">
          <div class="stat-value">${repos.length}</div>
          <div class="stat-label">Repositories</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">${ready}</div>
          <div class="stat-label">Ready</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">${totalFiles}</div>
          <div class="stat-label">Files Indexed</div>
        </div>
      </div>

      <div class="section">
        <div class="section-header">
          <div class="section-title">Your Repositories</div>
        </div>
        ${repos.length === 0 ? renderEmpty() : renderTable(repos)}
      </div>
    `;

    container.querySelectorAll('.repo-row').forEach(row => {
      row.addEventListener('click', () => {
        window.location.hash = `#/repo/${row.dataset.id}`;
      });
    });
  },
};

function renderEmpty() {
  return emptyState({
    icon: '[ ]',
    title: 'No repositories yet',
    desc: 'Import a public GitHub repository to get started.',
    actionHtml: `<a href="#/import" class="btn btn-primary">+ Import Repository</a>`,
  });
}

function renderTable(repos) {
  const rows = repos.map(r => `
    <div class="repo-row" data-id="${r.id}">
      <div class="repo-name">${esc(r.owner)}<span class="repo-owner">/</span>${esc(r.name)}</div>
      <div>${statusBadge(r.status)}</div>
      <div class="repo-files">${r.total_files} files</div>
      <div class="repo-arrow">&gt;</div>
    </div>
  `).join('');

  return `
    <div class="repo-table">
      <div class="repo-table-head">
        <span>Repository</span><span>Status</span><span>Files</span><span></span>
      </div>
      ${rows}
    </div>
  `;
}
