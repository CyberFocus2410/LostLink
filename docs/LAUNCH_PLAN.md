# LostLink Launch Plan & Roadmap

## 1. Current Architecture & Data Model

LostLink is a Deterministic Smart Lost & Found Matcher with an editorial UI and an explainable scoring engine.

### Current Backend Stack
- **Framework**: FastAPI (Python 3.11) with Pydantic v2 schemas and SQLAlchemy 2.0 ORM.
- **Database**: SQLite (local development and automated tests), moving to PostgreSQL with Alembic migrations.
- **Authentication**: JWT access tokens (15-min TTL, PyJWT) and cryptographically random refresh tokens (7-day TTL, SHA-256 hash stored server-side), delivered exclusively via `httpOnly`, `Secure` (in production), `SameSite=Lax` cookies.
- **Security**: Argon2id password hashing (`argon2-cffi`), Origin-header check CSRF protection middleware on mutating methods (`POST`, `PATCH`, `PUT`, `DELETE`), IP-based rate limiting (`slowapi`), and generic auth error responses preventing email enumeration.
- **Matching Algorithm**: Deterministic DSA scoring based on:
  $$S = 0.35C + 0.25L + 0.20D + 0.20K$$
  where $C$ is category compatibility, $L$ is location similarity, $D$ is linear date decay, and $K$ is keyword token Jaccard similarity.
- **In-Memory Index**: Inverted index by category and normalized keywords, warmed on startup from active database records. Runs in a single process / single worker.

### Current Frontend Stack
- **Framework**: React 19 + TypeScript + Vite.
- **Design System**: Editorial canvas (`#F6F7F4`), primary ink (`#263238`), teal accent (`#527C76`), sage (`#DCE8E1`), and warm sand (`#EEE8DE`).
- **Icons**: Lucide React.
- **State Management**: React Context (`AuthContext`) with cookie-based session hydration (`GET /api/auth/me`).

### Database Model (Current Revision: `a1b2c3d4e5f6`)
- `users`: `id` (UUID string), `display_name`, `email` (unique, lowercase), `password_hash` (Argon2id), `role` (`user`/`admin`), `is_active`, `created_at`.
- `refresh_tokens`: `id` (UUID string), `user_id` (FK to `users.id`), `token_hash` (SHA-256 hex string), `expires_at`, `revoked` (boolean), `created_at`.
- `reports`: `id` (UUID string), `type` (`LOST`/`FOUND`), `item_name`, `category`, `description`, `event_date`, `location_text`, `normalized_location`, `status` (`ACTIVE`/`RESOLVED`/`HIDDEN`), `owner_id` (FK to `users.id`, nullable for legacy/seed reports), `contact_name`, `contact_email`, `contact_phone`, `created_at`, `updated_at`.
- `contact_requests`: `id` (UUID string), `report_id` (FK to `reports.id`), `requester_name`, `requester_email`, `message`, `status` (`PENDING`/`ACCEPTED`/`DECLINED`), `created_at`.
- `report_flags`: `id` (UUID string), `report_id` (FK to `reports.id`), `reason`, `created_at`.

---

## 2. Gaps Blocking Public Launch & Mitigations

1. **Authentication & Ownership (Phase 1 — In Progress)**:
   - *Gap*: Anonymous report creation allowed unauthorized modifications and impersonation.
   - *Mitigation*: httpOnly cookie JWT + refresh token rotation; report ownership enforced; "My Reports" scoped to authenticated user.
2. **Campus-Specific Hardcoding (Phase 2)**:
   - *Gap*: Hardcoded location clusters tied to a single university campus.
   - *Mitigation*: Community/campus tenant model, optional GPS coordinates with haversine distance.
3. **Database Concurrency & Durability (Phase 3)**:
   - *Gap*: SQLite file locking and thread-safety limits in multi-user concurrent production.
   - *Mitigation*: PostgreSQL migration with UUID and timestamptz, verified with docker-compose.
4. **Mobile Usability & Installability (Phase 4)**:
   - *Gap*: Web-only navigation without offline caching or home screen launch.
   - *Mitigation*: PWA manifest, service worker shell caching, install prompt UI.
