"""Polling coordinator: one login + one events request per refresh."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import JopoxAuthError, JopoxClient, JopoxError, JopoxEvent, parse_events
from .const import (
    CONF_HIDE_DECLINED,
    CONF_METADATA_ID,
    CONF_SCAN_MINUTES,
    CONF_SUBSITE_ID,
    DEFAULT_HIDE_DECLINED,
    DEFAULT_SCAN_MINUTES,
    DOMAIN,
    MAX_SCAN_MINUTES,
    MIN_SCAN_MINUTES,
)

_LOGGER = logging.getLogger(__name__)


class JopoxCoordinator(DataUpdateCoordinator[list[JopoxEvent]]):
    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        minutes = int(entry.options.get(CONF_SCAN_MINUTES, DEFAULT_SCAN_MINUTES))
        minutes = max(MIN_SCAN_MINUTES, min(MAX_SCAN_MINUTES, minutes))
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(minutes=minutes),
        )
        self._client = JopoxClient(
            async_get_clientsession(hass), entry.data[CONF_EMAIL], entry.data[CONF_PASSWORD]
        )

    async def _async_update_data(self) -> list[JopoxEvent]:
        entry = self.config_entry
        try:
            token = await self._client.login()
            raw = await self._client.upcoming(
                token,
                entry.data[CONF_METADATA_ID],
                entry.data[CONF_SUBSITE_ID],
                dt_util.now(),
            )
        except JopoxAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except JopoxError as err:
            raise UpdateFailed(str(err)) from err

        events = parse_events(raw, dt_util.get_default_time_zone())
        if entry.options.get(CONF_HIDE_DECLINED, DEFAULT_HIDE_DECLINED):
            events = [e for e in events if e.status is not False]
        return events
