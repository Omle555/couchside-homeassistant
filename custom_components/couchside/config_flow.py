"""Set up Couchside from Home Assistant's UI, by hand or when it is discovered."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_TOKEN, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession

try:
    from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo
except ImportError:  # Home Assistant before 2025.1
    from homeassistant.components.zeroconf import ZeroconfServiceInfo

from .api import (
    CouchsideAuthError,
    CouchsideClient,
    CouchsideError,
    CouchsideNotAdminError,
    CouchsideOutsideNetworkError,
)
from .const import DEFAULT_PORT, DOMAIN

CREDENTIALS = vol.Schema({vol.Required(CONF_USERNAME): str, vol.Required(CONF_PASSWORD): str})


class CouchsideConfigFlow(ConfigFlow, domain=DOMAIN):
    """Signs in to a Couchside server with an administrator account."""

    VERSION = 1

    def __init__(self) -> None:
        self._host: str | None = None
        self._port: int = DEFAULT_PORT
        self._server: str | None = None

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Server address and account typed in by hand."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self._host = user_input[CONF_HOST].strip()
            self._port = user_input[CONF_PORT]
            result = await self._sign_in(user_input, errors)
            if result is not None:
                return result
        schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=self._host or ""): str,
                vol.Required(CONF_PORT, default=self._port): int,
            }
        ).extend(CREDENTIALS.schema)
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_zeroconf(self, discovery_info: ZeroconfServiceInfo) -> ConfigFlowResult:
        """Couchside announced itself on the network."""
        self._host = str(discovery_info.ip_address)
        self._port = discovery_info.port or DEFAULT_PORT
        self._server = discovery_info.properties.get("server") or discovery_info.hostname
        await self.async_set_unique_id(self._server.lower().removesuffix(".local."))
        self._abort_if_unique_id_configured(
            updates={CONF_HOST: self._host, CONF_PORT: self._port}
        )
        self.context["title_placeholders"] = {"name": self._server}
        return await self.async_step_zeroconf_confirm()

    async def async_step_zeroconf_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Account for a discovered server."""
        errors: dict[str, str] = {}
        if user_input is not None:
            result = await self._sign_in(user_input, errors)
            if result is not None:
                return result
        return self.async_show_form(
            step_id="zeroconf_confirm",
            data_schema=CREDENTIALS,
            errors=errors,
            description_placeholders={"name": self._server or "", "host": self._host or ""},
        )

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        """The saved session ended (signed out, or unused for 30 days)."""
        self._host = entry_data[CONF_HOST]
        self._port = entry_data[CONF_PORT]
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Sign in again."""
        errors: dict[str, str] = {}
        if user_input is not None:
            token = await self._login(user_input, errors)
            if token is not None:
                return self.async_update_reload_and_abort(
                    self._get_reauth_entry(), data_updates={CONF_TOKEN: token}
                )
        return self.async_show_form(
            step_id="reauth_confirm", data_schema=CREDENTIALS, errors=errors
        )

    async def _login(self, user_input: dict[str, Any], errors: dict[str, str]) -> str | None:
        """Signs in, filling `errors` on failure."""
        client = self._client()
        try:
            return await client.login(user_input[CONF_USERNAME], user_input[CONF_PASSWORD])
        except CouchsideAuthError:
            errors["base"] = "invalid_auth"
        except CouchsideNotAdminError:
            errors["base"] = "not_admin"
        except CouchsideOutsideNetworkError:
            errors["base"] = "outside_network"
        except CouchsideError:
            errors["base"] = "cannot_connect"
        return None

    async def _sign_in(
        self, user_input: dict[str, Any], errors: dict[str, str]
    ) -> ConfigFlowResult | None:
        """Signs in and creates the entry, or returns None with `errors` filled."""
        token = await self._login(user_input, errors)
        if token is None:
            return None
        if self._server is None:
            try:
                activity = await self._client(token).activity()
            except CouchsideError:
                errors["base"] = "cannot_connect"
                return None
            self._server = activity.get("server") or self._host
            await self.async_set_unique_id(self._server.lower())
            self._abort_if_unique_id_configured(
                updates={CONF_HOST: self._host, CONF_PORT: self._port}
            )
        return self.async_create_entry(
            title=f"Couchside on {self._server}",
            data={CONF_HOST: self._host, CONF_PORT: self._port, CONF_TOKEN: token},
        )

    def _client(self, token: str | None = None) -> CouchsideClient:
        return CouchsideClient(
            async_get_clientsession(self.hass), self._host or "", self._port, token
        )
