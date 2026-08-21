# AE WPM Demo

A full-stack Migration Portal demo with a separated frontend and backend: Vue 3 + Vite + MDS on the frontend, Django 5 + Django REST Framework on the backend.

---

## Prerequisites (Windows)

This guide targets **Windows** with **Command Prompt (CMD)**. Install the following before you start:

| Tool | Recommended version | Purpose |
|------|---------------------|---------|
| **Python** | 3.10 – 3.13 (verified on 3.13.5) | Run the Django backend |
| **pip** | Bundled with Python | Install Python dependencies |
| **Node.js** | 18.x or 20.x LTS | Run the frontend dev server |
| **npm** | Bundled with Node.js | Install frontend dependencies |

Optional: **Git** — clone and manage the codebase.

> **Note:** The frontend depends on internal Maersk npm packages such as `@maersk-global/mds-components-core`. Make sure your corporate npm registry or `.npmrc` is configured; otherwise `npm install` may fail.

---

## Project structure

```
AE WPM Demo/
├── backend/                    # Django backend
│   ├── api/                    # API app
│   │   ├── views/              # View functions (one module per frontend feature)
│   │   ├── routes/             # URL patterns per feature (included from urls.py)
│   │   ├── urls.py             # Main API router — mounts all feature routes
│   │   └── models.py
│   ├── config/                 # Django settings
│   └── manage.py
├── frontend/                   # Vue 3 frontend
│   ├── src/
│   │   ├── components/         # Shared components (AppHeader, PageShell, etc.)
│   │   ├── views/              # Pages (one .vue per route)
│   │   ├── router/             # Frontend routes (index.js)
│   │   └── data/               # Mock data for demos
│   ├── package.json
│   └── vite.config.js
├── requirements.txt            # Python dependencies
└── README.md
```

---

## Setup (Windows)

All commands below assume **CMD**. If your project path contains spaces, keep the quotes around the path.

### 1. Backend — install dependencies

Open **Command Prompt** and run:

```cmd
REM Go to project root
cd /d "c:\fcous\AE WPM Demo"

REM Create and activate a virtual environment (recommended)
python -m venv .venv
.venv\Scripts\activate.bat

REM Install Python packages
pip install -r requirements.txt
```

| Package | Version range | Description |
|---------|---------------|-------------|
| Django | `>=5.2,<6` | Web framework |
| djangorestframework | `>=3.16,<4` | REST API |
| django-cors-headers | `>=4.0,<5` | CORS support (allows frontend on port 3001) |

### 1b. Backend — the local database

`backend/db.sqlite3` **is** committed to the repository, so a fresh clone
already has the demo data and runs without any setup. After a pull, just
apply any migrations that came with it:

```cmd
cd /d "c:\fcous\AE WPM Demo\backend"
python manage.py migrate
```

To rebuild the database from scratch, delete `db.sqlite3` and reload the
fixture:

```cmd
python manage.py migrate
python manage.py loaddata scripts\api_data_dump.json
```

> Two caveats, because the database is versioned:
>
> - `db.sqlite3` is binary, so two people changing data on the same branch
>   produce a conflict Git cannot merge. Coordinate before committing it.
> - `scripts/api_data_dump.json` is an older snapshot, not a live export — it
>   can lag behind what is in `db.sqlite3`.
>
> Production does not use SQLite at all; the **AE_WPM** service runs against
> MSSQL (see **Port policy**).
>
> On the server (MSSQL), after pulling code that includes new migration files,
> run:
>
> ```cmd
> cd /d "c:\fcous\AE WPM Demo\backend"
> python manage.py migrate --database=default
> ```

### 2. Frontend — install dependencies

In the same or a new CMD window:

```cmd
cd /d "c:\fcous\AE WPM Demo\frontend"
npm install
```

| Package | Description |
|---------|-------------|
| `vue` | Vue 3 framework |
| `vue-router` | Client-side routing |
| `vite` | Build tool and dev server |
| `@maersk-global/mds-components-core` | Maersk Design System components (`mc-button`, `mc-top-bar`, etc.) |
| `axios` | HTTP client for API calls |

