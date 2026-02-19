"""
Toutiao crawler using API and web scraping.
"""
import json
import re
import time
from typing import Dict, List, Optional, Generator
from datetime import datetime
from loguru import logger
import requests

from crawler.base import BaseCrawler


class ToutiaoCrawler(BaseCrawler):
    """Crawler for Toutiao articles."""

    def __init__(self, config: Dict = None):
        super().__init__("toutiao", config)
        self.base_url = self.config.get("base_url", "https://www.toutiao.com")
        self.api_url = self.config.get("api_url", "https://www.toutiao.com/api/search/content/")

    def search(self, keyword: str, max_pages: int = None) -> Generator[Dict, None, None]:
        """
        Search Toutiao for articles by keyword.

        Args:
            keyword: Search keyword
            max_pages: Maximum pages to crawl

        Yields:
            Article data dictionaries
        """
        max_pages = max_pages or self.config.get("max_pages", 5)

        try:
            # Method 1: Try web search with parsing
            for article in self._search_web(keyword, max_pages):
                yield article

        except Exception as e:
            logger.warning(f"Web search failed: {e}, trying alternative method")

            # Method 2: Try API-based approach
            try:
                for article in self._search_api(keyword, max_pages):
                    yield article
            except Exception as e2:
                logger.error(f"API search also failed: {e2}")

    def _search_web(self, keyword: str, max_pages: int) -> Generator[Dict, None, None]:
        """
        Search using web scraping.

        Args:
            keyword: Search keyword
            max_pages: Maximum pages

        Yields:
            Article dictionaries
        """
        base_url = "https://www.toutiao.com/search/"

        for offset in range(0, max_pages * 20, 20):  # 20 items per page
            logger.info(f"Searching Toutiao for '{keyword}', offset {offset}")

            try:
                params = {
                    "keyword": keyword,
                    "offset": offset,
                    "count": 20,
                    "pd": "synthesis",
                }

                response = self.session.get(
                    base_url,
                    params=params,
                    headers=self.anti_spider.get_request_headers(referer="https://www.toutiao.com/")
                )

                if response.status_code == 200:
                    # Parse JSON data embedded in HTML
                    articles = self._parse_search_results(response.text, keyword)

                    for article in articles:
                        yield article

                    if not articles:
                        logger.info(f"No more articles found for '{keyword}'")
                        break

                else:
                    logger.warning(f"Search returned status {response.status_code}")

                # Rate limiting
                time.sleep(random.uniform(*self.config.get("delay_range", (3, 10))))

            except Exception as e:
                logger.error(f"Failed to search Toutiao web: {e}")
                break

    def _search_api(self, keyword: str, max_pages: int) -> Generator[Dict, None, None]:
        """
        Search using Toutiao API.

        Args:
            keyword: Search keyword
            max_pages: Maximum pages

        Yields:
            Article dictionaries
        """
        api_url = "https://www.toutiao.com/api/search/content/"

        for offset in range(0, max_pages * 20, 20):
            logger.info(f"Searching Toutiao API for '{keyword}', offset {offset}")

            try:
                params = {
                    "keyword": keyword,
                    "offset": offset,
                    "count": 20,
                    "pd": "synthesis",
                    "aid": "24",
                    "from": "search_result",
                }

                headers = self.anti_spider.get_request_headers(referer="https://www.toutiao.com/")
                headers.update({
                    "X-Requested-With": "XMLHttpRequest",
                })

                response = self.session.get(api_url, params=params, headers=headers)

                if response.status_code == 200:
                    try:
                        data = response.json()

                        for item in data.get("data", []):
                            if item.get("article_url"):
                                article = self.normalize_article_data({
                                    "id": item.get("item_id", ""),
                                    "title": item.get("title", ""),
                                    "content": item.get("abstract", ""),
                                    "author": item.get("source", ""),
                                    "url": item.get("article_url", ""),
                                    "time": item.get("publish_time", ""),
                                })

                                yield article

                    except json.JSONDecodeError:
                        logger.warning("Failed to parse API response as JSON")

                # Rate limiting
                time.sleep(random.uniform(*self.config.get("delay_range", (3, 10))))

            except Exception as e:
                logger.error(f"Failed to search Toutiao API: {e}")
                break

    def _parse_search_results(self, html: str, keyword: str) -> List[Dict]:
        """
        Parse article data from search result HTML.

        Args:
            html: HTML response
            keyword: Search keyword

        Returns:
            List of article dictionaries
        """
        articles = []

        try:
            # Extract JSON data embedded in HTML
            # Toutiao typically embeds data in script tags
            pattern = r'window\.INITIAL_STATE\s*=\s*({.*?});'
            match = re.search(pattern, html, re.DOTALL)

            if match:
                json_str = match.group(1)
                data = json.loads(json_str)

                # Navigate to search results
                # This path may vary based on Toutiao's current structure
                try:
                    search_data = data.get("searchResult", {}).get("data", {})

                    for item in search_data.get("data", []):
                        if item.get("article_url"):
                            article = self.normalize_article_data({
                                "id": item.get("item_id", ""),
                                "title": item.get("title", ""),
                                "content": item.get("abstract", ""),
                                "author": item.get("source", ""),
                                "url": item.get("article_url", ""),
                                "time": item.get("publish_time", ""),
                            })

                            articles.append(article)

                except (KeyError, AttributeError) as e:
                    logger.warning(f"Failed to extract articles from parsed JSON: {e}")

            # Fallback: Use regex to extract article info
            if not articles:
                articles = self._extract_with_regex(html)

        except Exception as e:
            logger.error(f"Failed to parse search results: {e}")

        return articles

    def _extract_with_regex(self, html: str) -> List[Dict]:
        """
        Extract article info using regex patterns.

        Args:
            html: HTML content

        Returns:
            List of article dictionaries
        """
        articles = []

        # Extract URLs
        url_pattern = r'href="(https://www\.toutiao\.com/article/\d+/)"'
        urls = re.findall(url_pattern, html)

        for url in urls[:10]:  # Limit to avoid excessive processing
            article = self.normalize_article_data({
                "id": self._extract_toutiao_id(url),
                "title": "",  # Will fetch from detail page
                "content": "",
                "url": url,
            })

            articles.append(article)

        return articles

    def get_article_detail(self, article_url: str) -> Optional[Dict]:
        """
        Get full article content.

        Args:
            article_url: Article URL

        Returns:
            Article dictionary with full content
        """
        try:
            response = self.session.get(
                article_url,
                headers=self.anti_spider.get_request_headers(referer="https://www.toutiao.com/")
            )

            if response.status_code == 200:
                return self._parse_article_detail(response.text, article_url)
            else:
                logger.warning(f"Failed to fetch article detail: status {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Failed to get article detail from {article_url}: {e}")
            return None

    def _parse_article_detail(self, html: str, url: str) -> Optional[Dict]:
        """
        Parse article detail from HTML.

        Args:
            html: Article page HTML
            url: Article URL

        Returns:
            Article dictionary
        """
        try:
            # Try to extract embedded JSON data
            pattern = r'window\.INITIAL_STATE\s*=\s*({.*?});'
            match = re.search(pattern, html, re.DOTALL)

            if match:
                json_str = match.group(1)
                data = json.loads(json_str)

                # Navigate to article data
                article_data = data.get("article", {})

                article = self.normalize_article_data({
                    "id": article_data.get("item_id", ""),
                    "title": article_data.get("title", ""),
                    "content": article_data.get("content", ""),
                    "author": article_data.get("media_info", {}).get("name", ""),
                    "url": url,
                    "time": article_data.get("publish_time", ""),
                })

                return article

            # Fallback: Use BeautifulSoup
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'lxml')

            title = soup.find('h1', class_='article-title')
            content = soup.find('article', class_='article-content')
            author = soup.find('a', class_='user-name')
            time_el = soup.find('time', class_='article-time')

            article = self.normalize_article_data({
                "id": self._extract_toutiao_id(url),
                "title": title.get_text(strip=True) if title else "",
                "content": content.get_text(separator='\n', strip=True) if content else "",
                "author": author.get_text(strip=True) if author else "",
                "url": url,
                "time": time_el.get_text(strip=True) if time_el else "",
            })

            return article

        except Exception as e:
            logger.error(f"Failed to parse article detail: {e}")
            return None

    def _extract_toutiao_id(self, url: str) -> str:
        """Extract article ID from URL."""
        match = re.search(r'/article/(\d+)/', url)
        if match:
            return match.group(1)

        # Fallback
        return str(hash(url))
