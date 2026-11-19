# Jopox+ API notes

Unofficial notes on the web API that the Jopox+ mobile app uses, as far as this integration needs it. Everything here was observed with a normal personal account; there is no public documentation, so it can change without notice. All ids below are placeholders.

## Base

`https://myapi.jopox.fi` (JSON over HTTPS). Every call except login sends:

```
Authorization: Bearer <accessToken>
Accept-Language: fi
x-metadata: <locker room metadataId>      # sent by the app on site-specific calls
```

## Login

```
POST /api/v1/myjopoxaccount/login
{"username": "<email>", "password": "<password>"}
-> 200 {"myJopoxAccountId": 123, "tokens": {"accessToken": "...", "refreshToken": "..."}}
```

The integration logs in again on every refresh instead of storing tokens. A token refresh route (`/api/v1/myjopoxaccount/tokenrefresh`) exists but is not used.

## Teams of the account

```
GET /api/v1/lockerrooms
-> {"mainUserSites": [], "subsiteAdminSites": [],
    "lockerRooms": [{"metadataId": 1, "siteName": "...", "siteShortName": "...",
                     "subsiteId": 2, "subsiteName": "...", "subsiteShortName": "...",
                     "sectionName": "...", "logoUrl": "...",
                     "isSubsiteAdmin": false, "isCabinet": false}]}
```

`metadataId` goes into the `x-metadata` header, `subsiteId` into the events URL. The team's public ICS link (`ics.jopox.fi/.../ical.php?...&cal=<code>_<subsiteId>`) uses the same subsite number.

## Own events

```
GET /api/v1/site/subsites/{subsiteId}/calendar/upcoming?year=YYYY&month=M&showMyEventsOnly=true
```

The Jopox+ app's "show only my events" selection is the `showMyEventsOnly` parameter.

- `showMyEventsOnly=false`: only the requested month, all events of the team, including those the child has no right to answer.
- `showMyEventsOnly=true`: a rolling list from today (about six weeks observed), only events where the child's group may answer IN/OUT. The `month` parameter has no effect. Declined and unanswered events are included.

Response:

```json
{"events": [{
  "id": 1, "eventType": 1, "typeTitle": "Harjoitus", "sportType": 0,
  "title": "...", "place": "...", "league": null,
  "date": "2026-01-01T15:00:00", "endTime": "2026-01-01T16:00:00", "duration": 60,
  "messageCount": 0, "enrollmentDueDate": null,
  "maxInPlayers": null, "inPlayersCount": null, "inCount": 5, "outCount": 3,
  "gamesCount": 0, "past": false, "hasInfo": true, "description": "<p>HTML</p>",
  "confirmedPlayersCount": 0, "hasLineup": null, "groups": [],
  "representedPersons": [{"isIn": true, "isInOutAllowed": true, "isOfficial": false,
                          "isPlayer": true, "id": 1, "firstname": "...", "lastname": "...",
                          "consent": true, "isMainUser": false, "adminSections": []}]
}]}
```

- `eventType`: 1 training (Harjoitus), 2 game (Ottelu), 3 event (Tapahtuma).
- `representedPersons[].isIn`: `true` = IN, `false` = OUT (declined), `null` = not answered.
- `representedPersons[].isInOutAllowed`: the person may answer for this event.
- `date` / `endTime` are local time without a time zone offset (the integration assumes the Home Assistant time zone).

## Other routes seen (not used)

Attendance and comment routes exist under `/api/v1/site/subsites/{id}/(events|games|trainings)/{eventId}/in-out` and `/comments` (write operations, deliberately not used), plus `/calendar/ics/`, `/calendar/upcoming/expiringsignups`, `/api/v1/site/exercises/persons`, `/api/v1/feed`, `/api/v1/notifications`.

## Being a good citizen

This integration polls at most every 15 minutes (every 4 hours by default), makes one login plus one GET per refresh, and never writes. Please keep any tooling built on these notes equally gentle.
