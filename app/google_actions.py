from __future__ import annotations

import base64
import json
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class GoogleActionExecutor:
    def __init__(self, store, cipher, settings):
        self.store, self.cipher, self.settings = store, cipher, settings

    def _token_data(self, sender: str) -> dict[str, object]:
        with self.store.connection() as con:
            row = con.execute("SELECT encrypted_token FROM oauth_connections WHERE provider='google' AND sender=?", (sender,)).fetchone()
        if not row:
            raise RuntimeError("Google account is not connected")
        return json.loads(self.cipher().decrypt(row["encrypted_token"].encode()).decode())

    def _refresh(self, sender: str, token: dict[str, object]) -> str:
        refresh_token = token.get("refresh_token")
        if not refresh_token:
            raise RuntimeError("Google refresh token missing. Reconnect Google and grant consent again.")
        data = urlencode({"client_id": self.settings.google_client_id, "client_secret": self.settings.google_client_secret, "refresh_token": refresh_token, "grant_type": "refresh_token"}).encode()
        with urlopen(Request("https://oauth2.googleapis.com/token", data=data, headers={"Content-Type": "application/x-www-form-urlencoded"}), timeout=15) as response:
            fresh = json.loads(response.read().decode())
        token.update(fresh)
        encrypted = self.cipher().encrypt(json.dumps(token).encode()).decode()
        with self.store.connection() as con:
            con.execute("UPDATE oauth_connections SET encrypted_token=?, connected_at=CURRENT_TIMESTAMP WHERE provider='google' AND sender=?", (encrypted, sender))
        return str(token["access_token"])

    def _request(self, sender: str, url: str, method: str, payload: dict[str, object]) -> dict[str, object]:
        token = self._token_data(sender)
        def send(access_token: str):
            request = Request(url, data=json.dumps(payload).encode(), method=method, headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"})
            with urlopen(request, timeout=20) as response: return json.loads(response.read().decode())
        try: return send(str(token["access_token"]))
        except HTTPError as error:
            if error.code != 401: raise
            return send(self._refresh(sender, token))

    def execute(self, sender: str, tool_name: str, payload: dict[str, object]) -> str:
        if tool_name == "email.send":
            raw = f"To: {payload['to']}\r\nSubject: {payload['subject']}\r\n\r\n{payload['body']}"
            encoded = base64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")
            result = self._request(sender, "https://gmail.googleapis.com/gmail/v1/users/me/messages/send", "POST", {"raw": encoded})
            return f"Gmail message sent ({result.get('id', 'accepted')})"
        if tool_name == "calendar.create":
            def rfc3339(value: str) -> str:
                return f"{value}:00+05:30" if len(value) == 16 else value
            event = {"summary": payload["title"], "start": {"dateTime": rfc3339(str(payload["starts_at"])), "timeZone": "Asia/Kolkata"}, "end": {"dateTime": rfc3339(str(payload["ends_at"])), "timeZone": "Asia/Kolkata"}}
            result = self._request(sender, "https://www.googleapis.com/calendar/v3/calendars/primary/events", "POST", event)
            return f"Calendar event created ({result.get('id', 'accepted')})"
        raise RuntimeError("Unsupported approved action")
