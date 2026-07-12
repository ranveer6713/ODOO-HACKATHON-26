# AssetFlow

**Enterprise Asset & Resource Management System**

AssetFlow is a centralized ERP platform that helps organizations manage departments,
employees, physical assets, shared resources, bookings, maintenance workflows, audits,
notifications, and reports — end-to-end, with role-based access control.

---

## Tech Stack

<<<<<<< HEAD
- Frontend: React + Vite
- Backend: FastAPI
- Database: PostgreSQL / SQLite (dev)
- ORM: SQLAlchemy
- Authentication: JWT
=======
| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15 (App Router) · React 19 · TypeScript · Tailwind CSS · TanStack Query |
| Backend | FastAPI · SQLAlchemy 2 · Pydantic v2 |
| Database | SQLite (single file, `DATABASE_URL`-overridable for Postgres) |
| Auth | Header-forwarded principal (`X-User-Id` / `X-User-Role`), RBAC-gated |
>>>>>>> 7cb671b ( final updates)

---

## Architecture

The backend is composed of **self-contained vertical-slice modules**, each mounted onto
one FastAPI app over one shared database by the foundation (`app/main.py`):

| Module | Prefix | Owns |
|--------|--------|------|
| Booking | `/api/bookings` | Reservation lifecycle + conflict detection |
| Maintenance | `/api/maintenance` | Request → approve → assign → resolve |
| Asset Audit | `/api/asset-audit` | Physical audit cycles & discrepancy reports |
| Notifications | `/api/notifications` | Recipient inbox (shared delivery port) |
| Activity Log | `/api/audit` | Append-only audit trail |
| Dashboard | `/api/dashboard` | Read-only KPI/aggregation projections |
| Reports | `/api/reports` | Tabular reports + CSV/PDF export |

Modules never import each other's ORM models — cross-module asset access goes through an
`AssetGateway` against the string-FK `assets` contract (`id`, `name`, `status`,
`department_id`).

**Frontend / backend split.** Assets, Departments, Employees, Categories, Allocations and
Transfers are referenced by string id in the production contract and are persisted in a
browser local store (seeded, fully functional in the UI). Booking, Maintenance, Asset
Audit, Notifications, Activity Log, Dashboard and Reports are served live by the backend.
The backend seeds its `assets` table (`AST-0001…AST-0016`) to mirror the frontend exactly,
so bookings/maintenance/audits resolve the same asset ids the UI shows.

---

## Getting Started

### Prerequisites
- Python 3.9+
- Node.js 18+

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The API is now at `http://localhost:8000` (interactive docs at `/docs`). Tables are created
and the demo asset estate is seeded automatically on startup.

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env.local     # NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
npm run dev
```

Open `http://localhost:3000`.

### Demo accounts

| Role | Email | Password |
|------|-------|----------|
| Administrator | `admin@assetflow.io` | `admin123` |
| Asset Manager | `manager@assetflow.io` | `manager123` |
| Technician | `tech@assetflow.io` | `tech123` |
| Employee | `employee@assetflow.io` | `employee123` |

> The Dashboard and Activity Log are gated to Asset Manager / Administrator roles.

---

## Core Modules & Workflows

- Authentication and Role-Based Access Control
<<<<<<< HEAD
- Organization Setup (Departments, Categories, Employees)
=======
- Organization Setup (Departments, Employees, Categories)
>>>>>>> 7cb671b ( final updates)
- Asset Registration and Directory
- Asset Allocation, Transfer and Return
- Resource Booking (approve · check-out · check-in · cancel)
- Maintenance Management (approve · assign · start · resolve)
- Asset Audit (create cycle · enroll assets · verify · report · close)
- Dashboard, Reports and Analytics (CSV / PDF export)
- Activity Logs and Notifications

<<<<<<< HEAD
## Backend Setup

```bash
cd backend
pip install -r requirements.txt
python seed.py          # initialise DB and seed demo data
uvicorn app.main:app --reload
```

API docs available at: http://127.0.0.1:8000/docs

## Demo Accounts

| Role           | Email                    | Password     |
|----------------|--------------------------|--------------|
| Admin          | admin@assetflow.com      | admin123     |
| Asset Manager  | manager@assetflow.com    | manager123   |
| Department Head| head@assetflow.com       | head123      |
| Employee       | employee@assetflow.com   | employee123  |
=======
---

## Testing

```bash
# Backend — 191 unit tests
cd backend && python -m pytest -q

# Frontend — type-check and production build
cd frontend && npm run typecheck && npm run build
```

---

## Project Structure

```
backend/
  app/
    database.py        # shared Base / engine / session (foundation)
    core/              # enums.py (Role), security.py (Principal + auth seam)
    seed.py            # seeds the assets contract table
    main.py            # mounts every module onto one app
    booking/ maintenance/ asset_audit/ notifications/ audit/ dashboard/ reports/
  tests/               # per-module + cross-module integration tests
frontend/
  src/
    app/               # Next.js App Router pages
    components/         # UI, layout and shared components
    lib/api/           # client, endpoints, types, local-store
    lib/hooks/          # TanStack Query hooks per module
```
>>>>>>> 7cb671b ( final updates)
