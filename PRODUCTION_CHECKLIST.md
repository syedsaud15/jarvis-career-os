# Production release checklist

## Before public launch

- Set strong, unique `JARVIS_API_KEY`, Google OAuth credentials, and `JARVIS_DOMAIN` only in server environment variables.
- Create the first user through `POST /auth/register`; users authenticate through `POST /auth/login`.
- Point the domain A record to the VPS and use `docker compose -f docker-compose.production.yml up -d --build`.
- Confirm `/health` and `/metrics` from the reverse proxy.
- Back up the `jarvis_data` Docker volume daily and test one restore.
- Run `python -m pytest -q` and `npm run lint && npm run build` before every release.
- Verify settings, notifications, activity, weekly reporting, interview prep and CSV export with a test account.
- Confirm each account can only see its own approvals, audit activity, applications and preferences.
- For the current personal release, require Caddy basic authentication and keep the GitHub repository private.
- Do not market this build as a public multi-user SaaS; server-derived user isolation and a complete login/session UI belong in that separate phase.

## Google public release

- Keep the app in testing mode for personal use.
- Before adding public users, publish a privacy-policy URL, terms URL, and support contact.
- In Google Auth Platform, submit the OAuth consent screen for verification. Gmail send and Calendar event scopes are sensitive scopes; Google may ask for justification and demo evidence.
- Do not request broader scopes than Gmail send and Calendar events.

## Monitoring and incident response

- Monitor `/health`, `/metrics`, container restart counts, and HTTPS certificate status.
- Review `/audit-logs` after every approved external action.
- On any credential exposure, rotate the Google client secret, Adzuna key, and `JARVIS_API_KEY`, then reconnect Google.

## Release boundary

The repository includes production infrastructure, but a public launch still requires external ownership steps: domain/DNS, VPS, HTTPS validation, backups, monitoring destinations, privacy/terms pages, and Google OAuth verification. Never mark these complete until they are verified in the live environment.
