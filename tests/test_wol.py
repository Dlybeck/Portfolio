"""Tests for Wake-on-LAN magic packet construction and the /dev/wol endpoint."""

import pytest
from unittest.mock import patch
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Patch require_auth BEFORE importing the router so the decorator bakes in
# a no-op instead of the real auth check.  This is the only clean way to
# bypass a decorator that is applied at import time.
# ---------------------------------------------------------------------------
def _passthrough(func):
    """Drop-in replacement for require_auth: sets state.token and calls through."""
    from functools import wraps

    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        request.state.token = "test-token"
        return await func(request, *args, **kwargs)
    return wrapper


with patch("core.dev_utils.require_auth", _passthrough):
    # Force a fresh import so the patched decorator is used
    import importlib
    import apis.route_wol as _wol_mod
    importlib.reload(_wol_mod)
    build_magic_packet = _wol_mod.build_magic_packet
    wol_router = _wol_mod.wol_router


# ---------------------------------------------------------------------------
# Unit tests — build_magic_packet (pure, no I/O)
# ---------------------------------------------------------------------------

class TestBuildMagicPacket:
    def test_correct_length(self):
        """Magic packet is 6 (header) + 6*100 (MAC repetitions) = 606 bytes."""
        packet = build_magic_packet("18:60:24:93:97:57")
        assert len(packet) == 606

    def test_header_is_six_ff_bytes(self):
        packet = build_magic_packet("18:60:24:93:97:57")
        assert packet[:6] == b"\xff" * 6

    def test_mac_repeated_100_times(self):
        mac = "18:60:24:93:97:57"
        expected_mac_bytes = bytes([0x18, 0x60, 0x24, 0x93, 0x97, 0x57])
        packet = build_magic_packet(mac)
        for i in range(100):
            offset = 6 + i * 6
            assert packet[offset:offset + 6] == expected_mac_bytes

    def test_known_mac_full_match(self):
        """Deterministic end-to-end check for a known MAC."""
        mac_bytes = bytes([0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF])
        expected = b"\xff" * 6 + mac_bytes * 100
        assert build_magic_packet("AA:BB:CC:DD:EE:FF") == expected

    def test_lowercase_mac(self):
        """MAC parsing should be case-insensitive."""
        assert build_magic_packet("aa:bb:cc:dd:ee:ff") == build_magic_packet("AA:BB:CC:DD:EE:FF")

    # --- invalid input ---
    def test_invalid_mac_too_few_parts(self):
        with pytest.raises(ValueError, match="Invalid MAC"):
            build_magic_packet("18:60:24:93:97")

    def test_invalid_mac_too_many_parts(self):
        with pytest.raises(ValueError, match="Invalid MAC"):
            build_magic_packet("18:60:24:93:97:57:AA")

    def test_invalid_mac_bad_hex(self):
        with pytest.raises(ValueError):
            build_magic_packet("ZZ:60:24:93:97:57")

    def test_invalid_mac_wrong_separator(self):
        with pytest.raises(ValueError, match="Invalid MAC"):
            build_magic_packet("18-60-24-93-97-57")


# ---------------------------------------------------------------------------
# Endpoint test — POST /wol (mocked socket, no real UDP)
# ---------------------------------------------------------------------------

# Minimal FastAPI app — auth is already a no-op via the patched import above.
_test_app = FastAPI()
_test_app.include_router(wol_router)
client = TestClient(_test_app)


class TestWolEndpoint:
    def test_post_wol_sends_packet_and_returns_200(self):
        """Patch _send_wol with an async no-op — no real UDP, no socket pollution."""
        async def _noop(mac):
            pass

        with patch("apis.route_wol._send_wol", side_effect=_noop):
            res = client.post("/wol")

        assert res.status_code == 200
        assert res.json() == {"status": "sent"}

    def test_post_wol_returns_500_on_socket_error(self):
        async def _fail(mac):
            raise OSError("network unreachable")

        with patch("apis.route_wol._send_wol", side_effect=_fail):
            res = client.post("/wol")

        assert res.status_code == 500
        assert res.json()["status"] == "error"
        assert "network unreachable" in res.json()["detail"]
