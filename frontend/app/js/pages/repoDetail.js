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
        <div class="page-title flex items-center gap-8" style="justify-content: space-between;">
          <span>${esc(repo.owner)} / ${esc(repo.name)}</span>
          <button id="delete-repo-btn" class="btn" data-repo-id="${repo.id}" style="color: var(--failed); border-color: var(--failed);">
            Delete repository
          </button>
        </div>
        <div class="page-subtitle flex items-center gap-8">
          ${statusBadge(repo.status)}
          <span class="text-muted">${repo.total_files} files &middot; branch ${esc(repo.default_branch)}</span>
        </div>
      </div>
      <div id="delete-status"></div>
      ${repo.status === 'ready' ? renderIndexSection(repo) : ''}
      ${repo.status === 'ready' ? renderScanSection(repo) : ''}
      ${repo.status === 'ready' ? renderDocsSection(repo) : ''}
      ${repo.status === 'failed' ? `<div class="banner banner--error"><div class="banner-title">Import failed</div><div class="banner-body">${esc(repo.error_message || 'Unknown error')}</div></div>` : ''}

<div class="section">
        <div class="section-header">
          <div class="section-title">Indexed Files</div>
        </div>
        ${files.length === 0 ? renderEmptyFiles() : renderFileGroups(files)}
      </div>
    `;

    attachIndexHandler();
    attachScanHandler();
    attachDocsHandler();
    attachDeleteHandler();
  },
};

function attachDeleteHandler() {
  const btn = document.getElementById('delete-repo-btn');
  if (!btn) return;

  btn.addEventListener('click', async () => {
    const repoId = btn.dataset.repoId;
    const statusEl = document.getElementById('delete-status');

    const confirmed = confirm(
      'Delete this repository? This removes it from disk, the vector store, and the database — including all chat history, security findings, and generated docs. This cannot be undone.'
    );
    if (!confirmed) return;

    btn.disabled = true;
    btn.textContent = 'Deleting...';

    try {
      await api.deleteRepository(repoId);
      window.location.hash = '#/';
    } catch (err) {
      btn.disabled = false;
      btn.textContent = 'Delete repository';
      statusEl.innerHTML = `<div class="banner banner--error"><div class="banner-body">${esc(err.detail || err.message)}</div></div>`;
    }
  });
}

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
function renderScanSection(repo) {
  return `
    <div id="scan-section" class="mt-16">
      <button id="scan-btn" class="btn" data-repo-id="${repo.id}">
        Scan for security issues
      </button>
      <div id="scan-progress" class="index-progress" style="display:none;">
        <div class="progress-bar"><div class="progress-bar-fill"></div></div>
        <span class="progress-label">Scanning files...</span>
      </div>
      <div id="scan-result"></div>
      <div id="findings-list"></div>
    </div>
  `;
}

function attachScanHandler() {
  const btn = document.getElementById('scan-btn');
  if (!btn) return;

  btn.addEventListener('click', async () => {
    const repoId = btn.dataset.repoId;
    const progressEl = document.getElementById('scan-progress');
    const resultEl = document.getElementById('scan-result');
    const findingsEl = document.getElementById('findings-list');

    btn.disabled = true;
    btn.textContent = 'Scanning...';
    progressEl.style.display = 'block';
    resultEl.innerHTML = '';
    findingsEl.innerHTML = '';

    try {
      const res = await api.scanRepository(repoId);
      progressEl.style.display = 'none';
      btn.disabled = false;
      btn.textContent = 'Re-scan for security issues';

      if (res.total_findings === 0) {
        resultEl.innerHTML = `<div class="banner banner--success"><div class="banner-body">No issues found across ${res.files_scanned} files.</div></div>`;
      } else {
        resultEl.innerHTML = `<div class="banner banner--error"><div class="banner-body">${res.total_findings} issue(s) found — ${res.critical_count} critical, ${res.high_count} high, ${res.medium_count} medium, ${res.low_count} low.</div></div>`;
        const findings = await api.getFindings(repoId);
        findingsEl.innerHTML = renderFindings(findings);
      }
    } catch (err) {
      progressEl.style.display = 'none';
      btn.disabled = false;
      btn.textContent = 'Retry scan';
      resultEl.innerHTML = `<div class="banner banner--error"><div class="banner-body">${esc(err.detail || err.message)}</div></div>`;
    }
  });
}

function renderFindings(findings) {
  if (!findings.length) return '';

  const rows = findings.map(f => `
    <div class="finding-item finding-item--${f.severity}">
      <div class="finding-severity">${esc(f.severity)}</div>
      <div class="finding-body">
        <div class="finding-title">${esc(f.title)}</div>
        <div class="finding-meta">${esc(f.file_path)}${f.line_number ? `:${f.line_number}` : ''}</div>
        <div class="finding-desc">${esc(f.description)}</div>
        ${f.matched_snippet ? `<div class="finding-snippet">${esc(f.matched_snippet)}</div>` : ''}
      </div>
    </div>
  `).join('');

  return `<div class="findings-list mt-16">${rows}</div>`;
}

const DOC_TYPES = [
  { key: 'readme', label: 'README' },
  { key: 'api', label: 'API Docs' },
  { key: 'architecture', label: 'Architecture' },
];

function renderDocsSection(repo) {
  const buttons = DOC_TYPES.map(d => `
    <button class="btn doc-gen-btn" data-repo-id="${repo.id}" data-doc-type="${d.key}">
      Generate ${d.label}
    </button>
  `).join('');

  return `
    <div id="docs-section" class="mt-16">
      <div class="flex gap-8">${buttons}</div>
      <div id="doc-progress" class="index-progress" style="display:none;">
        <div class="progress-bar"><div class="progress-bar-fill"></div></div>
        <span class="progress-label">Generating documentation...</span>
      </div>
      <div id="doc-result"></div>
      <div id="doc-content"></div>
    </div>
  `;
}

function attachDocsHandler() {
  const buttons = document.querySelectorAll('.doc-gen-btn');
  if (!buttons.length) return;

  buttons.forEach(btn => {
    btn.addEventListener('click', async () => {
      const repoId = btn.dataset.repoId;
      const docType = btn.dataset.docType;
      const progressEl = document.getElementById('doc-progress');
      const resultEl = document.getElementById('doc-result');
      const contentEl = document.getElementById('doc-content');

      buttons.forEach(b => b.disabled = true);
      progressEl.style.display = 'block';
      resultEl.innerHTML = '';
      contentEl.innerHTML = '';

      try {
        const res = await api.generateDoc(repoId, docType);
        progressEl.style.display = 'none';
        buttons.forEach(b => b.disabled = false);
        resultEl.innerHTML = `<div class="banner banner--success"><div class="banner-body">${docType} documentation generated.</div></div>`;
        contentEl.innerHTML = renderDocContent(res.content);
      } catch (err) {
        progressEl.style.display = 'none';
        buttons.forEach(b => b.disabled = false);
        resultEl.innerHTML = `<div class="banner banner--error"><div class="banner-body">${esc(err.detail || err.message)}</div></div>`;
      }
    });
  });
}

function renderDocContent(markdown) {
  return `<pre class="doc-viewer">${esc(markdown)}</pre>`;
}