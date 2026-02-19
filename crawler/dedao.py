"""
Dedao (得到) crawler for extracting course content and transcripts.
"""
import json
import re
import time
import random
from typing import Dict, Generator, Optional
from loguru import logger
from bs4 import BeautifulSoup

from crawler.base import BaseCrawler


class DedaoCrawler(BaseCrawler):
    """Crawler for Dedao (得到) courses and lectures."""

    def __init__(self, config: Dict = None):
        super().__init__("dedao", config)
        self.base_url = self.config.get("base_url", "https://www.dedao.cn")
        self.api_url = self.config.get("api_url", "https://www.dedao.cn/mobile/api")
        self.web_url = f"{self.base_url}/web"

    def search(self, keyword: str, max_pages: int = None) -> Generator[Dict, None, None]:
        """
        Search Dedao for courses by keyword.

        Args:
            keyword: Search keyword
            max_pages: Maximum pages to crawl

        Yields:
            Course/Lecture data dictionaries
        """
        max_pages = max_pages or self.config.get("max_pages", 3)

        logger.info(f"Searching Dedao for '{keyword}'")

        # Dedao uses web search for courses
        for page in range(1, max_pages + 1):
            try:
                # Use web search endpoint
                search_url = f"{self.web_url}/search"
                params = {
                    "keyword": keyword,
                    "page": page,
                }

                response = self.session.get(
                    search_url,
                    params=params,
                    headers=self.anti_spider.get_request_headers(referer=self.base_url)
                )

                if response.status_code != 200:
                    logger.warning(f"Dedao search returned status {response.status_code}")
                    break

                # Parse search results
                soup = BeautifulSoup(response.text, 'lxml')

                # Find course/lecture items
                course_items = soup.find_all('div', class_=re.compile('course|lecture|article', re.I))

                if not course_items:
                    logger.info(f"No more results found for '{keyword}' on page {page}")
                    break

                logger.info(f"Found {len(course_items)} items on page {page}")

                for item in course_items:
                    try:
                        course_data = self._parse_course_item(item)
                        if course_data:
                            # Get full details
                            detail = self.get_article_detail(course_data.get('url', ''))
                            if detail:
                                yield detail
                            else:
                                yield course_data

                    except Exception as e:
                        logger.warning(f"Failed to parse course item: {e}")
                        continue

                # Rate limiting
                time.sleep(random.uniform(*self.config.get("delay_range", (5, 10))))

            except Exception as e:
                logger.error(f"Failed to search Dedao page {page}: {e}")
                break

    def get_article_detail(self, article_url: str) -> Optional[Dict]:
        """
        Get full course/lecture content including transcript.

        Args:
            article_url: Course/Lecture URL

        Returns:
            Article dictionary with full content
        """
        try:
            # Extract ID from URL
            course_id = self._extract_id_from_url(article_url)
            if not course_id:
                logger.warning(f"Could not extract ID from URL: {article_url}")
                return None

            # Fetch course/lecture detail
            response = self.session.get(
                article_url,
                headers=self.anti_spider.get_request_headers(referer=self.base_url)
            )

            if response.status_code != 200:
                logger.warning(f"Failed to fetch article: {response.status_code}")
                return None

            # Parse content
            soup = BeautifulSoup(response.text, 'lxml')

            # Extract title
            title = ""
            title_elem = soup.find('h1') or soup.find('h2') or soup.find('title')
            if title_elem:
                title = title_elem.get_text().strip()

            # Extract content/transcript
            content = ""

            # Try to find article content
            content_elem = (
                soup.find('div', class_='article-content') or
                soup.find('div', class_='course-content') or
                soup.find('div', class_='transcript') or
                soup.find('article')
            )

            if content_elem:
                # Clean up
                for script in content_elem.find_all('script'):
                    script.decompose()
                for style in content_elem.find_all('style'):
                    style.decompose()
                content = content_elem.get_text('\n', strip=True)

            # Extract author/instructor
            author = ""
            author_elem = soup.find('span', class_=re.compile('author|instructor|teacher', re.I))
            if author_elem:
                author = author_elem.get_text().strip()

            # Extract metadata from embedded JSON
            script_data = soup.find('script', type='application/json')
            if script_data:
                try:
                    data = json.loads(script_data.string)
                    if isinstance(data, dict):
                        title = data.get('title', title)
                        content = data.get('content', data.get('transcript', content))
                        author = data.get('author', data.get('instructor', author))
                except json.JSONDecodeError:
                    pass

            # Ensure minimum content
            if not content:
                content = f"课程内容提取失败，请访问原页面查看：{article_url}"

            return self.normalize_article_data({
                "id": course_id,
                "title": title,
                "content": content,
                "author": author,
                "url": article_url,
            })

        except Exception as e:
            logger.error(f"Failed to get article detail from {article_url}: {e}")
            return None

    def _parse_course_item(self, item_elem) -> Optional[Dict]:
        """
        Parse course/lecture item from search result.

        Args:
            item_elem: BeautifulSoup element

        Returns:
            Course data dictionary
        """
        try:
            # Extract title and link
            link_elem = item_elem.find('a', href=True)
            if not link_elem:
                return None

            url = link_elem.get('href')
            if not url.startswith('http'):
                url = f"{self.base_url}{url}"

            title = link_elem.get_text().strip()
            if not title:
                title_elem = item_elem.find(re.compile('h1|h2|h3|h4'))
                if title_elem:
                    title = title_elem.get_text().strip()

            # Extract description
            content = ""
            desc_elem = item_elem.find('p', class_=re.compile('desc|summary|intro', re.I))
            if desc_elem:
                content = desc_elem.get_text().strip()

            # Extract author/instructor
            author = ""
            author_elem = item_elem.find('span', class_=re.compile('author|instructor', re.I))
            if author_elem:
                author = author_elem.get_text().strip()

            # Extract ID from URL
            article_id = self._extract_id_from_url(url)

            return {
                "id": article_id,
                "title": title,
                "content": content,
                "author": author,
                "url": url,
            }

        except Exception as e:
            logger.warning(f"Failed to parse course item: {e}")
            return None

    def _extract_id_from_url(self, url: str) -> str:
        """Extract course/lecture ID from URL."""
        # Try various patterns
        patterns = [
            r'/course/(\w+)',
            r'/article/(\w+)',
            r'/lecture/(\w+)',
            r'id=(\w+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        # Fallback
        return str(hash(url))
