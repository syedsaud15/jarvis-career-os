# Final production connections

## User accounts

The current production protection is the `JARVIS_API_KEY` gateway. Before a public multi-user launch, add an identity provider (Auth0, Clerk, or a company SSO) and map its verified user ID to the `sender` field. Do not expose the API without an authentication gateway.

## Gmail and Google Calendar

1. In Google Cloud Console, create a project and enable Gmail API and Google Calendar API.
2. Create an OAuth **Web application** client, adding this local redirect URI: `http://localhost:8000/integrations/google/callback`.
3. Add `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and `GOOGLE_REDIRECT_URI` only to `.env`.
4. For deployment, replace the redirect URI with `https://your-domain/integrations/google/callback` and add that exact URI in Google Cloud.
5. Request only `gmail.send` and `calendar.events` scopes. Every send/event remains approval-gated.

Never put client secrets, refresh tokens, or API keys in GitHub or screenshots.

## Domain deployment

1. Point the domain's A record to your Linux VPS public IP.
2. Set `JARVIS_DOMAIN`, `JARVIS_API_KEY`, and the production Google redirect URI in server `.env`.
3. Run `docker compose -f docker-compose.production.yml up -d --build`.
4. Caddy provisions HTTPS automatically after DNS resolves. Keep the database volume backed up.
