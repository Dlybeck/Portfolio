"""
Tailscale Health Monitor for Cloud Run

Continuously monitors Tailscale connection health and automatically recovers from failures.
This prevents the recurring SOCKS5 connection failures by ensuring Tailscale stays alive.

Features:
- Monitors tailscaled process
- Checks SOCKS5 proxy on port 1055
- Tests connectivity to Mac server
- Auto-restarts Tailscale if dead
- Runs as background task
"""

import asyncio
import subprocess
import socket
import time
import os
from typing import Dict, Optional
import httpx
from core.config import settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
SOCKS5_PORT = 1055
MAC_SERVER_IP = "100.84.184.84"
MAC_SERVER_PORT = 8888
HEALTH_CHECK_INTERVAL = 30  # seconds
MAX_CONSECUTIVE_FAILURES = 3


class TailscaleHealthMonitor:
    """Monitors and maintains Tailscale connection health"""

    def __init__(self):
        self.is_cloud_run = settings.K_SERVICE is not None
        self.consecutive_failures = 0
        self.last_check_time = 0
        self.last_status = "unknown"
        self.health_stats = {
            "total_checks": 0,
            "failures": 0,
            "recoveries": 0,
            "last_failure_time": None,
            "last_recovery_time": None,
        }

    def _check_tailscaled_process(self) -> bool:
        """Check if tailscaled process is running"""
        try:
            result = subprocess.run(
                ["pgrep", "-x", "tailscaled"],
                capture_output=True,
                timeout=5
            )
            is_running = result.returncode == 0
            logger.info(f"tailscaled process: {'✅ running' if is_running else '❌ not running'}")
            return is_running
        except Exception as e:
            logger.error(f"Error checking tailscaled process: {e}")
            return False

    def _check_socks5_proxy(self) -> bool:
        """Check if SOCKS5 proxy is listening on port 1055"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(("localhost", SOCKS5_PORT))
            sock.close()
            is_listening = result == 0
            logger.info(f"SOCKS5 proxy (:{SOCKS5_PORT}): {'✅ listening' if is_listening else '❌ not listening'}")
            return is_listening
        except Exception as e:
            logger.error(f"Error checking SOCKS5 proxy: {e}")
            return False

    async def _check_mac_connectivity(self) -> bool:
        """Test actual connectivity to Mac server through SOCKS5"""
        if not self.is_cloud_run:
            return True  # Skip in local development

        try:
            # Try to connect to Mac's code-server through SOCKS5
            async with httpx.AsyncClient(
                proxy=f"socks5://localhost:{SOCKS5_PORT}",
                timeout=5.0
            ) as client:
                response = await client.get(f"http://{MAC_SERVER_IP}:{MAC_SERVER_PORT}/")
                is_reachable = response.status_code < 500
                logger.info(f"Mac server connectivity: {'✅ reachable' if is_reachable else '⚠️ error response'} (status: {response.status_code})")
                return is_reachable
        except Exception as e:
            logger.error(f"❌ Mac server not reachable: {e}")
            return False

    def _check_tailscale_status(self) -> bool:
        """Check Tailscale connection status"""
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
                backend_state = status.get("BackendState", "unknown")
                is_connected = backend_state == "Running"
                logger.info(f"Tailscale status: {backend_state} {'✅' if is_connected else '❌'}")
                return is_connected
            else:
                logger.error(f"tailscale status failed: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error checking Tailscale status: {e}")
            return False

    async def _attempt_recovery(self) -> bool:
        """Attempt to recover Tailscale connection"""
        logger.info("Attempting Tailscale recovery...")

        try:
            # First, try to restart the connection with --reset to avoid flag conflicts
            result = subprocess.run(
                ["tailscale", "up", "--reset", "--accept-routes"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                logger.info("Tailscale reconnected successfully")
                await asyncio.sleep(5)  # Give it time to establish connection

                # Verify recovery
                if await self._check_mac_connectivity():
                    self.health_stats["recoveries"] += 1
                    self.health_stats["last_recovery_time"] = time.time()
                    return True
                else:
                    logger.warning("Tailscale up succeeded but Mac not reachable")
                    return False
            else:
                logger.error(f"Tailscale up failed: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Recovery failed: {e}")
            return False

    async def perform_health_check(self) -> Dict:
        """
        Perform comprehensive health check

        Returns:
            Dict with health status and details
        """
        self.health_stats["total_checks"] += 1
        self.last_check_time = time.time()

        logger.info(f"Health Check #{self.health_stats['total_checks']}")

        # Check all components
        checks = {
            "tailscaled_running": self._check_tailscaled_process(),
            "socks5_listening": self._check_socks5_proxy(),
            "tailscale_connected": self._check_tailscale_status(),
            "mac_reachable": await self._check_mac_connectivity(),
        }

        # Overall health - only require the CRITICAL checks
        # If Mac is reachable through SOCKS5, the connection is working!
        # Don't worry about process checks - they can have false negatives in containers
        critical_checks = checks["socks5_listening"] and checks["mac_reachable"]
        is_healthy = critical_checks

        if is_healthy:
            self.consecutive_failures = 0
            self.last_status = "healthy"
            logger.info("All systems healthy")
        else:
            self.consecutive_failures += 1
            self.health_stats["failures"] += 1
            self.health_stats["last_failure_time"] = time.time()
            self.last_status = "unhealthy"

            failed_checks = [k for k, v in checks.items() if not v]
            logger.warning(f"Health check failed. Failed: {', '.join(failed_checks)}")
            logger.warning(f"Consecutive failures: {self.consecutive_failures}/{MAX_CONSECUTIVE_FAILURES}")

            # Attempt recovery if we've had multiple consecutive failures
            if self.consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                logger.critical(f"{MAX_CONSECUTIVE_FAILURES} consecutive failures - triggering recovery")
                recovery_success = await self._attempt_recovery()

                if recovery_success:
                    self.consecutive_failures = 0
                    self.last_status = "recovered"
                    checks["mac_reachable"] = True
                    is_healthy = True

        return {
            "healthy": is_healthy,
            "status": self.last_status,
            "checks": checks,
            "consecutive_failures": self.consecutive_failures,
            "stats": self.health_stats,
            "last_check_time": self.last_check_time,
        }

    async def start_monitoring(self):
        """Start the health monitoring loop"""
        if not self.is_cloud_run:
            logger.info("Running locally - health monitoring disabled")
            return

        logger.info(f"Starting Tailscale health monitor (interval: {HEALTH_CHECK_INTERVAL}s)")

        while True:
            try:
                await self.perform_health_check()
                await asyncio.sleep(HEALTH_CHECK_INTERVAL)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(HEALTH_CHECK_INTERVAL)

    def get_status(self) -> Dict:
        """Get current health status (for health endpoint)"""
        return {
            "healthy": self.last_status in ["healthy", "recovered"],
            "status": self.last_status,
            "consecutive_failures": self.consecutive_failures,
            "last_check_time": self.last_check_time,
            "stats": self.health_stats,
        }


# Global singleton instance
_monitor: Optional[TailscaleHealthMonitor] = None


def get_health_monitor() -> TailscaleHealthMonitor:
    """Get or create the global health monitor instance"""
    global _monitor

    if _monitor is None:
        _monitor = TailscaleHealthMonitor()

    return _monitor


async def start_health_monitor():
    """Start the health monitor (called from main.py startup)"""
    monitor = get_health_monitor()
    await monitor.start_monitoring()
