"""Config flow: log in, pick the locker room (child/team), set options."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
)

from .api import JopoxAuthError, JopoxClient, JopoxError, LockerRoom
from .const import (
    CONF_HIDE_DECLINED,
    CONF_METADATA_ID,
    CONF_SCAN_MINUTES,
    CONF_SUBSITE_ID,
    CONF_TITLE,
    DEFAULT_HIDE_DECLINED,
    DEFAULT_SCAN_MINUTES,
    DOMAIN,
    MAX_SCAN_MINUTES,
    MIN_SCAN_MINUTES,
)


class JopoxConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._email = ""
        self._password = ""
        self._rooms: list[LockerRoom] = []

    @staticmethod
    @callback
    def async_get_options_flow(config_entry) -> OptionsFlow:
        return JopoxOptionsFlow()

    async def _login_and_rooms(self) -> str | None:
        client = JopoxClient(async_get_clientsession(self.hass), self._email, self._password)
        try:
            token = await client.login()
            self._rooms = await client.lockerrooms(token)
        except JopoxAuthError:
            return "invalid_auth"
        except JopoxError:
            return "cannot_connect"
        return None if self._rooms else "no_rooms"

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            self._email = user_input[CONF_EMAIL].strip()
            self._password = user_input[CONF_PASSWORD]
            if err := await self._login_and_rooms():
                errors["base"] = err
            else:
                return await self.async_step_room()
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required(CONF_EMAIL): str, vol.Required(CONF_PASSWORD): str}
            ),
            errors=errors,
        )

    async def async_step_room(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        by_key = {f"{r.metadata_id}:{r.subsite_id}": r for r in self._rooms}
        if user_input is not None:
            room = by_key[user_input["room"]]
            await self.async_set_unique_id(
                f"{self._email.lower()}_{room.metadata_id}_{room.subsite_id}"
            )
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=f"Jopox {room.label}",
                data={
                    CONF_EMAIL: self._email,
                    CONF_PASSWORD: self._password,
                    CONF_METADATA_ID: room.metadata_id,
                    CONF_SUBSITE_ID: room.subsite_id,
                    CONF_TITLE: room.label,
                },
            )
        options = [SelectOptionDict(value=k, label=r.label) for k, r in by_key.items()]
        return self.async_show_form(
            step_id="room",
            data_schema=vol.Schema(
                {vol.Required("room"): SelectSelector(SelectSelectorConfig(options=options))}
            ),
        )

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        entry = self._get_reauth_entry()
        if user_input is not None:
            self._email = entry.data[CONF_EMAIL]
            self._password = user_input[CONF_PASSWORD]
            if err := await self._login_and_rooms():
                errors["base"] = err
            else:
                return self.async_update_reload_and_abort(
                    entry, data_updates={CONF_PASSWORD: self._password}
                )
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_PASSWORD): str}),
            errors=errors,
        )


class JopoxOptionsFlow(OptionsFlow):
    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            user_input[CONF_SCAN_MINUTES] = int(user_input[CONF_SCAN_MINUTES])
            return self.async_create_entry(data=user_input)
        o = self.config_entry.options
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_HIDE_DECLINED,
                        default=o.get(CONF_HIDE_DECLINED, DEFAULT_HIDE_DECLINED),
                    ): bool,
                    vol.Required(
                        CONF_SCAN_MINUTES,
                        default=o.get(CONF_SCAN_MINUTES, DEFAULT_SCAN_MINUTES),
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=MIN_SCAN_MINUTES,
                            max=MAX_SCAN_MINUTES,
                            step=5,
                            unit_of_measurement="min",
                            mode=NumberSelectorMode.BOX,
                        )
                    ),
                }
            ),
        )
