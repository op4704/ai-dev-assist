/**
 * REPO CHAT PAGE
 * ─────────────────────────────────────────────────────────────────────
 * Route: #/repo/:id/chat
 * Lets the user ask questions about an indexed repository.
 * ─────────────────────────────────────────────────────────────────────
 */

import { api } from '../api/client.js';
import { renderTopbar } from '../templates/topbar.js';
import { esc } from '../templates/components.js';

let sessionId = null;
let messages = [];

export const chatPage = {
  topbar(params) {
    return renderTopbar({ crumbs: ['Dashboard', `Repository #${params.id}`, 'Chat'] });
  },

  async render(container, params) {
    sessionId = null;
    messages = [];

    container.innerHTML = `
      <a href="#/repo/${params.id}" class="back-link">&larr; Back to Repository</a>

      <div class="page-header">
        <div class="page-title">Chat with this repository</div>
      </div>

      <div id="chat-log" class="chat-log"></div>

      <div id="chat-status"></div>

      <form id="chat-form" class="chat-form">
        <input
          id="chat-input"
          type="text"
          placeholder="Ask something about this repo..."
          autocomplete="off"
        />
        <button type="submit" id="chat-send">Send</button>
      </form>
    `;

    const form = container.querySelector('#chat-form');
    const input = container.querySelector('#chat-input');
    const sendBtn = container.querySelector('#chat-send');
    const statusEl = container.querySelector('#chat-status');

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const question = input.value.trim();
      if (!question) return;

      addMessage('user', question);
      input.value = '';
      input.disabled = true;
      sendBtn.disabled = true;
      statusEl.textContent = 'Thinking...';

      try {
        const res = await api.sendChatMessage(params.id, question, sessionId);
        sessionId = res.session_id;
        addMessage('assistant', res.answer, res.citations);
        statusEl.textContent = '';
      } catch (err) {
        statusEl.innerHTML = `<div class="banner banner--error"><div class="banner-body">${esc(err.detail || err.message)}</div></div>`;
      } finally {
        input.disabled = false;
        sendBtn.disabled = false;
        input.focus();
      }
    });

    input.focus();
  },
};

function addMessage(role, content, citations = []) {
  messages.push({ role, content, citations });
  const log = document.getElementById('chat-log');
  if (!log) return;

  const citationsHtml = citations.length
    ? `<div class="chat-citations">${citations.map(c => `<span class="citation-pill">${esc(c)}</span>`).join('')}</div>`
    : '';

  log.insertAdjacentHTML('beforeend', `
    <div class="chat-message chat-message--${role}">
      <div class="chat-message-role">${role === 'user' ? 'You' : 'Assistant'}</div>
      <div class="chat-message-content">${esc(content)}</div>
      ${citationsHtml}
    </div>
  `);
  log.scrollTop = log.scrollHeight;
}