# LostLink — Functional Requirements Document (FRD)

**Version:** 1.0  
**Project type:** Data Structures PBL  
**Related document:** LostLink PRD  
**Status:** Implementation specification

## 1. System Overview

LostLink accepts lost and found reports, persists them, discovers plausible candidates, ranks them using a deterministic matching algorithm, and provides an explanation for each result.

The matching engine is decision support only. A score does not prove ownership or confirm that two reports refer to the same physical item.

## 2. Recommended Architecture

### Recommended stack
- **Frontend:** React + TypeScript + Vite.
- **Backend:** FastAPI + Pydantic.
- **Persistence:** SQLite for local PBL/demo; PostgreSQL may be used for multi-user deployment.
- **ORM/migrations:** SQLAlchemy + Alembic.
- **Testing:** pytest for backend; frontend lint/type checks and end-to-end tests where available.
- **DSA core:** deterministic, self-authored matching logic. If the faculty requires C++, implement the matcher in C++ and expose it through a small API/service boundary.

### Logical layers
1. Presentation layer: dashboard, report forms, list, details, and match results.
2. API layer: request validation, authentication/authorization if enabled, and response formatting.
3. Service layer: report lifecycle, matching, indexing, and contact requests.
4. Repository/data layer: persistent report records.
5. In-memory DSA indexes: report lookup, category index, inverted keyword index, and heap-based top-N selection.

The database is the source of truth. In-memory indexes must be updated safely or rebuilt from persisted records at startup.

## 3. Roles

- **Guest:** browse public-safe reports and search, depending on deployment policy.
- **Registered user:** create/edit their own reports, view matches, and request contact.
- **Moderator:** review flagged reports and hide/remove spam; optional for MVP.
- **System:** validate, persist, index, score, rank, and update report states.

## 4. Functional Requirements

| ID | Requirement | Acceptance criteria |
|---|---|---|
| FR-01 | Create report | User submits type, name, category, description, event date, and location. Valid report gets a unique ID and is persisted. |
| FR-02 | Validate input | Required fields, enum values, date format, and length limits are validated on client and server. Invalid requests return field-level errors. |
| FR-03 | View reports | List and detail endpoints return persisted reports with bounded result counts or pagination. |
| FR-04 | Search and filter | Search keyword and filter by type, category, date range, location, and status. Filters can be combined. |
| FR-05 | Edit report | Owner can update allowed fields; indexes and match results are refreshed. |
| FR-06 | Resolve report | Authorized owner/moderator can mark a report resolved/returned. Resolved reports are excluded from active matching by default. |
| FR-07 | Candidate generation | Compare only against active reports of the opposite type; category/date filtering is configurable. |
| FR-08 | Score candidates | Calculate category, location, date, and keyword scores from 0–100 and combine them using documented weights. |
| FR-09 | Rank candidates | Return top N candidates by total score descending with deterministic tie-breaking. |
| FR-10 | Explain matches | Each result includes total score, component scores, and human-readable reasons. |
| FR-11 | Contact request | User can initiate a contact request without public exposure of private contact details. If deferred, show a clearly labelled demo state rather than a fake successful request. |
| FR-12 | Persist data | Reports survive a server restart. Migration and seed instructions are documented. |
| FR-13 | Handle errors | UI and API handle 400/401/403/404/409/422/500 responses without crashing or silently swallowing failures. |
| FR-14 | Prevent stale results | Create/edit/resolve operations update indexes and invalidate or refresh related matches. |
| FR-15 | Audit key actions | Where authentication exists, record created, edited, resolved, flagged, and moderated actions with timestamp and actor. |

## 5. Report Lifecycle

Report types:
- `LOST`
- `FOUND`

Report states:
- `ACTIVE`
- `RESOLVED`
- `HIDDEN`

Lifecycle:
1. A new report is created as `ACTIVE`.
2. The report is indexed and eligible for matching.
3. The owner may edit it; relevant indexes must be updated.
4. An authorized user may resolve it.
5. Resolved or hidden reports are removed from active indexes or excluded by index-aware filters.
6. The system must not show resolved/hidden reports as active candidates by default.

## 6. Matching Engine Specification

### 6.1 Candidate generation

1. Load the source report.
2. If it is resolved/hidden, return an empty result or a documented conflict response.
3. Retrieve plausible candidate IDs using category and/or inverted keyword indexes.
4. Only consider reports of the opposite type.
5. Exclude the source report, resolved/hidden reports, duplicates, and candidates outside the configured date window.
6. Deduplicate candidate IDs.
7. Keep a linear-scan fallback for correctness and broad-search scenarios.

### 6.2 Text normalization

- Convert to lowercase.
- Trim and collapse whitespace.
- Normalize punctuation.
- Tokenize descriptions.
- Remove a small documented stop-word list while preserving useful item-specific terms.
- Return keyword score 0 when either token set is empty.

