/**
 * API CLIENT
 * ─────────────────────────────────────────────────────────────────────
 * The only file in the frontend that calls the backend.
 * All pages import from here — never use fetch() directly in pages.
 *
 * NEVER needs to change unless a backend endpoint changes.
 * ─────────────────────────────────────────────────────────────────────
 */

const API = '/api';

class ApiError extends Error {
  constructor(status, detail) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

async function request(method, path, body = null) {
  const opts = { method, headers: { 'Content-Type': 'application/json' } };
  if (body) opts.body = JSON.stringify(body);

  const res = await fetch(API + path, opts);

  if (res.status === 204) {
    if (!res.ok) throw new ApiError(res.status, 'An error occurred.');
    return null;
  }

  const data = await res.json();
  if (!res.ok) throw new ApiError(res.status, data.detail || 'An error occurred.');
  return data;
}


export const api = {
  getRepositories:   ()    => request('GET',  '/repositories'),
  importRepository:  (url) => request('POST', '/repository/import',  { github_url: url }),
  processRepository: (id)  => request('POST', '/repository/process', { repository_id: id }),
  getFiles:          (id)  => request('GET',  `/repository/${id}/files`),
  indexRepository:   (id)             => request('POST', `/repository/${id}/index`),
  scanRepository:    (id)             => request('POST', `/repository/${id}/scan`),
  getFindings:       (id)             => request('GET',  `/repository/${id}/findings`),
  generateDoc:       (id, docType)    => request('POST', `/repository/${id}/docs/${docType}`),
  getDoc:            (id, docType)    => request('GET',  `/repository/${id}/docs/${docType}`),
  deleteRepository:  (id)             => request('DELETE', `/repository/${id}`),

  sendChatMessage:   (id, question, sessionId = null) =>
    request('POST', `/repository/${id}/chat`, sessionId ? { question, session_id: sessionId } : { question }),
};