> `element-plus` and `handsontable` are legacy dependencies from an earlier import and are not used by the current pages. They can be removed in a future cleanup.

### 3. Start the app (two CMD windows)

**Window 1 — Backend:**

```cmd
cd /d "c:\fcous\AE WPM Demo\backend"
REM Activate venv if not already active
..\.venv\Scripts\activate.bat
python manage.py runserver
```

Backend URL: **http://127.0.0.1:8001**

> **Ports are split between dev and production — do not share 8000.**
> On the deployment server `SCRBAEXDEFRM217`, the Windows service **AE_WPM**
> (Waitress + MSSQL) permanently owns `127.0.0.1:8000`. Windows lets a second
> process bind a port that is already listening *without any error*, so a
> `runserver` on 8000 would silently run alongside the service and requests
> would be split at random between two backends using two different databases.
>
> `manage.py runserver` therefore defaults to **8001** and refuses to start if
> the port is already taken. See **Port policy** below.

### Migration Intake submit email notification (SendGrid)

When a Migration Intake request is submitted, backend now sends an email notification.

Required environment variables for backend process:

- `DJANGO_EMAIL_HOST=smtp.sendgrid.net`
- `DJANGO_EMAIL_PORT=587`
- `DJANGO_EMAIL_HOST_USER=apikey`
- `DJANGO_EMAIL_HOST_PASSWORD=<your_sendgrid_api_key>`
- `DJANGO_EMAIL_USE_TLS=True`
- `DJANGO_DEFAULT_FROM_EMAIL=noreply@maersk.com`
- `DJANGO_MIGRATION_INTAKE_NOTIFY_TO=<comma-separated team emails>`

Notes:

- Email subject includes migration ID, for example: `Migration Request MIR-20260808-001 - New Submission`.
- Email body includes submitted intake details (project, scope, products, countries, location strategy, FTE/job levels, risks, and more).

**Window 2 — Frontend:**

```cmd
cd /d "c:\fcous\AE WPM Demo\frontend"
npm run dev
```

Frontend URL: **http://localhost:3001** — open this in your browser.

> Use **port 3001** as the main entry point. The backend serves APIs only; Vite proxies `/api` to `http://127.0.0.1:8001` by default.
> To develop against the **production** backend instead, override the target rather than starting a second server:
>
> ```powershell
> $env:VITE_API_TARGET = 'http://127.0.0.1:8000'; npm run dev
> ```

### 4. Verify the backend

In CMD:

```cmd
curl http://127.0.0.1:8001/api/health/
```

Expected response (JSON): `{"status":"ok"}`

### 5. Other frontend commands

```cmd
cd /d "c:\fcous\AE WPM Demo\frontend"

REM Production build (output to frontend/dist/)
npm run build

REM Preview the production build locally
npm run preview
```

---

## Port policy

Development and production are deliberately kept on **separate ports** on the
deployment server `SCRBAEXDEFRM217`. Never run both on the same one.

| Port | Owner | Process | Database |
|------|-------|---------|----------|
| `127.0.0.1:8000` | **production** | Windows service **AE_WPM** (NSSM → Waitress), runs as `LocalSystem` | MSSQL `WPM Project` (`DJANGO_DB_ENGINE=mssql`) |
| `127.0.0.1:8001` | **development** | your own `manage.py runserver` | SQLite `backend/db.sqlite3` |
| `0.0.0.0:80` | **production** | Windows service **AE_Front_All** (Apache), serves `frontend/dist` and proxies `/api` → 8000 | — |

### Why this matters

Windows allows a second process to bind an address that is **already being
listened on** — `runserver` starts with no error at all and both processes stay
in `LISTENING`. New connections then go to whichever process bound last, so
requests are split unpredictably between two backends that run different code
against different databases. The symptoms look like "my code changes do
nothing" and "the data keeps coming and going".

Note also that **stopping Apache does not stop the backend**: `AE_Front_All` and
`AE_WPM` are independent services, so `Stop-Service AE_Front_All` leaves the
Waitress process holding 8000.

### What protects you

- `backend/manage.py` defaults `runserver` to `127.0.0.1:8001` and **exits with
  an error** if the target port is already listening.
