"""Sensor platform for RainPoint Tuya Cloud."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfTemperature,
    UnitOfTime,
    UnitOfVolume,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import BATTERY_MAP, ZONE_CODES, ZONES
from .coordinator import RainPointCoordinator
from .entity import RainPointEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry[RainPointCoordinator],
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up RainPoint sensors."""
    coordinator = entry.runtime_data
    entities: list[SensorEntity] = [RainPointBatterySensor(coordinator)]
    for zone in ZONES:
        entities.extend(
            [
                RainPointCycleRuntimeSensor(coordinator, zone),
                RainPointTotalRuntimeSensor(coordinator, zone),
                RainPointCycleWaterSensor(coordinator, zone),
                RainPointTotalWaterSensor(coordinator, zone),
                RainPointReportedFlowSensor(coordinator, zone),
                RainPointTemperatureSensor(coordinator, zone),
                RainPointMoistureSensor(coordinator, zone),
            ]
        )
    async_add_entities(entities)


class RainPointBatterySensor(RainPointEntity, SensorEntity):
    """Battery level mapped from RainPoint's four-state enum."""

    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:battery"

    def __init__(self, coordinator: RainPointCoordinator) -> None:
        super().__init__(coordinator, "battery", "battery")

    @property
    def native_value(self) -> int | None:
        """Return approximate battery percentage."""
        value = self.coordinator.data.status.get("BatteryCapacity")
        return BATTERY_MAP.get(str(value))


class RainPointZoneSensor(RainPointEntity, SensorEntity):
    """Base zone sensor."""

    def __init__(
        self,
        coordinator: RainPointCoordinator,
        zone: str,
        suffix: str,
    ) -> None:
        super().__init__(
            coordinator,
            f"{zone}_{suffix}",
            f"{zone}_{suffix}",
        )
        self.zone = zone


class RainPointCycleRuntimeSensor(RainPointZoneSensor):
    """Current/last cycle runtime."""

    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:timer-play-outline"

    def __init__(self, coordinator: RainPointCoordinator, zone: str) -> None:
        super().__init__(coordinator, zone, "cycle_runtime")

    @property
    def native_value(self) -> int:
        return round(self.coordinator.data.zones[self.zone].cycle_seconds)


class RainPointTotalRuntimeSensor(RainPointZoneSensor):
    """Cumulative runtime."""

    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:timer-sand-complete"

    def __init__(self, coordinator: RainPointCoordinator, zone: str) -> None:
        super().__init__(coordinator, zone, "total_runtime")

    @property
    def native_value(self) -> int:
        return round(self.coordinator.data.zones[self.zone].total_seconds)


class RainPointCycleWaterSensor(RainPointZoneSensor):
    """Estimated water used in current/last cycle."""

    _attr_native_unit_of_measurement = UnitOfVolume.GALLONS
    _attr_device_class = SensorDeviceClass.WATER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:water"

    def __init__(self, coordinator: RainPointCoordinator, zone: str) -> None:
        super().__init__(coordinator, zone, "cycle_water")

    @property
    def native_value(self) -> float:
        return round(self.coordinator.data.zones[self.zone].cycle_gallons, 3)


class RainPointTotalWaterSensor(RainPointZoneSensor):
    """Cumulative estimated water use."""

    _attr_native_unit_of_measurement = UnitOfVolume.GALLONS
    _attr_device_class = SensorDeviceClass.WATER
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:water-circle"

    def __init__(self, coordinator: RainPointCoordinator, zone: str) -> None:
        super().__init__(coordinator, zone, "total_water")

    @property
    def native_value(self) -> float:
        return round(self.coordinator.data.zones[self.zone].total_gallons, 3)


class RainPointReportedFlowSensor(RainPointZoneSensor):
    """Vendor-reported flow value, currently uncalibrated."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:waves"

    def __init__(self, coordinator: RainPointCoordinator, zone: str) -> None:
        super().__init__(coordinator, zone, "reported_flow")

    @property
    def native_value(self) -> float | None:
        value = self.coordinator.data.status.get(ZONE_CODES[self.zone]["flow"])
        try:
            return float(value)
        except (TypeError, ValueError):
            return None


class RainPointTemperatureSensor(RainPointZoneSensor):
    """Optional external sensor temperature."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:thermometer"

    def __init__(self, coordinator: RainPointCoordinator, zone: str) -> None:
        super().__init__(coordinator, zone, "temperature")

    @property
    def native_value(self) -> float | None:
        value = self.coordinator.data.status.get(
            ZONE_CODES[self.zone]["temperature"]
        )
        try:
            return float(value)
        except (TypeError, ValueError):
            return None


class RainPointMoistureSensor(RainPointZoneSensor):
    """Optional external sensor moisture."""

    _attr_device_class = SensorDeviceClass.MOISTURE
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:water-percent"

    def __init__(self, coordinator: RainPointCoordinator, zone: str) -> None:
        super().__init__(coordinator, zone, "moisture")

    @property
    def native_value(self) -> float | None:
        value = self.coordinator.data.status.get(
            ZONE_CODES[self.zone]["moisture"]
        )
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
