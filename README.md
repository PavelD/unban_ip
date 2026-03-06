# Unban IP - Home Assistant Custom Integration

A Home Assistant custom component that provides a service to unban IP addresses from the Home Assistant HTTP component's ban list.

## Features

- 🚫 Unban IP addresses from both file (`ip_bans.yaml`) and in-memory ban lists
- 📋 List all banned IP addresses (from file and memory)
- ⚡ Async I/O operations (no blocking calls)
- 📝 Comprehensive logging for troubleshooting
- ✅ Graceful error handling

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/PavelD/hacs-unban_ip`
6. Select category: "Integration"
7. Click "Add"
8. Search for "Unban IP" and install
9. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/unban_ip` directory to your Home Assistant's `custom_components` folder
2. Restart Home Assistant

## Configuration

Add the following to your `configuration.yaml`:

```yaml
unban_ip:
```

After adding this line, restart Home Assistant to load the integration.

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
3. (Optional) Enable debug mode to see detailed information:

```yaml
debug: true
```

4. Click **Call Service**
5. View the response in the "Response" section

#### Response Format

**Default Mode** (simple list):
```yaml
ips:
  - "10.0.0.5"
  - "192.168.1.25"
  - "192.168.2.26"
count: 3
```

**Debug Mode** (detailed breakdown):
```yaml
ips:
  - "10.0.0.5"
  - "192.168.1.25"
  - "192.168.2.26"
count: 3
file_ips:
  - "192.168.1.25"
  - "192.168.2.26"
memory_ips:
  - "10.0.0.5"
  - "192.168.1.25"
```

The `ips` list is automatically deduplicated and sorted. Debug mode shows which IPs come from the file vs in-memory ban lists.

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
        data:
          debug: true
        response_variable: ban_info
      - service: persistent_notification.create
        data:
          title: "Banned IPs Report"
          message: >
            Total: {{ ban_info.count }}
            File: {{ ban_info.file_ips | length }}
            Memory: {{ ban_info.memory_ips | length }}
```

## How It Works

### Unban Service

The integration performs two actions when unbanning an IP:

1. **File Removal**: Removes the IP address from `ip_bans.yaml` using async I/O operations
2. **In-Memory Removal**: Attempts to remove the IP from Home Assistant's in-memory ban list (if accessible)

### List Banned Service

The list service:

1. **Reads from File**: Asynchronously reads `ip_bans.yaml` to get banned IPs
2. **Reads from Memory**: Attempts to access Home Assistant's in-memory ban list
3. **Merges & Deduplicates**: Combines both sources, removes duplicates, and sorts the result
4. **Returns Response**: Provides the data in a structured format for use in automations

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
- In-memory ban list removal
- Integration reload
- List banned IPs in default and debug modes
- IP deduplication across file and memory sources
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

- **Issues**: [GitHub Issues](https://github.com/PavelD/hacs-unban_ip/issues)
- **Discussions**: [GitHub Discussions](https://github.com/PavelD/hacs-unban_ip/discussions)

## Changelog

### Version 1.1.0
- Added `unban_ip.list_banned` service to list all banned IPs
- Support for debug mode to show detailed IP source information (file vs memory)
- Service responses with structured data for use in automations
- Enhanced UI with friendly service names

### Version 1.0.0
- Initial release
- Support for unbanning IPs from file and memory
- Async I/O operations (no blocking calls)
- Comprehensive error handling and logging
- Clean, simple service interface: `unban_ip.execute`
