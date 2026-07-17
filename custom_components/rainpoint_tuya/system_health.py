"""System health support."""
from homeassistant.components import system_health
from homeassistant.core import HomeAssistant
from .const import DOMAIN

async def async_register(hass: HomeAssistant, register: system_health.SystemHealthRegistration) -> None:
    register.async_register_info(system_health_info)

async def system_health_info(hass: HomeAssistant) -> dict[str, object]:
    return {"configured_devices": len(hass.config_entries.async_entries(DOMAIN)), "cloud_api": "Tuya OpenAPI"}
