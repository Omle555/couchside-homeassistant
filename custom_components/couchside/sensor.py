"""Couchside sensors: library totals, what is playing now and the movie playing."""

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
    attributes: Callable[[dict[str, Any]], dict[str, Any]] | None = None


def label(item: dict[str, Any]) -> str:
    """`Alien`, or `Severance S01E02 Half Loop` for an episode."""
    if item.get("kind") != "episode" or not item.get("show_title"):
        return item["title"]
    code = ""
    if item.get("season") is not None and item.get("episode") is not None:
        code = f" S{item['season']:02d}E{item['episode']:02d}"
    return f"{item['show_title']}{code} {item['title']}"


NOTHING_PLAYING = "Nothing playing"


def movies_playing(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Movies being watched right now, newest first."""
    return [item for item in data.get("now_playing", []) if item.get("kind") == "movie"]


def clock(seconds: float | None) -> str | None:
    """`1:02:03` for 3723 seconds."""
    if seconds is None:
        return None
    minutes, secs = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}"


def movie_attributes(data: dict[str, Any]) -> dict[str, Any]:
    """Who is watching the newest movie and how far in, plus every movie playing."""
    movies = movies_playing(data)
    movie = movies[0] if movies else {}
    position = movie.get("position_seconds")
    runtime = movie.get("runtime_seconds")
    return {
        "viewer": movie.get("user"),
        "position": clock(position),
        "runtime": clock(runtime),
        "progress": round(100 * position / runtime) if position is not None and runtime else None,
        "item_id": movie.get("item_id"),
        "movies": [f"{item['title']} ({item['user']})" for item in movies],
    }


def now_playing_attributes(data: dict[str, Any]) -> dict[str, Any]:
    """Titles, viewers and the raw items for everything playing."""
    items = data.get("now_playing", [])
    return {
        "titles": [label(item) for item in items],
        "viewers": sorted({item["user"] for item in items}),
        "items": items,
    }


SENSORS = (
    CouchsideSensorDescription(
        key="movie_playing",
        icon="mdi:movie-open",
        value=lambda d: movies[0]["title"] if (movies := movies_playing(d)) else NOTHING_PLAYING,
        attributes=movie_attributes,
    ),
    CouchsideSensorDescription(
        key="now_playing",
        state_class=SensorStateClass.MEASUREMENT,
        value=lambda d: len(d.get("now_playing", [])),
        attributes=now_playing_attributes,
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
        if self.entity_description.attributes is None:
            return None
        return self.entity_description.attributes(self.coordinator.data)
