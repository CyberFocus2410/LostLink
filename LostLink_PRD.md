# LostLink — Product Requirements Document (PRD)

**Version:** 1.0  
**Project type:** Data Structures PBL  
**Product:** Smart Lost & Found Matcher  
**Status:** Implementation specification

## 1. Executive Summary

LostLink is a responsive lost-and-found platform for a campus, office, event venue, or small community. Users submit reports for items they have lost or found. The system identifies plausible candidates using category compatibility, location, date proximity, and descriptive keywords, then ranks them using an explainable score.

Each match includes a total score, component scores, and human-readable reasons. A match score is a heuristic ranking aid—not proof of ownership or a guarantee that an item has been recovered.

The project should demonstrate real Data Structures and Algorithms (DSA) concepts through the matching engine, indexes, sorting, and priority-queue-based top-match retrieval.

## 2. Problem Statement

Traditional lost-and-found workflows rely on manual browsing through notices, group chats, spreadsheets, or social posts. Reports can be inconsistent, item descriptions vary, and likely matches may be missed.

LostLink centralizes reports and uses a transparent matching algorithm to reduce manual browsing and help people identify promising candidates.

## 3. Product Vision

Make reporting and recovering lost property easier through a dependable, accessible, and explainable matching workflow.

## 4. Goals

- Let users create and manage lost/found reports with minimal friction.
- Automatically identify and rank plausible matches.
- Explain why each candidate received its score.
- Demonstrate hash-based lookup, indexing, string matching, sorting, and heaps.
- Persist records reliably and validate input on the server.
- Deliver a polished responsive interface that looks deliberately designed rather than generically AI-generated.
- Support a complete end-to-end demo: report → candidate matches → review → resolve.

## 5. Non-Goals for the MVP

- No claim that a match is certain or ownership is verified automatically.
- No computer vision, embeddings, generative AI, or external AI dependency in the core matching engine.
- No payment processing or public exposure of personal contact information.
- No complex real-time chat, public map system, or institution-wide integration.
- No production-grade identity verification in the initial PBL version.

## 6. Target Users and User Stories

### Reporter / owner
- As someone who lost an item, I want to submit details and see likely found reports.
- As a user, I want to understand why a report was suggested as a match.
- As a user, I want to mark my report resolved once the item is returned.

### Finder
- As someone who found an item, I want to register it and discover possible lost reports.
- As a finder, I want to avoid exposing sensitive details publicly.

### Community member
- As a user, I want to search and filter reports by category, date, location, and status.

### Moderator (optional)
- As a moderator, I want to hide spam, review flagged reports, and manage duplicate or unsafe content.

## 7. Scope and Priorities

### P0 — Must ship
- Create lost and found reports.
- Unique report IDs.
- View report list and details.
- Search and filter reports.
- Matching engine with weighted scores.
- Ranked top matches and component explanations.
- Resolve/returned workflow.
- Persistent storage.
- Input validation and clear errors.
- Unit tests for matching and report lifecycle.
- Responsive layouts and loading, empty, error, and success states.

### P1 — Should ship
- Edit reports.
- Contact-request workflow that does not publicly expose private contact details.
- Sort by score/date.
- Duplicate-report warning.
- Basic moderation.

### P2 — Later
- Email or push notifications.
- Photo uploads.
- Campus maps.
- Synonym dictionaries and spelling-tolerant matching.
- Organization accounts and analytics.

## 8. UX and Visual Design Direction

### Design principles
The visual language should feel calm, editorial, trustworthy, and functional. Use a light neutral canvas, warm-white surfaces, muted sage/teal accents, slate text, subtle borders, and restrained shadows.

Avoid the generic AI-dashboard look:
- No excessive gradients or glassmorphism.
- No neon colours or random decorative blobs.
- No oversized empty hero sections.
- No giant rounded cards everywhere.
- No decorative charts that do not represent real data.
- No fake notifications, fake counters, or dead buttons.

### Colour tokens

