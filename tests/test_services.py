import yaml
import pytest
from homeassistant.core import HomeAssistant

from custom_components.unban_ip.services import (
    async_setup_services,
    async_unload_services,
)
from custom_components.unban_ip.const import DOMAIN, IP_BANS_FILE


@pytest.mark.asyncio
async def test_service_registration(hass: HomeAssistant):
    """Test that the execute service registers correctly."""
    await async_setup_services(hass)
    assert hass.services.has_service(DOMAIN, "execute")

    await async_unload_services(hass)
    assert not hass.services.has_service(DOMAIN, "execute")


@pytest.mark.asyncio
async def test_unban_ip_removes_from_file_and_memory(
    hass: HomeAssistant, tmp_path, monkeypatch
):
    """Test that execute service removes IP from file and memory (dict format)."""

    # Create ban file with Home Assistant's dictionary format
    ban_file_path = tmp_path / IP_BANS_FILE
    bans = {
        "192.168.1.25": {"banned_at": "2025-11-06T21:42:12+00:00"},
        "192.168.2.26": {"banned_at": "2025-11-06T21:43:00+00:00"},
    }
    with open(ban_file_path, "w") as f:
        yaml.safe_dump(bans, f)

    # Mock hass.config.path to return the temp file path
    monkeypatch.setattr(hass.config, "path", lambda x: str(ban_file_path))

    # Create dummy in-memory ban list
    class DummyBan:
        def __init__(self):
            self.banned = {"192.168.1.25": "banned"}

    hass.data["http"] = type("dummy_http", (), {"_ban": DummyBan()})()

    # Register service
    await async_setup_services(hass)

    # Call service
    await hass.services.async_call(
        DOMAIN,
        "execute",
        {"ip_address": "192.168.1.25"},
        blocking=True,
    )

    # Check file - IP should be removed
    with open(ban_file_path, "r") as f:
        data = yaml.safe_load(f)
    assert "192.168.1.25" not in data
    assert "192.168.2.26" in data

    # Check in-memory ban list
    assert "192.168.1.25" not in hass.data["http"]._ban.banned


@pytest.mark.asyncio
async def test_unban_ip_not_found(hass: HomeAssistant, tmp_path, monkeypatch):
    """Test that execute service handles IP not in ban list gracefully."""

    # Create ban file
    ban_file_path = tmp_path / IP_BANS_FILE
    bans = {
        "192.168.1.25": {"banned_at": "2025-11-06T21:42:12+00:00"},
        "192.168.2.26": {"banned_at": "2025-11-06T21:43:00+00:00"},
    }
    with open(ban_file_path, "w") as f:
        yaml.safe_dump(bans, f)

    # Mock hass.config.path to return the temp file path
    monkeypatch.setattr(hass.config, "path", lambda x: str(ban_file_path))

    # Register service
    await async_setup_services(hass)

    # Call service with IP not in list
    await hass.services.async_call(
        DOMAIN,
        "execute",
        {"ip_address": "10.0.0.1"},
        blocking=True,
    )

    # Check file - should be unchanged
    with open(ban_file_path, "r") as f:
        data = yaml.safe_load(f)
    assert len(data) == 2
    assert "192.168.1.25" in data
    assert "192.168.2.26" in data


@pytest.mark.asyncio
async def test_unban_ip_file_not_found(hass: HomeAssistant, tmp_path, monkeypatch):
    """Test that execute service handles missing file gracefully."""

    # Point to a non-existent file
    ban_file_path = tmp_path / "nonexistent_ip_bans.yaml"
    monkeypatch.setattr(hass.config, "path", lambda x: str(ban_file_path))

    # Register service
    await async_setup_services(hass)

    # Call service - should not raise error
    await hass.services.async_call(
        DOMAIN,
        "execute",
        {"ip_address": "192.168.1.25"},
        blocking=True,
    )

    # File should still not exist
    assert not ban_file_path.exists()


@pytest.mark.asyncio
async def test_reload_services(hass: HomeAssistant):
    """Test that reload correctly unloads and reloads services."""
    from custom_components.unban_ip import async_reload_entry

    await async_setup_services(hass)
    assert hass.services.has_service(DOMAIN, "execute")

    await async_reload_entry(hass, None)
    assert hass.services.has_service(DOMAIN, "execute")
