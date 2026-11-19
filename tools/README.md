# Tools

## `events_probe.py`

A read-only debug helper. It logs in like the Jopox+ app, asks for the current month's events with `showMyEventsOnly=false` and `true`, and prints only **structure and counts** (field names, types, number of events). No titles, names, tokens or passwords are printed, so the output is safe to attach to an issue.

```bash
# Windows PowerShell
$env:JOPOX_EMAIL = "you@example.com"
$env:JOPOX_PASSWORD = Read-Host "Password"
python tools/events_probe.py            # first team of the account; pass 1, 2, ... for the next

# macOS / Linux
JOPOX_EMAIL=you@example.com python tools/events_probe.py   # asks for the password at a hidden prompt
```

Requirements: Python 3.8+, no extra packages. It makes about six requests with one-second pauses. Remove the environment variables from your shell when you are done.