5. **Photo Evidence (Phase 6)**:
   - *Gap*: Text-only descriptions make item identification ambiguous.
   - *Mitigation*: Object storage (Supabase/Cloudinary), server-side validation, EXIF stripping, camera capture input.
6. **Privacy & Contact Information (Phase 7)**:
   - *Gap*: Contact details submitted with reports could be exposed or scraped.
   - *Mitigation*: Blind contact flow where contact requests are mediated; email/phone revealed only after owner accepts; abuse reporting; delete account flow.
7. **Production Deployment & Stability (Phase 8)**:
   - *Gap*: No production container, orchestration, or automated E2E tests.
   - *Mitigation*: Single-service multi-stage Dockerfile on Render serving React static files via FastAPI with 1 worker, Playwright test suite, DEPLOYMENT.md.

---

## 3. Approved Phased Implementation Roadmap

### Phase 1: Authentication & User Accounts (COMPLETED)
- [x] Backend: User & RefreshToken models, Alembic migration `a1b2c3d4e5f6`.
- [x] Backend: Argon2id password hashing via `argon2-cffi`, JWT via `PyJWT`.
- [x] Backend: httpOnly, SameSite=Lax, Secure cookies for access (15 min) and refresh tokens (7 days, path `/api/auth`).
- [x] Backend: Refresh token rotation and server-side revocation on logout.
- [x] Backend: Origin-header check CSRF protection middleware.
- [x] Backend: Generic auth error messages and password policy (min 8 chars, letter + number).
- [x] Backend: Rate limiting on login and register endpoints via `slowapi`.
- [x] Backend: Report ownership enforcement (`owner_id`), permission checks on edit/resolve.
- [x] Backend: Dedicated `/api/reports/mine` endpoint for user-scoped reports.
- [x] Frontend: `AuthContext` with automatic cookie-based session verification.
- [x] Frontend: Login, Register, Forgot Password, and Reset Password views in editorial design system.
- [x] Frontend: Protected route wrappers and auth-aware navigation (Login/Logout buttons, user chip).
- [x] Frontend: "My Reports" connected to `/api/reports/mine` (removing localStorage dependency).
- [x] Frontend: Create report flow requiring authentication.

### Phase 2: Location Generalization & Multi-Community (COMPLETED)
- [x] Add `community` entity (name, slug) to partition matching domains.
- [x] Add optional `latitude` and `longitude` fields to reports.
- [x] Implement haversine distance scoring when coordinates are present, falling back to normalized text clusters.
- [x] Preserve deterministic 0–100 heuristic scoring and human-readable score explanation.
- [x] Define per-community facility clusters in DB with admin endpoints.
- [x] Update frontend with community selector, GPS coordinate detection via browser Geolocation.
- [x] Update formula explanation in README.

### Phase 3: PostgreSQL Migration & Verification (COMPLETED)
- [x] Transition `DATABASE_URL` to PostgreSQL (`postgresql+psycopg2` / `postgresql+psycopg`).
- [x] Run migrations and execute smoke tests against real PostgreSQL via `docker-compose.yml`.
- [x] Native PostgreSQL types: UUID, `TIMESTAMPTZ`, composite indexes on status, category, date, and owner.
- [x] SQLite-to-PostgreSQL data migration script (`backend/scripts/migrate_sqlite_to_postgres.py`).
- [x] Rebuild in-memory category/token indexes from database active reports on startup.
- [x] Health check `/api/health` verifying database connectivity and active index size.
- [x] Document single-worker requirement in README.

### Phase 4: Progressive Web App (PWA) (COMPLETED)
- [x] Configure `vite-plugin-pwa` with web app manifest (name, colors `#527C76` and `#F6F7F4`, standalone display).
- [x] Generate maskable icons and standard icon sets (192x192, 512x512).
- [x] Service worker: precache app shell, network-first for `/api` requests, offline fallback screen.
- [x] In-app install banner (`beforeinstallprompt`) and iOS Safari "Add to Home Screen" guide.
- [x] Touch target (44px) and 360px viewport audit.

