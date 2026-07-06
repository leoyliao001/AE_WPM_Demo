# Final CI Review — MDS Prototype

Standalone test page that recreates the **Final CI Review** screen from the Automation Excellence Portal using **Maersk Design System (MDS)** components.

This folder is **not** integrated into the main AE WPM Demo app. It runs on its own dev server (port **3002**).

## Original page analysis

| Area | Behaviour |
|------|-----------|
| **Left panel** | Search + automation status filter; clickable initiative cards with CI→PO→DM→CISM→EL progress strip |
| **Right panel — Approval** | Horizontal approval chain; meta (initiative, FTE); stage table with deadlines, expandable rows, sign-off & value-realised actions |
| **Right panel — Documents** | List of attachments with download links |
| **Data** | Originally from `/api/initiatives` + `localStorage`; this prototype uses seeded mock data in `localStorage` |

## Run locally (Windows CMD)

Requires `frontend` dependencies installed first (`npm install` in `frontend/`).

```cmd
cd /d "c:\fcous\AE WPM Demo\standalone\final-ci-review"
npm run dev
```

Or from the main frontend folder:

```cmd
cd /d "c:\fcous\AE WPM Demo\frontend"
npm run dev:final-ci
```

Open **http://localhost:3002**

## Test sign-off / EL actions

In the browser console:

```js
localStorage.setItem('intake_requestor_email', 'vinod.gupta@maersk.com')
```

Then select an initiative with a DM end date (e.g. **Pakistan Process Productivity Dashboard**) to exercise sign-off flows.

## Project structure

```
standalone/final-ci-review/
├── src/
│   ├── components/CiReviewPage.vue      # Main MDS layout
│   ├── components/CiStageDetail.vue     # Stage action panel
│   ├── composables/useFinalCiReview.js  # State & actions
│   ├── utils/finalCiReviewLogic.js      # Business logic
│   └── data/mockInitiatives.js          # Seed data
├── index.html
├── package.json
└── vite.config.js
```

## MDS components used

`mc-top-bar`, `mc-card`, `mc-input`, `mc-select`, `mc-option`, `mc-textarea`, `mc-button`, `mc-badge`, `mc-tag`, `mc-icon`, `mc-table`, `mc-notification`, `mc-loading-indicator`
