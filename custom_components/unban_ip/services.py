"""Define services for Unban IP integration."""

import logging
import os
import yaml
from homeassistant.core import HomeAssistant, ServiceCall

from .const import DOMAIN, IP_BANS_FILE

_LOGGER = logging.getLogger(__name__)


async def async_setup_services(hass: HomeAssistant):
    """Register Unban IP services."""

    async def handle_unban_ip(call: ServiceCall):
        """Handle unban_ip service call."""
        ip_to_unban = call.data.get("ip_address")
        _LOGGER.info(f"Attempting to unban IP: {ip_to_unban}")

        # Path to ip_bans.yaml
        ban_file_path = hass.config.path(IP_BANS_FILE)
        if not os.path.exists(ban_file_path):
            _LOGGER.warning(f"{IP_BANS_FILE} not found, nothing to unban.")
            return

        # Load bans
        try:
            with open(ban_file_path, "r") as f:
                bans = yaml.safe_load(f) or []
        except Exception as e:
            _LOGGER.error(f"Error reading {IP_BANS_FILE}: {e}")
            return

        # Ensure bans is a list
        if not isinstance(bans, list):
            _LOGGER.error(f"{IP_BANS_FILE} has invalid format (expected list)")
            return

        # Remove IP from file list (handle both string and dict formats)
        new_bans = []
        found = False
        for b in bans:
            # Handle both formats: plain strings or dictionaries with 'ip_address' key
            if isinstance(b, str):
                ip = b
            elif isinstance(b, dict):
                ip = b.get("ip_address")
            else:
                _LOGGER.warning(f"Skipping invalid ban entry: {b}")
                continue

            if ip == ip_to_unban:
                found = True
                _LOGGER.debug(f"Found IP {ip_to_unban} in {IP_BANS_FILE}")
            else:
                new_bans.append(b)

        if not found:
            _LOGGER.info(f"IP {ip_to_unban} not found in {IP_BANS_FILE}.")
        else:
            with open(ban_file_path, "w") as f:
                yaml.safe_dump(new_bans, f)
            _LOGGER.info(f"IP {ip_to_unban} removed from {IP_BANS_FILE}.")

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

    # Register the service
    hass.services.async_register(DOMAIN, "execute", handle_unban_ip)
    _LOGGER.debug("Service 'execute' registered.")


async def async_unload_services(hass: HomeAssistant):
    """Unregister all Unban IP services."""
    if hass.services.has_service(DOMAIN, "execute"):
        hass.services.async_remove(DOMAIN, "execute")
        _LOGGER.debug("Service 'execute' unregistered.")
