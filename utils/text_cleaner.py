"""
Text cleaning and preprocessing utilities.
"""
import re
import html
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup
from loguru import logger


class TextCleaner:
    """Text cleaning and quality assessment."""

    def __init__(self, min_length: int = 200, max_length: int = 50000):
        self.min_length = min_length
        self.max_length = max_length

    def clean_html(self, html_content: str) -> str:
        """
        Remove HTML tags and decode HTML entities.

        Args:
            html_content: Raw HTML content

        Returns:
            Cleaned text content
        """
        if not html_content:
            return ""

        # Parse HTML
        soup = BeautifulSoup(html_content, 'lxml')

        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()

        # Get text
        text = soup.get_text()

        # Decode HTML entities
        text = html.unescape(text)

        return text

    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text content.

        Args:
            text: Raw text content

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove special characters but keep Chinese, English, numbers
        text = re.sub(r'[^\u4e00-\u9fff\w\s.,!?;:、。，！？；：""''《》（）]', '', text)

        # Remove excessive punctuation
        text = re.sub(r'[.,!?;:、。，！？；：]{2,}', '，', text)

        # Trim whitespace
        text = text.strip()

        return text

    def remove_duplicates(self, text: str) -> str:
        """
        Remove duplicate paragraphs or sentences.

        Args:
            text: Text content

        Returns:
            Text with duplicates removed
        """
        if not text:
            return ""

        # Split into paragraphs
        paragraphs = text.split('\n')

        # Remove duplicates while preserving order
        seen = set()
        unique_paragraphs = []
        for para in paragraphs:
            para = para.strip()
            if para and para not in seen:
                seen.add(para)
                unique_paragraphs.append(para)

        return '\n'.join(unique_paragraphs)

    def calculate_quality_score(self, text: str, title: str = "") -> float:
        """
        Calculate content quality score (0.0-1.0).

        Args:
            text: Content text
            title: Article title

        Returns:
            Quality score
        """
        if not text:
            return 0.0

        score = 0.0

        # Length score (0.3)
        length = len(text)
        if self.min_length <= length <= self.max_length:
            length_score = 1.0
        elif length < self.min_length:
            length_score = length / self.min_length
        else:
            length_score = max(0.5, 1.0 - (length - self.max_length) / self.max_length)
        score += length_score * 0.3

        # Title presence score (0.1)
        if title and len(title) >= 10:
            score += 0.1

        # Structure score (0.2) - has paragraphs
        paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
        if len(paragraphs) >= 3:
            score += 0.2
        elif len(paragraphs) >= 1:
            score += 0.1

        # Content richness score (0.2) - has variety of characters
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        numbers = len(re.findall(r'\d', text))

        if chinese_chars > 100:
            score += 0.1
        if english_chars > 10 or numbers > 5:
            score += 0.1

        # Punctuation score (0.2) - proper punctuation usage
        punctuation_count = len(re.findall(r'[，。！？；：""''《》（）]', text))
        if punctuation_count > length / 50:  # At least 1 punctuation per 50 chars
            score += 0.2
        elif punctuation_count > length / 100:
            score += 0.1

        return min(1.0, score)

    def check_spam_or_ads(self, text: str, title: str = "", exclusion_keywords: Dict[str, List[str]] = None) -> Tuple[bool, List[str]]:
        """
        Check if content contains spam or advertisement keywords.

        Args:
            text: Content text
            title: Article title
            exclusion_keywords: Dictionary of exclusion keyword lists

        Returns:
            (is_spam, matched_keywords)
        """
        if exclusion_keywords is None:
            from config.keywords import EXCLUSION_KEYWORDS
            exclusion_keywords = EXCLUSION_KEYWORDS

        combined_text = f"{title} {text}".lower()
        matched = []

        for category, keywords in exclusion_keywords.items():
            for keyword in keywords:
                if keyword.lower() in combined_text:
                    matched.append(f"{category}:{keyword}")

        return len(matched) > 0, matched

    def process_article(self, title: str, content: str, exclusion_keywords: Dict[str, List[str]] = None) -> Dict:
        """
        Complete article processing pipeline.

        Args:
            title: Article title
            content: Raw content (may contain HTML)
            exclusion_keywords: Exclusion keyword dictionary

        Returns:
            Processed article data dictionary
        """
        # Clean HTML
        if '<' in content and '>' in content:
            content = self.clean_html(content)

        # Clean text
        content = self.clean_text(content)
        title = self.clean_text(title)

        # Remove duplicates
        content = self.remove_duplicates(content)

        # Calculate quality score
        quality_score = self.calculate_quality_score(content, title)

        # Check for spam/ads
        is_spam, spam_keywords = self.check_spam_or_ads(content, title, exclusion_keywords)

        # Validate content length
        is_valid = (
            len(content) >= self.min_length
            and len(content) <= self.max_length
            and not is_spam
            and quality_score >= 0.5
        )

        return {
            "title": title,
            "content": content,
            "content_length": len(content),
            "quality_score": quality_score,
            "is_valid": is_valid,
            "is_spam": is_spam,
            "spam_keywords": spam_keywords,
        }

    def format_for_export(self, article_data: Dict, format: str = "txt") -> str:
        """
        Format article data for export.

        Args:
            article_data: Article data dictionary
            format: Export format (txt, json, csv)

        Returns:
            Formatted string
        """
        if format == "txt":
            return f"""标题: {article_data.get('title', 'N/A')}
来源: {article_data.get('source', 'N/A')}
作者: {article_data.get('author', 'N/A')}
发布时间: {article_data.get('publish_time', 'N/A')}
URL: {article_data.get('url', 'N/A')}
分类: {article_data.get('category', 'N/A')}
质量评分: {article_data.get('quality_score', 'N/A')}

{'='*80}

{article_data.get('content', '')}

{'='*80}
"""
        elif format == "json":
            import json
            return json.dumps(article_data, ensure_ascii=False, indent=2)
        elif format == "csv":
            import csv
            from io import StringIO
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=article_data.keys())
            writer.writeheader()
            writer.writerow(article_data)
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported format: {format}")


def clean_batch(articles: List[Dict]) -> List[Dict]:
    """
    Clean a batch of articles.

    Args:
        articles: List of article dictionaries with raw content

    Returns:
        List of processed article dictionaries
    """
    cleaner = TextCleaner()
    processed = []

    for article in articles:
        result = cleaner.process_article(
            title=article.get("title", ""),
            content=article.get("content", "")
        )

        # Merge original data with processing results
        processed_article = {**article, **result}

        if result["is_valid"]:
            processed.append(processed_article)
        else:
            logger.warning(f"Article filtered out: {article.get('title', 'Unknown')} - "
                         f"Reasons: spam={result['is_spam']}, quality={result['quality_score']:.2f}")

    return processed
