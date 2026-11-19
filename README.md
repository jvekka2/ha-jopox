# Jopox for Home Assistant

A Home Assistant custom integration that shows **your own child's Jopox+ events** (trainings, games, other events) as a calendar, using the same "show only my events" filter as the Jopox+ mobile app.

> **Unofficial.** This project is not made by, affiliated with or endorsed by Jopox. It uses the same web API as the Jopox+ app, with your own account, read-only. Jopox can change that API at any time and the integration may stop working. Use at your own risk.

**Suomeksi:** Tämä lisäosa tuo Jopox+ -sovelluksessa näkyvät *omat* tapahtumat (harjoitukset, ottelut, tapahtumat) Home Assistantin kalenteriksi. Toisin kuin joukkueen ICS-kalenterilinkki, tämä näyttää vain oman lapsesi ryhmän tapahtumat, ja voit halutessasi piilottaa tapahtumat, joihin olet vastannut OUT. Asennus ja asetukset: ks. alla (kirjautuminen samalla sähköpostilla ja salasanalla kuin Jopox+ -sovelluksessa).

## Why

Jopox's team calendar link (ICS) lists every event of the whole team, including tournaments for other groups and events you have declined, and it has no attendance information. The Jopox+ app can filter to "my events". This integration asks Jopox for exactly that filtered list.

## Features

- One calendar entity per team/child (`calendar.jopox_…`) with only your events.
- Shows your answer in each event's description: `IN`, `OUT` or `ei vastattu` (not answered).
- Option to hide events you have declined (OUT) - on by default.
- Event title, place, start/end time and description (HTML converted to plain text).
- Read-only: it never changes attendance or anything else in Jopox.
- Gentle polling: one login plus one request per refresh, every 30 minutes by default (15-240 minutes).
- Setup from the UI, with re-authentication if your password changes. English and Finnish texts.

## Installation

### HACS (custom repository)

1. HACS > three-dot menu > **Custom repositories**.
2. Add `https://github.com/jvekka2/ha-jopox` with category **Integration**.
3. Install **Jopox**, then restart Home Assistant.

### Manual

Copy the `custom_components/jopox` folder into `/config/custom_components/jopox` and restart Home Assistant.

## Setup

1. **Settings > Devices & services > Add integration > Jopox.**
2. Enter the email and password you use in the Jopox+ app.
3. Choose the team. Your account may list several (one per child or group); add the integration once per team you want.

The password is stored in Home Assistant's config entry storage (`/config/.storage`), like other integrations that need a login. It is only sent to Jopox.

### Options

Settings > Devices & services > Jopox > Configure:

| Option | Default | Meaning |
|---|---|---|
| Hide events I have declined (OUT) | on | Removes events whose answer is OUT |
| Update interval | 30 min | 15-240 minutes |

## How updates work

Every refresh the integration logs in, then requests the upcoming events with `showMyEventsOnly=true`. New or changed events, and changes to your IN/OUT answers made in the Jopox+ app, show up at the next refresh. To refresh now, call `homeassistant.update_entity` on the calendar entity. If Jopox cannot be reached the entity becomes unavailable until a later refresh works.

## Limits

- Jopox returns a rolling list of roughly the next six weeks; paging is not implemented.
- Event end time uses the event's `duration` (assumed to be minutes) when no end time is given.
- Events are those Jopox returns for the persons your account represents in the chosen team.
- Developed and tested on Home Assistant 2026.11 only; older versions are untested.
- Not every Jopox site may behave the same way. Please open an issue if something looks wrong.

## Troubleshooting

- **"Wrong email or password":** check that you can log in to the Jopox+ app with the same details.
- **No teams found:** your account has no locker rooms/teams in Jopox.
- **Entity unavailable:** see the Home Assistant log for `custom_components.jopox`. Enable debug logs with `logger: logs: custom_components.jopox: debug`.
- **Something is empty or wrong:** run `tools/events_probe.py` (see `tools/`) and attach its output to an issue. It prints only structure and counts, no titles, names or tokens.

## For developers

- API notes: [docs/api.md](docs/api.md)
- Debug helper: [tools/README.md](tools/README.md)
- Contributions are welcome. Please do not post passwords, tokens, cookies or other people's names in issues.

## License

[MIT](LICENSE)