### 6.3 Component scores

All component scores are in the range 0–100.

**Category score C**
- 100 for an exact compatible category.
- 0 for an incompatible category.
- If hierarchical categories are introduced, define partial compatibility explicitly.

**Location score L**
- 100 for the same normalized location.
- 70 for a configured alias/nearby location.
- 0 for unrelated or unknown locations.
- Prefer a managed location alias table to ungrounded fuzzy assumptions.

**Date score D**
- Initial configurable rule: `D = max(0, 100 - 15 × absolute_day_difference)`.
- Same day yields 100; score decays with day gap.
- Configure the date window and decay rather than hard-coding it throughout the code.

**Keyword score K**
- Use Jaccard similarity of unique normalized token sets multiplied by 100.
- `J(A,B) = |A ∩ B| / |A ∪ B|`.
- If either set is empty, return 0.

### 6.4 Total score

Initial weights:

`S = 0.35C + 0.25L + 0.20D + 0.20K`

These are initial heuristics, not scientifically validated probabilities. Keep the weights in one configuration module and tune them using labelled test cases.

### 6.5 Match explanations

Each result should include:
- Total score.
- Category, location, date, and keyword component scores.
- Shared keywords.
- Human-readable reasons such as “Same category”, “Same reported location”, “Dates one day apart”, and “Shared terms: wallet, black”.
- A note: “Potential match—not verified ownership.”

### 6.6 Ranking

For small candidate sets, sort all candidates by score descending: `O(c log c)`.

For top-N-only retrieval, a bounded min-heap of size N can retain the best candidates in `O(c log N)` after scoring. Use deterministic tie-breaking:
1. Total score descending.
2. Date gap ascending.
3. Report ID ascending.

Do not claim that the entire matching process is `O(log n)` just because a heap is used. Candidate generation and scoring also contribute to runtime.

## 7. Data Structures Required

| Structure | Purpose | Expected complexity / note |
|---|---|---|
| Report lookup hash map | Report ID → report record/cache | Expected O(1) lookup; worst-case O(n). |
| Category index | Category → set/list of active report IDs | Efficient category-based candidate generation. |
| Inverted keyword index | Token → set/list of report IDs | Retrieve candidates containing relevant words. |
| Vector/dynamic array | Store candidate IDs and match results | Efficient iteration and append. |
| Priority queue / bounded heap | Keep top-N highest scores | O(log N) per insertion into a bounded heap; top item O(1). |
| Sorting | Produce complete ordered results | O(c log c). |
| String token sets | Compute shared terms/Jaccard score | Expected near-linear token operations with hash sets. |

If the course requires custom implementations, implement the hash table and heap manually and compare against STL versions. Do not claim that SQLite itself is your custom hash map.

## 8. Data Model

### Report
- `id`
- `type` (`LOST` or `FOUND`)
- `item_name`
- `category`
- `description`
- `event_date` (date-only)
- `location_id` or normalized `location_text`
- `status` (`ACTIVE`, `RESOLVED`, `HIDDEN`)
- `created_at`
- `updated_at`
- `owner_id` (nullable only for an explicitly configured local demo)

### MatchResult (optional persisted cache)
- `id`
- `source_report_id`
- `candidate_report_id`
- `total_score`
- `category_score`
- `location_score`
- `date_score`
- `keyword_score`
- `reasons_json`
- `calculated_at`

For MVP, matches may be calculated on request instead of persisted. If cached, invalidate them when source or candidate reports change.

### ContactRequest
- `id`
- `report_id`
- `requester_id`
- `recipient_id`
- `message`
- `status`
- `created_at`

Do not publish private contact details in public report payloads.

### User (if authentication is enabled)
- `id`
- `display_name`
- `email`
- `password_hash` or external `provider_id`
- `role`
- `created_at`

Never store plaintext passwords. Use a trusted authentication library/provider.

### AuditEvent (optional)
- `id`
- `actor_id`
- `entity_type`
- `entity_id`
- `action`
- `timestamp`
- `metadata_json`

Avoid recording unnecessary sensitive content.

## 9. API Contract

Use a consistent response envelope:

Success:
```json
{
  "data": {},
  "error": null,
  "meta": {}
}
```

Error:
```json
{
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Please correct the highlighted fields.",
    "fields": {}
  },
  "meta": {}
}
```

### Endpoints

