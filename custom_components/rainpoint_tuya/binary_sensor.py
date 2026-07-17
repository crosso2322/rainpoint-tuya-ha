"""Binary sensor platform for RainPoint Tuya Cloud."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
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
    """Set up RainPoint binary sensors."""
    async_add_entities(
        RainPointRunningBinarySensor(entry.runtime_data, zone) for zone in ZONES
    )


class RainPointRunningBinarySensor(RainPointEntity, BinarySensorEntity):
    """Zone running state."""

    _attr_device_class = BinarySensorDeviceClass.RUNNING
    _attr_icon = "mdi:sprinkler-variant"

    def __init__(self, coordinator: RainPointCoordinator, zone: str) -> None:
        super().__init__(
            coordinator,
            f"{zone}_running",
            f"{zone}_running",
        )
        self.zone = zone

    @property
    def is_on(self) -> bool:
        """Return whether the zone is watering."""
        status = self.coordinator.data.status
        codes = ZONE_CODES[self.zone]
        return (
            str(status.get(codes["work_status"], "0")) == "1"
            or status.get(codes["manual_switch"]) is False
        )
