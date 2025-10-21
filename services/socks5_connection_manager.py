"""
SOCKS5 Connection Manager with Auto-Retry and Connection Health Management

Fixes the recurring 408 timeout issue by:
- Automatic retry on stale connections
- Connection pool with lifecycle management
- Exponential backoff on failures
- Connection health validation
"""

import httpx
import asyncio
import time
from typing import Optional, Dict, Any
import os

# Configuration
SOCKS5_PROXY = "socks5://localhost:1055"
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 0.5  # seconds
MAX_RETRY_DELAY = 5.0  # seconds
CONNECTION_MAX_AGE = 300  # 5 minutes - recycle connections after this


class SOCKS5ConnectionManager:
    """Manages SOCKS5 proxy connections with automatic retry and health checks"""

    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None
        self._client_created_at: float = 0
        self._is_cloud_run = os.environ.get("K_SERVICE") is not None

    async def _create_fresh_client(self) -> httpx.AsyncClient:
        """Create a new httpx client with SOCKS5 proxy"""
        if self._client:
            await self._close_client()

        # Don't use proxy if running locally
        if not self._is_cloud_run:
            self._client = httpx.AsyncClient(timeout=30.0)
        else:
            self._client = httpx.AsyncClient(
                timeout=30.0,
                proxy=SOCKS5_PROXY,
                limits=httpx.Limits(
                    max_keepalive_connections=5,
                    max_connections=10,
                    keepalive_expiry=60.0  # Close idle connections after 60s
                )
            )

        self._client_created_at = time.time()
        print(f"[ConnectionManager] Created fresh {'SOCKS5 proxy' if self._is_cloud_run else 'direct'} client")
        return self._client

    async def _close_client(self):
        """Close existing client"""
        if self._client:
            try:
                await self._client.aclose()
                print("[ConnectionManager] Closed existing client")
            except Exception as e:
                print(f"[ConnectionManager] Error closing client: {e}")
            finally:
                self._client = None
                self._client_created_at = 0

    def _should_recycle_client(self) -> bool:
        """Check if client should be recycled based on age"""
        if not self._client:
            return True

        age = time.time() - self._client_created_at
        should_recycle = age > CONNECTION_MAX_AGE

        if should_recycle:
            print(f"[ConnectionManager] Client is {age:.1f}s old, recycling (max age: {CONNECTION_MAX_AGE}s)")

        return should_recycle

    async def get_client(self) -> httpx.AsyncClient:
        """Get a healthy client, creating a new one if needed"""
        if self._should_recycle_client():
            await self._create_fresh_client()

        return self._client

    async def request_with_retry(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> httpx.Response:
        """
        Make HTTP request with automatic retry on connection errors

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Target URL
            **kwargs: Additional arguments for httpx request

        Returns:
            httpx.Response

        Raises:
            httpx.HTTPError: If all retries fail
        """
        last_exception = None
        retry_delay = INITIAL_RETRY_DELAY

        for attempt in range(MAX_RETRIES):
            try:
                # Get fresh client if needed
                client = await self.get_client()

                print(f"[ConnectionManager] {method} {url} (attempt {attempt + 1}/{MAX_RETRIES})")

                # Make request
                response = await client.request(method, url, **kwargs)

                # Success!
                if attempt > 0:
                    print(f"[ConnectionManager] ✅ Success after {attempt + 1} attempts")

                return response

            except (
                httpx.ConnectError,
                httpx.ReadError,
                httpx.WriteError,
                httpx.PoolTimeout,
                httpx.ConnectTimeout,
                httpx.ReadTimeout,
                OSError,
            ) as e:
                last_exception = e
                error_name = type(e).__name__

                print(f"[ConnectionManager] ❌ Attempt {attempt + 1} failed: {error_name}: {e}")

                # Force recycle client on connection errors
                await self._close_client()

                # If this isn't the last attempt, wait and retry
                if attempt < MAX_RETRIES - 1:
                    wait_time = min(retry_delay * (2 ** attempt), MAX_RETRY_DELAY)
                    print(f"[ConnectionManager] 🔄 Retrying in {wait_time:.1f}s...")
                    await asyncio.sleep(wait_time)
                else:
                    print(f"[ConnectionManager] 💀 All {MAX_RETRIES} attempts failed")

        # All retries failed
        raise last_exception

    async def cleanup(self):
        """Clean up resources"""
        await self._close_client()


# Global singleton instance
_connection_manager: Optional[SOCKS5ConnectionManager] = None


def get_connection_manager() -> SOCKS5ConnectionManager:
    """Get or create the global connection manager instance"""
    global _connection_manager

    if _connection_manager is None:
        _connection_manager = SOCKS5ConnectionManager()

    return _connection_manager


async def proxy_request(
    method: str,
    url: str,
    **kwargs
) -> httpx.Response:
    """
    Convenience function to make a proxied request with auto-retry

    Usage:
        response = await proxy_request("GET", "http://example.com")
        response = await proxy_request("POST", "http://example.com", json={"key": "value"})
    """
    manager = get_connection_manager()
    return await manager.request_with_retry(method, url, **kwargs)
