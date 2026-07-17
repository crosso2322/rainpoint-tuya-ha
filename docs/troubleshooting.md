# Troubleshooting

Enable only integration logging:

```yaml
logger:
  logs:
    custom_components.rainpoint_tuya: debug
```

Do not leave `tinytuya: debug` enabled; it may expose authentication headers and access tokens. Download redacted diagnostics from the integration menu before opening an issue.
