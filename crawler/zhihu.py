"""
Zhihu crawler using requests (simplified, synchronous).
"""
import json
import re
import time
import random
from typing import Dict, Generator, Optional
from loguru import logger
from bs4 import BeautifulSoup

from crawler.base import BaseCrawler


class ZhihuCrawler(BaseCrawler):
    """Crawler for Zhihu articles and answers using requests."""

    def __init__(self, config: Dict = None):
        super().__init__("zhihu", config)
        self.base_url = self.config.get("base_url", "https://www.zhihu.com")
        self.search_url = self.config.get("search_url", "https://www.zhihu.com/api/v4/search_v3")

    def search(self, keyword: str, max_pages: int = None) -> Generator[Dict, None, None]:
        """
        Search Zhihu for articles by keyword.

        Args:
            keyword: Search keyword
            max_pages: Maximum pages to crawl

        Yields:
            Article data dictionaries
        """
        max_pages = max_pages or self.config.get("max_pages", 5)

        for page in range(1, max_pages + 1):
            logger.info(f"Searching Zhihu for '{keyword}', page {page}/{max_pages}")

            try:
                # Use Zhihu search API
                params = {
                    "q": keyword,
                    "type": "content",
                    "page": page,
                }

                response = self.session.get(
                    self.search_url,
                    params=params,
                    headers=self.anti_spider.get_request_headers(referer=self.base_url)
                )

                if response.status_code != 200:
                    logger.warning(f"Zhihu API returned status {response.status_code}")
                    # Fallback to web scraping
                    yield from self._search_via_web(keyword, max_pages)
                    break

                try:
                    data = response.json()

                    # Extract search results
                    items = data.get("data", [])

                    if not items:
                        logger.info(f"No more results found for '{keyword}' on page {page}")
                        break

                    logger.info(f"Found {len(items)} items on page {page}")

                    # Parse each item
                    for item in items:
                        try:
                            if item.get("type") not in ["answer", "article"]:
                                continue

                            object_data = item.get("object", {})
                            article = self._parse_search_result(object_data)
                            if article:
                                yield article

                        except Exception as e:
                            logger.warning(f"Failed to parse search result: {e}")
                            continue

                except json.JSONDecodeError:
                    logger.warning("Failed to parse API response as JSON")
                    break

                # Rate limiting
                time.sleep(random.uniform(*self.config.get("delay_range", (5, 15))))

            except Exception as e:
                logger.error(f"Failed to search Zhihu page {page}: {e}")
                # Try web scraping fallback
                yield from self._search_via_web(keyword, max_pages)
                break

    def _search_via_web(self, keyword: str, max_pages: int) -> Generator[Dict, None, None]:
        """
        Fallback web scraping method.

        Args:
            keyword: Search keyword
            max_pages: Maximum pages

        Yields:
            Article dictionaries
        """
        logger.info("Using web scraping fallback for Zhihu")

        url = f"{self.base_url}/search?type=content&q={keyword}"

        try:
            response = self.session.get(
                url,
                headers=self.anti_spider.get_request_headers(referer=self.base_url)
            )

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'lxml')

                # Find search result items
                items = soup.find_all('div', class_='List-item')

                for item in items:
                    try:
                        link_elem = item.find('a', href=re.compile(r'/answer/|/p/'))
                        if not link_elem:
                            continue

                        url = link_elem.get('href', '')
                        if not url.startswith('http'):
                            url = f"{self.base_url}{url}"

                        title = link_elem.get_text().strip()

                        # Extract ID from URL
                        article_id = self._extract_zhihu_id(url)

                        article = self.normalize_article_data({
                            "id": article_id,
                            "title": title,
                            "content": "",  # Will fetch full content later
                            "url": url,
                        })

                        yield article

                    except Exception as e:
                        logger.warning(f"Failed to parse web result: {e}")
                        continue

        except Exception as e:
            logger.error(f"Web scraping failed: {e}")

    def _parse_search_result(self, object_data: Dict) -> Optional[Dict]:
        """Parse a search result item from API."""
        try:
            # Extract ID
            article_id = str(object_data.get("id", ""))

            # Extract title
            title = object_data.get("title", "")
            if not title:
                # For answers, title is in question
                question = object_data.get("question", {})
                title = question.get("title", "")

            # Extract URL
            url = object_data.get("url", "")

            # Extract author
            author = ""
            author_data = object_data.get("author", {})
            if author_data:
                author = author_data.get("name", "")

            # Extract content excerpt
            content = object_data.get("excerpt", object_data.get("content", ""))

            # For answers, content may be in different field
            if not content:
                content = object_data.get("description", "")

            return self.normalize_article_data({
                "id": article_id,
                "title": title,
                "content": content,
                "author": author,
                "url": url,
            })

        except Exception as e:
            logger.warning(f"Failed to parse search result: {e}")
            return None

    def get_article_detail(self, article_url: str) -> Optional[Dict]:
        """
        Get full article content from URL.

        Args:
            article_url: Article URL

        Returns:
            Article dictionary with full content
        """
        try:
            response = self.session.get(
                article_url,
                headers=self.anti_spider.get_request_headers(referer=self.base_url)
            )

            if response.status_code != 200:
                logger.warning(f"Failed to fetch article: {response.status_code}")
                return None

            soup = BeautifulSoup(response.text, 'lxml')

            # Extract title
            title = ""
            title_elem = soup.find('h1', class_='Post-title') or soup.find('h1', class_='QuestionHeader-title')
            if title_elem:
                title = title_elem.get_text().strip()

            # Extract content
            content = ""
            content_elem = (
                soup.find('div', class_='Post-RichText') or
                soup.find('div', class_='RichContent-inner') or
                soup.find('div', class_='QuestionAnswer-content')
            )

            if content_elem:
                # Clean up
                for script in content_elem.find_all('script'):
                    script.decompose()
                for style in content_elem.find_all('style'):
                    style.decompose()
                content = content_elem.get_text('\n', strip=True)

            # Extract author
            author = ""
            author_elem = (
                soup.find('span', class_='UserLink-link') or
                soup.find('div', class_='AuthorInfo-name')
            )
            if author_elem:
                author = author_elem.get_text().strip()

            # Extract article ID
            article_id = self._extract_zhihu_id(article_url)

            return self.normalize_article_data({
                "id": article_id,
                "title": title,
                "content": content,
                "author": author,
                "url": article_url,
            })

        except Exception as e:
            logger.error(f"Failed to get article detail from {article_url}: {e}")
            return None

    def _extract_zhihu_id(self, url: str) -> str:
        """Extract article/answer ID from URL."""
        # Handle various Zhihu URL formats
        patterns = [
            r'/answer/(\d+)',
            r'/p/(\d+)',
            r'/question/\d+/answer/(\d+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        # Fallback: hash of URL
        return str(hash(url))


# Keep the old API-based crawler as alternative
class ZhihuAPICrawler(ZhihuCrawler):
    """Alternative crawler using Zhihu's internal API (may require authentication)."""

    pass  # Inherits from ZhihuCrawler which now uses API by default
