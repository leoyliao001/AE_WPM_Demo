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
| django-cors-headers | `>=4.0,<5` | CORS support (allows frontend on port 3002) |

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

Because the frontend uses private packages from GitHub Packages (Maersk scope),
you must authenticate npm before running `npm install`.

#### 2a. GitHub Packages login for `@maersk-global`

What you need:

- A GitHub account that can access Maersk packages.
- A GitHub Personal Access Token (PAT) with at least `read:packages`.
- If your org requires it, include `repo` scope as well.

Recommended one-time setup in PowerShell:

```powershell
# If your network needs a corporate proxy, set these first.
npm config set proxy http://10.0.11.1:9400
npm config set https-proxy http://10.0.11.1:9400

# Route Maersk package scopes to GitHub Packages.
npm config set @maersk-global:registry https://npm.pkg.github.com
npm config set @Maersk-Global:registry https://npm.pkg.github.com

# Login (interactive)
npm login --registry=https://npm.pkg.github.com --scope=@maersk-global --auth-type=legacy
```

During `npm login`, enter:

- Username: your GitHub username
- Password: your GitHub PAT
- Email: your GitHub email

Quick verification:

```powershell
npm ping
npm whoami --registry=https://npm.pkg.github.com
```

If `npm install` fails with `401 Unauthorized`, run `npm login` again.
If it fails with `ETIMEDOUT`, check proxy settings and retry.

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

Frontend URL: **http://localhost:3002** — open this in your browser.

### Project Charter (draft workflow)

- Toll Gates > Initiate > Project Charter opens `/migration-dashboard/:id/project-charter`.
- The charter reads Intake, locked Stakeholder Registration people, Scope Statement,
  saved Gantt dates/task completion and Business Case approval state live. Missing
  structured benefits, risks, scope waves, out-of-scope and assumptions are labelled
  unavailable; uploaded Business Case documents are not parsed or replaced by sample data.
- The `project_charter` table stores only charter-owned vision wording, phase notes,
  add-only additional success criteria, source fingerprint and draft revision/audit metadata.
  Saving or regenerating vision never updates the upstream artefacts. Stale saves/deletes
  are rejected; vision is regenerated only on explicit request.
- Admin (`/project-attributes`) includes Project Charters for browsing, creating,
  editing and deleting drafts directly in the maintenance page's record form,
  without reopening the project presentation page. Access Control has a separate Project Charter permission;
  project requestors can manage their own charter but cannot browse/delete Admin records.
- Run backend migrations before opening the feature. This release is draft-only:
  no submission, approval, approved-version archive or export is enabled. Saving a
  draft shows the Toll Gates item as in progress, not secured.

### Online Business Case

- `/migration-dashboard/:id/business-case` is an online record, not a mandatory
  final-document upload. Four sections cover Intake, read-only Scope, calculated
  financials and Business Case-owned narrative. Existing final attachments remain
  downloadable; old uploads are not interpreted as populated online records.
  Use **Edit project details** in Project overview to edit Intake, then
  **Save project details** or **Cancel editing**. Saving also includes pending
  Business Case changes; cancelling discards only Intake edits. Reload, financial
  refresh and Print / Save PDF are grouped under **More actions**.
  The workspace uses MDS buttons, tags and notifications, with brand typography
  and design tokens for surfaces, borders, form controls and responsive layouts.
  The compact page header places actions beside the title and metadata below.
  The layout follows Migration Intake: a white full-width canvas, bold page title,
  icon navigation and rounded section cards with blue, cyan, green and orange
  accent rules. Semantic status colours retain their meaning.
  Intake editing uses controlled single-select and searchable MDS multi-select
  fields with the same region/area/country, function/product and destination
  mappings as Migration Intake. The canonical catalogue is
  `backend/api/data/intake_options.json`, consumed by both frontend mappings and
  Business Case server validation. Parent changes retain dependent values for
  explicit review rather than silently deleting them. Unchanged legacy values
  remain saveable; changed selections must match the current catalogue and parents.
  Date order is validated server-side; migration type codes and area/country
  pairs are updated with their source fields. New custom destinations must first
  be approved at the Intake source; this editor does not replace that approval.
  Edit controls use a consistent medium MDS size and a two-column layout:
  Function/Products, Region/Areas and start/end dates share rows; rationale
  spans the full width. Function and multi-select dropdowns include search;
  short single-select lists remain unfiltered. Mobile uses one column.
  `business_case.saved_snapshot` stores the latest complete page capture.
  Every successful save, source refresh, submission or revision also appends
  the capture as `pageSnapshot` in `financial_history`, including project
  identity, Intake, Scope, narrative, financial inputs/results/rate basis,
  source versions and approval state at capture. Later source changes do not
  rewrite saved copies. Failed saves and version conflicts do not create copies.
  Both the business page and Admin editor expose read-only **Saved page snapshots**
  with version selection. Existing records keep an empty latest snapshot until
  their next successful save; old historical data is not presented as a complete
  capture. The normal business page continues showing live source data and its
  review warnings; snapshots are evidence, not an independent editable source.