| Method | Route | Purpose |
|---|---|---|
| GET | `/api/health` | Health check and service version. |
| GET | `/api/reports` | List/search reports; supports `q`, `type`, `category`, `status`, `date_from`, `date_to`, `location`, `page`, `limit`, and `sort`. |
| POST | `/api/reports` | Validate and persist a report; update indexes. |
| GET | `/api/reports/{id}` | Get report details; return 404 if missing; only return safe public fields. |
| PATCH | `/api/reports/{id}` | Update allowed fields; check authorization; update indexes and match results. |
| POST | `/api/reports/{id}/resolve` | Resolve report after authorization; remove it from active matching. |
| GET | `/api/reports/{id}/matches` | Return ranked candidates; supports `limit` (default 5, maximum 20) and `minimum_score`. |
| POST | `/api/contact-requests` | Create a contact request without exposing private contact details. |
| POST | `/api/reports/{id}/flag` | Flag a report for moderation. |

## 10. Frontend Requirements

### Screens
- Dashboard with real report counts and recent reports/matches.
- Reports list with search, filters, sort, pagination, and empty/loading/error states.
- Create/edit form with validation.
- Report detail and ranked match results.
- My Reports with status and resolve action.
- Optional moderation/contact-request views only if implemented in the backend.

### Interaction requirements
- Every page has appropriate loading, success, error, empty, and populated states.
- Forms show inline validation.
- Preserve form inputs after recoverable server errors.
- Disable submit while pending and prevent duplicate submissions.
- Use URL query parameters for shareable filters where appropriate.
- Show “Potential match—not verified ownership” on match views.
- No fake counters, fake notifications, dead buttons, or static mock results in live flows.
- Public payloads must not expose private contact details.
- All primary controls must be keyboard-accessible.

### Visual system

| Token | Value |
|---|---|
| Canvas | `#F6F7F4` |
| Surface | `#FFFFFF` |
| Primary ink | `#263238` |
| Secondary text | `#687579` |
| Muted sage | `#DCE8E1` |
| Primary teal | `#527C76` |
| Warm sand | `#EEE8DE` |
| Border | `#E1E6E2` |

Use a restrained, editorial layout with consistent spacing, typography, subtle borders, accessible focus states, and responsive behaviour. Avoid overused AI-dashboard patterns and gratuitous decoration.

## 11. Security, Privacy, and Reliability

- Validate and sanitize all input on the server.
- Use parameterized ORM/database operations.
- Enforce server-side ownership checks for mutations when auth exists.
- Hash passwords with a trusted algorithm if local password auth is used.
- Keep private contact details out of public list and match payloads.
- Limit description lengths and safely render user-submitted text.
- Add rate limiting and abuse controls before public deployment.
- Store secrets in environment variables; commit only `.env.example` placeholders.
- Use database transactions for report changes and index updates, or rebuild indexes from the database on startup.
- Avoid logging sensitive personal information.
- Provide database backup/export guidance.

## 12. Acceptance Tests

| ID | Scenario | Expected result |
|---|---|---|
| AT-01 | Create valid lost report | Record receives unique ID and persists. |
| AT-02 | Submit missing category | Field-level validation error; no record created. |
| AT-03 | Create opposite-type report with strong overlap | Expected candidate ranks highly with component breakdown. |
| AT-04 | Create same-type report | It is not returned as a match. |
| AT-05 | Resolve report | It disappears from active matching and indexes. |
| AT-06 | Edit category/description | Search index and match results reflect the change. |
| AT-07 | Search with no results | Helpful empty state; no crash. |
| AT-08 | Two candidates tie | Deterministic tie-breaker is applied. |
| AT-09 | Restart backend | Previously saved reports still exist. |
| AT-10 | API unavailable | UI shows actionable error and retry option. |
| AT-11 | Unauthorized update | 401/403 response; no mutation. |
| AT-12 | Mobile viewport | Forms, navigation, cards, and actions remain usable. |

## 13. Testing and Benchmarking

- Unit-test tokenization, Jaccard similarity, date scoring, category compatibility, and score weighting.
- Test same-type exclusion, resolved/hidden exclusion, no candidates, empty descriptions, punctuation/case normalization, date boundaries, ties, edit/index updates, and index removal.
- Add integration tests for report CRUD and persistence.
- Add an end-to-end test for create → match → review → resolve.
- Compare linear-scan candidate generation with indexed retrieval on reproducible seeded datasets.
- Report only measured timings; document hardware, dataset size, repetitions, and methodology.
- Explain time and space complexity and any trade-offs.

## 14. Definition of Done

- All P0 requirements pass acceptance tests.
- Frontend uses the real backend for all core operations.
- Database persists records across restarts.
- Matching results include scores and reasons.
- Indexes stay correct after create, edit, and resolve.
- README includes prerequisites, setup, environment variables, migrations, seed command, run commands, tests, architecture, API examples, limitations, and demo script.
- No dead buttons, fake success states, unlabelled mock data, broken routes, or unhandled console errors remain.
- A truthful implementation checklist lists what is implemented, tested, incomplete, and known to be limited.
