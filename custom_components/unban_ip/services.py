"""Define services for Unban IP integration."""

import logging
import os
import yaml
from homeassistant.core import HomeAssistant, ServiceCall

from .const import DOMAIN, IP_BANS_FILE

_LOGGER = logging.getLogger(__name__)


async def async_setup_services(hass: HomeAssistant):
    """Register Unban IP services."""

    async def handle_list_banned(call: ServiceCall):
        """Handle list_banned service call."""
        debug = call.data.get("debug", False)
        _LOGGER.info(f"Listing banned IPs (debug={debug})")

        file_ips = []
        memory_ips = []

        # Path to ip_bans.yaml
        ban_file_path = hass.config.path(IP_BANS_FILE)

        # Read IPs from file
        file_exists = await hass.async_add_executor_job(os.path.exists, ban_file_path)
        if file_exists:
            try:

                def read_bans():
                    with open(ban_file_path, "r") as f:
                        return yaml.safe_load(f) or {}

                bans = await hass.async_add_executor_job(read_bans)

                if isinstance(bans, dict):
                    file_ips = list(bans.keys())
                    _LOGGER.debug(f"Found {len(file_ips)} IPs in {IP_BANS_FILE}")
                else:
                    _LOGGER.warning(f"{IP_BANS_FILE} has invalid format")
            except Exception as e:
                _LOGGER.error(f"Error reading {IP_BANS_FILE}: {e}")
        else:
            _LOGGER.debug(f"{IP_BANS_FILE} not found")

        # Read IPs from memory
        try:
            http_component = hass.data.get("http")
            if http_component and hasattr(http_component, "_ban"):
                ban_obj = http_component._ban
                if hasattr(ban_obj, "banned"):
                    memory_ips = list(getattr(ban_obj, "banned", {}).keys())
                    _LOGGER.debug(f"Found {len(memory_ips)} IPs in memory ban list")
        except Exception as e:
            _LOGGER.warning(f"Could not read in-memory bans: {e}")

        # Merge and deduplicate IPs
        all_ips = sorted(set(file_ips + memory_ips))

        _LOGGER.info(f"Total banned IPs: {len(all_ips)}")

        # Build response
        response = {"ips": all_ips, "count": len(all_ips)}

        if debug:
            response["file_ips"] = sorted(file_ips)
            response["memory_ips"] = sorted(memory_ips)

        return response

    async def handle_unban_ip(call: ServiceCall):
        """Handle unban_ip service call."""
        ip_to_unban = call.data.get("ip_address")
        _LOGGER.info(f"Attempting to unban IP: {ip_to_unban}")

        # Path to ip_bans.yaml
        ban_file_path = hass.config.path(IP_BANS_FILE)

        # Check if file exists (async)
        file_exists = await hass.async_add_executor_job(os.path.exists, ban_file_path)
        if not file_exists:
            _LOGGER.warning(f"{IP_BANS_FILE} not found, nothing to unban.")
            return

        # Load bans (async file read)
        try:

            def read_bans():
                with open(ban_file_path, "r") as f:
                    return yaml.safe_load(f) or {}

            bans = await hass.async_add_executor_job(read_bans)
        except Exception as e:
            _LOGGER.error(f"Error reading {IP_BANS_FILE}: {e}")
            return

        # Home Assistant uses dictionary format: {"IP": {"banned_at": "..."}}
        if not isinstance(bans, dict):
            _LOGGER.error(
                f"{IP_BANS_FILE} has invalid format (expected dict, got {type(bans).__name__})"
            )
            return

        # Remove IP from ban dictionary
        if ip_to_unban in bans:
            del bans[ip_to_unban]
            _LOGGER.info(f"Found IP {ip_to_unban} in {IP_BANS_FILE}, removing...")

            # Write updated bans back to file (async)
            try:

                def write_bans():
                    with open(ban_file_path, "w") as f:
                        yaml.safe_dump(bans, f, default_flow_style=False)

                await hass.async_add_executor_job(write_bans)
                _LOGGER.info(f"IP {ip_to_unban} removed from {IP_BANS_FILE}.")
            except Exception as e:
                _LOGGER.error(f"Error writing {IP_BANS_FILE}: {e}")
                return
        else:
            _LOGGER.info(f"IP {ip_to_unban} not found in {IP_BANS_FILE}.")

        # In-memory unban (if supported by HA version)
        try:
            http_component = hass.data.get("http")
            if http_component and hasattr(http_component, "_ban"):
                ban_obj = http_component._ban
                if ip_to_unban in getattr(ban_obj, "banned", {}):
                    del ban_obj.banned[ip_to_unban]
                    _LOGGER.info(f"IP {ip_to_unban} removed from in-memory ban list.")
        except Exception as e:
            _LOGGER.warning(f"Could not remove IP from in-memory bans: {e}")

    # Register the services
    hass.services.async_register(DOMAIN, "execute", handle_unban_ip)
    _LOGGER.debug("Service 'execute' registered.")

    hass.services.async_register(
        DOMAIN, "list_banned", handle_list_banned, supports_response="only"
    )
    _LOGGER.debug("Service 'list_banned' registered.")


async def async_unload_services(hass: HomeAssistant):
    """Unregister all Unban IP services."""
    if hass.services.has_service(DOMAIN, "execute"):
        hass.services.async_remove(DOMAIN, "execute")
        _LOGGER.debug("Service 'execute' unregistered.")

    if hass.services.has_service(DOMAIN, "list_banned"):
        hass.services.async_remove(DOMAIN, "list_banned")
        _LOGGER.debug("Service 'list_banned' unregistered.")