- `business_case` stores draft details, one-time costs/adjustments, revisions,
  audit events and immutable calculation/source snapshots. Editing Intake here
  updates the original `migration_intake_submission` record. Scope-owned data
  stays in `scope_statement` and its job-level lines; out-of-scope, assumptions
  and dated migration waves are maintained there, not in Business Case.
- Admin has separate Business Case and Business Case Cost Rates maintenance cards,
  controlled by the `business_case` and `cost_rates` Access Control permissions.
  Administration uses record forms, not the presentation page. The project
  requestor remains the only user allowed to formally submit.
- Maintain fully loaded **annual** costs by exact source country / destination
  GSC site, job level and target-start year in `business_case_cost_rate`. Each
  rate has a currency, version and USD-per-local-unit conversion factor (USD = 1).
  There are no seeded illustrative rates. Missing rates or sources block
  financial calculation and submission, but do not prevent saving a draft.
- Calculations use locked Scope final FTE, Decimal arithmetic and USD totals:
  current/future annual cost = sum(FTE x annual rate x USD conversion);
  gross and recurring benefit = current minus future; benefit percentage =
  gross/current; net first-year benefit = gross minus adjusted one-time cost;
  payback months = adjusted one-time cost/(gross/12). The first-year formula is
  full run-rate, not prorated by waves. Zero current cost has no percentage;
  non-positive benefit has no payback period. These cases display explanations.
- A nonzero manual adjustment requires a reason and never overwrites the baseline.
  Source, rate and financial histories retain the basis used at each save/refresh/
  submission. Calculation refresh preserves adjustments.
- Complete/submit validates submitted Scope, all locked FTE, financial readiness,
  business owner, dates and required narrative, then starts the existing approval
  chain (Area Head, PMO, BPM, conditional FBP, WPM, parallel ELT/GSC Head).
  It does not create an alternative one-click approval path.
- Submitted records are locked. Reopening requires a reason, preserves the prior
  approval evidence, clears the active approval chain, and requires resubmission.
  Relevant upstream changes flag submitted/approved online cases for review and
  block further approvals until reviewed and resubmitted. Optimistic source and
  record versions reject stale saves. Scope can also be reopened with a reason;
  existing job-level locks must still be explicitly unlocked before FTE changes.
  Changes to Intake scope inputs (function/process, locations or target dates)
  also flag an already-submitted Scope for review and resubmission.
- Current financials require one source country and one destination GSC. Multiple
  locations are blocked explicitly until a per-location FTE allocation model is
  defined; no equal split or first-location assumption is made. Opportunity
  Assessment does not currently have an independent formal approval record.
- The Artefact Delivery Dashboard reads Scope Statement status from its project
  API: submitted scope without a review flag is Secured; a saved draft or scope
  requiring review is In progress; an unsaved scope is Not started.
- Access Control Super Admins have all attribute-table permissions and can
  manage other requestors' Opportunity Assessments and stakeholder assignments.
  Locked stakeholder roles must still be unlocked before editing. Submitted
  Scope Statements and Business Cases still require reopening with a revision
  reason; Business Case resubmission remains requestor-only and approval
  decisions remain restricted to configured approvers.
- Export uses the browser's Print / Save as PDF for the online view. No new
  package or Word/PPT export service is required. Apply backend migrations before
  opening the new pages.
- Stakeholder Registration's **Export** downloads an Excel workbook
  (`<Migration Request ID>-stakeholders.xlsx`) with Overview, Stakeholder Roles,
  Project Team, MSP Focals and the complete Change Log. Multiple assigned people
  get separate rows; unassigned and not-applicable roles are retained, together
  with contact information, notes and lock metadata. The export reflects current
  page data, including local draft roster changes, without saving or changing
  locks. Unsaved role-drawer selections must first be saved to appear on the page
  and in the export.

