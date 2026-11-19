"""The Jopox integration: the family's own Jopox+ events as a calendar."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import JopoxCoordinator

PLATFORMS = [Platform.CALENDAR]

type JopoxConfigEntry = ConfigEntry[JopoxCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: JopoxConfigEntry) -> bool:
    coordinator = JopoxCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    entry.async_on_unload(entry.add_update_listener(_options_updated))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _options_updated(hass: HomeAssistant, entry: JopoxConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: JopoxConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