- `frontend/vite.config.js` proxies `/api` to `127.0.0.1:8001` by default, and
  logs `[vite] /api -> ...` on startup so the target is never a guess.

### Developing against the production backend

Do **not** start a second server on 8000. Repoint the frontend instead:

```powershell
cd E:\AE_WPM_Demo\frontend
$env:VITE_API_TARGET = 'http://127.0.0.1:8000'
npm run dev
```

### Checking the current state

```powershell
Get-Service AE_Front_All, AE_WPM
Get-NetTCPConnection -LocalPort 8000, 8001 -State Listen |
  ForEach-Object { Get-CimInstance Win32_Process -Filter "ProcessId=$($_.OwningProcess)" } |
  Select-Object ProcessId, CommandLine
```

Each port must show **at most one** owner.

Full deployment details: [`E:\Apps\DEPLOYMENT.md`](../Apps/DEPLOYMENT.md).

---

## Application URLs

When running locally with the default dev setup (`npm run dev` + `python manage.py runserver`), use these addresses:

| Service | Base URL | Notes |
|---------|----------|-------|
| **Frontend (main entry)** | http://localhost:3001 | Open this in your browser |
| **Backend API (dev)** | http://127.0.0.1:8001 | API only — not the UI; `runserver` + SQLite |
| **Backend API (production service)** | http://127.0.0.1:8000 | Windows service **AE_WPM**, Waitress + MSSQL — never bind this port yourself |

The global `mc-top-bar` header links to the main pages. All frontend routes below are relative to `http://localhost:3001`.

### Frontend pages

| Page | URL | Description |
|------|-----|-------------|
| **Welcome** | http://localhost:3001/ | Landing page with tool cards and entry to the Project Attributes Database |
| **Future Service Model** | http://localhost:3001/future-service-model | Cost, capability, and country-level analytics for GSC transition planning — includes expandable process and country task tables |
| **Migration Intake** | http://localhost:3001/migration-intake | Submit a new migration request and capture intake details |
| **Migration Dashboard** | http://localhost:3001/migration-dashboard | Product-level migration summary and tracking overview |
| **L&D Dashboard** | http://localhost:3001/ld-dashboard | Learning, scoping tasks, and training timeline by project |
| **Project Dashboard** | http://localhost:3001/project-dashboard | Individual project opportunity assessment and milestone hub |
| **Milestone detail** | http://localhost:3001/project-dashboard/:section | Drill-down for a specific milestone (e.g. `gantt`, `approvals`, `business-case`, `cost`, `training`) |
| **Migration Chatbot** | http://localhost:3001/migration-chatbot | Guided Q&A and migration support chatbot demo |

### Redirects

| From | To |
|------|-----|
| http://localhost:3001/welcome | http://localhost:3001/ |
| http://localhost:3001/welcome2 | http://localhost:3001/future-service-model |

### Backend API

| Method | URL | View module | Status |
|--------|-----|-------------|--------|
| GET | http://127.0.0.1:8001/api/health/ | `api/views/health.py` → `health()` | **Live** |

> In development, the frontend proxies `/api/*` to the backend (see `frontend/vite.config.js`). You can also call endpoints directly on port 8001.

Most page content is still driven by mock data under `frontend/src/data/`. Feature API routes are scaffolded but not yet implemented — see **Backend architecture** below.

---

## Backend architecture

The API is split by **frontend feature area**. Each page has a matching pair of files under `backend/api/`:

| Frontend page | Frontend route | View module | Route module | API prefix |
|---------------|----------------|-------------|--------------|------------|
| Welcome | `/` | — | — | (no API yet) |
| Future Service Model | `/future-service-model` | `views/future_service_model.py` | `routes/future_service_model.py` | `/api/future-service-model/` |
| Migration Intake | `/migration-intake` | `views/migration_intake.py` | `routes/migration_intake.py` | `/api/migration-intake/` |
| Migration Dashboard | `/migration-dashboard` | `views/migration_dashboard.py` | `routes/migration_dashboard.py` | `/api/migration-dashboard/` |
| L&D Dashboard | `/ld-dashboard` | `views/ld_dashboard.py` | `routes/ld_dashboard.py` | `/api/ld-dashboard/` |
| Project Dashboard | `/project-dashboard` | `views/project_dashboard.py` | `routes/project_dashboard.py` | `/api/project-dashboard/` |
| Migration Chatbot | `/migration-chatbot` | `views/migration_chatbot.py` | `routes/migration_chatbot.py` | `/api/migration-chatbot/` |
| System | — | `views/health.py` | `routes/health.py` | `/api/health/` |

