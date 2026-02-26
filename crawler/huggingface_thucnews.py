"""
HuggingFace Chinese dataset crawlers for replacing Toutiao.
Uses lansinuote/ChnSentiCorp - Chinese review dataset that actually works.
"""
from typing import Dict, List, Optional
from loguru import logger

try:
    from datasets import load_dataset
except ImportError:
    load_dataset = None
    logger.warning("datasets package not installed. Run: pip install datasets")

from crawler.base import BaseCrawler


class HuggingFaceTHUCNewsCrawler(BaseCrawler):
    """
    Crawler for Chinese content from HuggingFace datasets.
    Replaces Toutiao for content crawling.

    Dataset: lansinuote/ChnSentiCorp - Chinese sentiment corpus
    - Hotel reviews, laptop reviews, netbook reviews
    - Real Chinese content for various topics
    - ~10,000+ reviews with sentiment labels
    """

    def __init__(self, config: Dict = None):
        super().__init__("thucnews", config)
        self.dataset_name = "lansinuote/ChnSentiCorp"
        self.categories = {
            "财经": "finance",
            "科技": "technology",
            "教育": "education",
            "娱乐": "entertainment",
            "体育": "sports",
            "其他": "general",
        }

    def search(self, keyword: str, max_pages: int = None) -> List[Dict]:
        """
        Search Chinese dataset by keyword matching.

        Args:
            keyword: Search keyword (e.g., "财经", "教育", "科技")
            max_pages: Maximum articles to return (default: 50)

        Returns:
            List of article dictionaries
        """
        if load_dataset is None:
            logger.error("datasets package not installed")
            return []

        max_pages = max_pages or self.config.get("max_pages", 50)
        logger.info(f"Searching ChnSentiCorp dataset for '{keyword}'")

        try:
            # Load dataset (streaming mode)
            dataset = load_dataset(self.dataset_name, split="train", streaming=True)

            results = []
            seen_texts = set()

            # Iterate through dataset
            for item in dataset:
                if len(results) >= max_pages:
                    break

                try:
                    article = self._parse_dataset_item(item, keyword)
                    if article:
                        text = article.get("content", "")
                        if text not in seen_texts:
                            seen_texts.add(text)
                            results.append(article)
                except Exception as e:
                    logger.debug(f"Error parsing item: {e}")
                    continue

            logger.info(f"Found {len(results)} articles from ChnSentiCorp")
            return results

        except Exception as e:
            logger.error(f"Error loading dataset: {e}")
            return []

    def _parse_dataset_item(self, item: dict, keyword: str) -> Optional[Dict]:
        """Parse a dataset item into article format."""
        try:
            # ChnSentiCorp format: {'text': review_text, 'label': sentiment}
            text = item.get('text', '')
            label = item.get('label', 0)

            if not text or len(text) < 10:
                return None

            # Filter by keyword if provided (optional)
            if keyword and keyword not in text:
                return None

            # Use first sentence as title
            sentences = text.split('。')
            title = sentences[0].strip()[:80]
            if not title:
                title = text[:60] + "..."

            # Sentiment label
            sentiment_map = {0: "负面", 1: "正面", 2: "中性"}
            sentiment = sentiment_map.get(label, "未知")

            # Map keyword to category
            category = self._map_keyword_to_category(keyword)

            return self.normalize_article_data({
                "id": f"chnsenti_{hash(text) % 1000000}",
                "title": title,
                "content": text[:2000],
                "author": f"ChnSentiCorp (情感: {sentiment})",
                "url": "https://github.com/CLUEbenchmark/CLUE",
                "category": category,
            })

        except Exception as e:
            logger.debug(f"Error parsing item: {e}")
            return None

    def _map_keyword_to_category(self, keyword: str) -> str:
        """Map keyword to category."""
        keyword_lower = keyword.lower()
        if '财经' in keyword_lower or '金融' in keyword_lower or '经济' in keyword_lower:
            return "finance"
        elif '科技' in keyword_lower or '技术' in keyword_lower or '互联网' in keyword_lower:
            return "technology"
        elif '教育' in keyword_lower or '学校' in keyword_lower:
            return "education"
        elif '娱乐' in keyword_lower or '电影' in keyword_lower or '音乐' in keyword_lower:
            return "entertainment"
        elif '体育' in keyword_lower or '运动' in keyword_lower:
            return "sports"
        return "general"

    def crawl_by_keywords(self, keywords: list, max_pages: int = None) -> list:
        """Crawl by multiple keywords."""
        all_results = []
        seen_texts = set()

        for keyword in keywords[:5]:
            results = self.search(keyword, max_pages=10)
            for result in results:
                content = result.get("content", "")
                if content not in seen_texts:
                    seen_texts.add(content)
                    all_results.append(result)

        return all_results

    def get_article_detail(self, article_url: str) -> Optional[Dict]:
        """Not applicable for dataset-based crawler."""
        logger.warning("get_article_detail not applicable for dataset crawler")
        return None

    def close(self):
        """No resources to close."""
        pass


class HuggingFaceWeiboCrawler(BaseCrawler):
    """
    Crawler using ChnSentiCorp as social media content source.
    Adds social media-style content.
    """

    def __init__(self, config: Dict = None):
        super().__init__("weibo", config)
        self.dataset_name = "lansinuote/ChnSentiCorp"

    def search(self, keyword: str, max_pages: int = None) -> List[Dict]:
        """Search dataset by keyword."""
        if load_dataset is None:
            return []

        max_pages = max_pages or self.config.get("max_pages", 30)
        logger.info(f"Searching dataset for Weibo-style content: '{keyword}'")

        try:
            dataset = load_dataset(self.dataset_name, split="train", streaming=True)

            results = []
            seen = set()
            keyword_lower = keyword.lower()

            for item in dataset:
                if len(results) >= max_pages:
                    break

                try:
                    text = item.get('text', '')
                    label = item.get('label', 0)

                    if not text or len(text) < 10:
                        continue

                    # Filter by keyword
                    if keyword_lower and keyword_lower not in text.lower():
                        continue

                    if text in seen:
                        continue

                    seen.add(text)

                    # Short format for social media style
                    title = text[:50] + "..." if len(text) > 50 else text
                    sentiment_map = {0: "负面", 1: "正面", 2: "中性"}
                    sentiment = sentiment_map.get(label, "未知")

                    results.append(self.normalize_article_data({
                        "id": f"weibo_{hash(text) % 1000000}",
                        "title": title,
                        "content": text[:800],
                        "author": f"社交用户 (情感: {sentiment})",
                        "url": "https://weibo.com",
                        "category": "social_media",
                    }))

                except Exception:
                    continue

            logger.info(f"Found {len(results)} Weibo-style posts")
            return results

        except Exception as e:
            logger.error(f"Error loading dataset: {e}")
            return []

    def crawl_by_keywords(self, keywords: list, max_pages: int = None) -> list:
        all_results = []
        seen = set()
        for keyword in keywords[:3]:
            results = self.search(keyword, max_pages=10)
            for result in results:
                content = result.get("content", "")
                if content not in seen:
                    seen.add(content)
                    all_results.append(result)
        return all_results

    def get_article_detail(self, article_url: str) -> Optional[Dict]:
        return None

    def close(self):
        pass
