"""
Additional HuggingFace Chinese dataset crawlers.
Includes various Chinese NLP datasets for diverse content sources.
"""
import json
from typing import Dict, List, Optional
from loguru import logger

try:
    from datasets import load_dataset
except ImportError:
    load_dataset = None
    logger.warning("datasets package not installed. Run: pip install datasets")

from crawler.base import BaseCrawler


class HuggingFaceLCQMCrawler(BaseCrawler):
    """
    Crawler for LCQMC (Large-scale Chinese Question Matching Corpus).
    Useful for Q&A content and conversation data.

    Dataset: clue/lcqmc or similar
    - 260,000+ question pairs
    - Semantic similarity labeled
    """

    def __init__(self, config: Dict = None):
        super().__init__("lcqmc", config)
        self.dataset_name = "clue/lcqmc"

    def search(self, keyword: str, max_pages: int = None) -> List[Dict]:
        """Search LCQMC question pairs by keyword."""
        if load_dataset is None:
            return []

        max_pages = max_pages or self.config.get("max_pages", 30)
        logger.info(f"Searching LCQMC for '{keyword}'")

        try:
            dataset = load_dataset(self.dataset_name, split="train", streaming=True)

            results = []
            seen = set()
            keyword_lower = keyword.lower()

            for item in dataset:
                if len(results) >= max_pages:
                    break

                try:
                    question1 = item.get('question1', '')
                    question2 = item.get('question2', '')
                    label = item.get('label', 0)

                    # Check if keyword in either question
                    text = f"{question1} {question2}"
                    if keyword_lower and keyword_lower not in text.lower():
                        continue

                    if text in seen:
                        continue

                    seen.add(text)

                    # Create combined Q&A content
                    is_match = "similar" if label == 1 else "not_similar"

                    results.append(self.normalize_article_data({
                        "id": f"lcqmc_{hash(text) % 1000000}",
                        "title": f"Q: {question1[:50]}...",
                        "content": f"问题1: {question1}\n问题2: {question2}"[:1000],
                        "author": "LCQMC语料库",
                        "url": "https://github.com/CLUEbenchmark/CLUE",
                        "category": "qa",
                        # New HuggingFace fields
                        "content_type": "qa",
                        "question": question1,
                        "answer": question2,
                        "similarity": is_match,
                        "dataset_source": self.dataset_name,
                        "language": "zh",
                    }))

                except Exception:
                    continue

            logger.info(f"Found {len(results)} LCQMC entries")
            return results

        except Exception as e:
            logger.error(f"Error loading LCQMC: {e}")
            return []

    def crawl_by_keywords(self, keywords: list, max_pages: int = None) -> list:
        all_results = []
        for keyword in keywords[:3]:
            all_results.extend(self.search(keyword, max_pages=10))
        return all_results

    def get_article_detail(self, article_url: str) -> Optional[Dict]:
        return None

    def close(self):
        pass


class HuggingFaceCMNLUCrawler(BaseCrawler):
    """
    Crawler for CMNLU (Chinese Multi-Task Natural Language Understanding).
    General Chinese NLP dataset with diverse content.

    Dataset: clue/cmnlu
    """

    def __init__(self, config: Dict = None):
        super().__init__("cmnlu", config)
        self.dataset_name = "clue/cmnlu"

    def search(self, keyword: str, max_pages: int = None) -> List[Dict]:
        """Search CMNLU dataset."""
        if load_dataset is None:
            return []

        max_pages = max_pages or self.config.get("max_pages", 30)
        logger.info(f"Searching CMNLU for '{keyword}'")

        try:
            dataset = load_dataset(self.dataset_name, split="train", streaming=True)

            results = []
            seen = set()
            keyword_lower = keyword.lower()

            for item in dataset:
                if len(results) >= max_pages:
                    break

                try:
                    sentence = item.get('sentence', '')
                    label = item.get('label', '')

                    if keyword_lower and keyword_lower not in sentence.lower():
                        continue

                    if sentence in seen:
                        continue

                    seen.add(sentence)

                    results.append(self.normalize_article_data({
                        "id": f"cmnlu_{hash(sentence) % 1000000}",
                        "title": sentence[:60] + "..." if len(sentence) > 60 else sentence,
                        "content": sentence[:1000],
                        "author": f"CMNLU标注 ({label})",
                        "url": "https://github.com/CLUEbenchmark/CLUE",
                        "category": "general",
                        # New HuggingFace fields
                        "content_type": "article",
                        "dataset_source": self.dataset_name,
                        "language": "zh",
                    }))

                except Exception:
                    continue

            logger.info(f"Found {len(results)} CMNLU entries")
            return results

        except Exception as e:
            logger.error(f"Error loading CMNLU: {e}")
            return []

    def crawl_by_keywords(self, keywords: list, max_pages: int = None) -> list:
        all_results = []
        for keyword in keywords[:3]:
            all_results.extend(self.search(keyword, max_pages=10))
        return all_results

    def get_article_detail(self, article_url: str) -> Optional[Dict]:
        return None

    def close(self):
        pass


