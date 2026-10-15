"""The Couchside media server integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_TOKEN, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import CouchsideClient
from .coordinator import CouchsideCoordinator

PLATFORMS = [Platform.BINARY_SENSOR, Platform.IMAGE, Platform.SENSOR]

type CouchsideConfigEntry = ConfigEntry[CouchsideCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: CouchsideConfigEntry) -> bool:
    """Connects to Couchside and sets up its sensors."""
    client = CouchsideClient(
        async_get_clientsession(hass),
        entry.data[CONF_HOST],
        entry.data[CONF_PORT],
        entry.data[CONF_TOKEN],
    )
    coordinator = CouchsideCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: CouchsideConfigEntry) -> bool:
    """Removes Couchside's sensors."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
