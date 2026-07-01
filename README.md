# AE WPM Demo

A full-stack Migration Portal demo with a separated frontend and backend: Vue 3 + Vite + MDS on the frontend, Django 5 + Django REST Framework on the backend.

---

## Prerequisites

Before starting the project, make sure the following tools are installed:

| Tool | Recommended version | Purpose |
|------|-------------------|---------|
| **Python** | 3.10 – 3.13 (verified on 3.13.5) | Run the Django backend |
| **pip** | Bundled with Python | Install Python dependencies |
| **Node.js** | 18.x or 20.x LTS | Run the frontend dev server |
| **npm** | Bundled with Node.js | Install frontend dependencies |

Optional:

- **Git** — clone and manage the codebase
- **Virtual environment** (`venv` / Conda) — isolate Python dependencies (recommended)

> **Note:** The frontend depends on internal Maersk npm packages such as `@maersk-global/mds-components-core`. Make sure your corporate npm registry or `.npmrc` is configured; otherwise `npm install` may fail.

---

## Project structure

```
AE WPM Demo/
├── backend/              # Django backend
│   ├── api/              # API app
│   ├── config/           # Django settings
│   └── manage.py
├── frontend/             # Vue 3 frontend
│   ├── src/
│   │   ├── components/   # Shared components (AppHeader, PageShell, etc.)
│   │   ├── views/        # Pages
│   │   ├── router/       # Routes
│   │   └── data/         # Mock data for demos
│   ├── package.json
│   └── vite.config.js
├── requirements.txt      # Python dependencies
└── README.md
```

---

## Backend — install and run

### 1. Install Python dependencies

From the project root:

```bash
# Enter the project root (keep quotes if the path contains spaces)
cd "c:\fcous\AE WPM Demo"

# Recommended: create and activate a virtual environment (optional)
python -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Windows CMD:
# .venv\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt
```

**`requirements.txt` includes:**

| Package | Version range | Description |
|---------|---------------|-------------|
| Django | `>=5.2,<6` | Web framework |
| djangorestframework | `>=3.16,<4` | REST API |
| django-cors-headers | `>=4.0,<5` | CORS support (allows frontend on port 3001) |

### 2. Start the backend

```bash
cd backend
python manage.py runserver
```

Default URL: **http://127.0.0.1:8000**

### 3. Verify the backend

Open the health check endpoint in a browser or via the command line:

```bash
curl http://127.0.0.1:8000/api/health/
```

Expected response (JSON), e.g. `{"status": "ok"}`

---

## Frontend — install and run

### 1. Install Node dependencies

```bash
cd "c:\fcous\AE WPM Demo\frontend"
npm install
```

**Main `package.json` dependencies:**

| Package | Description |
|---------|-------------|
| `vue` | Vue 3 framework |
| `vue-router` | Client-side routing |
| `vite` | Build tool and dev server |
| `@maersk-global/mds-components-core` | Maersk Design System components (`mc-button`, `mc-top-bar`, etc.) |
| `axios` | HTTP client for API calls |

> `element-plus` and `handsontable` are legacy dependencies from an earlier import and are not used by the current pages. They can be removed in a future cleanup.

### 2. Start the frontend dev server

```bash
npm run dev
```

Default URL: **http://localhost:3001**

### 3. Other frontend commands

```bash
# Production build (output to frontend/dist/)
npm run build

# Preview the production build locally
npm run preview
```

---

## Full startup flow (development)

Use **two terminals** — one for the backend, one for the frontend:

**Terminal 1 — Backend:**

```bash
cd "c:\fcous\AE WPM Demo\backend"
python manage.py runserver
```

**Terminal 2 — Frontend:**

```bash
cd "c:\fcous\AE WPM Demo\frontend"
npm run dev
```

Then open **http://localhost:3001** in your browser.

> For day-to-day development, use **port 3001** as the main entry point. The backend on port 8000 serves APIs only; Vite proxies `/api` to `http://localhost:8000`.

---

## Pages and routes

| Page | Route |
|------|-------|
| Welcome | `/` |
| Migration Intake Form | `/migration-intake` |
| Migration Dashboard | `/migration-dashboard` |
| L&D Dashboard | `/ld-dashboard` |
| Individual Project Dashboard | `/project-dashboard` |
| Milestone detail | `/project-dashboard/:section` |
| Migration Chatbot | `/migration-chatbot` |

The global `mc-top-bar` header provides navigation across all pages.

---

## API reference

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health/` | Health check |

Most page data currently comes from `frontend/src/data/mockData.js`. Business APIs are not fully wired up yet.

---

## Troubleshooting

### 1. PowerShell errors with paths that contain spaces

Wrap the path in quotes:

```powershell
cd "c:\fcous\AE WPM Demo\frontend"
```

### 2. 404 or Django page when visiting port 8000

Open the app at **http://localhost:3001**, not port 8000. Port 8000 is API-only.

### 3. Port already in use

- Backend on a different port: `python manage.py runserver 8001` (also update the proxy `target` in `frontend/vite.config.js`)
- Frontend on a different port: `npm run dev -- --port 3002` (also update `CORS_ALLOWED_ORIGINS` in `backend/config/settings.py`)

### 4. `npm install` fails (MDS packages not found)

Confirm you are logged into the corporate npm registry, or contact your team for `@maersk-global/*` package access.

### 5. Python dependency install fails

Verify Python ≥ 3.10 and use a virtual environment to avoid conflicts with system packages:

```bash
python --version
python -m venv .venv
```

---

## Tech stack summary

| Layer | Stack |
|-------|-------|
| Frontend | Vue 3, Vite 5, Vue Router, MDS Components |
| Backend | Django 5.2, Django REST Framework, SQLite |
| Dev ports | Frontend `3001`, Backend `8000` |
