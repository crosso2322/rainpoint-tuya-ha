"""Switch platform for RainPoint Tuya Cloud."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import ZONE_CODES, ZONES
from .coordinator import RainPointCoordinator
from .entity import RainPointEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry[RainPointCoordinator],
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up RainPoint switches."""
    async_add_entities(
        RainPointZoneSwitch(entry.runtime_data, zone) for zone in ZONES
    )


class RainPointZoneSwitch(RainPointEntity, SwitchEntity):
    """Irrigation zone switch."""

    def __init__(self, coordinator: RainPointCoordinator, zone: str) -> None:
        super().__init__(coordinator, f"{zone}_zone", f"{zone}_zone")
        self.zone = zone
        self._attr_icon = "mdi:water-pump"

    @property
    def is_on(self) -> bool:
        """Return whether watering is active."""
        status = self.coordinator.data.status
        codes = ZONE_CODES[self.zone]
        return (
            str(status.get(codes["work_status"], "0")) == "1"
            or status.get(codes["manual_switch"]) is False
        )

    async def async_turn_on(self, **kwargs) -> None:
        """Start watering."""
        await self.coordinator.async_start_zone(self.zone)

    async def async_turn_off(self, **kwargs) -> None:
        """Stop watering."""
        await self.coordinator.async_stop_zone(self.zone)
