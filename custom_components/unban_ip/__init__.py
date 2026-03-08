"""Init file for Unban IP custom integration."""

import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN
from .services import async_setup_services, async_unload_services

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Import YAML config."""
    if DOMAIN in config:
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": "import"},
                data=config[DOMAIN],
            )
        )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the Unban IP integration."""
    await async_setup_services(hass)
    _LOGGER.info("Unban IP integration setup completed.")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle unloading of the integration."""
    await async_unload_services(hass)
    _LOGGER.info("Unban IP integration unloaded.")
    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle reload of the integration (without restart)."""
    _LOGGER.info("Reloading Unban IP integration...")
    await async_unload_services(hass)
    await async_setup_services(hass)
    _LOGGER.info("Reload complete.")
