# Database Schema — AI Developer Assistant

## ER Diagram

```mermaid
erDiagram
    USERS ||--o{ REPOSITORIES : owns
    USERS ||--o{ CHAT_SESSIONS : starts
    REPOSITORIES ||--o{ FILES : contains
    REPOSITORIES ||--o{ CHAT_SESSIONS : "scoped to"
    REPOSITORIES ||--o{ AGENT_LOGS : "scoped to"
    FILES ||--o{ CHUNKS : "split into"
    CHUNKS ||--o| EMBEDDINGS_METADATA : "points to vector"
    CHAT_SESSIONS ||--o{ CHAT_MESSAGES : contains
    CHAT_SESSIONS ||--o{ AGENT_LOGS : "scoped to"

    USERS { int id PK, string email UK, string hashed_password, string full_name, datetime created_at }
    REPOSITORIES { int id PK, int user_id FK, string github_url, string owner, string name, string default_branch, string local_path, string status, string error_message, int total_files, datetime created_at, datetime updated_at }
    FILES { int id PK, int repository_id FK, string path, string language, int size_bytes, string content_hash, datetime created_at }
    CHUNKS { int id PK, int file_id FK, int repository_id FK, int chunk_index, text content, int start_line, int end_line, int token_count, datetime created_at }
    EMBEDDINGS_METADATA { int id PK, int chunk_id FK, string vector_id, string embedding_model, int dimension, datetime created_at }
    CHAT_SESSIONS { int id PK, int repository_id FK, int user_id FK, string title, datetime created_at }
    CHAT_MESSAGES { int id PK, int session_id FK, string role, text content, text citations, datetime created_at }
    AGENT_LOGS { int id PK, int repository_id FK, int session_id FK, string agent_name, text input_summary, text output_summary, string status, int latency_ms, datetime created_at }
```

## Status

| Table | Status | Populated by |
|---|---|---|
| `users` | **Live** | Auto-created demo user |
| `repositories` | **Live** | `POST /api/repository/import` |
| `files` | **Live** | `POST /api/repository/process` |
| `chunks` | Schema only | Phase 2 |
| `embeddings_metadata` | Schema only | Phase 2 |
| `chat_sessions` / `chat_messages` | Schema only | Phase 3 |
| `agent_logs` | Schema only | Phase 8 |

## Notable decisions

- `embeddings_metadata` stores only a Pinecone `vector_id` pointer, not the vector itself.
- `chunks.repository_id` is denormalized (avoids a join for "all chunks in this repo").
- Cascade deletes everywhere except `agent_logs.session_id`, which is `ON DELETE SET NULL` to preserve the audit trail.
- Unique constraints: `(user_id, github_url)` on repositories (409 on duplicate import), `(repository_id, path)` on files (idempotent re-processing).
