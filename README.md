# Unban IP - Home Assistant Custom Integration

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
![GitHub release](https://img.shields.io/github/v/release/PavelD/unban_ip)
![GitHub license](https://img.shields.io/github/license/PavelD/unban_ip)

A Home Assistant custom integration that allows removing banned IP addresses from the HTTP ban list **without restarting Home Assistant**.

[![Open your Home Assistant instance and open this repository in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=PavelD&repository=unban_ip)

## Features

- 🚫 Unban IP addresses from both file (`ip_bans.yaml`) and in-memory ban lists
- 📋 List all banned IP addresses
- ⚡ Async I/O operations (no blocking calls)
- 📝 Comprehensive logging for troubleshooting
- ✅ Graceful error handling

## Compatibility

Tested with recent versions of Home Assistant.

The integration relies on the internal HTTP ban manager used by the Home Assistant HTTP component.

## Installation

### HACS (Recommended)

Click the button below to open this repository directly in HACS:

[![Open your Home Assistant instance and open this repository in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=PavelD&repository=unban_ip)

Or add manually:

1. Open HACS
2. Go to **Integrations**
3. Click **⋮ → Custom repositories**
5. Add this repository URL: `https://github.com/PavelD/unban_ip`
6. Select category: "Integration"
7. Click "Add"
8. Search for "Unban IP" and install
9. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/unban_ip` directory to your Home Assistant's `custom_components` folder
2. Restart Home Assistant

## Configuration

Works with both YAML import and UI setup.

### Via UI

Go to **Settings → Devices & Services → Add Integration → Unban IP**

The integration will automatically register and the services will be available

### Via YAML (Legacy)

Add the following to your `configuration.yaml`:

```yaml
unban_ip:
```

After adding this line, restart Home Assistant to load the integration.

<img src="https://raw.githubusercontent.com/PavelD/unban_ip/main/images/integration.png" alt="Unban IP Integration" align="center"/>

## Usage

### Service Call

The integration provides a service called `unban_ip.execute` that can be called to remove an IP address from the ban list.

#### Via Developer Tools UI

1. Go to **Developer Tools** → **Services**
2. Select service: `unban_ip.execute`
3. Enter the IP address in the service data:

```yaml
ip_address: "192.168.1.25"
```

4. Click **Call Service**

#### Via Automation

```yaml
automation:
  - alias: "Unban IP on button press"
    trigger:
      - platform: state
        entity_id: input_button.unban_ip_button
    action:
      - service: unban_ip.execute
        data:
          ip_address: "192.168.1.25"
```

#### Via Script

```yaml
script:
  unban_my_ip:
    alias: "Unban My IP"
    sequence:
      - service: unban_ip.execute
        data:
          ip_address: "192.168.1.25"
```

### List Banned IPs

The integration also provides a service called `unban_ip.list_banned` that returns all currently banned IP addresses.

#### Via Developer Tools UI

1. Go to **Developer Tools** → **Services**
2. Select service: `unban_ip.list_banned`
3. Click **Call Service**
4. View the response in the "Response" section

#### Response Format

```yaml
ips:
  - "10.0.0.5"
  - "192.168.1.25"
  - "192.168.2.26"
count: 3
```

The `ips` list contains all currently banned IP addresses.

#### Via Automation

```yaml
automation:
  - alias: "Check banned IPs daily"
    trigger:
      - platform: time
        at: "09:00:00"
    action:
      - service: unban_ip.list_banned
        response_variable: banned_data
      - service: notify.notify
        data:
          message: "Currently {{ banned_data.count }} IPs are banned"
```

#### Via Script

```yaml
script:
  check_banned_ips:
    alias: "Check Banned IPs"
    sequence:
      - service: unban_ip.list_banned
        response_variable: ban_info
      - service: persistent_notification.create
        data:
          title: "Banned IPs Report"
          message: "Currently {{ ban_info.count }} IPs are banned"
```

## How It Works

### Unban Service

The integration uses Home Assistant's official ban manager API:

1. **File Removal**: Removes the IP address from `ip_bans.yaml` using async I/O operations
2. **Reload Ban Manager**: Calls `ban_manager.async_load()` to reload the ban list from file
3. **Automatic Sync**: The ban manager automatically syncs memory with the file

This ensures the file and in-memory ban list are always in sync.

### List Banned Service

The list service reads directly from Home Assistant's ban manager:

1. **Reads from Ban Manager**: Accesses the official ban manager to get all banned IPs
2. **Returns Sorted List**: Provides a sorted list of all currently banned IP addresses
3. **Structured Response**: Returns data in a format suitable for use in automations

Since we use `async_load()` when unbanning, the ban manager is always the single source of truth.

### Supported YAML Format

The integration works with Home Assistant's native `ip_bans.yaml` format:

```yaml
192.168.1.103:
  banned_at: '2025-12-07T19:50:53.118232+00:00'
192.168.1.14:
  banned_at: '2025-12-30T08:13:06.372591+00:00'
192.168.1.135:
  banned_at: '2025-12-31T08:14:01.737210+00:00'
```

This is a dictionary format where each IP address is a key with associated metadata.

## Logging

The integration logs all actions. To see detailed logs, add this to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.unban_ip: debug
```

### Log Messages

- **Info**: IP unban attempts, success/failure notifications
- **Debug**: Detailed operation information
- **Warning**: Non-critical issues (e.g., file not found, invalid entries)
- **Error**: Critical errors (e.g., file read/write failures)

## Troubleshooting

### Integration not loading

**Symptom**: Service `unban_ip.execute` is not available

**Solution**: 
1. Ensure `unban_ip:` is added to `configuration.yaml`
2. Restart Home Assistant
3. Check logs for errors: **Settings** → **System** → **Logs**

### IP not being unbanned

**Symptom**: Service call completes but IP remains banned

**Possible causes:**
1. IP address format mismatch (check `ip_bans.yaml` format)
2. File permissions issue
3. In-memory ban list not accessible

**Solution**:
1. Enable debug logging (see above)
2. Call the service again
3. Check logs for specific error messages
4. Verify IP address in `ip_bans.yaml` exactly matches the one you're trying to unban

### File not found warning

**Symptom**: Log shows `ip_bans.yaml not found`

**Explanation**: This is normal if no IPs have been banned yet. The file is created automatically by Home Assistant when the first IP is banned.

## Development

### Running Tests

```bash
# Install dependencies
pip install -r requirements_tests.txt

# Run tests
pytest tests/
```

### Test Coverage

The test suite includes:
- Service registration/unregistration (both `execute` and `list_banned`)
- Dictionary format IP removal (Home Assistant native format)
- IP not found scenarios
- Missing file handling
- Ban manager reload verification
- Integration reload
- List banned IPs from ban manager
- Empty results handling

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add/update tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/PavelD/unban_ip/issues)
- **Discussions**: [GitHub Discussions](https://github.com/PavelD/unban_ip/discussions)

## Changelog

### Version 1.4.0
- Intrduce Hassfest and fix reported issues
- **BREAKING**: Rename repository from hacs-unban_ip to unban_ip

### Version 1.3.3
- Add visual and UI metadata improvements to the Unban IP integration

### Version 1.3.2
- Add brand images (`icon.png`, `icon@2x.png`) for better Home Assistant UI integration
- Improved visual identity in HACS and Home Assistant integrations page

### Version 1.3.1
- **Fix**: Delete `ip_bans.yaml` file when last IP is removed instead of leaving empty `{}` content
- Prevents issues with adding new IPs after all bans are removed
- Improved code quality: simplified nested functions, better test isolation

### Version 1.3.0
- Add support of configuration via UI
- Keep YAML configuration option
- Improve services load and unload

### Version 1.2.0
- **BREAKING**: Refactored to use Home Assistant's official ban manager API
- Uses official `KEY_BAN_MANAGER` and `IP_BANS_FILE` constants from Home Assistant
- Calls `ban_manager.async_load()` after file changes for automatic sync
- **BREAKING**: Removed `debug` parameter from `list_banned` service
  - The service now returns only `ips` and `count` fields
  - Removed `file_ips` and `memory_ips` fields (no longer relevant with single source of truth)
  - **Migration**: Update automations/templates that use `file_ips` or `memory_ips` to use `ips` instead
- Simplified `list_banned` service (reads directly from ban manager)
- Added safe attribute access for HTTP component (handles edge cases where HTTP isn't loaded)
- More reliable and future-proof implementation

### Version 1.1.0
- Added `unban_ip.list_banned` service to list all banned IPs
- Service responses with structured data for use in automations
- Enhanced UI with friendly service names

### Version 1.0.0
- Initial release
- Support for unbanning IPs from file and memory
- Async I/O operations (no blocking calls)
- Comprehensive error handling and logging
- Clean, simple service interface: `unban_ip.execute`
