"""
Ximalaya (喜马拉雅) crawler for extracting audio content and transcripts.
"""
import json
import re
import time
import random
from typing import Dict, Generator, Optional
from loguru import logger
from bs4 import BeautifulSoup

from crawler.base import BaseCrawler


class XimalayaCrawler(BaseCrawler):
    """Crawler for Ximalaya (喜马拉雅) albums and audio tracks."""

    def __init__(self, config: Dict = None):
        super().__init__("ximalaya", config)
        self.base_url = self.config.get("base_url", "https://www.ximalaya.com")
        self.search_url = f"{self.base_url}/search"

    def search(self, keyword: str, max_pages: int = None) -> Generator[Dict, None, None]:
        """
        Search Ximalaya for albums/tracks by keyword.

        Args:
            keyword: Search keyword
            max_pages: Maximum pages to crawl

        Yields:
            Album/Track data dictionaries
        """
        max_pages = max_pages or self.config.get("max_pages", 3)

        logger.info(f"Searching Ximalaya for '{keyword}'")

        for page in range(1, max_pages + 1):
            try:
                # Ximalaya search endpoint
                params = {
                    "kw": keyword,
                    "page": page,
                    "condition": "album",  # Search for albums
                }

                response = self.session.get(
                    self.search_url,
                    params=params,
                    headers=self.anti_spider.get_request_headers(referer=self.base_url)
                )

                if response.status_code != 200:
                    logger.warning(f"Ximalaya search returned status {response.status_code}")
                    break

                # Parse search results
                soup = BeautifulSoup(response.text, 'lxml')

                # Find album items
                album_items = soup.find_all('div', class_=re.compile('album|item', re.I))

                if not album_items:
                    logger.info(f"No more results found for '{keyword}' on page {page}")
                    break

                logger.info(f"Found {len(album_items)} albums on page {page}")

                for item in album_items:
                    try:
                        album_data = self._parse_album_item(item)
                        if album_data:
                            # Get full details
                            detail = self.get_article_detail(album_data.get('url', ''))
                            if detail:
                                yield detail
                            else:
                                yield album_data

                    except Exception as e:
                        logger.warning(f"Failed to parse album item: {e}")
                        continue

                # Rate limiting
                time.sleep(random.uniform(*self.config.get("delay_range", (5, 10))))

            except Exception as e:
                logger.error(f"Failed to search Ximalaya page {page}: {e}")
                break

    def get_article_detail(self, article_url: str) -> Optional[Dict]:
        """
        Get full album/track content including transcript.

        Args:
            article_url: Album/Track URL

        Returns:
            Article dictionary with full content
        """
        try:
            # Extract ID from URL
            track_id = self._extract_id_from_url(article_url)
            if not track_id:
                logger.warning(f"Could not extract ID from URL: {article_url}")
                return None

            # Fetch album/track detail
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
            title_elem = soup.find('h1') or soup.find('h2', class_='title')
            if title_elem:
                title = title_elem.get_text().strip()

            # Extract content/transcript
            content = ""

            # Try to find track list or transcript
            content_elem = (
                soup.find('div', class_='album-text') or
                soup.find('div', class_='track-list') or
                soup.find('div', class_='intro') or
                soup.find('div', class_='description')
            )

            if content_elem:
                # Clean up
                for script in content_elem.find_all('script'):
                    script.decompose()
                for style in content_elem.find_all('style'):
                    style.decompose()
                content = content_elem.get_text('\n', strip=True)

            # If it's an album page, try to get track titles
            track_items = soup.find_all('li', class_=re.compile('track', re.I))
            if track_items:
                tracks = []
                for track in track_items[:20]:  # Limit to first 20 tracks
                    track_title = track.get_text().strip()
                    if track_title:
                        tracks.append(f"- {track_title}")
                if tracks:
                    content = f"专辑目录:\n" + "\n".join(tracks) + "\n\n" + content

            # Extract author/uploader
            author = ""
            author_elem = soup.find('span', class_=re.compile('author|uploader|nickname', re.I))
            if author_elem:
                author = author_elem.get_text().strip()

            # Extract metadata from embedded JSON
            script_elems = soup.find_all('script', type='application/json')
            for script_elem in script_elems:
                try:
                    data = json.loads(script_elem.string)
                    if isinstance(data, dict):
                        title = data.get('title', data.get('albumTitle', title))
                        content = data.get('intro', data.get('description', content))
                        author = data.get('nickname', data.get('anchor', author))
                        break
                except (json.JSONDecodeError, AttributeError):
                    continue

            # Ensure minimum content
            if not content:
                content = f"音频专辑内容提取失败，请访问原页面查看：{article_url}"

            return self.normalize_article_data({
                "id": track_id,
                "title": title,
                "content": content,
                "author": author,
                "url": article_url,
            })

        except Exception as e:
            logger.error(f"Failed to get article detail from {article_url}: {e}")
            return None

    def _parse_album_item(self, item_elem) -> Optional[Dict]:
        """
        Parse album/track item from search result.

        Args:
            item_elem: BeautifulSoup element

        Returns:
            Album data dictionary
        """
        try:
            # Extract title and link
            link_elem = item_elem.find('a', href=True)
            if not link_elem:
                return None

            url = link_elem.get('href')
            if not url.startswith('http'):
                url = f"{self.base_url}{url}"

            title = link_elem.get('title', '') or link_elem.get_text().strip()

            # Extract description
            content = ""
            desc_elem = item_elem.find('p', class_=re.compile('desc|intro', re.I))
            if desc_elem:
                content = desc_elem.get_text().strip()

            # Extract author/anchor
            author = ""
            author_elem = item_elem.find('span', class_=re.compile('author|anchor', re.I))
            if author_elem:
                author = author_elem.get_text().strip()

            # Extract ID from URL
            track_id = self._extract_id_from_url(url)

            return {
                "id": track_id,
                "title": title,
                "content": content,
                "author": author,
                "url": url,
            }

        except Exception as e:
            logger.warning(f"Failed to parse album item: {e}")
            return None

    def _extract_id_from_url(self, url: str) -> str:
        """Extract album/track ID from URL."""
        # Try various patterns
        patterns = [
            r'/album/(\w+)',
            r'/sound/(\w+)',
            r'/track/(\w+)',
            r'id=(\d+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        # Fallback
        return str(hash(url))
