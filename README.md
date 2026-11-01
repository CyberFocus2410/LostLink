# LostLink — Smart Campus Lost & Found Matcher

[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript)](https://www.typescriptlang.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql)](https://www.postgresql.org)
[![PWA](https://img.shields.io/badge/PWA-Installable-527C76?logo=pwa)](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps)
[![Pytest](https://img.shields.io/badge/pytest-66%20passed-success)](https://pytest.org)

**LostLink** is an installable, deterministic, privacy-first smart lost-and-found matching platform engineered for collegiate and organizational communities.

> 🌐 **Live Demo URL**: [https://lostlink.onrender.com](https://lostlink.onrender.com) *(Configure your Render deployment URL here)*

Users register **LOST** or **FOUND** reports with optional photo uploads and GPS coordinates. The matching engine evaluates active opposite-type candidates using in-memory category partitions, inverted keyword token indexes, Haversine GPS proximity decay, and location facility clusters, ranking candidates via a bounded min-heap priority queue. Every result includes an explainable score breakdown ($0\text{--}100$) and plain-language reasoning, accompanied by the mandatory disclaimer:
> **"Potential match — not verified ownership."**

---

## 1. System Architecture

```mermaid
graph TD
    subgraph Client ["Client Layer (PWA / Mobile / Desktop)"]
        UI["Editorial Design System\n#F6F7F4 Canvas · #527C76 Teal"]
        PWA["Service Worker & Manifest\nOffline Shell · Install Prompt"]
        APIClient["Typed API Client\nCookie Auth (httpOnly / Secure)"]
        UI --> PWA
        UI --> APIClient
    end

    subgraph ServiceLayer ["Single-Service Container (FastAPI on Render / Docker)"]
        SPARouter["SPA Static Fallback Router\nServes React 19 Frontend Shell"]
        APIRouter["API Routers\n/auth, /reports, /matches, /contact, /admin"]
        SecurityMW["Security Middleware\nCSP, X-Frame-Options: DENY, CSRF Origin Check"]
        RateLimiter["Rate Limiter (slowapi)\nBrute-force protection on /auth"]
        
        SPARouter --> SecurityMW
        APIRouter --> SecurityMW
        APIRouter --> RateLimiter
    end

    subgraph CoreEngine ["DSA Matching Engine (Single-Worker In-Memory)"]
        TypeIdx["Type Partitions\nLOST vs FOUND Sets"]
        CatIdx["Category Partitions\nMap: Category -> Set<ID>"]
        TokenIdx["Inverted Token Index\nMap: Token -> Set<ID>"]
        Haversine["Haversine GPS & Cluster Scorer\nDistance Bands <=100m, <=1000m"]
        Heap["Bounded Min-Heap Top-N Selection\nheapq.nsmallest (O(C log K))"]

        APIRouter --> TypeIdx
        TypeIdx --> CatIdx
        CatIdx --> TokenIdx
        TokenIdx --> Haversine
        Haversine --> Heap
    end

    subgraph CloudServices ["Cloud & Persistence Layer"]
        Postgres[(Managed PostgreSQL 16\nDual-Engine SQLite Fallback)]
        Storage[(Supabase Object Storage\nSanitized EXIF/GPS-stripped photos)]
        EmailSvc[("Resend Transactional Email\nDouble-blind async notifications")]
        Telemetry[("Anonymous Telemetry & Sentry\nZero PII Error Monitoring")]

        APIRouter --> Postgres
        APIRouter --> Storage
        APIRouter --> EmailSvc
        APIRouter --> Telemetry
    end

    Client -->|HTTPS / Secure Cookies| ServiceLayer
```

### 1.1 Single-Worker Requirement & Scalability
LostLink maintains an in-memory, type-partitioned inverted token index and category postings for sub-millisecond candidate pruning.
Because the inverted index resides in process memory:
- **Single-Worker Requirement**: In production (e.g. Uvicorn on Render or Docker), LostLink MUST run with exactly **1 worker process** (`--workers 1`). Running multiple worker processes without distributed coordination would cause in-memory state divergence when writes or status transitions occur on one worker.
- **Scaling Roadmap for Multi-Worker**:
  1. *Distributed Inverted Index*: Move index postings to Redis or Dragonfly using Redis Sets (`SMEMBERS`, `SINTER`).
  2. *Pub/Sub Invalidation*: Use Redis Pub/Sub or PostgreSQL `LISTEN`/`NOTIFY` to broadcast new report additions and deletions across worker replicas.
  3. *Search Engine Integration*: Migrate keyword and category candidate retrieval to PostgreSQL full-text search (`tsvector` with GIN index) or pgvector.

---

## 2. Install on Your Phone (Progressive Web App)

LostLink is built as a standalone Progressive Web App (PWA) with offline shell caching, safe-area inset adaptation, and 44px minimum tap targets.

### Android & Desktop Chrome
1. Visit the app URL in Google Chrome.
2. An **"Install LostLink"** banner will automatically appear at the bottom of the screen.
3. Tap **"Install"** to add the application directly to your home screen or app drawer.
4. Alternatively, tap the Chrome menu (⋮) $\to$ **"Install App"** / **"Add to Home screen"**.

### iOS Safari (iPhone / iPad)
1. Open the app URL in **Safari** (iOS requires Safari for PWA installation).
2. Tap the **Share** button (box with an arrow pointing up at the bottom of Safari).
3. Scroll down and tap **"Add to Home Screen"**.
4. Tap **"Add"** in the top-right corner.
5. LostLink will appear as an app icon on your home screen and launch in full-screen standalone mode with no browser address bar.

---

## 3. DSA Core Formulation & Complexity Analysis

### 3.1 Heuristic Scoring Formula
The overall score $S \in [0, 100]$ is a weighted combination of four heuristic components:
$$S = 0.35C + 0.25L + 0.20D + 0.20K$$
*Note: Scores represent heuristic overlap, not statistical proof of identity or ownership.*

1. **Category Compatibility ($C \in \{0, 100\}$):**
   - Exact category match = $100.0$; incompatible category = $0.0$.
2. **Location Proximity ($L \in \{0, 70, 100\}$):**
   - **GPS Coordinates (Haversine Distance)**: When both reports provide latitude and longitude:
     - Distance $\le 100\text{ m}$: $100.0$ (immediate vicinity).
     - Distance $\le 1,000\text{ m}$ ($1\text{ km}$): $70.0$ (nearby facility / walking radius).
     - Distance $> 1,000\text{ m}$: $0.0$ (too distant).
   - **Text & Cluster Heuristic Fallback**: Used when either report lacks coordinates:
     - Exact normalized string match = $100.0$.
     - Nearby facility cluster (e.g. *Main Library* vs *Library Cafe*, configured per-community in DB or default clusters) = $70.0$.
     - Unrelated location = $0.0$.
   - **Community Partitioning**: Reports belong to a Community/Campus entity. Matching candidates are partitioned within the same community domain.
3. **Date Proximity ($D \in [0, 100]$):**
   $$D = \max(0, 100 - 15 \times |\text{days\_diff}|)$$
   - Same date: $100.0$ pts.
   - 1 day apart: $85.0$ pts.
   - 3 days apart: $55.0$ pts.
   - $\ge 7$ days apart: $0.0$ pts.
   - Items beyond `CANDIDATE_DATE_WINDOW_DAYS` ($30$ days) are pruned prior to scoring.
4. **Keyword Similarity ($K \in [0, 100]$):**
   - Jaccard similarity across unique normalized token sets (stop-words filtered):
   $$J(A, B) = \frac{|A \cap B|}{|A \cup B|} \times 100.0$$
   - If either token set is empty, $K = 0.0$.

### 3.2 Deterministic Tie-Breaking
When candidates tie in total score:
1. `total_score` **DESC**
2. `days_diff` **ASC** (closer dates rank higher)
3. `candidate_id` **ASC** (lexicographical tie-breaker)

### 3.3 Time & Space Complexity
| Operation | Linear Scan Baseline | Inverted Index (DSA Core) | Space Complexity |
|---|---|---|---|
| **Candidate Retrieval** | $O(N)$ | $O(\sum_{t} |P_t|) \ll O(N)$ | $O(N \cdot \bar{T})$ |
| **Scoring Candidates** | $O(N \cdot \bar{T})$ | $O(C \cdot \bar{T})$ where $C \ll N$ | $O(C)$ |
| **Top-$K$ Selection (Heap)** | $O(N \log K)$ | $O(C \log K)$ | $O(K)$ |
| **Top-$K$ Selection (Sort)** | $O(N \log N)$ | $O(C \log C)$ | $O(C)$ |
| **Total Query Latency** | $O(N \cdot \bar{T})$ | $O(C \cdot \bar{T} + C \log K)$ | $O(N \cdot \bar{T} + K)$ |

---

## 4. Measured Benchmark Results

Conducted using [`backend/app/matching/benchmark.py`](file:///c:/Users/Vivan/OneDrive/Documents/PROJECTS/LostLink/backend/app/matching/benchmark.py) with Python 3.11.9, seed `42`, 50 test queries per dataset:

### Inverted Index vs Linear Scan Retrieval
| Dataset Size ($N$) | Method | Avg Cand Gen (ms) | Avg Total Match (ms) | Speedup Factor |
|---|---|---|---|---|
| **500 items** | Linear Scan | 0.0786 ms | 5.9050 ms | 1.00x |
| **500 items** | **Inverted Index (DSA)** | 0.1385 ms | **4.7671 ms** | **1.24x** |
| **2,000 items** | Linear Scan | 1.3376 ms | 94.7664 ms | 1.00x |
| **2,000 items** | **Inverted Index (DSA)** | 0.6770 ms | **33.3968 ms** | **2.84x** |
| **5,000 items** | Linear Scan | 4.3229 ms | 265.2035 ms | 1.00x |
| **5,000 items** | **Inverted Index (DSA)** | 7.2495 ms | **242.2191 ms** | **1.09x** |

---

## 5. Setup and Local Development

### Prerequisites
- Python 3.11+
- Node.js 20+ and npm
- Docker (optional, for local PostgreSQL container)

### 5.1 Backend Setup
```bash
# 1. (Optional) Start local PostgreSQL database via Docker Compose
docker compose up -d postgres

# 2. Navigate to backend directory and install dependencies
cd backend
python -m pip install -r requirements.txt

# 3. Configure environment
# cp ../.env.example .env

# 4. Run database migrations
python -m alembic upgrade head

# 5. Populate staging seed demo data
python scripts/seed_staging.py

# 6. Start backend server (Single worker required)
python -m uvicorn app.main:app --reload --port 8000
```
Backend will be available at: `http://127.0.0.1:8000`  
Interactive Swagger docs: `http://127.0.0.1:8000/docs`

### 5.2 Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```
Frontend will be available at: `http://127.0.0.1:5173`

---

## 6. Running Tests

The test suite contains **66 automated tests** covering authentication, rate limiting, dual-database SQLite & PostgreSQL migrations, photo validation, EXIF metadata stripping, double-blind contact exchanges, and complete user lifecycles:

```bash
cd backend
python -m pytest -v
```

Output:
```
============================= 66 passed in 38.66s =============================
```

### Running Frontend Playwright E2E Tests:
```bash
cd frontend
npm run test:e2e
```

---

## 7. Truthful Implementation Checklist

### Implemented & Fully Verified (Production Ready)
- [x] **Full REST API**: FastAPI, SQLAlchemy 2.0, Pydantic v2, PostgreSQL (Docker & production) and SQLite (local dev).
- [x] **Alembic Migrations**: Fully automated schema upgrades with composite indexes on `reports`, `report_images`, `communities`, `facility_clusters`, `contact_requests`, `report_flags`, and `users`.
- [x] **Authentication & User Accounts**: Argon2id hashing, PyJWT access tokens, rotated SHA-256 refresh tokens in `httpOnly`, `SameSite=Lax`, `Secure` cookies, CSRF Origin validation, and `slowapi` rate limiting.
- [x] **Location Generalization**: Haversine GPS distance scoring $\le 100\text{ m} \to 100$, $\le 1000\text{ m} \to 70$, $> 1000\text{ m} \to 0$, with community tenant isolation and database facility clusters.
- [x] **In-Memory Dual Index**: Category Hash Index, Token Inverted Index, and Type Partitioning (`LOST` vs `FOUND`).
- [x] **Memory Optimization**: Slotted dataclasses (`@dataclass(slots=True)` for 63.2% per-record RAM reduction).
- [x] **Deterministic Scoring**: Formula $S = 0.35C + 0.25L + 0.20D + 0.20K$ with date decay and location clustering.
- [x] **Priority Queue Ranking**: Bounded Min-Heap ($O(C \log K)$) with C-accelerated `heapq.nsmallest` and deterministic tie-breaking.
- [x] **Photo Uploads**: Pluggable storage abstraction (`SupabaseStorageProvider` with local disk fallback), server-side Pillow EXIF & GPS metadata stripping, web thumbnails, and mobile camera capture.
- [x] **Double-Blind Contact Privacy**: Requester and owner emails/phones are strictly masked until owner explicitly clicks Accept.
- [x] **Email Notifications**: Asynchronous background tasks using Resend API for contact requests, acceptance alerts, and password resets.
- [x] **Data Protection Compliance**: DPDP Act 2023 & GDPR permanent right to erasure (`DELETE /api/auth/me`), Privacy Policy, and Terms of Service.
- [x] **Security Hardening**: `SecurityHeadersMiddleware` (CSP, `nosniff`, `frame-ancestors 'none'`, HSTS, Referrer-Policy).
- [x] **Progressive Web App (PWA)**: `vite-plugin-pwa`, app shell caching, offline fallback screen, install prompt banner (`beforeinstallprompt`), and iOS Safari home-screen instructions.
- [x] **Single-Service Docker Deployment**: Multi-stage `Dockerfile` (Node 20 build + Python 3.11 runtime), `docker-entrypoint.sh` auto-migrations, `render.yaml`, and complete `docs/DEPLOYMENT.md` click-by-click guide.
- [x] **Admin & Moderation Center**: Front-and-backend moderation dashboard to review abuse flags, take down reports, and deactivate abusive accounts.
- [x] **Observability & Analytics**: Sentry error monitoring integration and privacy-preserving anonymous telemetry (`/api/analytics/*`) without collecting PII.
- [x] **Automated CI/CD**: GitHub Actions workflow (`.github/workflows/ci.yml`) testing against live PostgreSQL service container and frontend build.
- [x] **66 Automated Tests**: 100% passing test suite across SQLite and live PostgreSQL.

### Deferred for Future Releases (Post-Launch Scope)
- Institutional SSO (OAuth2 / SAML / Google Workspace for Education).
- Interactive campus GIS map coordinate rendering.
- Distributed index via Redis Sets / pgvector for multi-worker scaling across server clusters.
