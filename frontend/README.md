# CodeVault

A full-stack code snippet manager built to explore real system design tradeoffs — caching invalidation, cursor pagination, full-text search, and public-link sharing — rather than just CRUD.

**Live demo:** _(add link once deployed)_
**Repo:** https://github.com/Yashas2004/CODEVAULT

---

## Overview

CodeVault lets a user save, search, tag, and share code snippets. It's built as a two-service app — a FastAPI backend and a React frontend — with the kind of production concerns (caching, rate limiting, connection pooling) that a toy CRUD app usually skips.

### Features

- JWT auth (register/login)
- Full CRUD on snippets, scoped per user with ownership checks on every mutation
- Full-text search (Postgres `tsvector`, not `ILIKE`)
- Cursor-based pagination
- Redis-backed response caching with O(1) invalidation across all cached queries per user
- Redis-backed rate limiting on auth and write endpoints
- Public shareable links — view-only, no-auth access to a single snippet via an unguessable slug
- CI pipeline (GitHub Actions) running the full test suite on every push

---

## Architecture

┌─────────────┐ HTTPS/JSON ┌──────────────┐
│ React │ ───────────────────────► │ FastAPI │
│ (Vite) │ ◄─────────────────────── │ │
└─────────────┘ └──────┬───────┘
│
┌────────────────────────┼────────────────────────┐
▼ ▼ ▼
┌───────────────┐ ┌────────────────┐ ┌────────────────┐
│ PostgreSQL │ │ Redis │ │ GitHub Actions │
│ (Neon.tech) │ │ (Redis Cloud) │ │ CI │
│ │ │ │ │ │
│ full-text │ │ - cache versions │ │ pytest on every│
│ search index │ │ - rate limits │ │ push to main │
└───────────────┘ └──────────────────┘ └────────────────┘

---

## Tech Stack

| Layer    | Choice                                              |
| -------- | --------------------------------------------------- |
| Frontend | React (Vite), Tailwind CSS, axios, react-router-dom |
| Backend  | FastAPI (Python 3.10), SQLAlchemy                   |
| Database | PostgreSQL (Neon.tech, serverless)                  |
| Cache    | Redis (Redis Cloud)                                 |
| Auth     | JWT (python-jose) + bcrypt (via passlib)            |
| Testing  | pytest + httpx, isolated DB branch                  |
| CI/CD    | GitHub Actions                                      |

---

## Design decisions

Each of these was a deliberate choice with a tradeoff, not the default option.

### 1. Cache versioning instead of key deletion

**Problem:** search results are cached per query string. Deleting a specific cache key on write doesn't help — a user could have dozens of different cached queries (`"react"`, `"auth"`, `""`, paginated variants of each) that all go stale the moment they create a snippet.

**Solution:** every cache key is scoped to a per-user version number: `snippets:{user_id}:v{version}:{query}:{cursor}:{limit}`. A write bumps the version with `INCR`, which instantly invalidates _every_ cached query for that user in O(1) — without needing to know or enumerate what was cached.

### 2. Cursor-based pagination, not OFFSET

`?cursor={last_id}&limit=20` instead of `?page=3&limit=20`. `OFFSET` gets linearly slower as page number grows, since Postgres still has to scan and discard all preceding rows. Cursor pagination uses `WHERE id < :cursor ORDER BY id DESC LIMIT :n`, which hits the primary key index directly regardless of how deep you page.

### 3. Postgres full-text search over `ILIKE`

`ILIKE '%query%'` can't use a standard B-tree index (leading wildcard), so it becomes a full table scan as data grows. Replaced with a `tsvector` column, a GIN index, and a trigger that keeps it updated on insert/update — weighted so title matches rank above tag/language matches.

### 4. Redis-based rate limiting

Sliding-window counter via `INCR` + `EXPIRE`, keyed by IP + endpoint path. Applied per-endpoint: login (10/min), register (5/min), snippet creation (30/min) — tighter on auth endpoints since they're the more common target for abuse.

### 5. Sync endpoints, not async

Deliberately not using `async def` + async SQLAlchemy drivers. Async buys concurrency headroom that isn't needed until there's real concurrent load, at the cost of rewriting the whole data layer. Scaling path instead: horizontal — more Uvicorn worker processes (`--workers N`) — which is a smaller, more reversible change than an async rewrite.

### 6. Explicit connection pool tuning

`pool_pre_ping=True` and `pool_recycle=1800` in `database.py`. Neon (like most serverless Postgres providers) aggressively closes idle connections; without these, the app would intermittently throw "server closed the connection unexpectedly" errors under low traffic.

### 7. Ownership checks on every mutation

Every update/delete query filters by `id AND owner_id`, not just `id` — and returns `404`, not `403`, when the row belongs to someone else (so an attacker can't even confirm the resource exists). Covered explicitly in tests: `test_user_cannot_delete_others_snippet`, `test_user_cannot_update_others_snippet`.

### 8. Public sharing via unguessable slug, not exposed IDs

Sharing needed a way to expose one snippet publicly without leaking the whole ID space. Options considered:

- Make `GET /snippets/{id}` public → rejected: sequential integer IDs let anyone enumerate every user's snippets
- Use the row's own primary key as the public identifier → rejected: couples internal schema to a public contract permanently

Instead: a separate `share_slug` (`secrets.token_urlsafe(12)`, cryptographically random) is generated only when a user explicitly opts in, stored alongside an `is_public` flag. The public route is a fully separate, unauthenticated FastAPI router (`/public/snippets/{slug}`) so its lack of an auth dependency is structurally obvious, not just a missing `Depends()` buried in an authenticated file.

---

## API Reference

| Method | Endpoint                       | Auth | Description                       |
| ------ | ------------------------------ | ---- | --------------------------------- |
| POST   | `/users/register`              | No   | Create account                    |
| POST   | `/users/login`                 | No   | Get JWT                           |
| GET    | `/snippets/?q=&cursor=&limit=` | Yes  | Search + paginate own snippets    |
| POST   | `/snippets/`                   | Yes  | Create snippet                    |
| PUT    | `/snippets/{id}`               | Yes  | Update own snippet                |
| DELETE | `/snippets/{id}`               | Yes  | Delete own snippet                |
| POST   | `/snippets/{id}/share`         | Yes  | Generate/enable public share link |
| DELETE | `/snippets/{id}/share`         | Yes  | Revoke public sharing             |
| GET    | `/public/snippets/{slug}`      | No   | View a publicly shared snippet    |

---

## Running locally

**Backend**

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
# create backend/.env with DATABASE_URL, REDIS_URL, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
uvicorn app.main:app --reload
```

**Frontend**

```bash
cd frontend
npm install
npm run dev
```

## Testing

```bash
cd backend
python -m pytest tests/ -v
```

10 tests covering auth, CRUD, cache invalidation correctness, pagination boundaries, and cross-user access control. Runs automatically on every push via GitHub Actions.

---

## Author

Yashas — [LinkedIn](https://www.linkedin.com/in/yashas-r-790316308) · [GitHub](https://github.com/Yashas2004)