### How routing is wired

```
config/urls.py          →  path("api/", include("api.urls"))
api/urls.py             →  path("health/", include("api.routes.health")), …
api/routes/health.py    →  path("", health)           →  GET /api/health/
api/views/health.py     →  def health(request): …
```

### How to add a new endpoint

1. **Write the view** in the matching `backend/api/views/<feature>.py` file.
2. **Register the URL** in `backend/api/routes/<feature>.py` (uncomment or add a `path(...)`).
3. **Call it from the frontend** in the matching `frontend/src/views/<Page>.vue` (via `axios` to `/api/...`).
4. Optionally add models in `backend/api/models.py` and serializers later.

Example — add `GET /api/migration-dashboard/summary/`:

```python
# backend/api/views/migration_dashboard.py
@api_view(["GET"])
def migration_summary(request):
    return Response({...})
```

```python
# backend/api/routes/migration_dashboard.py
from api.views.migration_dashboard import migration_summary

urlpatterns = [
    path("summary/", migration_summary, name="migration-dashboard-summary"),
]
```

### Where to look (quick reference)

| What you need | File |
|---------------|------|
| Frontend URL → page component | `frontend/src/router/index.js` |
| Page UI | `frontend/src/views/*.vue` |
| Mock / static data (current) | `frontend/src/data/mockData.js`, `serviceModelData.js` |
| All API mounts | `backend/api/urls.py` |
| Per-feature URL patterns | `backend/api/routes/*.py` |
| Per-feature view functions | `backend/api/views/*.py` |
| Django project entry | `backend/config/urls.py` |

---

## Troubleshooting (Windows)

### 1. `cd` does not change drive or folder

Use `cd /d` to switch drives and directories in CMD:

```cmd
cd /d "c:\fcous\AE WPM Demo\frontend"
```

### 2. Path contains spaces

Wrap the path in quotes:

```cmd
cd /d "c:\fcous\AE WPM Demo\frontend"
```

### 3. 404 or Django page when visiting the backend port

Open the app at **http://localhost:3001**, not the backend port. The backend is API-only.

### 4. `runserver` refuses to start: "already being listened on"

This is the guard in `backend/manage.py` doing its job — something already owns
that port, and Windows would otherwise let `runserver` bind it silently. Find
the owner:

```powershell
Get-NetTCPConnection -LocalPort 8001 -State Listen |
  ForEach-Object { Get-CimInstance Win32_Process -Filter "ProcessId=$($_.OwningProcess)" } |
  Select-Object ProcessId, CommandLine
```

Usually it is a `runserver` you forgot to close. Stop it, or start this one on
another free port: `python manage.py runserver 8002`.

If the owner is the **AE_WPM** service on 8000, do not stop it and do not bind
8000 — point the frontend at it with `VITE_API_TARGET` instead (see **Port
policy**).

- Frontend on a different port: `npm run dev -- --port 3002` (also update `CORS_ALLOWED_ORIGINS` in `backend/config/settings.py`)

### 5. `npm install` fails (MDS packages not found)

Confirm you are logged into the corporate npm registry, or contact your team for `@maersk-global/*` package access.

### 6. Python dependency install fails

Check your Python version and recreate the virtual environment:

```cmd
python --version
cd /d "c:\fcous\AE WPM Demo"
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
```

---

## Tech stack summary

| Layer | Stack |
|-------|-------|
| Frontend | Vue 3, Vite 5, Vue Router, MDS Components |
| Backend | Django 5.2, Django REST Framework, SQLite |
| Dev ports | Frontend `3001`, Backend `8001` (production service owns `8000`) |
