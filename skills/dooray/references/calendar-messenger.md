# Calendar and messenger

Public evidence: [Dooray Go SDK calendar](https://github.com/dooray-go/dooray-sdk/tree/develop/openapi/calendar), [messenger](https://github.com/dooray-go/dooray-sdk/tree/develop/openapi/messenger).

- `GET /calendar/v1/calendars`: calendars.
- `GET /calendar/v1/calendars/{calendarId}/events`: events; specify `timeMin` and `timeMax`.
- An all-day event sets `wholeDayFlag: true`. The inclusive date selected by a human is converted to an **exclusive end** one day later. Confirm the target calendar's timezone; don't assume every user is in KST.
- `GET /messenger/v1/channels`: channels.
- `POST /messenger/v1/channels/direct-send`: sends a real DM. Never use it for exploratory verification. Confirm recipient IDs, show the user the message, and require explicit permission plus write-policy and apply gates.

The public SDK documents endpoint usage; the Python skill's unit tests mock network calls. These notes do not claim each operation has been live-verified with this user's token.