| Token | Value | Usage |
|---|---|---|
| Canvas | `#F6F7F4` | Main application background |
| Surface | `#FFFFFF` | Forms, tables, item details |
| Primary ink | `#263238` | Main text |
| Secondary text | `#687579` | Helper text and metadata |
| Muted sage | `#DCE8E1` | Soft highlights |
| Primary teal | `#527C76` | Primary action and focus accents |
| Warm sand | `#EEE8DE` | Secondary surfaces |
| Border | `#E1E6E2` | Dividers and controls |
| Success | `#47745C` | Resolved/success states |
| Warning | `#9A7137` | Review/warning states |
| Error | `#A64F4F` | Validation/errors |

### UI rules
- Use a consistent 8-point spacing scale.
- Use restrained radii (approximately 6–12 px).
- Use a readable sans-serif such as Inter or Geist.
- Keep headings, labels, metadata, and actions visually distinct.
- Use accessible contrast and visible keyboard focus.
- Every form field must have a visible label.
- Status must not be communicated by colour alone.
- Design desktop and mobile intentionally.
- Use animation only when it clarifies a transition; respect reduced-motion preferences.

## 9. Information Architecture

1. **Dashboard:** summary counts, report actions, recent reports, and recent potential matches.
2. **Reports:** searchable/filterable list with status, category, date, location, and ID.
3. **Create/Edit Report:** report type, item name, category, description, event date, location, and optional private contact method.
4. **Report Detail:** full report information, lifecycle status, and match results.
5. **Match Results:** ranked candidates, score, component breakdown, reasons, and safe contact/review action.
6. **My Reports:** reports created by the current user and their status.
7. **Moderation/Settings (optional):** review flagged reports, hide spam, and manage categories.

## 10. Product Workflow

1. User submits a LOST or FOUND report.
2. Server validates and persists the report.
3. Relevant category and keyword indexes are updated.
4. Matching engine retrieves plausible reports of the opposite type.
5. Resolved/hidden reports and incompatible candidates are excluded.
6. Candidate scores are calculated and ranked.
7. UI displays the top candidates with explanations.
8. Users review the potential match and use a safe contact workflow.
9. Authorized user marks the report returned/resolved.
10. Resolved reports are excluded from active matching.

## 11. Success Measures

- All P0 user flows work end-to-end.
- Data persists after the server restarts.
- Curated test cases rank expected candidates above deliberately unrelated candidates in expected scenarios.
- Each result shows score, component scores, and explanations.
- Invalid submissions return field-level errors.
- No primary action is dead or fake.
- On a local test dataset of 5,000 reports, ordinary search and match requests should feel responsive; actual performance must be measured and documented.
- A first-time tester can submit a report and inspect its matches without guidance.

## 12. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| False positives | Label results as potential matches and show score breakdowns. |
| False negatives from wording | Normalize text, tokenize, allow manual search, and consider optional edit distance. |
| Privacy exposure | Keep contact details private and use contact requests. |
| Stale index entries | Update index postings when reports are edited/resolved or rebuild indexes from the database. |
| Mock frontend behaviour | Require all core actions to use real API endpoints and persistent data. |
| Scope creep | Complete P0 before adding photos, maps, notifications, or AI. |

## 13. Delivery Phases

1. Data model, API skeleton, migrations, and seed data.
2. Report CRUD, validation, filters, and persistence tests.
3. Matching engine, indexes, score explanations, and unit tests.
4. Responsive frontend and real API integration.
5. End-to-end QA, performance comparison, accessibility review, documentation, and demo rehearsal.

## 14. Definition of Done

- All P0 functional requirements pass acceptance tests.
- Frontend uses the actual backend for core report and matching operations.
- Database persists data across restarts.
- Match results include total score, component scores, and explanations.
- Index maintenance is tested after create, edit, and resolve.
- README includes setup, migrations, seed data, tests, and troubleshooting.
- No broken navigation, dead primary actions, unlabelled mock data, or unhandled errors remain.
- Screenshots and a short PBL demo script are prepared.
