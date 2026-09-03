# Final career-workspace verification

## Completed locally (2026-09-03)

- 17 backend tests passed, including the authenticated HTTP career workflow and exact version-2 backup/restore round trip. PostgreSQL recovery test is separately configured in CI.
- Frontend lint passed. Production frontend build passed with `npm run build -- --configLoader native` (this Windows sandbox blocks the default configuration loader's child process).
- Browser inspection at 390px phone width: all seven demo pages fit without page-level horizontal overflow. Insights also checked at 320px; desktop checked at 1440px.
- Live local-browser checks: combined location/work-mode filters, empty results, workspace copilot, interview questions, Escape-to-close with focus restoration, role capture, applied/interview transitions, notes, follow-up and saved preferences.
- Axe automated WCAG Level-A rules (`wcag2a`, `wcag21a`): zero reported violations across all seven demo pages at desktop and phone widths. Editable personal action/settings forms also passed. This is not a full WCAG certification or a complete screen-reader/contrast audit.
- Skill-gap roadmap is visible in Insights; mobile users can upload/update resumes from there.
- Eight UTC calendar weeks show captures and recorded stage-change events. Current week is partial. Pre-existing transitions cannot be reconstructed and are explicitly described as unavailable, rather than invented.
- Private source link replaced with creator GitHub profile and an explicit private-repository note. Repository visibility was not changed.

## CI release gate (requires the new commit to be pushed)

1. `backend`: unit/HTTP tests plus a dedicated PostgreSQL 16 recovery test.
2. `dashboard`: lint and production build.
3. `browser-workflows`: four Playwright desktop/mobile scenarios, including demo API isolation, downloads, filters, keyboard, personal workflow and accessibility checks.
4. `production-container`: real Nginx public/private HTTP authentication boundary.

The Playwright test files collect locally, but the runner cannot spawn workers in this Windows sandbox (`spawn EPERM`). Do not claim that CI browser tests or the PostgreSQL recovery test passed until that new run is green. Local browser checks above were run through the available in-app browser instead.

After green CI, confirm the same commit is Live in Render. Recheck `/demo` without credentials and `/` with authentication. Existing production data and real Gmail/Calendar were not modified by these tests.

## Safe backup and recovery

Use **Insights → Download career backup** in the authenticated workspace. Version 2 contains captured jobs, profile, preferences, application notes, follow-ups, resume versions and recorded application stage history. It deliberately excludes passwords, OAuth tokens, approvals, unrelated action history and uncaptured job cache.

Keep the JSON private: it contains resume and career information. To restore it into a new local SQLite database, from the repository root:

```powershell
python -m scripts.restore_backup path-to-private-backup.json --destination restored-career.db
```

The destination must not already exist. There is no production overwrite or web restore endpoint. Version-1 exports are rejected because they did not contain enough relational data for reliable recovery. Google must be reconnected separately. A PostgreSQL production replacement/credential recovery is deliberately not performed by this offline tool.

CLI export, using the configured database, is also available:

```powershell
python -m scripts.export_backup --output path-to-new-private-backup.json
```

## Local test commands

```powershell
python -m pytest -q
# Restricted Windows temp-folder fallback:
python -m scripts.verify_local
```

```powershell
cd dashboard
npm ci
npm run build
npx playwright install chromium
npm run test:e2e
```

The browser tests start a loopback-only synthetic server. No production credentials or Google actions are used. Its optional `?qa-a11y=1` audit controls are test-harness-only and are not shipped in the production image.
