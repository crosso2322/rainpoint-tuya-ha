# RainPoint Tuya Cloud for Home Assistant

A HACS-compatible custom integration for the Tuya-based RainPoint Smart 2-Zone Water Timer.

## v1.0 features

- UI setup, reauthentication, and reconfiguration
- Left and right irrigation controls
- Per-zone watering duration
- Correct inverted RainPoint valve logic
- Running-state, battery, runtime, and estimated-water entities
- Persistent cumulative runtime and estimated water usage
- Optional probe entities unavailable until probes are paired
- Vendor flow entities unavailable until nonzero flow is reported
- Redacted diagnostics and System Health
- HACS/Hassfest validation and automated GitHub releases

## Upgrade from v0.1.0

1. Back up Home Assistant.
2. Replace `/config/custom_components/rainpoint_tuya` with the v1.0.0 folder.
3. Restart Home Assistant.
4. Existing config entries and entity IDs should remain because the integration domain and entity unique IDs are unchanged.
5. Review the duration and GPM settings under the integration configuration.

## HACS custom repository

Add `https://github.com/cross02322/rainpoint-tuya-ha` as a HACS custom repository of type **Integration**.

## Confirmed protocol

- Start left: `LeftManualTimer=<minutes>` and `LeftManualSwitch=false`
- Stop left: `LeftManualSwitch=true`
- Start right: `RightManualTimer=<minutes>` and `RightManualSwitch=false`
- Stop right: `RightManualSwitch=true`
- Running: work status equals `"1"`

## Calibration

For a 5-gallon bucket: `GPM = 300 / fill_seconds`.

Estimated usage is based on observed valve runtime multiplied by the configured GPM.

## Security

Download diagnostics from Home Assistant before filing an issue. Credentials and device IDs are redacted. Do not enable TinyTuya debug logging when sharing logs because it may include access tokens or authentication headers.
