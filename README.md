# AI Research & Knowledge Agent

Next.js frontend + FastAPI/LangGraph backend. Users register, upload PDFs to a private pgvector knowledge base, and ask questions; a planner routes each one to direct / document / web / both / image variants, then synthesizes an answer.

## Architecture
Next.js → FastAPI → LangGraph (planner → document / web / image routes → synthesis) → answer.
Routes: `direct, document, web, both, image, image_document, image_web, image_both`.

## Backend (unchanged core, from Phase 1)
- RAG: PDF → extraction → cleaning → chunking → `all-MiniLM-L6-v2` (384-d) → PostgreSQL + pgvector
- Hybrid retrieval: semantic search + PostgreSQL full-text search → Reciprocal Rank Fusion
- Vision model: `qwen/qwen3.8-27b` via Groq
- Auth: bcrypt + JWT (`Authorization: Bearer`), every query filtered by the token's user id — the browser never sends a user id

## Frontend
Next.js 15 (App Router), React 19, TypeScript, plain CSS (warm espresso/cream theme). No UI framework.
Pages: `/` landing, `/login`, `/register`, `/home`, `/research`, `/knowledge-base`, `/documents`, `/activity`, `/history`, `/history/[id]`, `/settings`.
API access goes through `src/lib/api.ts`, using `NEXT_PUBLIC_API_BASE_URL`.

## Local development
```bash
# backend
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in real values
psql -f migrations/001_add_users_and_ownership.sql
uvicorn main:app --reload

# frontend
cd frontend && cp .env.example .env.local   # set NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
npm install && npm run dev
```
See `DEPLOYMENT.md` for production.

## API used by the frontend
`POST /auth/register|login|logout`, `GET /auth/me`, `POST /upload-pdf`, `GET /documents`, `DELETE /documents/{id}`,
`POST /agentic-research-multimodal`, `GET /research-history`, `GET /research-history/{id}`.

## Known limitations (please read)
- **Frontend build still needs to be verified on the developer machine.** The source was inspected here, but a complete `npm install && npm run build` could not be completed in this environment. Run both locally before deployment and commit the generated `package-lock.json`.
- **No live per-node progress.** The backend executes the graph in one HTTP request, so the Activity panel can show request-level loading but not true server-sent stage updates.
- **Web source listing is limited.** The current frontend receives a `has_web_result` flag rather than a structured list of web URLs.
- **JWT is stored in browser `localStorage`.** This is workable for a portfolio/MVP, but stronger production session hardening would use Secure/HttpOnly cookies and CSRF protection.
- **Auth logout is stateless.** A token remains valid until expiry if it has been copied; the browser simply discards it on logout.
- **Rate limiting is not implemented in the app.** Add platform/WAF or backend rate limiting before broad public use.
- **Legacy endpoints remain in `main.py`.** The frontend uses the authenticated multimodal endpoint, document APIs, and auth APIs; unused legacy endpoints can be removed in a later hardening pass.
- Backend upload limits are enforced server-side: PDF 25 MB and image 4 MB by default.
- `requirements.txt` is a pinned environment export; after successful local installation/build, consider keeping it aligned with the tested deployment environment.
