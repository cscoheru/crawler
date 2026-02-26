"""
Ximalaya (喜马拉雅) crawler using category browsing approach.
This crawler browses categories directly instead of using the broken search.
"""
import asyncio
import re
from typing import Dict, Optional
from loguru import logger
from playwright.async_api import async_playwright, Browser, Page

from crawler.base import BaseCrawler


class XimalayaCategoryCrawler(BaseCrawler):
    """Ximalaya crawler using category browsing and mobile API."""

    def __init__(self, config: Dict = None):
        super().__init__("ximalaya", config)
        self.base_url = self.config.get("base_url", "https://www.ximalaya.com")
        # Category IDs for different topics
        self.categories = {
            "psychology": "36",  # 心理 category
            "management": "357",  # 管理 category
            "finance": "358",  # 财经 category
            "general": ""  # Main page
        }

    def search(self, keyword: str, max_pages: int = None):
        """
        Search Ximalaya by browsing relevant categories.

        Args:
            keyword: Search keyword (used to select category)
            max_pages: Maximum pages to crawl

        Yields:
            Album data dictionaries
        """
        max_pages = max_pages or self.config.get("max_pages", 2)
        logger.info(f"Searching Ximalaya (category browsing) for '{keyword}'")

        # Map keyword to category
        category_id = self._map_keyword_to_category(keyword)
        logger.info(f"Using category ID: {category_id}")

        # Run async search
        import asyncio
        return asyncio.run(self._search_async(category_id, max_pages))

    def _map_keyword_to_category(self, keyword: str) -> str:
        """Map search keyword to category ID."""
        keyword_lower = keyword.lower()

        # Direct keyword matches
        if '心理' in keyword_lower or '咨询' in keyword_lower:
            return self.categories.get("psychology", "")
        elif '管理' in keyword_lower or '企业' in keyword_lower:
            return self.categories.get("management", "")
        elif '财经' in keyword_lower or '金融' in keyword_lower or '经济' in keyword_lower:
            return self.categories.get("finance", "")

        # Default to psychology for general searches
        return self.categories.get("psychology", "")

    def _search_async(self, category_id: str, max_pages: int):
        """Async search implementation."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            try:
                # Build category URL
                if category_id:
                    url = f"{self.base_url}/channel/{category_id}/"
                else:
                    url = f"{self.base_url}/"

                logger.info(f"Browsing category: {url}")
                await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                await page.wait_for_timeout(3000)

                # Extract album links
                album_links = await page.query_selector_all('a[href*="/album/"]')
                logger.info(f"Found {len(album_links)} album links on page")

                # First collect all URLs to avoid context destruction
                seen_urls = set()
                max_results = 50
                album_urls = []

                for link in album_links[:max_results]:
                    try:
                        href = await link.get_attribute('href')
                        if not href or href in seen_urls:
                            continue
                        seen_urls.add(href)
                        # Convert to full URL if relative
                        if href.startswith('/'):
                            href = self.base_url + href
                        album_urls.append(href)
                    except Exception:
                        continue

                logger.info(f"Collected {len(album_urls)} unique album URLs")

                # Then get details for each album
                count = 0
                for album_url in album_urls:
                    try:
                        detail = await self._get_album_detail(page, album_url)
                        if detail:
                            yield detail
                            count += 1
                    except Exception as e:
                        logger.debug(f"Failed to process album: {e}")
                        continue

                logger.info(f"Extracted {count} albums from category")

            finally:
                await browser.close()

    async def _get_album_detail(self, page: Page, album_url: str) -> Optional[Dict]:
        """Get album details."""
        try:
            await page.goto(album_url, wait_until='domcontentloaded', timeout=20000)
            await page.wait_for_timeout(2000)

            # Extract title
            title_elem = await page.query_selector('h1, .album-title, .title')
            title = await title_elem.inner_text() if title_elem else ""

            # Extract description
            desc_elem = await page.query_selector('.album-intro, .intro, .description')
            desc = await desc_elem.inner_text() if desc_elem else ""

            # Extract track list
            tracks_elem = await page.query_selector('.track-list, .sound-list')
            tracks_text = ""

            if tracks_elem:
                track_items = await tracks_elem.query_selector_all('li, .track-item, .sound-item')
                if track_items:
                    tracks = []
                    for track in track_items[:20]:
                        track_title = await track.inner_text()
                        tracks.append(f"- {track_title.strip()}")
                    if tracks:
                        tracks_text = "\n专辑目录:\n" + "\n".join(tracks[:15]) + "\n\n"

            # Extract author
            author_elem = await page.query_selector('.author, .anchor, .nickname')
            author = await author_elem.inner_text() if author_elem else ""

            # Combine content
            content = tracks_text + desc
            content = re.sub(r'\s+', ' ', content).strip()

            return self.normalize_article_data({
                "id": self._extract_id(album_url),
                "title": title[:200],
                "content": content[:5000],
                "author": author[:100],
                "url": album_url,
            })

        except Exception as e:
            logger.debug(f"Failed to get album detail: {e}")
            return None

    def _extract_id(self, url: str) -> str:
        """Extract album ID from URL."""
        match = re.search(r'/album/(\d+)', url)
        if match:
            return match.group(1)
        return str(hash(url))

    def crawl_by_keywords(self, keywords: list, max_pages: int = None) -> list:
        """Crawl by multiple keywords (sync wrapper)."""
        all_results = []
        seen_urls = set()

        for keyword in keywords[:3]:  # Limit keywords
            results = self.search(keyword, max_pages=1)
            for result in results:
                if result.get("url") not in seen_urls:
                    seen_urls.add(result.get("url"))
                    all_results.append(result)

        return all_results

    def get_article_detail(self, article_url: str) -> Optional[Dict]:
        """Get article detail (sync wrapper using Playwright)."""
        import asyncio

        async def _get_detail():
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                try:
                    result = await self._get_album_detail(page, article_url)
                    return result
                finally:
                    await browser.close()

        return asyncio.run(_get_detail())

    async def close(self):
        """Close (placeholder for compatibility)."""
        pass
