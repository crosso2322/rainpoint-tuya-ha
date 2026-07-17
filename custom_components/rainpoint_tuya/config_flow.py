"""Config flow for RainPoint Tuya Cloud."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
)

from .api import (
    RainPointApiError,
    RainPointAuthenticationError,
    RainPointCloudApi,
    RainPointCredentials,
)
from .const import (
    CONF_API_DEVICE_ID,
    CONF_API_KEY,
    CONF_API_REGION,
    CONF_API_SECRET,
    CONF_DEVICE_ID,
    CONF_LEFT_DURATION,
    CONF_LEFT_GPM,
    CONF_POLL_INTERVAL,
    CONF_RIGHT_DURATION,
    CONF_RIGHT_GPM,
    DEFAULT_DURATION,
    DEFAULT_GPM,
    DEFAULT_NAME,
    DEFAULT_POLL_INTERVAL,
    DOMAIN,
    MAX_POLL_INTERVAL,
    MIN_POLL_INTERVAL,
)

REGIONS = ["us", "us-e", "eu", "eu-w", "in", "cn"]


def _user_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(
                CONF_NAME, default=defaults.get(CONF_NAME, DEFAULT_NAME)
            ): str,
            vol.Required(
                CONF_API_REGION,
                default=defaults.get(CONF_API_REGION, "us"),
            ): SelectSelector(
                SelectSelectorConfig(options=REGIONS, translation_key="api_region")
            ),
            vol.Required(
                CONF_API_KEY, default=defaults.get(CONF_API_KEY, "")
            ): str,
            vol.Required(
                CONF_API_SECRET, default=defaults.get(CONF_API_SECRET, "")
            ): str,
            vol.Required(
                CONF_API_DEVICE_ID,
                default=defaults.get(CONF_API_DEVICE_ID, ""),
            ): str,
            vol.Required(
                CONF_DEVICE_ID, default=defaults.get(CONF_DEVICE_ID, "")
            ): str,
        }
    )


def _options_schema(options: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(
                CONF_POLL_INTERVAL,
                default=options.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL),
            ): NumberSelector(
                NumberSelectorConfig(
                    min=MIN_POLL_INTERVAL,
                    max=MAX_POLL_INTERVAL,
                    step=1,
                    mode=NumberSelectorMode.BOX,
                    unit_of_measurement="s",
                )
            ),
            vol.Required(
                CONF_LEFT_DURATION,
                default=options.get(CONF_LEFT_DURATION, DEFAULT_DURATION),
            ): NumberSelector(
                NumberSelectorConfig(
                    min=1,
                    max=60,
                    step=1,
                    mode=NumberSelectorMode.SLIDER,
                    unit_of_measurement="min",
                )
            ),
            vol.Required(
                CONF_RIGHT_DURATION,
                default=options.get(CONF_RIGHT_DURATION, DEFAULT_DURATION),
            ): NumberSelector(
                NumberSelectorConfig(
                    min=1,
                    max=60,
                    step=1,
                    mode=NumberSelectorMode.SLIDER,
                    unit_of_measurement="min",
                )
            ),
            vol.Required(
                CONF_LEFT_GPM,
                default=options.get(CONF_LEFT_GPM, DEFAULT_GPM),
            ): NumberSelector(
                NumberSelectorConfig(
                    min=0,
                    max=50,
                    step=0.01,
                    mode=NumberSelectorMode.BOX,
                    unit_of_measurement="gal/min",
                )
            ),
            vol.Required(
                CONF_RIGHT_GPM,
                default=options.get(CONF_RIGHT_GPM, DEFAULT_GPM),
            ): NumberSelector(
                NumberSelectorConfig(
                    min=0,
                    max=50,
                    step=0.01,
                    mode=NumberSelectorMode.BOX,
                    unit_of_measurement="gal/min",
                )
            ),
        }
    )


class RainPointConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Handle initial setup."""
        errors: dict[str, str] = {}

        if user_input is not None:
            device_id = user_input[CONF_DEVICE_ID].strip()
            await self.async_set_unique_id(device_id)
            self._abort_if_unique_id_configured()

            credentials = RainPointCredentials(
                api_region=user_input[CONF_API_REGION],
                api_key=user_input[CONF_API_KEY].strip(),
                api_secret=user_input[CONF_API_SECRET].strip(),
                api_device_id=user_input[CONF_API_DEVICE_ID].strip(),
                device_id=device_id,
            )
            api = RainPointCloudApi(credentials)

            try:
                status = await self.hass.async_add_executor_job(api.get_status)
                required = {
                    "LeftManualSwitch",
                    "LeftManualTimer",
                    "LeftWorkStatus",
                    "RightManualSwitch",
                    "RightManualTimer",
                    "RightWorkStatus",
                }
                if not required.issubset(status):
                    errors["base"] = "unsupported_device"
                else:
                    name = user_input.pop(CONF_NAME)
                    return self.async_create_entry(title=name, data=user_input)
            except RainPointAuthenticationError:
                errors["base"] = "invalid_auth"
            except RainPointApiError:
                errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=_user_schema(user_input),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> RainPointOptionsFlow:
        """Create the options flow."""
        return RainPointOptionsFlow(config_entry)


class RainPointOptionsFlow(config_entries.OptionsFlow):
    """Handle RainPoint options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Manage options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=_options_schema(dict(self.config_entry.options)),
        )
