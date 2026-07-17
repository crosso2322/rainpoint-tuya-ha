# RainPoint Tuya Cloud for Home Assistant

A HACS-compatible custom integration for the Tuya-based RainPoint Smart 2-Zone Water Timer.

## Confirmed protocol mapping

The timer uses code-based Tuya Cloud commands and inverted valve booleans:

- Start left: `LeftManualTimer=<minutes>` + `LeftManualSwitch=false`
- Stop left: `LeftManualSwitch=true`
- Start right: `RightManualTimer=<minutes>` + `RightManualSwitch=false`
- Stop right: `RightManualSwitch=true`
- Running: `LeftWorkStatus == "1"` / `RightWorkStatus == "1"`
- Idle: work status `"0"`

## Entities

- Left and right irrigation switches
- Left and right default duration controls
- Left and right calibrated gallons-per-minute controls
- Running binary sensors
- Battery sensor
- Current/last cycle runtime
- Cumulative runtime
- Estimated cycle and cumulative water usage
- Raw vendor flow values
- Optional temperature and moisture values

Water use starts at zero until a GPM calibration is entered. Runtime and cumulative estimated usage are persisted in Home Assistant storage.

## Installation now (manual)

1. Download the release ZIP.
2. Copy `custom_components/rainpoint_tuya` into `/config/custom_components/`.
3. Restart Home Assistant.
4. Go to **Settings → Devices & services → Add integration**.
5. Search for **RainPoint Tuya Cloud**.
6. Enter the same Tuya credentials and device IDs used by the working TinyTuya test.

## Installation through HACS after publishing to GitHub

1. Create a public GitHub repository.
2. Upload this repository structure without nesting it inside another folder.
3. Create a GitHub release, starting with `v0.1.0`.
4. In HACS, open **Custom repositories**.
5. Add the repository URL as category **Integration**.
6. Download, restart Home Assistant, then add the integration.

## Tuya fields

- **API region:** Usually `us` for the United States. Use the same value as `tinytuya.json`.
- **Access ID / Secret:** Tuya IoT Cloud project credentials.
- **Cloud authorization device ID:** The `apiDeviceID` value used by TinyTuya.
- **Timer device ID:** The RainPoint sub-device ID successfully used with `cloud.sendcommand()`.

## Calibration later

Fill a known container and calculate:

`GPM = gallons × 60 ÷ fill_seconds`

For a 5-gallon bucket:

`GPM = 300 ÷ fill_seconds`

Enter the result through the integration's configuration page or the GPM number entities.

## Safety

Cloud commands can be delayed. Keep the timer's physical controls available and test with short durations first. The integration polls every 10 seconds by default and supports a minimum of 5 seconds to avoid excessive Tuya Cloud API use.

## Development

The repository includes HACS and Hassfest validation workflows.
