/**
 * CHAT — REPO PICKER PAGE
 * ─────────────────────────────────────────────────────────────────────
 * Route: #/chat
 * Lists all repositories; clicking one opens its chat page.
 * ─────────────────────────────────────────────────────────────────────
 */

import { api } from '../api/client.js';
import { renderTopbar } from '../templates/topbar.js';
import { statusBadge, emptyState, esc } from '../templates/components.js';

export const chatListPage = {
  topbar() {
    return renderTopbar({ crumbs: ['Dashboard', 'Chat'] });
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

    container.innerHTML = `
      <div class="page-header">
        <div class="page-title">Chat</div>
        <div class="page-subtitle">Pick a repository to start asking questions about it</div>
      </div>

      ${repos.length === 0 ? renderEmpty() : renderRepoPicker(repos)}
    `;

    container.querySelectorAll('.repo-row').forEach(row => {
      row.addEventListener('click', () => {
        const id = row.dataset.id;
        const ready = row.dataset.ready === 'true';
        window.location.hash = ready ? `#/repo/${id}/chat` : `#/repo/${id}`;
      });
    });
  },
};

function renderEmpty() {
  return emptyState({
    icon: '[ ]',
    title: 'No repositories yet',
    desc: 'Import a repository first, then come back here to chat with it.',
    actionHtml: `<a href="#/import" class="btn btn-primary">+ Import Repository</a>`,
  });
}

function renderRepoPicker(repos) {
  const rows = repos.map(r => `
    <div class="repo-row" data-id="${r.id}" data-ready="${r.status === 'ready'}">
      <div class="repo-name">${esc(r.owner)}<span class="repo-owner">/</span>${esc(r.name)}</div>
      <div>${statusBadge(r.status)}</div>
      <div class="repo-files">${r.total_files} files</div>
      <div class="repo-arrow">${r.status === 'ready' ? '&gt;' : ''}</div>
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