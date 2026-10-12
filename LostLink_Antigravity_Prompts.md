# LostLink — Antigravity Prompts

Use these prompts sequentially in the same workspace. The full PRD/FRD is in `LostLink_PRD_FRD_Antigravity_Prompts.docx`.

## Prompt 1 — Product planning and repo setup

You are the senior product engineer and UX lead building LostLink, a Smart Lost & Found Matcher for a Data Structures PBL. First inspect the existing workspace and report what is already present. Do not overwrite working code blindly. Create an implementation plan, architecture diagram, file structure, data model, API contract and acceptance-test checklist before coding.

Product: users submit LOST or FOUND item reports. The system ranks opposite-type, active candidate reports by category, location, date and descriptive keywords. Every result must show a transparent 0–100 heuristic score, component scores and plain-language reasons. It must never claim ownership is verified.

Preferred stack: React + TypeScript + Vite frontend; FastAPI + Pydantic + SQLAlchemy backend; SQLite for local demo; Alembic migrations; pytest. If the course explicitly requires the algorithm in C++, preserve that requirement and implement the matching engine in C++ behind a clean service/API boundary. Do not substitute opaque AI or a hosted matching API for the DSA engine.

Visual direction: premium but restrained, light muted tones, editorial clarity, purposeful whitespace, strong typography and precise alignment. Tokens: canvas #F6F7F4, surface #FFFFFF, ink #263238, secondary #687579, sage #DCE8E1, teal #527C76, warm sand #EEE8DE, border #E1E6E2. Avoid generic AI dashboard patterns, excessive gradients, glassmorphism, neon, random blobs, excessive rounded cards and decorative charts. Do not code until the plan and structure are clear. Then summarize the planned milestones and wait for the next prompt.

## Prompt 2 — Build backend and persistence

Implement the LostLink backend according to the agreed plan. Create maintainable modules for API routes, schemas, models, repositories, services, matching, indexing, configuration and tests. Use FastAPI, Pydantic, SQLAlchemy, Alembic and SQLite for local development.

Implement:
- GET /api/health
- GET /api/reports with q, type, category, status, date range, location, pagination and sort filters
- POST /api/reports
- GET /api/reports/{id}
- PATCH /api/reports/{id}
- POST /api/reports/{id}/resolve
- GET /api/reports/{id}/matches with limit and minimum score
- POST /api/contact-requests and POST /api/reports/{id}/flag if they fit the agreed MVP scope

Use validated enums for LOST/FOUND and ACTIVE/RESOLVED/HIDDEN. Validate required fields, lengths and dates server-side. Generate unique IDs safely. Persist all reports; never use a global in-memory list as the source of truth. Add migrations, seed data and a .env.example. Use a service/repository architecture and consistent JSON success/error response formats. Add tests for valid creation, invalid input, filters, missing IDs, edits, resolution and persistence. Keep private contact details out of public response schemas. Do not expose stack traces. Run the tests and fix failures before reporting completion. Do not build a fake backend or silently skip tests.

## Prompt 3 — Build the matching engine and DSA evidence

Implement LostLink's deterministic, explainable matching engine. Do not use an LLM, embeddings or opaque third-party matching service. Opposite report types only; exclude resolved/hidden reports and the source report. Use configurable candidate windows and category compatibility rules.

Normalize text with lowercase, whitespace/punctuation normalization and tokenization. Calculate C category score, L location score, D date score and K Jaccard keyword similarity, each 0–100. Initial weights: S = 0.35C + 0.25L + 0.20D + 0.20K. Put the weights and date decay in one configuration module and document that they are heuristic, not probabilities. Use an initial date rule D = max(0, 100 - 15 × absolute day difference), configurable and covered by tests. Exact normalized location can score 100; configured alias/nearby location can score 70; unrelated/unknown location scores 0. Category exact compatible match scores 100, incompatible category 0. Empty token sets must return keyword score 0.

Build and maintain a category index and inverted token-to-report-ID index, deduplicate candidate IDs, and keep indexes consistent after create/edit/resolve/hide. Add a safe linear-scan fallback for correctness. Rank deterministically by total score descending, then date gap ascending, then ID ascending. Use full sorting for simple cases and demonstrate a bounded min-heap for top-N results if appropriate. Return total score, all component scores, shared keywords and readable reasons.

