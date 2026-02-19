"""
Bilibili crawler for extracting video metadata and subtitles.
"""
import json
import re
import time
from typing import Dict, Generator, Optional
from loguru import logger

from crawler.base import BaseCrawler


class BilibiliCrawler(BaseCrawler):
    """Crawler for Bilibili videos."""

    def __init__(self, config: Dict = None):
        super().__init__("bilibili", config)
        self.base_url = self.config.get("base_url", "https://www.bilibili.com")
        self.search_api = self.config.get("search_url", "https://api.bilibili.com/x/web-interface/search/type")

    def search(self, keyword: str, max_pages: int = None) -> Generator[Dict, None, None]:
        """
        Search Bilibili for videos by keyword.

        Args:
            keyword: Search keyword
            max_pages: Maximum pages to crawl

        Yields:
            Video data dictionaries
        """
        max_pages = max_pages or self.config.get("max_pages", 5)

        for page in range(1, max_pages + 1):
            logger.info(f"Searching Bilibili for '{keyword}', page {page}/{max_pages}")

            try:
                params = {
                    "keyword": keyword,
                    "search_type": "video",  # Search for videos
                    "page": page,
                }

                response = self.session.get(
                    self.search_api,
                    params=params,
                    headers=self.anti_spider.get_request_headers(referer=self.base_url)
                )

                if response.status_code == 200:
                    try:
                        data = response.json()

                        # Check if API call was successful
                        if data.get("code") != 0:
                            logger.warning(f"Bilibili API error: {data.get('message', 'Unknown error')}")
                            break

                        # Extract video results
                        videos = data.get("data", {}).get("result", [])

                        if not videos:
                            logger.info(f"No more videos found for '{keyword}' on page {page}")
                            break

                        # Parse each video
                        for video in videos:
                            try:
                                # Bilibili search results use special format
                                # Fields are named like "title", "description", "author", etc.
                                # but values contain HTML tags that need decoding

                                # Extract video ID from URI
                                bvid = video.get("bvid", "")
                                if not bvid:
                                    # Try to extract from arcurl or other fields
                                    arcurl = video.get("arcurl", "")
                                    match = re.search(r'BV[\w]+', arcurl)
                                    if match:
                                        bvid = match.group(0)

                                if not bvid:
                                    continue

                                # Decode HTML entities in title and description
                                title = self._decode_html_entities(video.get("title", ""))
                                description = self._decode_html_entities(video.get("description", ""))
                                author = video.get("author", "")

                                # Parse other metadata
                                video_data = {
                                    "id": bvid,
                                    "bvid": bvid,
                                    "title": title,
                                    "description": description,
                                    "author": author,
                                    "url": f"{self.base_url}/video/{bvid}",
                                    "duration": video.get("duration", ""),  # Duration in seconds
                                    "play_count": video.get("play", 0),
                                    "pubdate": video.get("pubdate", 0),
                                    "tags": video.get("tag", ""),
                                    "pic": video.get("pic", ""),
                                    "review": video.get("review", 0),
                                }

                                # Normalize to standard format
                                normalized = self.normalize_article_data({
                                    "id": bvid,
                                    "title": title,
                                    "content": description,  # Will fetch full content + subtitles later
                                    "author": author,
                                    "url": f"{self.base_url}/video/{bvid}",
                                    "publish_time": video.get("pubdate", ""),
                                })

                                # Add Bilibili-specific fields
                                normalized["bvid"] = bvid
                                normalized["duration"] = video.get("duration", 0)
                                normalized["play_count"] = video.get("play", 0)

                                yield normalized

                            except Exception as e:
                                logger.warning(f"Failed to parse video result: {e}")
                                continue

                        logger.info(f"Found {len(videos)} videos on page {page}")

                    except json.JSONDecodeError:
                        logger.error("Failed to parse Bilibili API response as JSON")
                        break

                else:
                    logger.warning(f"Bilibili search returned status {response.status_code}")

                # Rate limiting
                time.sleep(random.uniform(*self.config.get("delay_range", (5, 15))))

            except Exception as e:
                logger.error(f"Failed to search Bilibili page {page}: {e}")
                break

    def get_article_detail(self, article_url: str) -> Optional[Dict]:
        """
        Get full video content including subtitles.

        Args:
            article_url: Video URL (e.g., https://www.bilibili.com/video/BV1xx411c7mD)

        Returns:
            Article dictionary with full content and subtitles
        """
        # Extract BV ID from URL
        match = re.search(r'BV[\w]+', article_url)
        if not match:
            logger.error(f"Invalid Bilibili URL: {article_url}")
            return None

        bvid = match.group(0)

        try:
            # Get video page
            response = self.session.get(
                article_url,
                headers=self.anti_spider.get_request_headers(referer=self.base_url)
            )

            if response.status_code != 200:
                logger.warning(f"Failed to fetch video page: {response.status_code}")
                return None

            # Extract video info from page
            video_info = self._extract_video_info(response.text, bvid)

            if not video_info:
                return None

            # Extract subtitles if available
            subtitles = self._extract_subtitles(bvid)

            # Combine description and subtitles as content
            content_parts = []

            if video_info.get("description"):
                content_parts.append(f"视频简介:\n{video_info['description']}")

            if subtitles:
                content_parts.append(f"\n视频字幕:\n{subtitles}")

            content = "\n".join(content_parts)

            # Build article data
            article_data = self.normalize_article_data({
                "id": bvid,
                "title": video_info.get("title", ""),
                "content": content,
                "author": video_info.get("uploader", ""),
                "url": article_url,
                "time": video_info.get("pubdate", ""),
            })

            # Add Bilibili-specific fields
            article_data["bvid"] = bvid
            article_data["duration"] = video_info.get("duration", 0)
            article_data["view_count"] = video_info.get("view", 0)
            article_data["like_count"] = video_info.get("like", 0)
            article_data["subtitle_content"] = subtitles

            return article_data

        except Exception as e:
            logger.error(f"Failed to get video detail from {article_url}: {e}")
            return None

    def _extract_video_info(self, html: str, bvid: str) -> Optional[Dict]:
        """
        Extract video information from page HTML.

        Args:
            html: Page HTML content
            bvid: Video BV ID

        Returns:
            Dictionary with video metadata
        """
        try:
            # Bilibili embeds data in __INITIAL_STATE__ or __playinfo__ script tags
            patterns = [
                r'__INITIAL_STATE__\s*=\s*({.+?});',
                r'__playinfo__\s*=\s*({.+?});',
                r'window.__INITIAL_STATE__\s*=\s*({.+?});',
            ]

            for pattern in patterns:
                match = re.search(pattern, html, re.DOTALL)
                if match:
                    try:
                        data_str = match.group(1)
                        data = json.loads(data_str)

                        # Navigate to video data
                        # Structure may vary, try different paths
                        video_data = None

                        # Try path 1
                        if "videoData" in data:
                            video_data = data["videoData"]
                        # Try path 2
                        elif "videoInfo" in data:
                            video_data = data["videoInfo"]
                        # Try path 3 (bvid as key)
                        elif bvid in data:
                            video_data = data[bvid]
                        # Try nested path
                        elif "video" in data and "videoInfo" in data["video"]:
                            video_data = data["video"]["videoInfo"]

                        if video_data:
                            return {
                                "title": video_data.get("title", ""),
                                "description": video_data.get("desc", video_data.get("description", "")),
                                "uploader": video_data.get("owner", {}).get("name", ""),
                                "pubdate": video_data.get("pubdate", 0),
                                "duration": video_data.get("duration", 0),
                                "view": video_data.get("stat", {}).get("view", 0),
                                "like": video_data.get("stat", {}).get("like", 0),
                            }

                    except json.JSONDecodeError:
                        continue

            # Fallback: try to extract from meta tags
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'lxml')

            title_meta = soup.find('meta', property='og:title')
            desc_meta = soup.find('meta', property='og:description')
            author_meta = soup.find('meta', property='og:author')

            if title_meta or desc_meta:
                return {
                    "title": title_meta.get('content', '') if title_meta else '',
                    "description": desc_meta.get('content', '') if desc_meta else '',
                    "uploader": author_meta.get('content', '') if author_meta else '',
                }

        except Exception as e:
            logger.warning(f"Failed to extract video info: {e}")

        return None

    def _extract_subtitles(self, bvid: str) -> Optional[str]:
        """
        Extract subtitles for a video.

        Args:
            bvid: Video BV ID

        Returns:
            Combined subtitle text or None
        """
        try:
            # Try to get subtitle list
            # API: https://api.bilibili.com/x/player/wbi/playurl?bvid={bvid}&fnval=16
            # Note: This API may require authentication or cookies

            subtitle_url = f"https://api.bilibili.com/x/player/wbi/playurl"

            params = {
                "bvid": bvid,
                "fnval": 16,  # Request subtitle data
                "fnver": 0,
                "fourk": 1,
            }

            response = self.session.get(
                subtitle_url,
                params=params,
                headers=self.anti_spider.get_request_headers(referer=self.base_url)
            )

            if response.status_code == 200:
                data = response.json()

                if data.get("code") == 0:
                    # Check for subtitle data
                    subtitle_info = data.get("data", {}).get("subtitle", {})

                    if subtitle_info.get("subtitles"):
                        # Download and parse each subtitle
                        all_texts = []

                        for sub in subtitle_info["subtitles"]:
                            try:
                                # Subtitle URL
                                sub_url = sub.get("subtitle_url", "")

                                if sub_url:
                                    # Make sure URL is absolute
                                    if not sub_url.startswith("http"):
                                        sub_url = f"https:{sub_url}"

                                    # Fetch subtitle content
                                    sub_response = self.session.get(sub_url, headers=self.anti_spider.get_request_headers())

                                    if sub_response.status_code == 200:
                                        # Parse subtitle JSON
                                        sub_data = sub_response.json()

                                        # Extract text from subtitle lines
                                        if "body" in sub_data:
                                            for line in sub_data["body"]:
                                                if "content" in line:
                                                    all_texts.append(line["content"])

                            except Exception as e:
                                logger.debug(f"Failed to fetch subtitle: {e}")
                                continue

                        if all_texts:
                            return "\n".join(all_texts)

        except Exception as e:
            logger.debug(f"Failed to extract subtitles for {bvid}: {e}")

        return None

    def _decode_html_entities(self, text: str) -> str:
        """
        Decode HTML entities in text.

        Args:
            text: Text with HTML entities

        Returns:
            Decoded text
        """
        if not text:
            return ""

        # Replace common HTML entities
        replacements = {
            "&quot;": '"',
            "&amp;": "&",
            "&lt;": "<",
            "&gt;": ">",
            "&nbsp;": " ",
            "&#39;": "'",
            "&rsquo;": "'",
            "&lsquo;": "'",
            "&rdquo;": '"',
            "&ldquo;": '"',
            "&mdash;": "—",
            "&hellip;": "…",
        }

        for entity, char in replacements.items():
            text = text.replace(entity, char)

        # Remove remaining HTML tags
        text = re.sub(r'<[^>]+>', '', text)

        return text.strip()

    def _extract_bvid(self, url: str) -> str:
        """Extract BV ID from URL."""
        match = re.search(r'BV[\w]+', url)
        if match:
            return match.group(0)

        # Fallback
        return str(hash(url))


# Helper for random (imported in method)
import random
