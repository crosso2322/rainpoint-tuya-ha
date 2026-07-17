"""Diagnostics support for RainPoint Tuya Cloud."""
from __future__ import annotations
from typing import Any
from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant
from .const import CONF_API_DEVICE_ID, CONF_API_KEY, CONF_API_SECRET, CONF_DEVICE_ID

TO_REDACT = {CONF_API_KEY, CONF_API_SECRET, CONF_API_DEVICE_ID, CONF_DEVICE_ID}

async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry) -> dict[str, Any]:
    coordinator = entry.runtime_data
    zones = {}
    for zone, runtime in coordinator.data.zones.items():
        zones[zone] = {
            "active": runtime.active,
            "cycle_seconds": runtime.cycle_seconds,
            "total_seconds": runtime.total_seconds,
            "cycle_gallons": runtime.cycle_gallons,
            "total_gallons": runtime.total_gallons,
        }
    return {
        "entry": {"title": entry.title, "data": async_redact_data(dict(entry.data), TO_REDACT), "options": dict(entry.options)},
        "coordinator": {"last_update_success": coordinator.last_update_success, "last_exception": str(coordinator.last_exception) if coordinator.last_exception else None},
        "device_status": dict(coordinator.data.status),
        "runtime": zones,
    }
