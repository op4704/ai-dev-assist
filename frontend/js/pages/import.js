/**
 * IMPORT PAGE
 * ─────────────────────────────────────────────────────────────────────
 * Route: #/import
 * Form to submit a GitHub URL, then drives import -> process as two
 * sequential API calls, showing live step progress.
 * ─────────────────────────────────────────────────────────────────────
 */

import { api } from '../api/client.js';
import { renderTopbar } from '../templates/topbar.js';
import { esc } from '../templates/components.js';

export const importPage = {
  topbar() {
    return renderTopbar({ crumbs: ['Dashboard', 'Import Repository'] });
  },

  async render(container) {
    container.innerHTML = `
      <div class="page-header">
        <div class="page-title">Import Repository</div>
        <div class="page-subtitle">Paste a public GitHub repository URL to analyze it</div>
      </div>

      <div class="form-card">
        <div class="form-group">
          <label class="form-label" for="repo-url">GitHub Repository URL</label>
          <input id="repo-url" class="form-input" type="text" placeholder="https://github.com/owner/repo" autocomplete="off" />
          <div class="form-hint">Must be a public repository. Private repos aren't supported yet.</div>
        </div>
        <button id="import-btn" class="btn btn-primary">Import &amp; Process</button>
      </div>

      <div id="progress-area"></div>
    `;

    const input = container.querySelector('#repo-url');
    const btn = container.querySelector('#import-btn');
    const progressArea = container.querySelector('#progress-area');

    input.addEventListener('keydown', e => { if (e.key === 'Enter') btn.click(); });

    btn.addEventListener('click', async () => {
      const url = input.value.trim();
      if (!url) return;

      btn.disabled = true;
      btn.textContent = 'Working...';
      progressArea.innerHTML = renderSteps({ clone: 'active', process: 'waiting' });

      try {
        const repo = await api.importRepository(url);
        progressArea.innerHTML = renderSteps({ clone: 'done', process: 'active' });

        const processed = await api.processRepository(repo.id);
        progressArea.innerHTML = renderSteps({ clone: 'done', process: 'done' }, processed);

        setTimeout(() => { window.location.hash = `#/repo/${processed.id}`; }, 900);
      } catch (err) {
        const failedStep = err.detail && err.detail.includes('clone') ? 'clone' : 'process';
        const state = failedStep === 'clone' ? { clone: 'error', process: 'waiting' } : { clone: 'done', process: 'error' };
        progressArea.innerHTML = renderSteps(state) + `
          <div class="banner banner--error">
            <div class="banner-title">Import failed</div>
            <div class="banner-body">${esc(err.detail || err.message)}</div>
          </div>
        `;
        btn.disabled = false;
        btn.textContent = 'Import & Process';
      }
    });
  },
};

const ICONS = { done: '✓', active: '', waiting: '·', error: '✗' };

function stepIcon(state) {
  if (state === 'active') return `<span class="spinner"></span>`;
  return `<span class="step-icon step-icon--${state}">${ICONS[state]}</span>`;
}

function renderSteps(state, result = null) {
  return `
    <div class="progress-box">
      <div class="progress-title">Progress</div>
      <div class="step-row">
        ${stepIcon(state.clone)}
        <span class="step-text ${state.clone === 'waiting' ? 'step-text--waiting' : ''}">Cloning repository</span>
      </div>
      <div class="step-row">
        ${stepIcon(state.process)}
        <span class="step-text ${state.process === 'waiting' ? 'step-text--waiting' : ''}">Filtering &amp; indexing files</span>
        ${result ? `<span class="step-meta">${result.total_files} files</span>` : ''}
      </div>
    </div>
  `;
}
