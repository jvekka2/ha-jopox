"""Calendar platform: the child's own Jopox+ events."""
from __future__ import annotations

from datetime import datetime

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from . import JopoxConfigEntry
from .api import JopoxEvent
from .const import CONF_TITLE, DOMAIN
from .coordinator import JopoxCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: JopoxConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([JopoxCalendar(entry.runtime_data, entry)])


def _to_event(e: JopoxEvent) -> CalendarEvent:
    return CalendarEvent(
        start=e.start,
        end=e.end,
        summary=e.title,
        description=e.description,
        location=e.location,
        uid=e.uid,
    )


class JopoxCalendar(CoordinatorEntity[JopoxCoordinator], CalendarEntity):
    _attr_has_entity_name = True
    _attr_name = None

    def __init__(self, coordinator: JopoxCoordinator, entry: JopoxConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_calendar"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.data.get(CONF_TITLE) or "Jopox",
            "manufacturer": "Jopox",
        }

    @property
    def event(self) -> CalendarEvent | None:
        now = dt_util.now()
        for e in self.coordinator.data or []:
            if e.end > now:
                return _to_event(e)
        return None

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        return [
            _to_event(e)
            for e in self.coordinator.data or []
            if e.end > start_date and e.start < end_date
        ]
