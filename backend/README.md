# AI Research Agent — Backend (Phase 1: Auth + User Isolation)

FastAPI + LangGraph + PostgreSQL/pgvector. The RAG, hybrid retrieval (semantic + full-text + RRF),
LangGraph routing and multimodal logic are unchanged; this phase adds authentication and
per-user data ownership around them.

## What changed in Phase 1

- `auth.py` — bcrypt password hashing, JWT (HS256, 7-day expiry), `get_current_user` dependency
- `schemas.py` — Pydantic models for auth, documents, history
- `models.py` — new `User` and `Document` tables; `user_id` on `document_chunks` and `research_queries`; `route` on `research_queries`
- `migrations/001_add_users_and_ownership.sql` — re-runnable migration for an existing database
- `hybrid_retrieve`, `search_uploaded_documents`, `has_uploaded_documents` now require `user_id`
- `agent_workflow.py` — `user_id` added to `ResearchState`, passed to every retrieval node
- `/upload-pdf` — no longer builds a file path from the client filename (path-traversal fix); temp file is always deleted
- `/agentic-research-multimodal` — now saves each run to the user's research history
- CORS origins configurable via `FRONTEND_URL`
- `requirements.txt` converted from UTF-16 to UTF-8; added `pyjwt`, `bcrypt`, `email-validator`

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows  (source .venv/bin/activate on macOS/Linux)
pip install -r requirements.txt
cp .env.example .env          # then fill in real values
```

Apply the migration to your existing database:

```bash
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f migrations/001_add_users_and_ownership.sql
```

Old rows (created before auth) get `user_id = NULL` and become invisible through the API.
See the note at the bottom of the SQL file to assign them to your first account.

Run:

```bash
uvicorn main:app --reload
```

## API overview

| Method | Path | Auth |
|---|---|---|
| POST | `/auth/register`, `/auth/login` | public |
| POST | `/auth/logout` | required |
| GET | `/auth/me` | required |
| POST | `/upload-pdf` | required |
| POST | `/agentic-research-multimodal` (form: `question`, optional image `file`) | required |
| GET | `/documents` | required |
| DELETE | `/documents/{id}` | required |
| GET | `/research-history`, `/research-history/{id}` | required |

Legacy/experimental endpoints (`/chat`, `/research`, `/agent`, `/rag`, `/web-research`,
`/vector-search`, `/hybrid-search`, `/agentic-research`, `/analyze-image`) are kept but now
require auth and are user-scoped. The new frontend will not use them; consider removing them before production.

Send the token as `Authorization: Bearer <access_token>`.

## Known limitations (be aware)

- **Not run end-to-end.** The changes were written and syntax-checked (`py_compile`) without network access,
  so nothing here has been executed against a real Postgres, Groq, or the installed dependencies.
  Please run the migration and smoke-test register -> login -> upload -> research on your machine.
- Logout is client-side only (stateless JWT); tokens stay valid until expiry.
- No rate limiting on `/auth/*`.
- The Document row and its chunks are written in one transaction, but embedding is done synchronously
  in the request, so large PDFs will make the upload request slow.
- `requirements.txt` is still a full `pip freeze`; it has not been pruned.
