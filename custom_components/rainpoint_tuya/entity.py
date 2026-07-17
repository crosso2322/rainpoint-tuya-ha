"""Base entities for RainPoint Tuya Cloud."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import RainPointCoordinator


class RainPointEntity(CoordinatorEntity[RainPointCoordinator]):
    """Base RainPoint entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: RainPointCoordinator,
        key: str,
        translation_key: str,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.unique_id}_{key}"
        self._attr_translation_key = translation_key

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        status = self.coordinator.data.status
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.entry.unique_id or self.coordinator.entry.entry_id)},
            name=self.coordinator.entry.title,
            manufacturer="RainPoint / Tuya",
            model="Smart 2-Zone Water Timer",
            sw_version=str(status.get("MCU_Version", "Unknown")),
        )
