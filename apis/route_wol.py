import socket
import logging
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from core.config import settings
from core.dev_utils import require_auth

logger = logging.getLogger(__name__)

wol_router = APIRouter()

# Tailscale IP of the Proxmox host — used as a direct unicast target
# in addition to the LAN broadcast, so the packet reaches Cloud Run → Tailscale → host.
PROXMOX_TAILSCALE_IP = "100.124.207.84"
WOL_PORT = 7


def build_magic_packet(mac: str) -> bytes:
    """Construct a WoL magic packet from a colon-separated MAC address.

    Format: 6 bytes of 0xFF followed by 100 repetitions of the 6-byte MAC.
    Raises ValueError if the MAC is not exactly 6 colon-separated hex pairs.
    """
    parts = mac.split(":")
    if len(parts) != 6 or not all(len(p) == 2 for p in parts):
        raise ValueError(f"Invalid MAC address: {mac}")
    mac_bytes = bytes(int(p, 16) for p in parts)
    return b"\xff" * 6 + mac_bytes * 100


async def _send_wol(mac: str) -> None:
    """Send the magic packet to both broadcast and the Proxmox Tailscale IP."""
    packet = build_magic_packet(mac)
    targets = [
        ("255.255.255.255", WOL_PORT),   # LAN broadcast
        (PROXMOX_TAILSCALE_IP, WOL_PORT),  # Tailscale unicast
    ]
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        for addr in targets:
            sock.sendto(packet, addr)
            logger.info("WoL magic packet sent to %s:%d", *addr)


@wol_router.post("/wol")
@require_auth
async def wake_on_lan(request: Request):
    """Send a Wake-on-LAN magic packet to the Proxmox host."""
    try:
        await _send_wol(settings.WOL_MAC_ADDRESS)
        return JSONResponse({"status": "sent"})
    except Exception as e:
        logger.exception("WoL send failed")
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=500)