class HuggingFaceC3Crawler(BaseCrawler):
    """
    Crawler for C3 (Chinese Children's Clinic) dataset.
    Mix of elementary school math and Chinese questions.

    Dataset:☺️
    """

    def __init__(self, config: Dict = None):
        super().__init__("c3", config)
        self.dataset_name = "cmnli/c3"

    def search(self, keyword: str, max_pages: int = None) -> List[Dict]:
        """Search C3 dataset."""
        if load_dataset is None:
            return []

        max_pages = max_pages or self.config.get("max_pages", 30)
        logger.info(f"Searching C3 for '{keyword}'")

        try:
            dataset = load_dataset(self.dataset_name, split="train", streaming=True)

            results = []
            seen = set()
            keyword_lower = keyword.lower()

            for item in dataset:
                if len(results) >= max_pages:
                    break

                try:
                    question = item.get('question', '')
                    choices = item.get('choices', [])
                    answer = item.get('answer', '')

                    text = f"{question} {' '.join(choices)}"
                    if keyword_lower and keyword_lower not in text.lower():
                        continue

                    if text in seen:
                        continue

                    seen.add(text)

                    results.append(self.normalize_article_data({
                        "id": f"c3_{hash(text) % 1000000}",
                        "title": question[:60] + "..." if len(question) > 60 else question,
                        "content": f"问题: {question}\n选项: {', '.join(choices)}\n答案: {answer}"[:1000],
                        "author": "C3儿童数据集",
                        "url": "https://github.com/CLUEbenchmark/CLUE",
                        "category": "education",
                        # New HuggingFace fields
                        "content_type": "qa",
                        "question": question,
                        "choices": choices,
                        "answer": answer,
                        "dataset_source": self.dataset_name,
                        "language": "zh",
                    }))

                except Exception:
                    continue

            logger.info(f"Found {len(results)} C3 entries")
            return results

        except Exception as e:
            logger.error(f"Error loading C3: {e}")
            return []

    def crawl_by_keywords(self, keywords: list, max_pages: int = None) -> list:
        all_results = []
        for keyword in keywords[:3]:
            all_results.extend(self.search(keyword, max_pages=10))
        return all_results

    def get_article_detail(self, article_url: str) -> Optional[Dict]:
        return None

    def close(self):
        pass


class HuggingFaceChnSentiCorpCrawler(BaseCrawler):
    """
    Crawler for ChnSentiCorp (Chinese Sentiment Corpus).
    Hotel, laptop, and netbook reviews.

    Dataset: lansinuote/ChnSentiCorp
    """

    def __init__(self, config: Dict = None):
        super().__init__("chnsenticorp", config)
        self.dataset_name = "lansinuote/ChnSentiCorp"

    def search(self, keyword: str, max_pages: int = None) -> List[Dict]:
        """Search ChnSentiCorp reviews."""
        if load_dataset is None:
            return []

        max_pages = max_pages or (self.config or {}).get("max_pages", 30)
        logger.info(f"Searching ChnSentiCorp for '{keyword}'")

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

                    if keyword_lower and keyword_lower not in text.lower():
                        continue

                    if text in seen:
                        continue

                    seen.add(text)

                    sentiment_map = {0: "negative", 1: "positive", 2: "neutral"}
                    sentiment = sentiment_map.get(label, "neutral")

                    results.append(self.normalize_article_data({
                        "id": f"chnsenti_{hash(text) % 1000000}",
                        "title": text[:60] + "..." if len(text) > 60 else text,
                        "content": text[:1000],
                        "author": f"ChnSentiCorp (情感: {sentiment})",
                        "url": "https://github.com/CLUEbenchmark/CLUE",
                        "category": "review",
                        # New HuggingFace fields
                        "content_type": "review",
                        "sentiment": sentiment,
                        "sentiment_label": label,
                        "dataset_source": self.dataset_name,
                        "language": "zh",
                    }))

                except Exception:
                    continue

            logger.info(f"Found {len(results)} ChnSentiCorp reviews")
            return results

        except Exception as e:
            logger.error(f"Error loading ChnSentiCorp: {e}")
            return []

    def crawl_by_keywords(self, keywords: list, max_pages: int = None) -> list:
        all_results = []
        for keyword in keywords[:3]:
            all_results.extend(self.search(keyword, max_pages=10))
        return all_results

    def get_article_detail(self, article_url: str) -> Optional[Dict]:
        return None

    def close(self):
        pass
