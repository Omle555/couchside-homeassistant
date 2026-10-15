"""Shared base for Couchside entities."""

from __future__ import annotations

from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import base_url
from .const import DOMAIN
from .coordinator import CouchsideCoordinator


class CouchsideEntity(CoordinatorEntity[CouchsideCoordinator]):
    """An entity belonging to one Couchside server."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: CouchsideCoordinator, key: str) -> None:
        super().__init__(coordinator)
        entry = coordinator.config_entry
        self._attr_unique_id = f"{entry.unique_id}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.unique_id)},
            name=entry.title,
            manufacturer="Couchside",
            model="Media server",
            sw_version=(coordinator.data or {}).get("version"),
            configuration_url=base_url(entry.data[CONF_HOST], entry.data[CONF_PORT]),
        )
