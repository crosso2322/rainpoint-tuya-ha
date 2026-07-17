"""Constants for the RainPoint Tuya Cloud integration."""

from datetime import timedelta
from typing import Final

DOMAIN: Final = "rainpoint_tuya"
PLATFORMS: Final = ["switch", "number", "binary_sensor", "sensor"]

CONF_API_REGION: Final = "api_region"
CONF_API_KEY: Final = "api_key"
CONF_API_SECRET: Final = "api_secret"
CONF_API_DEVICE_ID: Final = "api_device_id"
CONF_DEVICE_ID: Final = "device_id"
CONF_POLL_INTERVAL: Final = "poll_interval"
CONF_LEFT_DURATION: Final = "left_duration"
CONF_RIGHT_DURATION: Final = "right_duration"
CONF_LEFT_GPM: Final = "left_gpm"
CONF_RIGHT_GPM: Final = "right_gpm"

DEFAULT_NAME: Final = "RainPoint 2-Zone Timer"
DEFAULT_POLL_INTERVAL: Final = 10
MIN_POLL_INTERVAL: Final = 5
MAX_POLL_INTERVAL: Final = 300
DEFAULT_DURATION: Final = 10
DEFAULT_GPM: Final = 0.0

DEFAULT_SCAN_INTERVAL: Final = timedelta(seconds=DEFAULT_POLL_INTERVAL)

BATTERY_MAP: Final = {
    "0": 10,
    "1": 35,
    "2": 65,
    "3": 100,
}

ZONE_LEFT: Final = "left"
ZONE_RIGHT: Final = "right"
ZONES: Final = (ZONE_LEFT, ZONE_RIGHT)

ZONE_CODES: Final = {
    ZONE_LEFT: {
        "manual_switch": "LeftManualSwitch",
        "manual_timer": "LeftManualTimer",
        "work_status": "LeftWorkStatus",
        "remain_time": "LeftRemainTime",
        "flow": "LeftFlow",
        "flow_count": "LeftFlowCount",
        "temperature": "LeftTemp",
        "moisture": "LeftMoisure",
        "stop": "LeftStopirrigation",
        "next_time": "LeftNextTime",
    },
    ZONE_RIGHT: {
        "manual_switch": "RightManualSwitch",
        "manual_timer": "RightManualTimer",
        "work_status": "RightWorkStatus",
        "remain_time": "RightRemainTime",
        "flow": "RithtFlow",  # Vendor spelling.
        "flow_count": "RightFlowCount",
        "temperature": "RightTemp",
        "moisture": "RightMoisure",
        "stop": "RightStopIrrigation",
        "next_time": "RightNextTime",
    },
}

ATTRIBUTION: Final = "Data provided by the Tuya Cloud API"
