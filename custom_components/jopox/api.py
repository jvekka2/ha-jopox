"""Small read-only client for the Jopox+ API (own account only).

No Home Assistant imports here so it can be tested on its own.
Endpoints were found by reading the Jopox+ app's own requests; see docs/api.md.
"""
from __future__ import annotations

import html
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, tzinfo
from typing import Any

import aiohttp

from .const import API_BASE

_LOGGER = logging.getLogger(__name__)

_TIMEOUT = aiohttp.ClientTimeout(total=30)
_UA = "ha-jopox/0.1 (own account, read-only)"


class JopoxError(Exception):
    """Generic API problem."""


class JopoxAuthError(JopoxError):
    """Login rejected."""


@dataclass
class LockerRoom:
    metadata_id: int
    subsite_id: int
    label: str


@dataclass
class JopoxEvent:
    uid: str
    title: str
    start: datetime
    end: datetime
    location: str | None
    description: str
    event_type: int
    status: bool | None  # True = IN, False = OUT, None = not answered
    in_out_allowed: bool


class JopoxClient:
    """Login + events. A fresh login is done per refresh; the token is never stored."""

    def __init__(self, session: aiohttp.ClientSession, email: str, password: str) -> None:
        self._session = session
        self._email = email
        self._password = password

    async def _request(self, method: str, path: str, *, token: str | None = None,
                       meta: int | None = None, json: Any = None) -> Any:
        headers = {"User-Agent": _UA, "Accept": "application/json", "Accept-Language": "fi"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        if meta is not None:
            headers["x-metadata"] = str(meta)
        try:
            async with self._session.request(
                method, API_BASE + path, headers=headers, json=json, timeout=_TIMEOUT
            ) as resp:
                if resp.status in (401, 403):
                    raise JopoxAuthError(f"HTTP {resp.status}")
                if resp.status >= 400:
                    raise JopoxError(f"HTTP {resp.status} for {path.split('?')[0]}")
                return await resp.json(content_type=None)
        except aiohttp.ClientError as err:
            raise JopoxError(f"Connection problem: {err}") from err

    async def login(self) -> str:
        data = await self._request(
            "POST", "/api/v1/myjopoxaccount/login",
            json={"username": self._email, "password": self._password},
        )
        try:
            return data["tokens"]["accessToken"]
        except (KeyError, TypeError) as err:
            raise JopoxAuthError("Unexpected login response") from err

    async def lockerrooms(self, token: str) -> list[LockerRoom]:
        data = await self._request("GET", "/api/v1/lockerrooms", token=token)
        rooms = []
        for r in data.get("lockerRooms", []):
            label = " / ".join(
                x for x in (r.get("siteName"), r.get("subsiteName"), r.get("sectionName")) if x
            )
            rooms.append(LockerRoom(r["metadataId"], r["subsiteId"], label or str(r["metadataId"])))
        return rooms

    async def upcoming(self, token: str, metadata_id: int, subsite_id: int,
                       now: datetime) -> list[dict]:
        path = (f"/api/v1/site/subsites/{subsite_id}/calendar/upcoming"
                f"?year={now.year}&month={now.month}&showMyEventsOnly=true")
        data = await self._request("GET", path, token=token, meta=metadata_id)
        return data.get("events", []) if isinstance(data, dict) else []


def _html_to_text(value: str | None) -> str:
    """Event descriptions are HTML (<p>, <br>, &nbsp;); reduce to plain text."""
    if not value:
        return ""
    text = re.sub(r"(?i)</p>|<br\s*/?>|</li>", "\n", value)
    text = re.sub(r"(?i)<li[^>]*>", "- ", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text).replace("\xa0", " ")
    text = re.sub(r"[ \t]+\n", "\n", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def parse_events(raw: list[dict], tz: tzinfo) -> list[JopoxEvent]:
    """Convert API events to JopoxEvent. Naive timestamps are treated as local time."""
    out: list[JopoxEvent] = []
    for e in raw:
        try:
            start = datetime.fromisoformat(e["date"])
        except (KeyError, ValueError, TypeError):
            continue
        if start.tzinfo is None:
            start = start.replace(tzinfo=tz)
        end = None
        if e.get("endTime"):
            try:
                end = datetime.fromisoformat(e["endTime"])
                if end.tzinfo is None:
                    end = end.replace(tzinfo=tz)
            except ValueError:
                end = None
        if end is None or end <= start:
            end = start + timedelta(minutes=int(e.get("duration") or 60))

        persons = [p for p in (e.get("representedPersons") or []) if p.get("isPlayer", True)]
        allowed = any(p.get("isInOutAllowed") for p in persons)
        status: bool | None = None
        for p in persons:
            if p.get("isIn") is True:
                status = True
                break
            if p.get("isIn") is False:
                status = False

        kind = {1: "training", 2: "game"}.get(e.get("eventType"), "event")
        label = {True: "IN", False: "OUT", None: "ei vastattu"}[status]
        desc = f"Ilmoittautuminen: {label}"
        if e.get("typeTitle"):
            desc = f"{e['typeTitle']} · {desc}"
        text = _html_to_text(e.get("description"))
        if text:
            desc += f"\n\n{text}"

        out.append(JopoxEvent(
            uid=f"{kind}_{e.get('id')}",
            title=e.get("title") or e.get("typeTitle") or "Jopox",
            start=start,
            end=end,
            location=e.get("place") or None,
            description=desc,
            event_type=e.get("eventType") or 0,
            status=status,
            in_out_allowed=allowed,
        ))
    out.sort(key=lambda x: x.start)
    return out
