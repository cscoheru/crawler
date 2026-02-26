"""
Toutiao crawler using alternative approaches.
"""
import asyncio
import re
import json
from typing import Dict, Optional
from loguru import logger
from playwright.async_api import async_playwright, Browser, Page

from crawler.base import BaseCrawler


class ToutiaoCrawlerAlternative(BaseCrawler):
    """Toutiao crawler using alternative methods."""

    def __init__(self, config: Dict = None):
        super().__init__("toutiao", config)
        self.base_url = self.config.get("base_url", "https://www.toutiao.com")
        self.api_url = self.config.get("api_url", "https://www.toutiao.com/api/search/content/")

    def search(self, keyword: str, max_pages: int = None):
        """
        Search Toutiao for articles using multiple methods.

        Args:
            keyword: Search keyword
            max_pages: Maximum pages to crawl

        Returns:
            List of article data dictionaries
        """
        max_pages = max_pages or (self.config or {}).get("max_pages", 2)
        logger.info(f"Searching Toutiao (alternative) for '{keyword}'")

        # Try multiple approaches
        import asyncio
        return asyncio.run(self._search_multi_method(keyword, max_pages))

    async def _search_multi_method(self, keyword: str, max_pages: int):
        """Try multiple search methods."""
        results = []

        # Method 1: Playwright web scraping
        playwright_results = await self._search_playwright(keyword, max_pages)
        if playwright_results:
            logger.info(f"Playwright found {len(playwright_results)} results")
            results.extend(playwright_results)

        # Method 2: Try different API endpoints (if playwright found nothing)
        if not results:
            api_results = await self._search_api_alternative(keyword)
            if api_results:
                logger.info(f"Alternative API found {len(api_results)} results")
                results.extend(api_results)

        if not results:
            logger.info("All search methods returned no results")

        return results

    async def _search_playwright(self, keyword: str, max_pages: int):
        """Search using Playwright."""
        results = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            try:
                # Try different search URLs
                search_urls = [
                    f"https://www.toutiao.com/search/?keyword={keyword}",
                    f"https://m.toutiao.com/search?keyword={keyword}",
                    f"https://www.toutiao.com/search/?keyword={keyword}&pd=article",
                ]

                for url in search_urls:
                    logger.info(f"Trying: {url}")
                    await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                    await page.wait_for_timeout(5000)

                    # Look for article links
                    # Toutiao uses /a/{id} pattern for articles
                    article_links = await page.query_selector_all('a[href*="/a/"]')

                    if article_links:
                        logger.info(f"Found {len(article_links)} article links")

                        seen = set()
                        for link in article_links[:20]:
                            try:
                                href = await link.get_attribute('href')
                                if not href or href in seen:
                                    continue

                                seen.add(href)

                                # Collect URLs first, then get details
                                if not href.startswith('http'):
                                    full_url = f"{self.base_url}{href}"
                                else:
                                    full_url = href

                                # Get full article detail
                                detail = await self._get_article_detail_async(page, full_url)
                                if detail:
                                    results.append(detail)
                                else:
                                    # Create basic article from link
                                    text = await link.inner_text()
                                    results.append(self.normalize_article_data({
                                        "id": self._extract_id(full_url),
                                        "title": text.strip()[:200],
                                        "content": "",
                                        "url": full_url,
                                    }))

                            except Exception as e:
                                logger.debug(f"Failed to process link: {e}")
                                continue

                        if results:
                            break

            finally:
                await browser.close()

        return results

    async def _search_api_alternative(self, keyword: str):
        """Try alternative API endpoints."""
        import httpx

        results = []

        # Try different API patterns
        api_patterns = [
            {
                'url': 'https://www.toutiao.com/api/search/content/',
                'params': {
                    'keyword': keyword,
                    'offset': 0,
                    'count': 20,
                    'pd': 'article',
                    'aid': '24',
                }
            },
            {
                'url': 'https://www.toutiao.com/api/search/',
                'params': {
                    'keyword': keyword,
                    'search_type': 'article',
                }
            },
        ]

        async with httpx.AsyncClient(timeout=15.0) as client:
            for pattern in api_patterns:
                try:
                    response = await client.get(
                        pattern['url'],
                        params=pattern['params'],
                        headers={
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                            'Referer': 'https://www.toutiao.com/',
                        }
                    )

                    if response.status_code == 200:
                        try:
                            data = response.json()

                            # Check different response structures
                            articles = []

                            # Check data.data structure
                            if isinstance(data.get('data'), dict):
                                articles = data['data'].get('data', [])
                            # Check data_head structure
                            elif data.get('data_head'):
                                articles = data['data_head']

                            if articles:
                                logger.info(f"API returned {len(articles)} articles")

                                for item in articles[:20]:
                                    article = self._parse_api_item(item)
                                    if article:
                                        results.append(article)

                                if results:
                                    return results

                        except Exception as e:
                            logger.debug(f"API parsing failed: {e}")

                except Exception as e:
                    logger.debug(f"API request failed: {e}")
                    continue

        return results

    def _parse_api_item(self, item: dict) -> Optional[Dict]:
        """Parse article from API response."""
        try:
            # Try different field names
            article_info = item.get('article_info', item)
            title = item.get('title', '')
            if not title and article_info:
                title = article_info.get('title', '')

            url = item.get('article_url', '')
            if not url and article_info:
                url = article_info.get('article_url', '')

            # Extract ID from URL
            article_id = self._extract_id(url) if url else str(hash(title))

            return self.normalize_article_data({
                "id": article_id,
                "title": title[:200],
                "content": item.get('abstract', item.get('content', ''))[:1000],
                "author": item.get('source', item.get('author', ''))[:100],
                "url": url,
            })

        except Exception:
            return None

    async def _get_article_detail_async(self, page: Page, article_url: str) -> Optional[Dict]:
        """Get article detail using Playwright."""
        try:
            await page.goto(article_url, wait_until='domcontentloaded', timeout=20000)
            await page.wait_for_timeout(2000)

            # Extract content
            content_elem = await page.query_selector('article, .article-content, .content')
            content = await content_elem.inner_text() if content_elem else ""

            # Clean content
            content = re.sub(r'\s+', ' ', content).strip()

            if not content:
                # Try to get text from body
                body_elem = await page.query_selector('body')
                content = await body_elem.inner_text()
                content = re.sub(r'\s+', ' ', content).strip()

            # Extract title
            title_elem = await page.query_selector('h1, .title, article-title')
            title = await title_elem.inner_text() if title_elem else ""

            # Extract author
            author_elem = await page.query_selector('.author, .source, .name')
            author = await author_elem.inner_text() if author_elem else ""

            return self.normalize_article_data({
                "id": self._extract_id(article_url),
                "title": title[:200],
                "content": content[:3000],
                "author": author[:100],
                "url": article_url,
            })

        except Exception as e:
            logger.debug(f"Failed to get detail: {e}")
            return None

    def _extract_id(self, url: str) -> str:
        """Extract article ID from URL."""
        # Try /a/{id} pattern
        match = re.search(r'/a/(\d+)', url)
        if match:
            return match.group(1)
        # Try article_id pattern
        match = re.search(r'article_id=(\d+)', url)
        if match:
            return match.group(1)
        return str(hash(url))

    def crawl_by_keywords(self, keywords: list, max_pages: int = None) -> list:
        """Crawl by multiple keywords."""
        all_results = []
        seen_urls = set()

        for keyword in keywords[:3]:
            results = self.search(keyword, max_pages=1)
            for result in results:
                url = result.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    all_results.append(result)

        return all_results

    def get_article_detail(self, article_url: str) -> Optional[Dict]:
        """Get article detail (sync wrapper)."""
        import asyncio
        return asyncio.run(self._get_article_detail_sync(article_url))

    async def _get_article_detail_sync(self, article_url: str):
        """Async wrapper for sync compatibility."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            try:
                result = await self._get_article_detail_async(page, article_url)
                return result
            finally:
                await browser.close()

    async def close(self):
        """Close (placeholder)."""
        pass
