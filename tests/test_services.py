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

    # Create in-memory ban list
    class DummyBan:
        def __init__(self):
            self.banned = {"192.168.1.25": "banned", "10.0.0.5": "banned"}

    hass.data["http"] = type("dummy_http", (), {"_ban": DummyBan()})()

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
async def test_list_banned_debug_mode(hass: HomeAssistant, tmp_path, monkeypatch):
    """Test list_banned service in debug mode."""
    # Create ban file
    ban_file_path = tmp_path / IP_BANS_FILE
    bans = {
        "192.168.1.25": {"banned_at": "2025-11-06T21:42:12+00:00"},
        "192.168.2.26": {"banned_at": "2025-11-06T21:43:00+00:00"},
    }
    with open(ban_file_path, "w") as f:
        yaml.safe_dump(bans, f)

    monkeypatch.setattr(hass.config, "path", lambda x: str(ban_file_path))

    # Create in-memory ban list
    class DummyBan:
        def __init__(self):
            self.banned = {"192.168.1.25": "banned", "10.0.0.5": "banned"}

    hass.data["http"] = type("dummy_http", (), {"_ban": DummyBan()})()

    # Register service
    await async_setup_services(hass)

    # Call service with debug=True
    response = await hass.services.async_call(
        DOMAIN,
        "list_banned",
        {"debug": True},
        blocking=True,
        return_response=True,
    )

    # Check response format (debug mode)
    assert "ips" in response
    assert "count" in response
    assert "file_ips" in response  # Should be present in debug mode
    assert "memory_ips" in response  # Should be present in debug mode

    # Check merged list
    assert response["count"] == 3
    assert set(response["ips"]) == {"192.168.1.25", "192.168.2.26", "10.0.0.5"}

    # Check file IPs
    assert set(response["file_ips"]) == {"192.168.1.25", "192.168.2.26"}

    # Check memory IPs
    assert set(response["memory_ips"]) == {"192.168.1.25", "10.0.0.5"}


@pytest.mark.asyncio
async def test_list_banned_file_not_found(hass: HomeAssistant, tmp_path, monkeypatch):
    """Test list_banned service when ban file doesn't exist."""
    ban_file_path = tmp_path / "nonexistent_ip_bans.yaml"
    monkeypatch.setattr(hass.config, "path", lambda x: str(ban_file_path))

    # Create in-memory ban list
    class DummyBan:
        def __init__(self):
            self.banned = {"10.0.0.5": "banned"}

    hass.data["http"] = type("dummy_http", (), {"_ban": DummyBan()})()

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

    # Should only have memory IPs
    assert response["count"] == 1
    assert response["ips"] == ["10.0.0.5"]


@pytest.mark.asyncio
async def test_list_banned_no_memory_bans(hass: HomeAssistant, tmp_path, monkeypatch):
    """Test list_banned service when there are no in-memory bans."""
    # Create ban file
    ban_file_path = tmp_path / IP_BANS_FILE
    bans = {
        "192.168.1.25": {"banned_at": "2025-11-06T21:42:12+00:00"},
    }
    with open(ban_file_path, "w") as f:
        yaml.safe_dump(bans, f)

    monkeypatch.setattr(hass.config, "path", lambda x: str(ban_file_path))

    # No http component or empty memory bans
    hass.data["http"] = None

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

    # Should only have file IPs
    assert response["count"] == 1
    assert response["ips"] == ["192.168.1.25"]


@pytest.mark.asyncio
async def test_list_banned_empty_result(hass: HomeAssistant, tmp_path, monkeypatch):
    """Test list_banned service when there are no banned IPs."""
    # Create empty ban file
    ban_file_path = tmp_path / IP_BANS_FILE
    with open(ban_file_path, "w") as f:
        yaml.safe_dump({}, f)

    monkeypatch.setattr(hass.config, "path", lambda x: str(ban_file_path))

    # Empty memory bans
    class DummyBan:
        def __init__(self):
            self.banned = {}

    hass.data["http"] = type("dummy_http", (), {"_ban": DummyBan()})()

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

    # Should have empty lists
    assert response["count"] == 0
    assert response["ips"] == []


@pytest.mark.asyncio
async def test_list_banned_deduplication(hass: HomeAssistant, tmp_path, monkeypatch):
    """Test that list_banned properly deduplicates IPs present in both sources."""
    # Create ban file with IPs
    ban_file_path = tmp_path / IP_BANS_FILE
    bans = {
        "192.168.1.25": {"banned_at": "2025-11-06T21:42:12+00:00"},
        "192.168.2.26": {"banned_at": "2025-11-06T21:43:00+00:00"},
    }
    with open(ban_file_path, "w") as f:
        yaml.safe_dump(bans, f)

    monkeypatch.setattr(hass.config, "path", lambda x: str(ban_file_path))

    # Create in-memory ban list with same IPs
    class DummyBan:
        def __init__(self):
            self.banned = {
                "192.168.1.25": "banned",
                "192.168.2.26": "banned",
            }

    hass.data["http"] = type("dummy_http", (), {"_ban": DummyBan()})()

    # Register service
    await async_setup_services(hass)

    # Call service with debug mode
    response = await hass.services.async_call(
        DOMAIN,
        "list_banned",
        {"debug": True},
        blocking=True,
        return_response=True,
    )

    # Both sources have 2 IPs
    assert len(response["file_ips"]) == 2
    assert len(response["memory_ips"]) == 2

    # But merged list should only have 2 (deduplicated)
    assert response["count"] == 2
    assert len(response["ips"]) == 2
    assert set(response["ips"]) == {"192.168.1.25", "192.168.2.26"}
