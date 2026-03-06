import pytest

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture
def ban_file(tmp_path):
    """Create a temporary ip_bans.yaml file."""
    file_path = tmp_path / "ip_bans.yaml"
    data = [
        {"ip_address": "192.168.1.25", "banned_at": "2025-11-06T21:42:12"},
        {"ip_address": "192.168.2.26", "banned_at": "2025-11-06T21:43:00"},
    ]
    file_path.write_text(
        "- ip_address: 192.168.1.25\n  banned_at: '2025-11-06T21:42:12'\n"
        "- ip_address: 192.168.2.26\n  banned_at: '2025-11-06T21:43:00'\n"
    )
    return file_path
