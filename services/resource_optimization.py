"""
Resource optimization utilities for tracking per-service usage and
automatically stopping inactive services.

Design goals:
- Lightweight, non-intrusive tracking focused on worker services only
- Configurable idle timeout and CPU/memory sampling
- Optional psutil-based process measurements with graceful fallback
- Safe shutdown of idle services (no aggressive interruption of active work)
- Simple resource usage estimation (daily/weekly/monthly windows)
"""

from __future__ import annotations

import time
import logging
from typing import Dict, List, Tuple

try:
    import psutil  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    psutil = None  # type: ignore

logger = logging.getLogger(__name__)


class ServiceInfo:
    """Minimal per-service registry entry."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.last_active: float = time.time()
        self.running: bool = False


class ResourceOptimizer:
    """Core logic for per-service resource optimization.

        Public API:
    - track_service_usage(service_name: str, capture_now: bool = True)
    - estimate_resources(service_name: str, period: str = 'daily') -> dict
    - check_and_shutdown() -> None
    - set idle timeout and sampling interval via attributes
    """

    def __init__(
        self,
        idle_timeout_sec: int = 300,
        sampling_interval_sec: int = 60,
        log: logging.Logger | None = None,
    ) -> None:
        self.idle_timeout: int = idle_timeout_sec
        self.sampling_interval: int = sampling_interval_sec
        self._services: Dict[str, ServiceInfo] = {}
        self._usage_history: Dict[str, List[Tuple[float, float, float]]] = {}
        self._log = log or logger

    # -- Public API -----------------------------------------------------
    def track_service_usage(self, service_name: str, capture_now: bool = True) -> None:
        """Mark a service as recently used and optionally snapshot resource usage."""
        now = time.time()
        info = self._services.get(service_name)
        if info is None:
            info = ServiceInfo(service_name)
            self._services[service_name] = info
        info.last_active = now
        if capture_now:
            cpu, mem = self._measure(service_name)
            self._append_history(service_name, now, cpu, mem)
        info.running = bool(info.running or self._probe_running(service_name))

    def estimate_resources(
        self, service_name: str, period: str = "daily"
    ) -> Dict[str, float | int]:
        """Return simple statistics for the given service over the requested period."""
        hist = self._usage_history.get(service_name, [])
        if not hist:
            return {"cpu_mean": 0.0, "memory_mean_mb": 0.0, "samples": 0}

        now = time.time()
        if period == "daily":
            window_sec = 60 * 60 * 24
        elif period == "weekly":
            window_sec = 60 * 60 * 24 * 7
        elif period == "monthly":
            window_sec = 60 * 60 * 24 * 30
        else:
            window_sec = 60 * 60 * 24

        window = [row for row in hist if now - row[0] <= window_sec]
        if not window:
            window = hist[-1:]
        cpu_mean = sum(r[1] for r in window) / len(window)
        mem_mean = sum(r[2] for r in window) / len(window)
        return {
            "cpu_mean": round(cpu_mean, 2),
            "memory_mean_mb": round(mem_mean, 2),
            "samples": len(window),
        }

    def check_and_shutdown(self) -> None:
        """Shutdown idle services based on configured idle timeout."""
        now = time.time()
        for name, info in list(self._services.items()):
            if now - info.last_active >= self.idle_timeout:
                if info.running:
                    self._shutdown(name)
                    info.running = False
                    self._log.info("ResourceOptimizer: shut down idle service %s", name)
                else:
                    self._log.debug(
                        "ResourceOptimizer: idle service %s but not running", name
                    )

    # -- Internal helpers ----------------------------------------------
    def _probe_running(self, service_name: str) -> bool:
        procs = self._find_processes(service_name)
        return any(p.is_running() for p in procs) if psutil else False

    def _find_processes(self, service_name: str):
        if psutil is None:
            return []
        matches = []
        try:
            for p in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    cmdline = " ".join(p.info.get("cmdline") or [])
                    if (
                        service_name in (p.info.get("name") or "")
                        or service_name in cmdline
                    ):
                        matches.append(p)
                except psutil.NoSuchProcess:
                    continue
        except Exception:  # pragma: no cover
            return []
        return matches

    def _measure(self, service_name: str) -> Tuple[float, float]:
        if psutil is None:
            return 0.0, 0.0
        procs = self._find_processes(service_name)
        if not procs:
            return 0.0, 0.0
        try:
            total_cpu = sum(p.cpu_percent(interval=None) for p in procs)
            mem_bytes = sum(p.memory_info().rss for p in procs)
            mem_mb = mem_bytes / (1024 * 1024)
            return float(round(total_cpu, 2)), float(round(mem_mb, 2))
        except Exception:  # pragma: no cover
            return 0.0, 0.0

    def _append_history(
        self, service_name: str, ts: float, cpu: float, mem: float
    ) -> None:
        self._usage_history.setdefault(service_name, []).append((ts, cpu, mem))
        # prune older samples to keep memory footprint small
        cutoff = time.time() - (60 * 60 * 24 * 365)
        self._usage_history[service_name] = [
            row for row in self._usage_history[service_name] if row[0] >= cutoff
        ]

    def _shutdown(self, service_name: str) -> bool:
        if psutil is None:
            self._log.warning(
                "psutil not installed; cannot shutdown service '%s' safely.",
                service_name,
            )
            return False
        procs = self._find_processes(service_name)
        if not procs:
            self._log.info(
                "No running processes found for '%s' during shutdown.", service_name
            )
            return True
        for p in procs:
            try:
                p.terminate()
            except Exception:
                pass
        try:
            gone, alive = psutil.wait_procs(procs, timeout=5)
        except Exception:  # pragma: no cover
            gone, alive = [], procs
        for p in alive:
            try:
                p.kill()
            except Exception:
                pass
        self._log.info(
            "Shutdown requested for service '%s' (pids=%s)",
            service_name,
            [p.pid for p in procs],
        )
        return True


# --- Module-level singleton for quick ad-hoc usage -----------------------
_default_optimizer = ResourceOptimizer()


def track_service_usage(service_name: str, capture_now: bool = True) -> None:
    _default_optimizer.track_service_usage(service_name, capture_now=capture_now)


def estimate_resources(
    service_name: str, period: str = "daily"
) -> Dict[str, float | int]:
    return _default_optimizer.estimate_resources(service_name, period=period)


def check_and_shutdown() -> None:
    _default_optimizer.check_and_shutdown()


def set_idle_timeout(seconds: int) -> None:
    _default_optimizer.idle_timeout = int(seconds)
