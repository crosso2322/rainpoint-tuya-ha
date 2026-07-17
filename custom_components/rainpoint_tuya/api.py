"""Synchronous TinyTuya API wrapper."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
import tinytuya

class RainPointApiError(Exception): pass
class RainPointAuthenticationError(RainPointApiError): pass
class RainPointConnectionError(RainPointApiError): pass

@dataclass(slots=True, frozen=True)
class RainPointCredentials:
    api_region: str
    api_key: str
    api_secret: str
    api_device_id: str
    device_id: str

class RainPointCloudApi:
    """TinyTuya wrapper; public methods must run in an HA executor."""
    def __init__(self, credentials: RainPointCredentials) -> None:
        self.credentials = credentials
        self._cloud: tinytuya.Cloud | None = None

    def _get_cloud(self) -> tinytuya.Cloud:
        if self._cloud is None:
            self._cloud = tinytuya.Cloud(apiRegion=self.credentials.api_region, apiKey=self.credentials.api_key, apiSecret=self.credentials.api_secret, apiDeviceID=self.credentials.api_device_id)
        return self._cloud

    @staticmethod
    def _raise_for_error(response: Any) -> None:
        if not isinstance(response, dict):
            raise RainPointConnectionError(f"Unexpected Tuya response: {response!r}")
        if response.get("success") is True:
            return
        code = response.get("code")
        msg = str(response.get("msg", "Unknown Tuya Cloud error"))
        lower = msg.lower()
        if code in {1010,1011,1012,1013,1014,1106,1107,28841002,28841101} or any(x in lower for x in ("permission","token","authorization")):
            raise RainPointAuthenticationError(f"{code}: {msg}")
        raise RainPointConnectionError(f"{code}: {msg}")

    def get_status(self) -> dict[str, Any]:
        try:
            response = self._get_cloud().getstatus(self.credentials.device_id)
        except Exception as err:
            raise RainPointConnectionError(f"TinyTuya status request failed: {err}") from err
        self._raise_for_error(response)
        result = response.get("result", [])
        if not isinstance(result, list):
            raise RainPointConnectionError("Tuya status result is not a list")
        return {item["code"]: item.get("value") for item in result if isinstance(item, dict) and "code" in item}

    def send_commands(self, commands: list[dict[str, Any]]) -> None:
        try:
            response = self._get_cloud().sendcommand(self.credentials.device_id, {"commands": commands})
        except Exception as err:
            raise RainPointConnectionError(f"TinyTuya command request failed: {err}") from err
        self._raise_for_error(response)

    def start_zone(self, timer_code: str, switch_code: str, minutes: int) -> None:
        self.send_commands([{"code": timer_code, "value": int(minutes)}, {"code": switch_code, "value": False}])

    def stop_zone(self, switch_code: str) -> None:
        self.send_commands([{"code": switch_code, "value": True}])
