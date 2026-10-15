"""Polls Couchside for library totals and what is playing."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import CouchsideAuthError, CouchsideClient, CouchsideError, CouchsideNotAdminError
from .const import DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


class CouchsideCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetches GET /api/v1/activity on a schedule."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: CouchsideClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
            config_entry=entry,
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.client.activity()
        except (CouchsideAuthError, CouchsideNotAdminError) as err:
            raise ConfigEntryAuthFailed("Sign in to Couchside again") from err
        except CouchsideError as err:
            raise UpdateFailed(str(err)) from err
