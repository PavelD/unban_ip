# Changelog

## Version 1.4.1
- **Fix**: Enable YAML configuration support by changing `CONFIG_SCHEMA` from `config_entry_only_config_schema` to `empty_config_schema`
  - Resolves error: "The unban_ip integration does not support YAML configuration"
  - Integration now supports both UI setup and YAML configuration (`unban_ip:` in configuration.yaml)
- **Fix**: Remove invalid lines from services.yaml definition
- Update CI/CD workflows

## Version 1.4.0
- Introduce Hassfest integration
- **BREAKING**: Rename repository from `hacs-unban_ip` to `ha-unban_ip`

## Version 1.3.3
- Add visual and UI metadata improvements

## Version 1.3.2
- Add brand images for better Home Assistant UI integration

## Version 1.3.1
- **Fix**: Delete `ip_bans.yaml` file when last IP is removed instead of leaving empty `{}` content

## Version 1.3.0
- Add support for configuration via UI
- Improve service loading and unloading

## Version 1.2.0
- **BREAKING**: Refactored to use Home Assistant's official ban manager API
- **BREAKING**: Removed `debug` parameter from `list_banned` service
  - Service now returns only `ips` and `count` fields
  - **Migration**: Update automations/templates that use `file_ips` or `memory_ips` to use `ips` instead

## Version 1.1.0
- Added `unban_ip.list_banned` service to list all banned IPs

## Version 1.0.0
- Initial release
- New service `unban_ip.execute`
