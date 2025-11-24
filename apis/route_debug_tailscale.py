"""
Debug endpoints to test Tailscale, SOCKS5, and Mac connectivity from Cloud Run
Access these at /debug/tailscale/* to diagnose connection issues
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import subprocess
import socket
import httpx
import asyncio
from core.config import settings

debug_router = APIRouter()

MAC_SERVER_IP = settings.MAC_SERVER_IP
MAC_SERVER_PORT = settings.MAC_SERVER_PORT
SOCKS5_PROXY = settings.SOCKS5_PROXY
SOCKS5_PORT = settings.SOCKS5_PORT


@debug_router.get("/tailscale/status")
async def tailscale_status():
    """Check if Tailscale is running and connected"""
    results = {}

    # 1. Check if tailscaled process is running
    try:
        result = subprocess.run(["pgrep", "-x", "tailscaled"], capture_output=True, timeout=5)
        results["tailscaled_running"] = result.returncode == 0
        if results["tailscaled_running"]:
            results["tailscaled_pid"] = result.stdout.decode().strip()
    except Exception as e:
        results["tailscaled_running"] = False
        results["tailscaled_error"] = str(e)

    # 2. Check Tailscale status
    try:
        result = subprocess.run(
            ["tailscale", "status", "--json"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            import json
            status = json.loads(result.stdout)
            results["tailscale_connected"] = status.get("BackendState") == "Running"
            results["tailscale_self_ip"] = status.get("Self", {}).get("TailscaleIPs", ["unknown"])[0]
            results["tailscale_backend_state"] = status.get("BackendState")
        else:
            results["tailscale_connected"] = False
            results["tailscale_error"] = result.stderr
    except Exception as e:
        results["tailscale_connected"] = False
        results["tailscale_error"] = str(e)

    # 3. Check if SOCKS5 port is listening
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(("localhost", SOCKS5_PORT))
        sock.close()
        results["socks5_listening"] = result == 0
    except Exception as e:
        results["socks5_listening"] = False
        results["socks5_error"] = str(e)

    results["is_cloud_run"] = settings.K_SERVICE is not None
    results["environment"] = "Cloud Run" if results["is_cloud_run"] else "Local"

    return JSONResponse(results)


@debug_router.get("/tailscale/ping-mac")
async def ping_mac():
    """Test if Mac server is reachable via Tailscale (direct, no SOCKS5)"""
    results = {
        "target": f"{MAC_SERVER_IP}:{MAC_SERVER_PORT}",
        "method": "direct TCP connection (no SOCKS5)"
    }

    try:
        # Try direct TCP connection to Mac
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        start_time = asyncio.get_event_loop().time()
        result = sock.connect_ex((MAC_SERVER_IP, MAC_SERVER_PORT))
        elapsed = asyncio.get_event_loop().time() - start_time
        sock.close()

        results["reachable"] = result == 0
        results["latency_ms"] = round(elapsed * 1000, 2)

        if result != 0:
            results["error_code"] = result
            results["error"] = f"Connection refused or timeout (error code: {result})"
    except Exception as e:
        results["reachable"] = False
        results["error"] = str(e)

    return JSONResponse(results)


@debug_router.get("/tailscale/test-http-socks5")
async def test_http_socks5():
    """Test HTTP request to Mac through SOCKS5 proxy"""
    results = {
        "target": f"http://{MAC_SERVER_IP}:{MAC_SERVER_PORT}/",
        "proxy": SOCKS5_PROXY
    }

    try:
        async with httpx.AsyncClient(
            proxy=SOCKS5_PROXY,
            timeout=10.0
        ) as client:
            start_time = asyncio.get_event_loop().time()
            response = await client.get(f"http://{MAC_SERVER_IP}:{MAC_SERVER_PORT}/")
            elapsed = asyncio.get_event_loop().time() - start_time

            results["success"] = True
            results["status_code"] = response.status_code
            results["latency_ms"] = round(elapsed * 1000, 2)
            results["headers"] = dict(response.headers)
            results["body_preview"] = response.text[:200] if response.text else ""
    except Exception as e:
        results["success"] = False
        results["error"] = str(e)
        results["error_type"] = type(e).__name__

    return JSONResponse(results)


@debug_router.get("/tailscale/test-websocket-socks5")
async def test_websocket_socks5():
    """Test if websockets library can use SOCKS5 proxy"""
    results = {
        "target": f"ws://{MAC_SERVER_IP}:{MAC_SERVER_PORT}/",
        "proxy": SOCKS5_PROXY
    }

    try:
        # Check if python-socks is available
        import python_socks
        results["python_socks_installed"] = True
        results["python_socks_version"] = python_socks.__version__
    except ImportError as e:
        results["python_socks_installed"] = False
        results["error"] = "python-socks not installed"
        return JSONResponse(results)

    try:
        import websockets

        # Try to connect to Mac's WebSocket
        ws_url = f"ws://{MAC_SERVER_IP}:{MAC_SERVER_PORT}/"

        start_time = asyncio.get_event_loop().time()
        async with websockets.connect(
            ws_url,
            proxy=SOCKS5_PROXY,
            ping_interval=None,  # Disable ping for quick test
            close_timeout=5
        ) as ws:
            elapsed = asyncio.get_event_loop().time() - start_time
            results["success"] = True
            results["latency_ms"] = round(elapsed * 1000, 2)
            results["message"] = "WebSocket connection successful"
    except Exception as e:
        results["success"] = False
        results["error"] = str(e)
        results["error_type"] = type(e).__name__

    return JSONResponse(results)


@debug_router.get("/tailscale/full-diagnostic")
async def full_diagnostic():
    """Run all diagnostic tests and return comprehensive report"""

    # Run all tests
    status = await tailscale_status()
    ping = await ping_mac()
    http = await test_http_socks5()
    websocket = await test_websocket_socks5()

    # Compile results
    report = {
        "environment": {
            "is_cloud_run": settings.K_SERVICE is not None,
            "k_service": settings.K_SERVICE,
            "mac_server_ip": MAC_SERVER_IP,
            "mac_server_port": MAC_SERVER_PORT,
            "socks5_proxy": SOCKS5_PROXY
        },
        "tailscale_status": status.body.decode() if hasattr(status, 'body') else status,
        "direct_ping": ping.body.decode() if hasattr(ping, 'body') else ping,
        "http_via_socks5": http.body.decode() if hasattr(http, 'body') else http,
        "websocket_via_socks5": websocket.body.decode() if hasattr(websocket, 'body') else websocket,
    }

    # Determine overall status
    import json
    status_data = json.loads(status.body) if hasattr(status, 'body') else status
    ping_data = json.loads(ping.body) if hasattr(ping, 'body') else ping
    http_data = json.loads(http.body) if hasattr(http, 'body') else http
    ws_data = json.loads(websocket.body) if hasattr(websocket, 'body') else websocket

    all_checks = {
        "tailscale_connected": status_data.get("tailscale_connected", False),
        "socks5_listening": status_data.get("socks5_listening", False),
        "mac_reachable_direct": ping_data.get("reachable", False),
        "mac_reachable_http_socks5": http_data.get("success", False),
        "websocket_socks5_works": ws_data.get("success", False),
    }

    report["summary"] = {
        "all_checks": all_checks,
        "overall_healthy": all(all_checks.values()),
        "failed_checks": [k for k, v in all_checks.items() if not v]
    }

    return JSONResponse(report)