Add unit tests for exact match, partial match, unrelated category, same-type exclusion, resolved exclusion, empty descriptions, punctuation/case normalization, no candidates, date boundaries, ties, edit/index update and resolution/index removal. Add a benchmark script comparing linear scan and indexed candidate generation on reproducible seeded datasets. Report measured timings only; never fabricate benchmark results. Document time and space complexity and explain any trade-offs.

## Prompt 4 — Build the frontend design system and screens

Build the LostLink frontend with React, TypeScript and Vite, using a small consistent component system. Do not produce a generic AI-generated dashboard. Design it like a carefully art-directed, trustworthy campus service: light muted neutral background, warm-white surfaces, sage and muted teal accents, slate typography, subtle borders, compact purposeful cards, strong spacing rhythm and clear hierarchy.

Use the following tokens consistently: #F6F7F4 canvas, #FFFFFF surface, #263238 primary text, #687579 secondary text, #DCE8E1 muted sage, #527C76 primary accent, #EEE8DE warm secondary, #E1E6E2 borders. Use accessible contrast, keyboard focus, visible labels, a restrained radius system and one icon family. Avoid gradients as decoration, glassmorphism, neon, giant rounded cards, random blobs, excessive animation and fake charts.

Build responsive screens:
1. Dashboard with clear actions, real report counts, recent reports and real potential matches.
2. Reports list with search, filters, sort, pagination and empty/loading/error states.
3. Create/edit report form with field validation.
4. Report detail and ranked match results.
5. My reports with status and resolve action.
6. Optional moderation/contact request views only if the backend is implemented.

Use realistic seeded demo content, not lorem ipsum. Make desktop and mobile layouts intentionally. Keep components small and reusable. All primary controls must work. Do not fabricate data or hardcode success states. Do not wire the interface to mock arrays once the API exists. Build the visual foundation and screens, then report the pages/components completed and any gaps.

## Prompt 5 — Integrate frontend with backend

Connect every core LostLink screen to the actual API. Create a typed API client and centralize base URL configuration using environment variables. Use real GET/POST/PATCH requests for reports, search, filters, matching and resolution. Ensure the frontend never calculates a fake match score independently of the backend.

Implement loading, empty, success, validation, server-error and network-error states. Disable submit while pending, prevent duplicate submissions, preserve form inputs on recoverable errors, and provide retry actions where appropriate. Show total score, component breakdown and reasons returned by the server. Include the message 'Potential match—not verified ownership' on match screens. Hide private contact data in public lists. Ensure edits and resolution refresh affected reports and matches.

Add .env.example with safe placeholders. Test the app with the backend stopped, with an invalid form, with no results, and with a successful create-to-match-to-resolve workflow. Remove mock data from production paths. Do not claim an integration works unless you have run it end-to-end.

## Prompt 6 — QA, security, accessibility and delivery

Perform a full LostLink quality pass. Inspect the complete repository and compare it against the PRD/FRD. Run backend tests, frontend lint/type checks, production build and end-to-end tests if the workspace supports them. Fix actual failures instead of merely listing them.

Verify: database persistence after restart; server-side validation; create/edit/resolve index consistency; correct opposite-type matching; deterministic rankings; match explanations; pagination and combined filters; no dead buttons; no fake counts or mock results in live flows; safe error messages; no private contact fields in public API responses; authorization checks for mutations where auth exists; keyboard navigation and visible focus; responsive layouts; accessible labels and contrast; no broken routes or console errors.

Create/update README with prerequisites, environment variables, migrations, seed command, frontend/backend startup commands, tests, architecture, API examples, known limitations and demo script. Add a concise DSA explanation and measured benchmark methodology. Search for secrets and ensure none are committed. End with a truthful checklist: implemented, tested, not implemented, and known limitations. Do not mark a requirement complete without evidence.

## Prompt 7 — Optional C++ core if required by faculty

If this PBL requires the DSA implementation to be in C++, create a separate C++17 matching-engine module with ItemReport, report lookup, category index, inverted keyword index, Jaccard keyword scoring, weighted scoring and a max-heap/bounded top-N ranking. Keep business rules deterministic and unit-testable. Do not merely call Python's built-in matching logic from C++ or use a library that hides the core algorithm. Provide a documented interface and a small JSON input/output adapter or service boundary so the frontend/backend can use it. Add CMake or clear build instructions, sample input/output, unit tests and complexity analysis. Keep the database as the source of truth and rebuild in-memory indexes safely on startup. First inspect the current architecture and propose the smallest integration that preserves working code.
