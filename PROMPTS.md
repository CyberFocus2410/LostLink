Prompt 1: Audit and roadmap
Audit the whole repo and produce docs/LAUNCH_PLAN.md. Cover:
1. Current architecture and data model (tables, columns, relationships).
2. Gaps blocking a public launch: authentication, ownership of reports, photo uploads, email notifications, SQLite limits, in-memory index with multiple workers, CORS, rate limiting, input validation, campus-specific location logic.
3. A phased task list in dependency order with risk notes.
Don't change any code yet. Ask me clarifying questions at the end if anything is ambiguous.


Prompt 2: PostgreSQL migration
Migrate the database layer from SQLite to PostgreSQL.
- Use DATABASE_URL from env (postgresql+psycopg driver), with SQLite still usable for local dev and tests via a different URL.
- Fix any SQLite-specific types or behavior. Use proper UUID, timestamptz, and indexes on status, type, category, event_date, and owner_id.
- Create a new Alembic migration; don't edit old ones. Test it against a fresh Postgres (use docker-compose.yml with a postgres service for local).
- Add a script to migrate existing SQLite data into Postgres.
- On startup, rebuild the in-memory category/token indexes from ACTIVE reports in the database, and add a /api/health check that confirms the DB connection and index size.
- Document in README that the app must run with a single worker because of the in-memory index, and note what would be needed to scale it later.



Prompt 3: Users and authentication
Add real user accounts.
Backend:
- users table: id (UUID), name, email (unique, lowercased), password_hash, phone (optional), email_verified, is_active, role (USER/ADMIN), created_at, updated_at.
- Endpoints: register, login, logout, refresh, me, update profile, change password, delete account (soft-delete or anonymize, and keep reports consistent), forgot/reset password.
- Hash passwords with argon2 (or bcrypt). Issue short-lived access tokens via httpOnly, Secure, SameSite=Lax cookies. Never store tokens in localStorage.
- Add owner_id (FK to users) to reports; only the owner can edit, resolve or delete their report; admins can moderate. Migrate existing rows to a "legacy" system user.
- Rate-limit login/register/reset endpoints. Validate input strictly with Pydantic. Return generic errors that don't reveal whether an email exists.
Frontend:
- Login, Register, Forgot Password, and Profile pages in the existing design system (#F6F7F4 canvas, #527C76 teal, #263238 ink); protected routes; auth context; "My Reports" shows only the logged-in user's reports; mobile-first forms.
Add tests for auth flows and permission checks (including "user A cannot edit user B's report").


Prompt 4: Photo uploads
Add photo upload for reports (up to 3 images per report).
- Store images in object storage (Supabase Storage or Cloudinary; use env vars, and put the provider behind a small storage interface so it can be swapped).
- Validate server-side: allowed types (jpeg/png/webp), max 5 MB each, verify real content type, strip EXIF/GPS metadata, generate resized thumbnails.
- Add a report_images table, upload/delete endpoints (owner only), and show images on the Browse, Detail and Match cards with lazy loading and an image-less fallback.
- On the frontend, use <input type="file" accept="image/*" capture="environment"> so phone users can use the camera, with client-side compression before upload and a preview with a remove button.
- Add tests, and update the privacy notes (photos are public to logged-in users).



Prompt 5: Privacy, contact flow, and security hardening
Harden privacy and security for public use.
1. Contact flow: users never see each other's email or phone. Contact requests are stored in the DB and visible only to the report owner, who can accept or decline. Only after acceptance is the requester's chosen contact method revealed. Add a block/report-abuse option and admin moderation endpoints.
2. Email notifications: send emails (use Resend, Brevo or SMTP via env vars) for verification, password reset, a new strong match (score >= a configurable threshold), and new contact requests. Use FastAPI background tasks and never block requests.
3. Security: strict CORS from env, security headers (CSP, X-Content-Type-Options, frame-ancestors), request size limits, global rate limiting, structured logging without PII, and no stack traces in production responses.
4. Add a Privacy Policy and Terms page, plus a "Delete my account and data" flow, consistent with data-protection expectations (India's DPDP Act, and GDPR if users outside India are possible).
5. Run a dependency vulnerability check (pip-audit, npm audit) and fix what's reasonable.
Add tests for the contact-reveal rules and for the privacy guarantees in the README.


Prompt 6: Generalize beyond one campus (optional)
The location scoring currently relies on campus facility clusters. Make it work for a public app without breaking existing behavior:
- Add a "community/campus" entity (name, slug). Reports belong to one; matching only runs within the same community by default. Admins can define facility clusters per community in the DB instead of hardcoded config.
- Add optional latitude/longitude on reports; when present on both sides, use haversine distance to derive the location score (keep the existing 0/70/100 scale), and fall back to the text/cluster method otherwise.
- Keep the scoring formula and tie-breaking deterministic, update the explanation text, benchmarks, and tests, and update the README's formula section.


Prompt 7: Make it an installable PWA
Turn the frontend into an installable, mobile-first Progressive Web App.
- Use vite-plugin-pwa with a web app manifest: name "LostLink", short_name, theme_color #527C76, background_color #F6F7F4, display "standalone", start_url "/", and 192/512 plus maskable icons (generate a simple, clean icon set from a teal "link" glyph).
- Service worker: precache the app shell; network-first for /api calls (never cache authenticated API responses or personal data); an offline fallback page; and an "update available" toast.
- Add an in-app "Install LostLink" button using the beforeinstallprompt event (Android/desktop Chrome), and an iOS-specific hint explaining Share → Add to Home Screen, shown only on iOS Safari when not already installed.
- Add the viewport meta tag, safe-area insets, 44px minimum tap targets, apple-touch-icon and apple-mobile-web-app tags. Audit all screens at 360px width.
- Run a Lighthouse audit (PWA, performance, accessibility) and fix issues until the PWA criteria pass. Report the scores.


Prompt 8: Deployment
Prepare production deployment on Render with a single service.
- Multi-stage Dockerfile: build the React app, then serve it as static files from FastAPI (SPA fallback for client-side routes, /api for the API), running uvicorn with exactly 1 worker.
- Run alembic upgrade head on release/startup safely.
- Add render.yaml (or equivalent), a production-settings module, a full .env.example covering DATABASE_URL, SECRET_KEY, storage keys, email keys, ALLOWED_ORIGINS, and APP_BASE_URL, and a /api/health endpoint for health checks.
- Add a GitHub Actions workflow: run backend pytest and frontend lint/typecheck/build on every push and PR.
- Write docs/DEPLOYMENT.md as a click-by-click guide for me covering: creating the Neon/Supabase database, creating the storage bucket, setting env vars in Render, deploying, adding a custom domain with HTTPS, and a database backup/restore procedure.
List every manual step I must perform, since you can't create accounts for me.


Prompt 9: Final QA and launch readiness
Do a final launch-readiness pass.
1. Write end-to-end tests (Playwright) for: register → verify email → log in → report lost item with photo → see matches → send contact request → owner accepts → resolve → delete account.
2. Seed script for a staging environment with realistic demo data and a demo admin.
3. Add basic admin screens: list/flag/remove reports, view abuse reports, deactivate users.
4. Add error monitoring (Sentry, optional via env var) and basic product analytics that don't collect PII.
5. Update README.md: live demo URL placeholder, "Install on your phone" instructions for Android and iOS, updated architecture diagram (Postgres, storage, auth, PWA), and an updated "Truthful Implementation Checklist" that moves finished items out of "Deferred".
6. Produce docs/LAUNCH_CHECKLIST.md with a pre-launch security and privacy review, and a list of anything still risky.