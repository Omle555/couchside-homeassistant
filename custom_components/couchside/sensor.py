"""Couchside sensors: library totals and what is playing now."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import CouchsideConfigEntry
from .coordinator import CouchsideCoordinator
from .entity import CouchsideEntity


@dataclass(frozen=True, kw_only=True)
class CouchsideSensorDescription(SensorEntityDescription):
    """How to read one sensor from GET /api/v1/activity."""

    value: Callable[[dict[str, Any]], Any]


def label(item: dict[str, Any]) -> str:
    """`Alien`, or `Severance S01E02 Half Loop` for an episode."""
    if item.get("kind") != "episode" or not item.get("show_title"):
        return item["title"]
    code = ""
    if item.get("season") is not None and item.get("episode") is not None:
        code = f" S{item['season']:02d}E{item['episode']:02d}"
    return f"{item['show_title']}{code} {item['title']}"


SENSORS = (
    CouchsideSensorDescription(
        key="now_playing",
        state_class=SensorStateClass.MEASUREMENT,
        value=lambda d: len(d.get("now_playing", [])),
    ),
    CouchsideSensorDescription(
        key="converting",
        state_class=SensorStateClass.MEASUREMENT,
        value=lambda d: d.get("converting", 0),
    ),
    CouchsideSensorDescription(
        key="movies",
        state_class=SensorStateClass.MEASUREMENT,
        value=lambda d: d.get("movies"),
    ),
    CouchsideSensorDescription(
        key="shows",
        state_class=SensorStateClass.MEASUREMENT,
        value=lambda d: d.get("shows"),
    ),
    CouchsideSensorDescription(
        key="episodes",
        state_class=SensorStateClass.MEASUREMENT,
        value=lambda d: d.get("episodes"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CouchsideConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Adds the Couchside sensors."""
    async_add_entities(CouchsideSensor(entry.runtime_data, d) for d in SENSORS)


class CouchsideSensor(CouchsideEntity, SensorEntity):
    """One number from Couchside."""

    entity_description: CouchsideSensorDescription

    def __init__(
        self, coordinator: CouchsideCoordinator, description: CouchsideSensorDescription
    ) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        return self.entity_description.value(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.key != "now_playing":
            return None
        items = self.coordinator.data.get("now_playing", [])
        return {
            "titles": [label(item) for item in items],
            "viewers": sorted({item["user"] for item in items}),
            "items": items,
        }
