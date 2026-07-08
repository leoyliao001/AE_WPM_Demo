# Migration Intake — Single-file HTML Export

Standalone single HTML export of the **Migration Project Intake Form**.

## Build

From the `frontend` folder (requires `npm install` once):

```cmd
cd /d "c:\fcous\AE WPM Demo\frontend"
npm run build:migration-intake-html
```

Output: `exports/Migration-Intake.html`

## Share with others

Send `Migration-Intake.html`. Recipients double-click to open in **Chrome** or **Edge**.

- Styles are embedded in the file
- MDS icons load from Maersk CDN (internet required for icons)
- Form drafts save to browser `localStorage`
- Submit is virtual (no backend required)

## Rebuild after form changes

Run the build command again after editing `frontend/src/views/MigrationIntake.vue` or related data files.
