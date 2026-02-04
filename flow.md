# Project Flow (Current State)

This document explains how the Clover Payment Analysis Platform works **right now** (what’s implemented so far), how requests move through the system, and where data is stored.

## 1) What’s in the repo today

### Backend (implemented)
- A **Django REST Framework** API in `backend/`
- Custom user + role model (`ADMIN`, `AGENT`) in `backend/apps/accounts/`
- Statement upload + manual entry APIs in `backend/apps/statements/`
- A lightweight **HTML test UI** for login + dashboard in `backend/test_ui.html` and `backend/dashboard.html`

### Frontend (planned)
- Flutter app is planned (see `workflow.md` and `archietcure.md`), but not present as a Flutter codebase yet.

## 2) Current end-to-end flow

### A) Start the backend (dev default)
1. Run Django from `backend/` (see `README.md` / `backend/backend_README.md`).
2. `backend/manage.py` defaults to `config.settings.development`, which uses **SQLite** in dev.

### B) Register / login (test UI)
1. Open `backend/test_ui.html` in a browser.
2. Register via `POST /api/v1/auth/register/`.
3. Login via `POST /api/v1/auth/login/`.
4. On successful login, the test UI stores:
   - `accessToken` in `localStorage`
   - `currentUser` in `localStorage`
5. The UI redirects to `backend/dashboard.html`.

### C) Use the dashboard
`backend/dashboard.html` reads the `accessToken` from `localStorage` and uses it as:
`Authorization: Bearer <token>`

It supports two statement flows:

#### 1) Upload a PDF/image statement
- UI action: “Upload”
- API call: `POST /api/v1/statements/upload/` (multipart form-data with `file`)
- Backend behavior:
  - Validates type and size (max 10MB, PDF/JPG/PNG)
  - Creates a `MerchantStatement` row with `source='UPLOAD'`, `status='PENDING'`
  - Saves the actual file to Django’s `MEDIA_ROOT` (see “Data Storage” below)
  - Extraction is **not implemented yet** (marked as TODO in code)

#### 2) Manual statement entry
- UI action: “Manual Entry”
- API call: `POST /api/v1/statements/manual/` (JSON)
- Backend behavior:
  - Creates a `MerchantStatement` row with `source='MANUAL'`, `status='COMPLETED'`
  - Creates a `StatementData` row linked 1:1 to that statement

### D) List and view statements (API)
- `GET /api/v1/statements/` returns statements:
  - Admin: all statements
  - Agent: only their own statements
- `GET /api/v1/statements/{id}/` returns statement details (same access rules)

## 3) How data is stored

### A) Database
The source of truth is the Django database.

**In development (current default):**
- SQLite file: `backend/db.sqlite3` (set in `backend/config/settings/development.py`)

**In production/base config (intended):**
- PostgreSQL (configured in `backend/config/settings/base.py`)

**Key tables/models:**
- Users:
  - `accounts_user` (`backend/apps/accounts/models.py`)
  - `accounts_userprofile` (auto-created via signals in `backend/apps/accounts/signals.py`)
- Statements:
  - `statements_merchantstatement` (`backend/apps/statements/models.py`)
  - `statements_statementdata` (`backend/apps/statements/models.py`)

### B) Uploaded files (statements, avatars)
The database stores metadata (filename, size, type) and the filesystem stores the bytes.

**Storage location:**
- `MEDIA_ROOT` is `backend/media/` (from `backend/config/settings/base.py`)
- Statement uploads go under: `backend/media/statements/YYYY/MM/`
  - Example already in repo: `backend/media/statements/2026/02/dummy_statement.pdf`
- User avatars go under: `backend/media/avatars/`

### C) Client-side storage (test UI only)
The HTML test UI uses browser storage:
- `localStorage.accessToken`
- `localStorage.currentUser`

This is only for the dev/test HTML pages (not a final production client).

## 4) Security & access control (current)

### Authentication
- JWT auth via `djangorestframework-simplejwt` (configured in `backend/config/settings/base.py`)
- Backend expects: `Authorization: Bearer <access_token>`

### Roles
- `ADMIN` vs `AGENT` stored on the user model (`backend/apps/accounts/models.py`)
- Statements are filtered by role in `backend/apps/statements/views.py`

### Error format
- API errors are normalized via `backend/utils/exceptions.py` (DRF `EXCEPTION_HANDLER`)

## 5) What we’ve completed so far (as of now)
- Backend project scaffold + settings (dev + production)
- Custom user model + profile creation signals
- Registration/login with JWT token issuance
- Basic admin-only user management endpoints
- Statement upload endpoint (stores file + creates DB record)
- Manual entry endpoint (creates statement + minimal numeric fields)
- Simple HTML test UI + dashboard for exercising the API

## 6) Known gaps / next milestones (not implemented yet)
- PDF/image extraction pipeline (currently only stores uploads, no parsing)
- Pricing models (Cost-plus, iPlus, Discount, Flat) and savings engine
- Merchant/analysis domain model beyond the basic `MerchantStatement`
- Proposal/PDF generation
- Flutter iPad-first app + offline drafts + sync
- Admin-controlled catalogs (devices/fees/pricing rules)

Notes:
- The statements app currently has **no committed migration file** under `backend/apps/statements/migrations/`; you may need to run `python manage.py makemigrations statements` + `python manage.py migrate` when setting up a fresh DB.

