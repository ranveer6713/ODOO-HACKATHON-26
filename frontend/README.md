# AssetFlow — Frontend

Production-grade frontend for the **Enterprise Asset & Resource Management System**, built for the Odoo Hackathon.

## Tech Stack

- **Next.js 15** (App Router) + **TypeScript**
- **Tailwind CSS** + hand-authored **shadcn/ui**-style component library (Radix primitives)
- **TanStack Query** — server state, caching, optimistic invalidation
- **React Hook Form** + **Zod** — typed, validated forms
- **Recharts** — dashboards & analytics
- **next-themes** — full light/dark mode
- **Framer Motion**, **Lucide**, **Sonner** (toasts)

## Getting Started

```bash
cd frontend
npm install
cp .env.example .env.local      # point NEXT_PUBLIC_API_BASE_URL at the backend
npm run dev                     # http://localhost:3000
```

The FastAPI backend is expected at `http://localhost:8000` (configurable via
`NEXT_PUBLIC_API_BASE_URL`). CORS on the backend already allows `:3000`.

### Demo accounts

Authentication is a client-side session gate (the backend auth seam is a
permissive stub). Sign in with any of the seeded roles — one click autofills:

| Role | Email | Password |
|------|-------|----------|
| Administrator | admin@assetflow.io | admin123 |
| Asset Manager | manager@assetflow.io | manager123 |
| Technician | tech@assetflow.io | tech123 |
| Employee | employee@assetflow.io | employee123 |

## Architecture

```
src/
  app/
    (app)/            # authenticated shell: sidebar + topbar + breadcrumbs
      dashboard, departments, employees, categories, assets, assets/[id],
      allocation, transfers, booking, maintenance, audit, audit/[id],
      notifications, activity, reports, settings, profile
    login/            # split-screen auth
  components/
    ui/               # primitives (button, card, dialog, sheet, select, …)
    shared/           # DataTable, StatCard, StatusBadge, charts, states, …
    layout/           # sidebar, topbar, search (⌘K), notifications, user menu
    assets/, booking/, maintenance/   # feature components
  lib/
    api/              # typed client, endpoints, DTO types, local store
    hooks/            # one TanStack Query hook module per domain
    auth/             # client session
    constants.ts      # status → label/tone maps, chart palette
    nav.ts            # navigation model
```

### Data layer

- **Live backend modules** (typed & wired): Dashboard, Bookings, Maintenance,
  Asset Audit, Notifications, Activity Logs, Reports — all through a single
  `api` client with a shared `{ items, meta }` pagination envelope, centralized
  error handling, and identity headers.
- **Reference entities** (Assets, Departments, Employees, Categories,
  Allocations, Transfers) have no backend in the integration contract (they are
  external string-FK references). They are served by a **browser-persisted store**
  with a realistic seed, exposing the same async, paginated API so every screen
  is fully interactive end-to-end. Reset from **Settings → Local Data**.

### Every state, handled

Loading skeletons, empty states, error states with retry, success toasts,
optimistic cache invalidation, form validation, conflict detection (booking),
and workflow timelines are implemented across the app.

## Scripts

```bash
npm run dev         # dev server
npm run build       # production build
npm run start       # serve production build
npm run typecheck   # tsc --noEmit
```
