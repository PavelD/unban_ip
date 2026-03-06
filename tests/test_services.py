import yaml
import pytest
from unittest.mock import AsyncMock, MagicMock
from homeassistant.core import HomeAssistant

from custom_components.unban_ip.services import (
    async_setup_services,
    async_unload_services,
)
from custom_components.unban_ip.const import DOMAIN, IP_BANS_FILE, KEY_BAN_MANAGER


def create_mock_ban_manager(banned_ips=None):
    """Create a mock ban manager for testing."""
    if banned_ips is None:
        banned_ips = {}
    
    mock_manager = MagicMock()
    mock_manager.banned = banned_ips
    mock_manager.async_load = AsyncMock()
    return mock_manager


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
    """Test that execute service removes IP from file and reloads ban manager."""

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

    # Mock ban manager
    mock_ban_manager = create_mock_ban_manager({"192.168.1.25": "banned"})
    hass.http = MagicMock()
    hass.http.app = {KEY_BAN_MANAGER: mock_ban_manager}

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

    # Check that async_load was called to reload ban manager
    mock_ban_manager.async_load.assert_called_once()


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


@pytest.mark.asyncio
async def test_list_banned_service_registration(hass: HomeAssistant):
    """Test that the list_banned service registers correctly."""
    await async_setup_services(hass)
    assert hass.services.has_service(DOMAIN, "list_banned")

    await async_unload_services(hass)
    assert not hass.services.has_service(DOMAIN, "list_banned")


@pytest.mark.asyncio
async def test_list_banned_default_mode(hass: HomeAssistant, tmp_path, monkeypatch):
    """Test list_banned service in default mode (no debug)."""
    # Create ban file
    ban_file_path = tmp_path / IP_BANS_FILE
    bans = {
        "192.168.1.25": {"banned_at": "2025-11-06T21:42:12+00:00"},
        "192.168.2.26": {"banned_at": "2025-11-06T21:43:00+00:00"},
    }
    with open(ban_file_path, "w") as f:
        yaml.safe_dump(bans, f)

    monkeypatch.setattr(hass.config, "path", lambda x: str(ban_file_path))

    # Mock ban manager
    mock_ban_manager = create_mock_ban_manager({"192.168.1.25": "banned", "10.0.0.5": "banned"})
    hass.http = MagicMock()
    hass.http.app = {KEY_BAN_MANAGER: mock_ban_manager}

    # Register service
    await async_setup_services(hass)

    # Call service without debug parameter
    response = await hass.services.async_call(
        DOMAIN,
        "list_banned",
        {},
        blocking=True,
        return_response=True,
    )

    # Check response format (default mode)
    assert "ips" in response
    assert "count" in response
    assert "file_ips" not in response  # Should not be in default mode
    assert "memory_ips" not in response  # Should not be in default mode

    # Check merged list
    assert response["count"] == 3
    assert set(response["ips"]) == {"192.168.1.25", "192.168.2.26", "10.0.0.5"}
    # Should be sorted
    assert response["ips"] == ["10.0.0.5", "192.168.1.25", "192.168.2.26"]


@pytest.mark.asyncio
async def test_list_banned_no_bans(hass: HomeAssistant):
    """Test list_banned service when there are no banned IPs."""
    # Mock ban manager with empty bans
    mock_ban_manager = create_mock_ban_manager({})
    hass.http = MagicMock()
    hass.http.app = {KEY_BAN_MANAGER: mock_ban_manager}

    # Register service
    await async_setup_services(hass)

    # Call service
    response = await hass.services.async_call(
        DOMAIN,
        "list_banned",
        {},
        blocking=True,
        return_response=True,
    )

    # Should have empty list
    assert response["count"] == 0
    assert response["ips"] == []


@pytest.mark.asyncio
async def test_list_banned_multiple_ips(hass: HomeAssistant):
    """Test list_banned service with multiple IPs."""
    # Mock ban manager with multiple IPs
    mock_ban_manager = create_mock_ban_manager({
        "192.168.1.25": "banned",
        "192.168.2.26": "banned",
        "10.0.0.5": "banned",
    })
    hass.http = MagicMock()
    hass.http.app = {KEY_BAN_MANAGER: mock_ban_manager}

    # Register service
    await async_setup_services(hass)

    # Call service
    response = await hass.services.async_call(
        DOMAIN,
        "list_banned",
        {},
        blocking=True,
        return_response=True,
    )

    # Check response
    assert response["count"] == 3
    assert set(response["ips"]) == {"192.168.1.25", "192.168.2.26", "10.0.0.5"}
    # Should be sorted
    assert response["ips"] == ["10.0.0.5", "192.168.1.25", "192.168.2.26"]