### Phase 5: Matching Engine Hardening & Performance (COMPLETED)
- [x] Index memory optimization via slotted dataclasses (`@dataclass(slots=True)` for `ReportRecord` and `ScoredMatch`).
- [x] Type-partitioned inverted index (`self.type_index`) reducing candidate record lookup overhead by ~50%.
- [x] Bounded min-heap extraction accelerated via C-level `heapq.nsmallest` while preserving deterministic tie-breaking.
- [x] Diagnostic metrics endpoint reporting active indexed reports, token counts, and memory footprint in `/api/health`.
- [x] Benchmark regression suite executed across 500, 2000, and 5000 records (3.32x speedup measured at 2000 records).
- [x] Full test suite (55/55 passed) and frontend build verification.

---

### *WAIT FOR USER GO-AHEAD BEFORE STARTING PHASES 6, 7, 8*

### Phase 6: Photo Uploads (COMPLETED)
- [x] Pluggable storage abstraction (`SupabaseStorageProvider`, `LocalStorageProvider`) configured via environment variables.
- [x] Server-side image validation: allowed types (jpeg, png, webp), 5 MB file size limit, magic bytes inspection.
- [x] Security: EXIF and GPS metadata stripping using Pillow; automated thumbnail generation.
- [x] `report_images` table with owner-only upload and deletion endpoints (`POST/DELETE /api/reports/{id}/images`).
- [x] Alembic migration `c4d5e6f7a8b9_add_report_images_table` applied to SQLite and PostgreSQL.
- [x] Frontend: `<input type="file" accept="image/*" capture="environment">` with client compression, thumbnail previews, and lazy-loaded display cards.

### Phase 7: Contact-Request Flow, Privacy & Moderation (COMPLETED)
- [x] Strict double-blind contact workflow: contact details never returned in public report payloads; requester details masked until owner accepts.
- [x] Contact requests workflow: owner approves/declines request before requester contact details are unlocked.
- [x] Abuse reporting system (`report_flags`) with moderation review endpoints (`/api/admin/flags`, `/api/admin/reports/{id}/status`).
- [x] Asynchronous email notifications using FastAPI background tasks and Resend API (contact requests, acceptances, match alerts, password resets).
- [x] Compliance: "Delete My Account & Personal Data" flow (`DELETE /api/auth/me`), Privacy Policy and Terms of Service pages.
- [x] Security hardening: SecurityHeadersMiddleware (CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy).
- [x] Alembic migration `d5e6f7a8b9c0_add_contact_privacy_and_moderation` applied to SQLite and PostgreSQL.

### Phase 8: Production Deployment on Render & Infrastructure (COMPLETED)
- [x] Multi-stage Dockerfile: build React frontend, serve static assets via FastAPI with single Uvicorn worker.
- [x] Automated `alembic upgrade head` execution on container boot (`docker-entrypoint.sh`).
- [x] GitHub Actions CI workflow (`.github/workflows/ci.yml`) testing against live PostgreSQL service container and frontend build.
- [x] Comprehensive `docs/DEPLOYMENT.md` guide covering Render, managed PostgreSQL (Neon/Supabase), storage configuration, DNS, and backups.
- [x] Pre-launch security and privacy review checklist (`docs/LAUNCH_CHECKLIST.md`).

### Phase 9: Final QA & Launch Readiness (COMPLETED)
- [x] End-to-End Playwright test suite (`frontend/e2e/user-journey.spec.ts`) and backend full lifecycle integration test.
- [x] Staging demo seed script (`backend/scripts/seed_staging.py`) with admin, student accounts, communities, pairs, and flags.
- [x] Admin & Moderation Center (frontend `/admin` page + backend endpoints for flags, report takedown, user deactivation).
- [x] Sentry error monitoring integration and privacy-preserving anonymous product analytics (`/api/analytics/*`).
- [x] Updated README.md (live demo URL placeholder, Android/iOS install instructions, updated architecture diagram, and Truthful Implementation Checklist reflecting 66 passing tests).
- [x] Definitive pre-launch security & privacy review audit (`docs/LAUNCH_CHECKLIST.md`).

