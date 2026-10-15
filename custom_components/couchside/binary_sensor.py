"""Couchside binary sensors: something is playing, a library scan is running."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import CouchsideConfigEntry
from .coordinator import CouchsideCoordinator
from .entity import CouchsideEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CouchsideConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Adds the Couchside binary sensors."""
    coordinator = entry.runtime_data
    async_add_entities(
        [
            CouchsideBinarySensor(coordinator, "playing", lambda d: bool(d.get("now_playing"))),
            CouchsideBinarySensor(coordinator, "scanning", lambda d: bool(d.get("scanning"))),
        ]
    )


class CouchsideBinarySensor(CouchsideEntity, BinarySensorEntity):
    """An on/off state read from Couchside."""

    def __init__(
        self,
        coordinator: CouchsideCoordinator,
        key: str,
        value: Callable[[dict[str, Any]], bool],
    ) -> None:
        super().__init__(coordinator, key)
        self._value = value

    @property
    def is_on(self) -> bool:
        return self._value(self.coordinator.data)
