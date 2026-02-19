"""
WeChat Official Account crawler using Sogou search.
"""
import re
import time
import random
from typing import Dict, Generator, Optional
from urllib.parse import urlencode, urlparse
from loguru import logger
from bs4 import BeautifulSoup

from crawler.base import BaseCrawler


class WeChatCrawler(BaseCrawler):
    """Crawler for WeChat Official Accounts via Sogou search."""

    def __init__(self, config: Dict = None):
        super().__init__("wechat", config)
        self.sogou_url = self.config.get("sogou_url", "https://weixin.sogou.com")
        self.search_url = f"{self.sogou_url}/weixin"

    def search(self, keyword: str, max_pages: int = None) -> Generator[Dict, None, None]:
        """
        Search WeChat articles by keyword using Sogou.

        Args:
            keyword: Search keyword
            max_pages: Maximum pages to crawl

        Yields:
            Article data dictionaries
        """
        max_pages = max_pages or self.config.get("max_pages", 3)

        for page in range(0, max_pages):
            logger.info(f"Searching WeChat for '{keyword}', page {page + 1}/{max_pages}")

            try:
                # Sogou WeChat search parameters
                params = {
                    "type": 2,  # 2 = articles
                    "query": keyword,
                    "ie": "utf8",
                    "page": page + 1,
                }

                url = f"{self.search_url}?{urlencode(params)}"

                response = self.session.get(
                    url,
                    headers=self.anti_spider.get_request_headers(referer=self.sogou_url)
                )

                if response.status_code != 200:
                    logger.warning(f"Sogou returned status {response.status_code}")
                    break

                # Parse HTML
                soup = BeautifulSoup(response.text, 'lxml')

                # Find article entries
                articles = soup.find_all('div', class_='news-box')
                if not articles:
                    articles = soup.find_all('li', class_='news-list-item')

                if not articles:
                    logger.info(f"No more articles found for '{keyword}' on page {page + 1}")
                    break

                logger.info(f"Found {len(articles)} articles on page {page + 1}")

                # Extract article data
                for article in articles:
                    try:
                        article_data = self._parse_sogou_article(article)
                        if article_data:
                            # Get full content from article page
                            full_article = self.get_article_detail(article_data['url'])
                            if full_article:
                                yield full_article
                            else:
                                yield article_data

                    except Exception as e:
                        logger.warning(f"Failed to parse article: {e}")
                        continue

                # Rate limiting
                delay = random.uniform(*self.config.get("delay_range", (5, 12)))
                time.sleep(delay)

            except Exception as e:
                logger.error(f"Failed to search WeChat page {page + 1}: {e}")
                break

    def get_article_detail(self, article_url: str) -> Optional[Dict]:
        """
        Get full article content from WeChat page.

        Args:
            article_url: Article URL

        Returns:
            Article dictionary with full content
        """
        try:
            # Handle Sogou redirect URLs
            if 'sogou.com' in article_url:
                # Follow redirect to get actual WeChat URL
                response = self.session.get(
                    article_url,
                    headers=self.anti_spider.get_request_headers(),
                    allow_redirects=False
                )

                if response.status_code in (301, 302, 303, 307, 308):
                    article_url = response.headers.get('Location', article_url)

            # Fetch article from WeChat MP (mp.weixin.qq.com)
            if 'mp.weixin.qq.com' not in article_url:
                logger.debug(f"Skipping non-WeChat URL: {article_url}")
                return None

            response = self.session.get(
                article_url,
                headers=self.anti_spider.get_request_headers(referer="https://mp.weixin.qq.com")
            )

            if response.status_code != 200:
                logger.warning(f"Failed to fetch article: {response.status_code}")
                return None

            # Parse article content
            soup = BeautifulSoup(response.text, 'lxml')

            # Extract title
            title = ""
            title_elem = soup.find('h1', class_='rich_media_title')
            if title_elem:
                title = title_elem.get_text().strip()
            else:
                title_meta = soup.find('meta', property='og:title')
                if title_meta:
                    title = title_meta.get('content', '').strip()

            # Extract content
            content_elem = soup.find('div', class_='rich_media_content')
            if content_elem:
                # Clean up content
                for script in content_elem.find_all('script'):
                    script.decompose()
                for style in content_elem.find_all('style'):
                    style.decompose()
                content = content_elem.get_text('\n', strip=True)
            else:
                content = ""

            # Extract author
            author = ""
            author_elem = soup.find('span', class_='rich_media_meta_text')
            if author_elem:
                author = author_elem.get_text().strip()

            # Extract publish time
            publish_time = ""
            time_elem = soup.find('em', id='post-date')
            if time_elem:
                publish_time = time_elem.get_text().strip()

            # Extract article ID from URL
            article_id = ""
            match = re.search(r'/s/([A-Za-z0-9_-]+)', article_url)
            if match:
                article_id = match.group(1)
            else:
                match = re.search(r'mid=(\d+)', article_url)
                if match:
                    article_id = f"wx_{match.group(1)}"

            return self.normalize_article_data({
                "id": article_id,
                "title": title,
                "content": content,
                "author": author,
                "publish_time": publish_time,
                "url": article_url,
            })

        except Exception as e:
            logger.error(f"Failed to get article detail from {article_url}: {e}")
            return None

    def _parse_sogou_article(self, article_elem) -> Optional[Dict]:
        """
        Parse article from Sogou search result.

        Args:
            article_elem: BeautifulSoup element

        Returns:
            Article data dictionary
        """
        try:
            # Extract title and link
            title_elem = article_elem.find('h3')
            if not title_elem:
                title_elem = article_elem.find('a', class_='account-title')

            if not title_elem:
                return None

            link_elem = title_elem.find('a') if title_elem.name != 'a' else title_elem
            if not link_elem or not link_elem.get('href'):
                return None

            url = link_elem.get('href')
            title = link_elem.get_text().strip()

            # Extract snippet/content preview
            content = ""
            content_elem = article_elem.find('p', class_='txt-info')
            if content_elem:
                content = content_elem.get_text().strip()

            # Extract author/account name
            author = ""
            author_elem = article_elem.find('a', class_='account')
            if author_elem:
                author = author_elem.get_text().strip()

            # Extract article ID from URL
            article_id = ""
            match = re.search(r'/s/([A-Za-z0-9_-]+)', url)
            if match:
                article_id = match.group(1)

            return {
                "id": article_id,
                "title": title,
                "content": content,
                "author": author,
                "url": url,
            }

        except Exception as e:
            logger.warning(f"Failed to parse Sogou article: {e}")
            return None
