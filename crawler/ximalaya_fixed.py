"""
Ximalaya (喜马拉雅) crawler using category browsing approach.
"""
import re
import asyncio
from typing import Dict, Optional, List
from loguru import logger
from playwright.async_api import async_playwright

from crawler.base import BaseCrawler


class XimalayaCrawlerFixed(BaseCrawler):
    """Ximalaya crawler using category browsing."""

    def __init__(self, config: Dict = None):
        super().__init__("ximalaya", config)
        self.base_url = (config or {}).get("base_url", "https://www.ximalaya.com")
        self.categories = {
            "psychology": "36",
            "management": "357",
            "finance": "358",
        }

    def search(self, keyword: str, max_pages: int = None) -> List[Dict]:
        """Search Ximalaya by category browsing."""
        max_pages = max_pages or self.config.get("max_pages", 1)
        logger.info(f"Searching Ximalaya for '{keyword}'")

        category_id = self._map_keyword_to_category(keyword)

        # Run async search synchronously
        results = asyncio.run(self._search_async(category_id, max_pages))
        return results

    def _map_keyword_to_category(self, keyword: str) -> str:
        """Map keyword to category ID."""
        keyword_lower = keyword.lower()
        if '心理' in keyword_lower or '咨询' in keyword_lower:
            return self.categories.get("psychology", "")
        elif '管理' in keyword_lower or '企业' in keyword_lower:
            return self.categories.get("management", "")
        elif '财经' in keyword_lower:
            return self.categories.get("finance", "")
        return ""

    async def _search_async(self, category_id: str, max_pages: int) -> List[Dict]:
        """Async search implementation."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            results = []

            try:
                url = f"{self.base_url}/channel/{category_id}/" if category_id else self.base_url + "/"
                logger.info(f"Browsing: {url}")

                await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                await page.wait_for_timeout(3000)

                # Get album links
                album_links = await page.query_selector_all('a[href*="/album/"]')
                logger.info(f"Found {len(album_links)} album links")

                seen = set()
                max_results = 30

                # First collect all URLs to avoid context destruction
                album_urls = []
                for link in album_links[:max_results]:
                    try:
                        href = await link.get_attribute('href')
                        if not href or href in seen:
                            continue
                        seen.add(href)
                        # Convert to full URL if relative
                        if href.startswith('/'):
                            href = self.base_url + href
                        album_urls.append(href)
                    except Exception:
                        continue

                logger.info(f"Collected {len(album_urls)} unique album URLs")

                # Then get details for each album
                for album_url in album_urls:
                    try:
                        detail = await self._get_detail(page, album_url)
                        if detail:
                            results.append(detail)
                    except Exception as e:
                        logger.debug(f"Error: {e}")
                        continue

                logger.info(f"Extracted {len(results)} albums")

            finally:
                await browser.close()

        return results

    async def _get_detail(self, page, album_url: str) -> Optional[Dict]:
        """Get album details."""
        try:
            await page.goto(album_url, wait_until='domcontentloaded', timeout=20000)
            await page.wait_for_timeout(3000)

            # Try h1 first for title (most reliable)
            title_elem = await page.query_selector('h1')
            title = await title_elem.inner_text() if title_elem else ""

            # If h1 is empty, try other selectors
            if not title or len(title) < 3:
                title_elem = await page.query_selector('.album-title, .detail-title')
                title = await title_elem.inner_text() if title_elem else ""

            # Get description/intro
            desc_elem = await page.query_selector('.album-intro, .intro, .description, .album-desc')
            desc = await desc_elem.inner_text() if desc_elem else ""

            # Get tracks
            tracks_text = ""
            tracks_elem = await page.query_selector('.track-list, .sound-list, .album-list')
            if tracks_elem:
                track_items = await tracks_elem.query_selector_all('li, .track-item, .sound-item')
                tracks = []
                for track in track_items[:15]:
                    track_title = await track.inner_text()
                    if track_title.strip():
                        tracks.append(f"- {track_title.strip()}")
                if tracks:
                    tracks_text = "专辑目录:\n" + "\n".join(tracks) + "\n\n"

            # Get author/nickname
            author_elem = await page.query_selector('.author, .anchor, .nickname, .uploader-name, [class*="author"]')
            author = await author_elem.inner_text() if author_elem else ""

            content = (tracks_text + desc).strip()
            content = re.sub(r'\s+', ' ', content)[:5000]

            return self.normalize_article_data({
                "id": self._extract_id(album_url),
                "title": title[:200],
                "content": content,
                "author": author[:100],
                "url": album_url,
            })

        except Exception as e:
            logger.debug(f"Error getting detail: {e}")
            return None

    def _extract_id(self, url: str) -> str:
        """Extract album ID."""
        match = re.search(r'/album/(\d+)', url)
        return match.group(1) if match else str(hash(url))

    def crawl_by_keywords(self, keywords: list, max_pages: int = None) -> list:
        """Crawl by keywords."""
        all_results = []
        seen_urls = set()

        for keyword in keywords[:2]:
            for result in self.search(keyword, max_pages=1):
                url = result.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    all_results.append(result)

        return all_results

    def get_article_detail(self, article_url: str) -> Optional[Dict]:
        """Get article detail sync wrapper."""
        return asyncio.run(self._get_detail_sync(article_url))

    async def _get_detail_sync(self, article_url: str):
        """Sync wrapper for detail fetching."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            try:
                return await self._get_detail(page, article_url)
            finally:
                await browser.close()

    def close(self):
        """Close placeholder."""
        pass
