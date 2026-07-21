/**
 * REPO DETAIL PAGE
 * ─────────────────────────────────────────────────────────────────────
 * Route: #/repo/:id
 * Shows a single repository's status + its indexed files, grouped by
 * language for readability.
 * ─────────────────────────────────────────────────────────────────────
 */

import { api } from '../api/client.js';
import { renderTopbar } from '../templates/topbar.js';
import { statusBadge, emptyState, formatBytes, esc } from '../templates/components.js';

export const repoDetailPage = {
  topbar(params) {
    return renderTopbar({ crumbs: ['Dashboard', `Repository #${params.id}`] });
  },

  async render(container, params) {
    container.innerHTML = `<div class="loading-screen"><span class="blink">_</span></div>`;

    let repos, files;
    try {
      repos = await api.getRepositories();
      files = await api.getFiles(params.id);
    } catch (err) {
      container.innerHTML = `<div class="banner banner--error"><div class="banner-title">Failed to load repository</div><div class="banner-body">${esc(err.message)}</div></div>`;
      return;
    }

    const repo = repos.find(r => String(r.id) === String(params.id));
    if (!repo) {
      container.innerHTML = `<div class="banner banner--error"><div class="banner-title">Repository not found</div></div>`;
      return;
    }

    container.innerHTML = `
      <a href="#/" class="back-link">&larr; Back to Dashboard</a>

      <div class="page-header">
        <div class="page-title">${esc(repo.owner)} / ${esc(repo.name)}</div>
        <div class="page-subtitle flex items-center gap-8">
          ${statusBadge(repo.status)}
          <span class="text-muted">${repo.total_files} files &middot; branch ${esc(repo.default_branch)}</span>
        </div>
      </div>
      ${repo.status === 'ready' ? renderIndexSection(repo) : ''}
      
      ${repo.status === 'failed' ? `<div class="banner banner--error"><div class="banner-title">Import failed</div><div class="banner-body">${esc(repo.error_message || 'Unknown error')}</div></div>` : ''}

<div class="section">
        <div class="section-header">
          <div class="section-title">Indexed Files</div>
        </div>
        ${files.length === 0 ? renderEmptyFiles() : renderFileGroups(files)}
      </div>
    `;

    attachIndexHandler();
  },
};

function renderEmptyFiles() {
  return emptyState({
    icon: '[ ]',
    title: 'No files indexed',
    desc: 'This repository has no supported source files, or processing has not completed yet.',
  });
}

function renderFileGroups(files) {
  const groups = {};
  for (const f of files) {
    const lang = f.language || 'other';
    (groups[lang] = groups[lang] || []).push(f);
  }

  const sections = Object.keys(groups).sort().map(lang => {
    const items = groups[lang].map(f => `
      <div class="file-item">
        <div class="file-path">${renderPath(f.path)}</div>
        <div><span class="file-lang-pill">${esc(lang)}</span></div>
        <div class="file-size">${formatBytes(f.size_bytes)}</div>
      </div>
    `).join('');
    return `<div class="lang-group-header">${esc(lang)} &middot; ${groups[lang].length}</div>${items}`;
  }).join('');

  return `
    <div class="file-list">
      <div class="file-list-header"><span>Path</span><span>Language</span><span>Size</span></div>
      ${sections}
    </div>
  `;
}

function renderPath(path) {
  const parts = path.split('/');
  const filename = parts.pop();
  const dir = parts.length ? parts.join('/') + '/' : '';
  return `<span class="file-path-dir">${esc(dir)}</span>${esc(filename)}`;
}

function renderIndexSection(repo) {
  return `
    <div id="index-section">
      <a href="#/repo/${repo.id}/chat" class="btn btn-primary">Chat with this repo</a>
      <button id="index-btn" class="btn" data-repo-id="${repo.id}">
        Index this repo (${repo.total_files} files)
      </button>
      <div id="index-progress" class="index-progress" style="display:none;">
        <div class="progress-bar"><div class="progress-bar-fill"></div></div>
        <span class="progress-label">Indexing... this may take a few minutes</span>
      </div>
      <div id="index-result"></div>
    </div>
  `;
}

function attachIndexHandler() {
  const btn = document.getElementById('index-btn');
  if (!btn) return;

  btn.addEventListener('click', async () => {
    const repoId = btn.dataset.repoId;
    const progressEl = document.getElementById('index-progress');
    const resultEl = document.getElementById('index-result');

    btn.disabled = true;
    btn.textContent = 'Indexing...';
    progressEl.style.display = 'block';
    resultEl.innerHTML = '';

    try {
      const res = await api.indexRepository(repoId);
      progressEl.style.display = 'none';
      resultEl.innerHTML = `<div class="banner banner--success"><div class="banner-body">Indexed ${res.chunks_created} chunks from ${res.files_processed} files. Ready to chat.</div></div>`;
      btn.style.display = 'none';
    } catch (err) {
      progressEl.style.display = 'none';
      btn.disabled = false;
      btn.textContent = 'Retry indexing';
      resultEl.innerHTML = `<div class="banner banner--error"><div class="banner-body">${esc(err.detail || err.message)}</div></div>`;
    }
  });
}