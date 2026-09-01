# Deployment runbook

## Local production-style run

1. Keep secrets only in `.env`; do not commit it.
2. Build and start the API with `docker compose up --build`.
3. The production Compose stack builds and serves both the dashboard and API. Caddy terminates HTTPS, serves the dashboard, strips the `/api` prefix, and injects the server-side API key upstream.
4. Persist the Docker `jarvis_data` volume; it contains local memory, the job cache, applications, approvals, and profile data.

## Security checklist

- Set `JARVIS_API_KEY` before exposing the API beyond localhost.
- Configure the reverse proxy to add the same value as the `X-API-Key` header for dashboard API requests.
- Never expose `.env`, OAuth credentials, database files, or Adzuna keys in source control or screenshots.
- Rotate a key immediately if it has appeared in a screenshot or commit.

## Operational checks

- `GET /health` should report `status: ok`.
- Use `GET /audit-logs` to review approvals.
- Use `GET /jobs` to inspect cached job records.
- Back up the persistent volume before database or deployment changes.
- Poll `GET /metrics` from your uptime monitor for basic user and pending-approval metrics.

See `PRODUCTION_CHECKLIST.md` for the public-release, Google-verification, account, backup, and monitoring runbook.

## VPS production launch

1. Point the domain A/AAAA records to the VPS.
2. Install Docker Engine and the Compose plugin on the VPS.
3. Clone the private repository and create `.env` from `.env.example`.
4. Set `JARVIS_DOMAIN`, a long random `JARVIS_API_KEY`, provider credentials, and the production Google redirect URI.
5. Generate a password hash with `docker run --rm caddy:2-alpine caddy hash-password --plaintext "YOUR-STRONG-PASSWORD"`, then set `JARVIS_ADMIN_USER` and `JARVIS_ADMIN_PASSWORD_HASH` in `.env`.
6. Run `docker compose -f docker-compose.production.yml up -d --build`.
7. Verify `https://YOUR_DOMAIN/`, `https://YOUR_DOMAIN/health`, dashboard API calls, and Google OAuth callback.
8. Configure daily encrypted backups of the `jarvis_data` volume and external uptime monitoring.

## External integrations

Gmail and Google Calendar remain approval-gated until a Google Cloud OAuth project and redirect URI are configured. Do not add production OAuth secrets to the repository.
