"""Config flow for RainPoint Tuya Cloud."""
from __future__ import annotations
import logging
from typing import Any
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import NumberSelector, NumberSelectorConfig, NumberSelectorMode, SelectSelector, SelectSelectorConfig
from .api import RainPointApiError, RainPointAuthenticationError, RainPointCloudApi, RainPointCredentials
from .const import CONF_API_DEVICE_ID, CONF_API_KEY, CONF_API_REGION, CONF_API_SECRET, CONF_DEVICE_ID, CONF_LEFT_DURATION, CONF_LEFT_GPM, CONF_POLL_INTERVAL, CONF_RIGHT_DURATION, CONF_RIGHT_GPM, DEFAULT_DURATION, DEFAULT_GPM, DEFAULT_NAME, DEFAULT_POLL_INTERVAL, DOMAIN, MAX_POLL_INTERVAL, MIN_POLL_INTERVAL

_LOGGER = logging.getLogger(__name__)
REGIONS = ["us", "us-e", "eu", "eu-w", "in", "cn"]
REQUIRED_CODES = {"LeftManualSwitch","LeftManualTimer","LeftWorkStatus","RightManualSwitch","RightManualTimer","RightWorkStatus"}

def connection_schema(defaults: dict[str, Any] | None = None, *, include_name: bool) -> vol.Schema:
    defaults = defaults or {}
    schema: dict[Any, Any] = {}
    if include_name:
        schema[vol.Required(CONF_NAME, default=defaults.get(CONF_NAME, DEFAULT_NAME))] = str
    schema.update({
        vol.Required(CONF_API_REGION, default=defaults.get(CONF_API_REGION, "us")): SelectSelector(SelectSelectorConfig(options=REGIONS, translation_key="api_region")),
        vol.Required(CONF_API_KEY, default=defaults.get(CONF_API_KEY, "")): str,
        vol.Required(CONF_API_SECRET, default=defaults.get(CONF_API_SECRET, "")): str,
        vol.Required(CONF_API_DEVICE_ID, default=defaults.get(CONF_API_DEVICE_ID, "")): str,
        vol.Required(CONF_DEVICE_ID, default=defaults.get(CONF_DEVICE_ID, "")): str,
    })
    return vol.Schema(schema)

def options_schema(options: dict[str, Any]) -> vol.Schema:
    number = lambda minimum, maximum, step, unit, mode=NumberSelectorMode.BOX: NumberSelector(NumberSelectorConfig(min=minimum,max=maximum,step=step,mode=mode,unit_of_measurement=unit))
    return vol.Schema({
        vol.Required(CONF_POLL_INTERVAL, default=options.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL)): number(MIN_POLL_INTERVAL, MAX_POLL_INTERVAL, 1, "s"),
        vol.Required(CONF_LEFT_DURATION, default=options.get(CONF_LEFT_DURATION, DEFAULT_DURATION)): number(1,60,1,"min",NumberSelectorMode.SLIDER),
        vol.Required(CONF_RIGHT_DURATION, default=options.get(CONF_RIGHT_DURATION, DEFAULT_DURATION)): number(1,60,1,"min",NumberSelectorMode.SLIDER),
        vol.Required(CONF_LEFT_GPM, default=options.get(CONF_LEFT_GPM, DEFAULT_GPM)): number(0,50,0.01,"gal/min"),
        vol.Required(CONF_RIGHT_GPM, default=options.get(CONF_RIGHT_GPM, DEFAULT_GPM)): number(0,50,0.01,"gal/min"),
    })

async def validate(hass, user_input: dict[str, Any]) -> dict[str, Any]:
    creds = RainPointCredentials(str(user_input[CONF_API_REGION]).strip(), str(user_input[CONF_API_KEY]).strip(), str(user_input[CONF_API_SECRET]).strip(), str(user_input[CONF_API_DEVICE_ID]).strip(), str(user_input[CONF_DEVICE_ID]).strip())
    status = await hass.async_add_executor_job(RainPointCloudApi(creds).get_status)
    missing = REQUIRED_CODES.difference(status)
    if missing:
        raise ValueError(f"Missing required codes: {sorted(missing)}")
    return {CONF_API_REGION: creds.api_region, CONF_API_KEY: creds.api_key, CONF_API_SECRET: creds.api_secret, CONF_API_DEVICE_ID: creds.api_device_id, CONF_DEVICE_ID: creds.device_id}

class RainPointConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors = {}
        if user_input is not None:
            try:
                data = await validate(self.hass, user_input)
                await self.async_set_unique_id(data[CONF_DEVICE_ID])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=str(user_input[CONF_NAME]).strip() or DEFAULT_NAME, data=data)
            except RainPointAuthenticationError: errors["base"] = "invalid_auth"
            except RainPointApiError: errors["base"] = "cannot_connect"
            except ValueError: errors["base"] = "unsupported_device"
            except Exception:
                _LOGGER.exception("Unexpected RainPoint validation error")
                errors["base"] = "unknown"
        return self.async_show_form(step_id="user", data_schema=connection_schema(user_input, include_name=True), errors=errors)

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> FlowResult:
        self._entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors = {}
        if user_input is not None:
            try:
                data = await validate(self.hass, user_input)
                self.hass.config_entries.async_update_entry(self._entry, data=data)
                await self.hass.config_entries.async_reload(self._entry.entry_id)
                return self.async_abort(reason="reauth_successful")
            except RainPointAuthenticationError: errors["base"] = "invalid_auth"
            except RainPointApiError: errors["base"] = "cannot_connect"
            except ValueError: errors["base"] = "unsupported_device"
            except Exception:
                _LOGGER.exception("Unexpected RainPoint reauth error")
                errors["base"] = "unknown"
        return self.async_show_form(step_id="reauth_confirm", data_schema=connection_schema(user_input or dict(self._entry.data), include_name=False), errors=errors)

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        errors = {}
        if user_input is not None:
            try:
                data = await validate(self.hass, user_input)
                self.hass.config_entries.async_update_entry(entry, data=data, unique_id=data[CONF_DEVICE_ID])
                await self.hass.config_entries.async_reload(entry.entry_id)
                return self.async_abort(reason="reconfigure_successful")
            except RainPointAuthenticationError: errors["base"] = "invalid_auth"
            except RainPointApiError: errors["base"] = "cannot_connect"
            except ValueError: errors["base"] = "unsupported_device"
            except Exception:
                _LOGGER.exception("Unexpected RainPoint reconfigure error")
                errors["base"] = "unknown"
        return self.async_show_form(step_id="reconfigure", data_schema=connection_schema(user_input or dict(entry.data), include_name=False), errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return RainPointOptionsFlow(config_entry)

class RainPointOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry): self.config_entry = config_entry
    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(step_id="init", data_schema=options_schema(dict(self.config_entry.options)))
