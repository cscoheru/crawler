"""
Proxy pool management for scraping.
"""
import requests
import time
from typing import List, Dict, Optional
from loguru import logger
from concurrent.futures import ThreadPoolExecutor, as_completed


class ProxyPool:
    """Manage proxy pool from various sources."""

    def __init__(self):
        self.proxies: List[Dict[str, str]] = []
        self.failed_proxies: set = set()
        self.last_validation: float = 0
        self.validation_interval: int = 3600  # Validate every hour

    def fetch_free_proxies(self) -> List[str]:
        """
        Fetch free proxies from public sources.

        Returns:
            List of proxy URLs
        """
        proxies = []

        # TODO: Implement scraping from free proxy websites
        # Examples:
        # - https://www.free-proxy-list.net/
        # - https://proxy-list.download/
        # - https://www.proxy-list.download/API

        logger.warning("Free proxy fetching not implemented, please use paid proxies")

        return proxies

    def fetch_from_api(self, api_url: str, api_key: str = None) -> List[str]:
        """
        Fetch proxies from paid API service.

        Args:
            api_url: API endpoint URL
            api_key: Optional API key

        Returns:
            List of proxy URLs
        """
        try:
            headers = {}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"

            response = requests.get(api_url, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()

            # Parse response based on API format
            # This is a generic example, adjust based on your API provider
            if isinstance(data, list):
                return [f"http://{p['host']}:{p['port']}" for p in data]
            elif isinstance(data, dict) and "proxies" in data:
                return [f"http://{p['host']}:{p['port']}" for p in data["proxies"]]
            else:
                logger.error(f"Unexpected API response format: {type(data)}")
                return []

        except Exception as e:
            logger.error(f"Failed to fetch proxies from API: {e}")
            return []

    def validate_proxy(self, proxy_url: str, test_url: str = "http://httpbin.org/ip", timeout: int = 10) -> bool:
        """
        Validate a single proxy.

        Args:
            proxy_url: Proxy URL
            test_url: URL to test
            timeout: Request timeout

        Returns:
            True if proxy works
        """
        try:
            proxies = {
                "http": proxy_url,
                "https": proxy_url
            }

            start_time = time.time()
            response = requests.get(test_url, proxies=proxies, timeout=timeout)
            elapsed = time.time() - start_time

            if response.status_code == 200:
                logger.debug(f"Proxy OK: {proxy_url} ({elapsed:.2f}s)")
                return True

        except Exception as e:
            logger.debug(f"Proxy failed: {proxy_url} - {e}")

        return False

    def validate_all(self, test_url: str = "http://httpbin.org/ip", max_workers: int = 20) -> int:
        """
        Validate all proxies in the pool.

        Args:
            test_url: Test URL
            max_workers: Concurrent validation workers

        Returns:
            Number of valid proxies
        """
        if not self.proxies:
            logger.warning("No proxies to validate")
            return 0

        logger.info(f"Validating {len(self.proxies)} proxies...")

        valid_proxies = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.validate_proxy, proxy["url"], test_url): proxy
                for proxy in self.proxies
            }

            for future in as_completed(futures):
                proxy = futures[future]
                if future.result():
                    valid_proxies.append(proxy)

        self.proxies = valid_proxies
        self.failed_proxies.clear()
        self.last_validation = time.time()

        logger.info(f"Validation complete: {len(self.proxies)} valid proxies")

        return len(self.proxies)

    def get_random(self) -> Optional[Dict[str, str]]:
        """
        Get a random proxy from the pool.

        Returns:
            Proxy dictionary or None
        """
        if not self.proxies:
            return None

        import random
        return random.choice(self.proxies)

    def mark_failed(self, proxy_url: str):
        """Mark a proxy as failed."""
        self.failed_proxies.add(proxy_url)
        # Remove from pool
        self.proxies = [p for p in self.proxies if p["url"] != proxy_url]

    def add_proxy(self, proxy_url: str, **metadata):
        """
        Add a proxy to the pool.

        Args:
            proxy_url: Proxy URL
            **metadata: Additional metadata (source, type, etc.)
        """
        proxy_data = {
            "url": proxy_url,
            "added_at": time.time(),
            **metadata
        }

        if proxy_url not in [p["url"] for p in self.proxies]:
            self.proxies.append(proxy_data)
            logger.debug(f"Added proxy: {proxy_url}")

    def remove_old_proxies(self, max_age: int = 86400):
        """
        Remove proxies older than max_age seconds.

        Args:
            max_age: Maximum age in seconds (default: 24 hours)
        """
        current_time = time.time()
        original_count = len(self.proxies)

        self.proxies = [
            p for p in self.proxies
            if current_time - p.get("added_at", 0) < max_age
        ]

        removed = original_count - len(self.proxies)
        if removed > 0:
            logger.info(f"Removed {removed} old proxies")

    def get_stats(self) -> Dict:
        """Get proxy pool statistics."""
        return {
            "total_proxies": len(self.proxies),
            "failed_proxies": len(self.failed_proxies),
            "last_validation": self.last_validation,
            "needs_validation": time.time() - self.last_validation > self.validation_interval
        }
