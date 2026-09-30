# Deployment

Recommended split for this project:

- **Frontend:** Vercel (Next.js)
- **Backend:** Render (FastAPI)
- **Database:** Neon Postgres with pgvector

This keeps the existing application architecture: Next.js → FastAPI → LangGraph → PostgreSQL/pgvector + Groq.

## 0. Before deployment

1. Use the cleaned source ZIP/repository; do not commit real `.env` files or credentials.
2. Run the backend syntax check: `python -m compileall -q backend`.
3. In `frontend/`, run `npm install` and then `npm run build` locally. Commit the generated `package-lock.json` so the dependency tree is reproducible.
4. Test register/login, PDF upload, document, web, both, image, image+document, image+web, and image+document+web.

## 1. Production database — Neon

Create a Neon Postgres project and use its **pooled** connection string for the backend. Neon supports pgvector; enable it with:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Then run:

```bash
psql "$DATABASE_URL" -f backend/migrations/001_add_users_and_ownership.sql
```

The migration is designed to bootstrap a fresh database as well as upgrade the existing schema. The embedding column remains `vector(384)`.

Neon documents pgvector support and recommends pooled connections for applications with many concurrent connections. citeturn768261search0turn565270search6

## 2. Backend — Render

Create a **Web Service** with the repository root set to `backend/`. Render's documented FastAPI start command is:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

Build command:

```bash
pip install -r requirements.txt
```

Set these backend environment variables in Render's environment/secrets UI:

```text
GROQ_API_KEY=<real secret>
DATABASE_URL=<Neon pooled URL>
JWT_SECRET=<long random secret>
FRONTEND_URL=<exact Vercel origin>
MAX_PDF_BYTES=26214400
MAX_IMAGE_BYTES=4194304
```

You do not need to set the `DB_*` variables when `DATABASE_URL` is present.

Add health check path:

```text
/health
```

**Compute note:** the backend imports `sentence-transformers` and PyTorch at startup. Render's free web service is 512 MB RAM; the project README notes this workload needs about 1 GB+, so use a service with enough memory for model loading rather than relying on the 512 MB free instance. Render currently lists a 1 CPU / 2 GB web service option. citeturn926206search0turn926206search3

Render provides managed TLS/HTTPS for web services and supports environment variables/secrets. citeturn103304search3turn926206search4

## 3. Frontend — Vercel

Create a Vercel project from the repository and set its **Root Directory** to:

```text
frontend
```

Vercel natively supports Next.js deployments. citeturn768261search1

Set this frontend environment variable:

```text
NEXT_PUBLIC_API_BASE_URL=https://YOUR-BACKEND.onrender.com
```

Remember that variables beginning with `NEXT_PUBLIC_` are exposed to the browser. Only put the public backend URL there — never put the Groq key, database URL/password, or JWT secret in a `NEXT_PUBLIC_*` variable. citeturn768261search2

## 4. CORS

Set the Render backend variable:

```text
FRONTEND_URL=https://YOUR-APP.vercel.app
```

Do not add a trailing slash. After changing it, redeploy the backend.

## 5. Next.js version

The generated frontend currently declares Next.js 15.x. Next.js 15 is still in Maintenance LTS, while 16.x is Active LTS. Before production, run a local install/build and make sure the installed Next.js version has the latest security patch available for the chosen major. Do not do a major-version upgrade without testing. citeturn103304search7turn341081search0

## 6. Authentication note

The current project uses backend JWT authentication with the token kept in browser `localStorage`. This works for the portfolio/MVP architecture, but it is not the strongest production session design because JavaScript can access the token. A later hardening pass can move authentication to secure, HttpOnly cookies plus CSRF protection.

Also note that the current `/auth/logout` is client-side/stateless: an already-issued token remains valid until expiry if it is stolen.

## 7. Rate limiting

Before making the app broadly public, add rate limiting/WAF protection for:

- `/auth/register`
- `/auth/login`
- `/agentic-research-multimodal`
- `/upload-pdf`

The current source does not include distributed rate limiting.

## 8. Web-source visibility

The backend currently returns `has_web_result` rather than a structured list of web URLs. Therefore the UI can honestly show that web research was used, but should not present a fake list of web sources.

Groq's built-in browser search is currently supported by GPT-OSS 20B and related supported models; Qwen 3.8 27B is the project's vision model. citeturn103304search2turn103304search5

## 9. Final production checklist

- [ ] Clean ZIP/repository contains no real secrets
- [ ] Frontend has a committed `package-lock.json`
- [ ] `npm run build` passes
- [ ] Backend `compileall` passes
- [ ] Neon database created
- [ ] pgvector enabled
- [ ] Migration applied
- [ ] Render backend deployed
- [ ] `/health` returns 200
- [ ] Render secrets/environment variables configured
- [ ] Vercel frontend deployed
- [ ] `NEXT_PUBLIC_API_BASE_URL` set
- [ ] Render `FRONTEND_URL` set exactly
- [ ] Auth tested
- [ ] All 8 agent routes tested in production
- [ ] User A cannot retrieve User B's documents
- [ ] PDF and image size limits tested
- [ ] No API/database secrets appear in frontend bundle
