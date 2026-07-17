"""Data coordinator for RainPoint Tuya Cloud."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
import logging
import time
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    RainPointApiError,
    RainPointAuthenticationError,
    RainPointCloudApi,
)
from .const import (
    CONF_LEFT_DURATION,
    CONF_LEFT_GPM,
    CONF_POLL_INTERVAL,
    CONF_RIGHT_DURATION,
    CONF_RIGHT_GPM,
    DEFAULT_DURATION,
    DEFAULT_GPM,
    DEFAULT_POLL_INTERVAL,
    DOMAIN,
    ZONE_CODES,
    ZONE_LEFT,
    ZONE_RIGHT,
    ZONES,
)

_LOGGER = logging.getLogger(__name__)
STORAGE_VERSION = 1


@dataclass(slots=True)
class ZoneRuntime:
    """Runtime and estimated usage for one valve zone."""

    active: bool = False
    active_since: float | None = None
    cycle_seconds: float = 0.0
    total_seconds: float = 0.0
    cycle_gallons: float = 0.0
    total_gallons: float = 0.0


@dataclass(slots=True)
class RainPointData:
    """Coordinator data."""

    status: dict[str, Any] = field(default_factory=dict)
    zones: dict[str, ZoneRuntime] = field(
        default_factory=lambda: {zone: ZoneRuntime() for zone in ZONES}
    )


class RainPointCoordinator(DataUpdateCoordinator[RainPointData]):
    """Coordinate cloud polling and runtime accounting."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        api: RainPointCloudApi,
    ) -> None:
        self.entry = entry
        self.api = api
        poll_interval = int(
            entry.options.get(
                CONF_POLL_INTERVAL,
                entry.data.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL),
            )
        )
        self.data_model = RainPointData()
        self._store: Store[dict[str, Any]] = Store(
            hass, STORAGE_VERSION, f"{DOMAIN}.{entry.entry_id}"
        )
        self._last_save = 0.0

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=timedelta(seconds=poll_interval),
            always_update=True,
        )

    async def async_load_runtime(self) -> None:
        """Load persistent usage counters."""
        stored = await self._store.async_load()
        if not stored:
            return

        for zone in ZONES:
            zone_data = stored.get(zone, {})
            runtime = self.data_model.zones[zone]
            runtime.total_seconds = float(zone_data.get("total_seconds", 0.0))
            runtime.total_gallons = float(zone_data.get("total_gallons", 0.0))

    async def async_save_runtime(self) -> None:
        """Persist cumulative usage counters."""
        payload = {
            zone: {
                "total_seconds": runtime.total_seconds,
                "total_gallons": runtime.total_gallons,
            }
            for zone, runtime in self.data_model.zones.items()
        }
        await self._store.async_save(payload)
        self._last_save = time.monotonic()

    def duration(self, zone: str) -> int:
        """Return configured zone duration."""
        key = CONF_LEFT_DURATION if zone == ZONE_LEFT else CONF_RIGHT_DURATION
        return int(self.entry.options.get(key, DEFAULT_DURATION))

    def gpm(self, zone: str) -> float:
        """Return calibrated gallons per minute."""
        key = CONF_LEFT_GPM if zone == ZONE_LEFT else CONF_RIGHT_GPM
        return float(self.entry.options.get(key, DEFAULT_GPM))

    @staticmethod
    def _is_running(status: dict[str, Any], zone: str) -> bool:
        codes = ZONE_CODES[zone]
        work_status = str(status.get(codes["work_status"], "0"))
        switch_value = status.get(codes["manual_switch"])
        return work_status == "1" or switch_value is False

    async def _async_update_data(self) -> RainPointData:
        try:
            status = await self.hass.async_add_executor_job(self.api.get_status)
        except RainPointAuthenticationError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except RainPointApiError as err:
            raise UpdateFailed(str(err)) from err
        except Exception as err:  # Defensive boundary around third-party library.
            raise UpdateFailed(f"Unexpected TinyTuya error: {err}") from err

        now = time.monotonic()
        for zone in ZONES:
            runtime = self.data_model.zones[zone]
            running = self._is_running(status, zone)

            if running and not runtime.active:
                runtime.active = True
                runtime.active_since = now
                runtime.cycle_seconds = 0.0
                runtime.cycle_gallons = 0.0

            elif running and runtime.active and runtime.active_since is not None:
                delta = max(0.0, now - runtime.active_since)
                runtime.active_since = now
                runtime.cycle_seconds += delta
                runtime.total_seconds += delta

                gallons = (delta / 60.0) * self.gpm(zone)
                runtime.cycle_gallons += gallons
                runtime.total_gallons += gallons

            elif not running and runtime.active:
                if runtime.active_since is not None:
                    delta = max(0.0, now - runtime.active_since)
                    runtime.cycle_seconds += delta
                    runtime.total_seconds += delta
                    gallons = (delta / 60.0) * self.gpm(zone)
                    runtime.cycle_gallons += gallons
                    runtime.total_gallons += gallons
                runtime.active = False
                runtime.active_since = None
                await self.async_save_runtime()

        self.data_model.status = status

        if now - self._last_save >= 300 and any(
            runtime.active for runtime in self.data_model.zones.values()
        ):
            await self.async_save_runtime()

        return self.data_model

    async def async_start_zone(self, zone: str) -> None:
        """Start a zone, then request a prompt refresh."""
        codes = ZONE_CODES[zone]
        minutes = self.duration(zone)
        try:
            await self.hass.async_add_executor_job(
                self.api.start_zone,
                codes["manual_timer"],
                codes["manual_switch"],
                minutes,
            )
        except RainPointAuthenticationError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except RainPointApiError as err:
            raise UpdateFailed(str(err)) from err
        await self.async_request_refresh()

    async def async_stop_zone(self, zone: str) -> None:
        """Stop a zone, then request a prompt refresh."""
        codes = ZONE_CODES[zone]
        try:
            await self.hass.async_add_executor_job(
                self.api.stop_zone,
                codes["manual_switch"],
            )
        except RainPointAuthenticationError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except RainPointApiError as err:
            raise UpdateFailed(str(err)) from err
        await self.async_request_refresh()
