"""
Base crawler class with common functionality.
"""
import time
import random
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Generator
from loguru import logger

from utils.anti_spider import AntiSpiderManager, RequestSession
from config.settings import PLATFORM_CONFIG


class BaseCrawler(ABC):
    """Base class for all crawlers."""

    def __init__(self, source: str, config: Dict = None):
        self.source = source
        self.config = config or PLATFORM_CONFIG.get(source, {})
        self.anti_spider = AntiSpiderManager(
            proxy_enabled=self.config.get("proxy_enabled", False),
            request_delay=self.config.get("delay_range", (3, 10))
        )
        self.session = RequestSession(self.anti_spider)

        logger.info(f"Initialized {self.source} crawler")

    @abstractmethod
    def search(self, keyword: str, max_pages: int = None) -> Generator[Dict, None, None]:
        """
        Search for articles by keyword.

        Args:
            keyword: Search keyword
            max_pages: Maximum number of pages to crawl

        Yields:
            Article data dictionaries
        """
        pass

    @abstractmethod
    def get_article_detail(self, article_url: str) -> Optional[Dict]:
        """
        Get full article details.

        Args:
            article_url: Article URL

        Returns:
            Article data dictionary or None if failed
        """
        pass

    def crawl_by_keywords(self, keywords: List[str], max_pages: int = None) -> List[Dict]:
        """
        Crawl articles for multiple keywords.

        Args:
            keywords: List of keywords to search
            max_pages: Maximum pages per keyword

        Returns:
            List of article dictionaries
        """
        all_articles = []

        for keyword in keywords:
            logger.info(f"Searching for keyword: {keyword}")

            try:
                for article in self.search(keyword, max_pages):
                    all_articles.append(article)

            except Exception as e:
                logger.error(f"Failed to search for keyword '{keyword}': {e}")

        # Remove duplicates based on URL
        seen_urls = set()
        unique_articles = []

        for article in all_articles:
            url = article.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_articles.append(article)

        logger.info(f"Found {len(unique_articles)} unique articles for {len(keywords)} keywords")

        return unique_articles

    def normalize_article_data(self, raw_data: Dict) -> Dict:
        """
        Normalize article data to standard format.

        Args:
            raw_data: Raw article data from crawler

        Returns:
            Normalized article dictionary
        """
        return {
            "source": self.source,
            "article_id": raw_data.get("id") or raw_data.get("article_id", ""),
            "title": raw_data.get("title", "").strip(),
            "content": raw_data.get("content", ""),
            "author": raw_data.get("author", ""),
            "publish_time": self._parse_time(raw_data.get("publish_time", raw_data.get("time", ""))),
            "url": raw_data.get("url", ""),
        }

    def _parse_time(self, time_str: str) -> Optional[str]:
        """
        Parse time string to ISO format.

        Args:
            time_str: Time string

        Returns:
            ISO format time string or None
        """
        # TODO: Implement proper time parsing for various formats
        # For now, return as-is
        return time_str if time_str else None

    def close(self):
        """Close crawler and cleanup resources."""
        if self.session:
            self.session.close()
        logger.info(f"Closed {self.source} crawler")
