"""Couchside image: art of the movie playing now."""

from __future__ import annotations

from typing import Any

from homeassistant.components.image import ImageEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from . import CouchsideConfigEntry
from .api import CouchsideError
from .coordinator import CouchsideCoordinator
from .entity import CouchsideEntity
from .sensor import movies_playing


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CouchsideConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Adds the movie poster image."""
    async_add_entities([CouchsideMoviePoster(entry.runtime_data)])


def movie_item_id(data: dict[str, Any] | None) -> int | None:
    """Item id of the newest movie playing, if any."""
    movies = movies_playing(data or {})
    return movies[0].get("item_id") if movies else None


class CouchsideMoviePoster(CouchsideEntity, ImageEntity):
    """Backdrop (or poster) of the movie playing, served through Home Assistant."""

    def __init__(self, coordinator: CouchsideCoordinator) -> None:
        super().__init__(coordinator, "movie_poster")
        ImageEntity.__init__(self, coordinator.hass)
        self._item_id = movie_item_id(coordinator.data)
        self._cached: tuple[int, bytes] | None = None
        self._attr_image_last_updated = dt_util.utcnow()

    @callback
    def _handle_coordinator_update(self) -> None:
        item_id = movie_item_id(self.coordinator.data)
        if item_id != self._item_id:
            self._item_id = item_id
            self._attr_image_last_updated = dt_util.utcnow()
        super()._handle_coordinator_update()

    async def async_image(self) -> bytes | None:
        """The backdrop, else the poster, of the movie playing; None when none is."""
        item_id = self._item_id
        if item_id is None:
            return None
        if self._cached and self._cached[0] == item_id:
            return self._cached[1]
        client = self.coordinator.client
        try:
            art = await client.item_image(item_id, "backdrop") or await client.item_image(
                item_id, "poster"
            )
        except CouchsideError:
            return None
        if art is None:
            return None
        content, self._attr_content_type = art
        self._cached = (item_id, content)
        return content
