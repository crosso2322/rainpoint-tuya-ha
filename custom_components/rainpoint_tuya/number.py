"""Number platform for RainPoint Tuya Cloud."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfTime, UnitOfVolumeFlowRate
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    CONF_LEFT_DURATION,
    CONF_LEFT_GPM,
    CONF_RIGHT_DURATION,
    CONF_RIGHT_GPM,
    DEFAULT_DURATION,
    DEFAULT_GPM,
    ZONE_LEFT,
    ZONE_RIGHT,
)
from .coordinator import RainPointCoordinator
from .entity import RainPointEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry[RainPointCoordinator],
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up RainPoint numbers."""
    coordinator = entry.runtime_data
    async_add_entities(
        [
            RainPointDurationNumber(coordinator, ZONE_LEFT, CONF_LEFT_DURATION),
            RainPointDurationNumber(coordinator, ZONE_RIGHT, CONF_RIGHT_DURATION),
            RainPointGpmNumber(coordinator, ZONE_LEFT, CONF_LEFT_GPM),
            RainPointGpmNumber(coordinator, ZONE_RIGHT, CONF_RIGHT_GPM),
        ]
    )


class RainPointOptionNumber(RainPointEntity, NumberEntity):
    """Base number backed by config entry options."""

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: RainPointCoordinator,
        zone: str,
        option_key: str,
        suffix: str,
    ) -> None:
        super().__init__(
            coordinator,
            f"{zone}_{suffix}",
            f"{zone}_{suffix}",
        )
        self.option_key = option_key

    async def async_set_native_value(self, value: float) -> None:
        """Update an option without requiring manual YAML edits."""
        new_options = dict(self.coordinator.entry.options)
        new_options[self.option_key] = value
        self.coordinator.hass.config_entries.async_update_entry(
            self.coordinator.entry,
            options=new_options,
        )


class RainPointDurationNumber(RainPointOptionNumber):
    """Default watering duration."""

    _attr_native_min_value = 1
    _attr_native_max_value = 60
    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_mode = NumberMode.SLIDER
    _attr_icon = "mdi:timer-outline"

    def __init__(
        self,
        coordinator: RainPointCoordinator,
        zone: str,
        option_key: str,
    ) -> None:
        super().__init__(coordinator, zone, option_key, "duration")

    @property
    def native_value(self) -> float:
        """Return duration."""
        return float(
            self.coordinator.entry.options.get(
                self.option_key,
                DEFAULT_DURATION,
            )
        )


class RainPointGpmNumber(RainPointOptionNumber):
    """Calibrated flow rate."""

    _attr_native_min_value = 0
    _attr_native_max_value = 50
    _attr_native_step = 0.01
    _attr_native_unit_of_measurement = UnitOfVolumeFlowRate.GALLONS_PER_MINUTE
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:waves-arrow-right"

    def __init__(
        self,
        coordinator: RainPointCoordinator,
        zone: str,
        option_key: str,
    ) -> None:
        super().__init__(coordinator, zone, option_key, "flow_rate")

    @property
    def native_value(self) -> float:
        """Return GPM calibration."""
        return float(
            self.coordinator.entry.options.get(
                self.option_key,
                DEFAULT_GPM,
            )
        )
