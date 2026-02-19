"""
Anti-spider utilities: request delays, proxy pool, user-agent rotation.
"""
import random
import time
from typing import Optional, List, Dict
from fake_useragent import UserAgent
from loguru import logger
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed


class AntiSpiderManager:
    """Manage anti-spider measures."""

    def __init__(self, proxy_enabled: bool = False, request_delay: tuple = (3, 10)):
        self.proxy_enabled = proxy_enabled
        self.request_delay = request_delay
        self.ua = UserAgent()
        self.proxy_pool: List[str] = []
        self.failed_proxies: set = set()
        self.last_request_time: Dict[str, float] = {}

        # Initialize proxy pool if enabled
        if proxy_enabled:
            self._init_proxy_pool()

    def _init_proxy_pool(self):
        """Initialize proxy pool from various sources."""
        # Add configured proxies
        from config.settings import PROXY_POOL
        self.proxy_pool.extend(PROXY_POOL)

        # TODO: Add free proxy scraping or paid API integration
        logger.info(f"Initialized proxy pool with {len(self.proxy_pool)} proxies")

    def get_random_user_agent(self) -> str:
        """
        Get a random user agent.

        Returns:
            Random User-Agent string
        """
        try:
            # Prefer mobile UA for better anti-detection
            return self.ua.random
        except Exception:
            fallback_ua = (
                "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                "Version/16.0 Mobile/15E148 Safari/604.1"
            )
            return fallback_ua

    def get_random_proxy(self) -> Optional[str]:
        """
        Get a random working proxy.

        Returns:
            Proxy URL or None if proxy disabled
        """
        if not self.proxy_enabled or not self.proxy_pool:
            return None

        # Filter out failed proxies
        available = [p for p in self.proxy_pool if p not in self.failed_proxies]

        if not available:
            logger.warning("No available proxies, resetting failed list")
            self.failed_proxies.clear()
            available = self.proxy_pool

        return random.choice(available) if available else None

    def mark_proxy_failed(self, proxy: str):
        """Mark a proxy as failed."""
        if proxy:
            self.failed_proxies.add(proxy)
            logger.debug(f"Marked proxy as failed: {proxy}")

    def reset_proxy_status(self, proxy: str):
        """Reset a proxy's failed status."""
        if proxy in self.failed_proxies:
            self.failed_proxies.remove(proxy)
            logger.debug(f"Reset proxy status: {proxy}")

    def wait_between_requests(self, domain: str = "default"):
        """
        Wait for a random delay between requests to the same domain.

        Args:
            domain: Domain name for rate limiting
        """
        current_time = time.time()

        # Check if we recently requested this domain
        if domain in self.last_request_time:
            elapsed = current_time - self.last_request_time[domain]
            min_delay = self.request_delay[0]

            if elapsed < min_delay:
                wait_time = min_delay - elapsed + random.uniform(0, 2)
                logger.debug(f"Rate limiting {domain}: waiting {wait_time:.2f}s")
                time.sleep(wait_time)

        # Update last request time
        self.last_request_time[domain] = time.time()

        # Add random delay
        delay = random.uniform(*self.request_delay)
        time.sleep(delay)

    def get_request_headers(self, referer: str = None) -> Dict[str, str]:
        """
        Get randomized request headers.

        Args:
            referer: Optional referer URL

        Returns:
            Dictionary of request headers
        """
        headers = {
            "User-Agent": self.get_random_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0",
        }

        if referer:
            headers["Referer"] = referer

        return headers

    def test_proxy(self, proxy: str, test_url: str = "http://httpbin.org/ip", timeout: int = 10) -> bool:
        """
        Test if a proxy is working.

        Args:
            proxy: Proxy URL
            test_url: URL to test against
            timeout: Request timeout in seconds

        Returns:
            True if proxy works, False otherwise
        """
        try:
            proxies = {"http": proxy, "https": proxy}
            response = requests.get(test_url, proxies=proxies, timeout=timeout)
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"Proxy test failed for {proxy}: {e}")
            return False

    def validate_proxy_pool(self, test_url: str = "http://httpbin.org/ip", max_workers: int = 10):
        """
        Validate all proxies in the pool and remove failed ones.

        Args:
            test_url: URL to test against
            max_workers: Number of concurrent workers
        """
        if not self.proxy_pool:
            logger.warning("No proxies to validate")
            return

        logger.info(f"Validating {len(self.proxy_pool)} proxies...")

        working_proxies = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.test_proxy, proxy, test_url): proxy
                for proxy in self.proxy_pool
            }

            for future in as_completed(futures):
                proxy = futures[future]
                try:
                    if future.result():
                        working_proxies.append(proxy)
                        logger.debug(f"Proxy OK: {proxy}")
                    else:
                        logger.debug(f"Proxy failed: {proxy}")
                except Exception as e:
                    logger.error(f"Error testing proxy {proxy}: {e}")

        self.proxy_pool = working_proxies
        self.failed_proxies.clear()

        logger.info(f"Proxy validation complete: {len(self.proxy_pool)}/{len(working_proxies)} working")


class RequestSession:
    """Enhanced requests session with anti-spider features."""

    def __init__(self, anti_spider: AntiSpiderManager):
        self.anti_spider = anti_spider
        self.session = requests.Session()

    def get(self, url: str, **kwargs) -> requests.Response:
        """
        Perform GET request with anti-spider measures.

        Args:
            url: Target URL
            **kwargs: Additional arguments for requests.get

        Returns:
            Response object
        """
        # Extract domain for rate limiting
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc or "default"

        # Rate limiting
        self.anti_spider.wait_between_requests(domain)

        # Get proxy
        proxy = self.anti_spider.get_random_proxy()
        if proxy:
            kwargs.setdefault("proxies", {"http": proxy, "https": proxy})

        # Get headers
        kwargs.setdefault("headers", {})
        if "Referer" not in kwargs["headers"]:
            kwargs["headers"].update(self.anti_spider.get_request_headers(referer=f"{parsed.scheme}://{parsed.netloc}"))

        # Retry logic
        max_retries = kwargs.pop("max_retries", 3)
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=kwargs.pop("timeout", 30), **kwargs)

                # Check if blocked
                if self._is_blocked(response):
                    raise Exception("Request blocked")

                # Reset proxy status on success
                if proxy:
                    self.anti_spider.reset_proxy_status(proxy)

                return response

            except Exception as e:
                logger.warning(f"Request failed (attempt {attempt + 1}/{max_retries}): {e}")

                # Mark proxy as failed
                if proxy:
                    self.anti_spider.mark_proxy_failed(proxy)
                    proxy = self.anti_spider.get_random_proxy()
                    if proxy:
                        kwargs["proxies"] = {"http": proxy, "https": proxy}

                if attempt == max_retries - 1:
                    raise

    def _is_blocked(self, response: requests.Response) -> bool:
        """
        Check if response indicates blocking.

        Args:
            response: Response object

        Returns:
            True if blocked, False otherwise
        """
        # Check status code
        if response.status_code in [403, 429]:
            return True

        # Check content for blocking indicators
        blocking_indicators = [
            "访问过于频繁",
            "请求过多",
            "验证码",
            "captcha",
            "access denied",
            "rate limit"
        ]

        content = response.text.lower()
        return any(indicator in content for indicator in blocking_indicators)

    def close(self):
        """Close the session."""
        self.session.close()
