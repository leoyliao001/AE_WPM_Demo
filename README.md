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

Backend URL: **http://127.0.0.1:8000**

**Window 2 — Frontend:**

```cmd
cd /d "c:\fcous\AE WPM Demo\frontend"
npm run dev
```

Frontend URL: **http://localhost:3001** — open this in your browser.

> Use **port 3001** as the main entry point. The backend on port 8000 serves APIs only; Vite proxies `/api` to `http://localhost:8000`.

### 4. Verify the backend

In CMD:

```cmd
curl http://127.0.0.1:8000/api/health/
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

## Application URLs

When running locally with the default dev setup (`npm run dev` + `python manage.py runserver`), use these addresses:

| Service | Base URL | Notes |
|---------|----------|-------|
| **Frontend (main entry)** | http://localhost:3001 | Open this in your browser |
| **Backend API** | http://127.0.0.1:8000 | API only — not the UI |

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
| GET | http://127.0.0.1:8000/api/health/ | `api/views/health.py` → `health()` | **Live** |

> In development, the frontend proxies `/api/*` to the backend (see `frontend/vite.config.js`). You can also call endpoints directly on port 8000.

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

### 3. 404 or Django page when visiting port 8000

Open the app at **http://localhost:3001**, not port 8000. Port 8000 is API-only.

### 4. Port already in use

- Backend on a different port: `python manage.py runserver 8001` (also update the proxy `target` in `frontend/vite.config.js`)
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
| Dev ports | Frontend `3001`, Backend `8000` |
