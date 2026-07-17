"""RainPoint Tuya Cloud integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .api import RainPointCloudApi, RainPointCredentials
from .const import (
    CONF_API_DEVICE_ID,
    CONF_API_KEY,
    CONF_API_REGION,
    CONF_API_SECRET,
    CONF_DEVICE_ID,
    PLATFORMS,
)
from .coordinator import RainPointCoordinator

type RainPointConfigEntry = ConfigEntry[RainPointCoordinator]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: RainPointConfigEntry,
) -> bool:
    """Set up RainPoint from a config entry."""
    credentials = RainPointCredentials(
        api_region=entry.data[CONF_API_REGION],
        api_key=entry.data[CONF_API_KEY],
        api_secret=entry.data[CONF_API_SECRET],
        api_device_id=entry.data[CONF_API_DEVICE_ID],
        device_id=entry.data[CONF_DEVICE_ID],
    )
    coordinator = RainPointCoordinator(
        hass,
        entry,
        RainPointCloudApi(credentials),
    )
    await coordinator.async_load_runtime()
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    await hass.config_entries.async_forward_entry_setups(
        entry,
        [Platform(platform) for platform in PLATFORMS],
    )
    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: RainPointConfigEntry,
) -> bool:
    """Unload a config entry."""
    await entry.runtime_data.async_save_runtime()
    return await hass.config_entries.async_unload_platforms(
        entry,
        [Platform(platform) for platform in PLATFORMS],
    )


async def async_reload_entry(
    hass: HomeAssistant,
    entry: RainPointConfigEntry,
) -> None:
    """Reload after options update."""
    await hass.config_entries.async_reload(entry.entry_id)