> Use **port 3002** as the development frontend entry point. The backend serves APIs only; Vite proxies `/api` to `http://127.0.0.1:8001` by default.
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
| `127.0.0.1:3002` | **development** | Vite dev server (`npm run dev`) | proxies `/api` → 8001 by default |
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
- `frontend/vite.config.js` starts the dev frontend on `127.0.0.1:3002`, proxies
  `/api` to `127.0.0.1:8001` by default, and logs `[vite] /api -> ...` on startup
  so the target is never a guess.

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
Get-NetTCPConnection -LocalPort 3002, 8000, 8001 -State Listen |
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
| **Frontend (dev main entry)** | http://localhost:3002 | Open this in your browser for local development |
| **Backend API (dev)** | http://127.0.0.1:8001 | API only — not the UI; `runserver` + SQLite |
| **Backend API (production service)** | http://127.0.0.1:8000 | Windows service **AE_WPM**, Waitress + MSSQL — never bind this port yourself |

The global `mc-top-bar` header links to the main pages. All local frontend routes below are relative to `http://localhost:3002`.

### Frontend pages

| Page | URL | Description |
|------|-----|-------------|
| **Welcome** | http://localhost:3002/ | Landing page with tool cards and entry to the Project Attributes Database |
| **Future Service Model** | http://localhost:3002/future-service-model | Cost, capability, and country-level analytics for GSC transition planning — includes expandable process and country task tables |
| **Migration Intake** | http://localhost:3002/migration-intake | Submit a new migration request and capture intake details |
| **Migration Dashboard** | http://localhost:3002/migration-dashboard | Product-level migration summary and tracking overview |
| **L&D Dashboard** | http://localhost:3002/ld-dashboard | Learning, scoping tasks, and training timeline by project |
| **Project Dashboard** | http://localhost:3002/project-dashboard | Individual project opportunity assessment and milestone hub |
| **Milestone detail** | http://localhost:3002/project-dashboard/:section | Drill-down for a specific milestone (e.g. `gantt`, `approvals`, `business-case`, `cost`, `training`) |
| **Migration Chatbot** | http://localhost:3002/migration-chatbot | Guided Q&A and migration support chatbot demo |
| **Scope Statement** | http://localhost:3002/migration-dashboard/:id/scope-statement | Project-linked scope workspace, opened from Toll Gates → Initiate → Scope Statement |

#### Scope Statement workspace

The Scope Statement uses the selected intake project's numeric ID in its URL and
displays its Migration Request ID, project name and original ambition FTE. Its
visual layout follows Toll Gates: a project summary, five FTE indicators, a
headcount agreement table, and paired exception / scope narrative panels.

Agreed and exception FTE for JL2, JL3 and JL4 are **manually maintained**, not
automatically sourced from Opportunity Assessment. Final FTE accepts whole
numbers. The headcount agreement has one shared **Attachement** upload and
download list (PDF, DOCX, MSG or XLSX, up to 20 MB per file). Existing job-level
files are retained and linked to their statement by migration 0052. The page shows variances,
reconciliation against intake ambition, and submission readiness.

Authorised editors can save drafts and use a single **Lock / Unlock** control
at the top of the page. Lock requires complete agreed, exception and final FTE
for all levels, manually confirmed Migratable FTE, Scope text (maximum 2,000 characters), a shared attachment and
matching wave totals when provided. It freezes all editable page fields and
uploads, including Admin edits, while downloads remain available. Existing
partially locked statements are treated as page-locked and can be unlocked in
one action. All three underlying level locks are still recorded for Business
Case and Charter compatibility. Submission requires the whole page to be locked.
Submitted statements must first be reopened with a revision reason, then unlocked
before editing; reopening does not discard files.
Save/upload errors remain inline without hiding the form.

**Migratable FTE** is an independent manual Scope total, initially prefilled from
the agreed JL2/JL3/JL4 sum, not an automatically authoritative aggregate.
The user must explicitly confirm it; editing its value clears confirmation.
Drafts may be saved before confirmation, but Lock and Submit require confirmation.
The saved manual value is never replaced by subsequent JL changes. Reconciliation
uses this manual total plus exceptions against Intake ambition. Business Case and
Charter read the confirmed manual total from Scope; new Business Case snapshots
include its value and confirmation state. Final FTE by JL remains the cost model,
wave allocation and final delivery commitment basis. Changing either the manual
value or its confirmation invalidates the Business Case source version and
triggers the existing review workflow. Existing records are not auto-confirmed
or backfilled; untouched historical approvals and saved snapshots stay intact.

### Redirects

| From | To |
|------|-----|
| http://localhost:3002/welcome | http://localhost:3002/ |
| http://localhost:3002/welcome2 | http://localhost:3002/future-service-model |

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

Open the local dev app at **http://localhost:3002**, not the backend port. The backend is API-only.

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

- Frontend on a different port: `npm run dev -- --port 3003` (also update `CORS_ALLOWED_ORIGINS` in `backend/config/settings.py`)

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
| Dev ports | Frontend `3002`, Backend `8001` (production service owns `8000`) |
