"""Synchronous TinyTuya API wrapper."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import tinytuya


class RainPointApiError(Exception):
    """Base RainPoint API exception."""


class RainPointAuthenticationError(RainPointApiError):
    """Authentication or authorization failure."""


class RainPointConnectionError(RainPointApiError):
    """Cloud communication failure."""


@dataclass(slots=True)
class RainPointCredentials:
    """Tuya Cloud credentials."""

    api_region: str
    api_key: str
    api_secret: str
    api_device_id: str
    device_id: str


class RainPointCloudApi:
    """Thin wrapper around TinyTuya's synchronous Cloud API."""

    def __init__(self, credentials: RainPointCredentials) -> None:
        self.credentials = credentials
        self._cloud = tinytuya.Cloud(
            apiRegion=credentials.api_region,
            apiKey=credentials.api_key,
            apiSecret=credentials.api_secret,
            apiDeviceID=credentials.api_device_id,
        )

    @staticmethod
    def _raise_for_error(response: Any) -> None:
        if not isinstance(response, dict):
            raise RainPointConnectionError(f"Unexpected Tuya response: {response!r}")

        if response.get("success") is True:
            return

        code = response.get("code")
        message = response.get("msg", "Unknown Tuya Cloud error")

        auth_codes = {
            1010, 1011, 1012, 1013, 1014, 1106, 1107, 28841002, 28841101
        }
        if code in auth_codes or "permission" in str(message).lower():
            raise RainPointAuthenticationError(f"{code}: {message}")

        raise RainPointConnectionError(f"{code}: {message}")

    def get_status(self) -> dict[str, Any]:
        """Return device status keyed by Tuya code."""
        response = self._cloud.getstatus(self.credentials.device_id)
        self._raise_for_error(response)
        result = response.get("result", [])
        if not isinstance(result, list):
            raise RainPointConnectionError("Tuya status result is not a list")

        return {
            item["code"]: item.get("value")
            for item in result
            if isinstance(item, dict) and "code" in item
        }

    def send_commands(self, commands: list[dict[str, Any]]) -> None:
        """Send one or more code-based DP commands."""
        response = self._cloud.sendcommand(
            self.credentials.device_id,
            {"commands": commands},
        )
        self._raise_for_error(response)

    def start_zone(self, timer_code: str, switch_code: str, minutes: int) -> None:
        """Start a zone using the RainPoint inverted switch convention."""
        self.send_commands(
            [
                {"code": timer_code, "value": int(minutes)},
                {"code": switch_code, "value": False},
            ]
        )

    def stop_zone(self, switch_code: str) -> None:
        """Stop a zone using the RainPoint inverted switch convention."""
        self.send_commands([{"code": switch_code, "value": True}])
