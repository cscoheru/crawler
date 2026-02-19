"""
Rule-based content classification using keyword matching.
"""
import re
from typing import Dict, List, Optional, Tuple
from loguru import logger

from config.keywords import KEYWORD_RULES, EXCLUSION_KEYWORDS


class RuleBasedClassifier:
    """Classify content using keyword matching rules."""

    def __init__(self, keyword_rules: Dict = None, exclusion_keywords: Dict = None):
        self.keyword_rules = keyword_rules or KEYWORD_RULES
        self.exclusion_keywords = exclusion_keywords or EXCLUSION_KEYWORDS

    def classify(self, title: str, content: str) -> Dict:
        """
        Classify article based on keyword matching.

        Args:
            title: Article title
            content: Article content

        Returns:
            Dictionary with category, confidence, and scores
        """
        # Combine title and content (title gets higher weight)
        text = f"{title} {title} {content}"  # Title counted twice

        scores = {}
        total_matches = {}

        # Calculate scores for each category
        for category, rule in self.keyword_rules.items():
            category_score = 0.0
            matches = []

            for keyword, weight in rule["keywords"].items():
                # Count keyword occurrences
                count = text.lower().count(keyword.lower())

                if count > 0:
                    # Score = weight * count (with diminishing returns)
                    match_score = weight * min(count, 5) / 5
                    category_score += match_score
                    matches.append((keyword, count))

            scores[category] = category_score
            total_matches[category] = matches

        # Normalize scores (0-1)
        max_score = max(scores.values()) if scores else 0
        if max_score > 0:
            normalized_scores = {k: v / max_score for k, v in scores.items()}
        else:
            normalized_scores = scores

        # Determine winner
        if max_score == 0:
            return {
                "category": "other",
                "confidence": 0.0,
                "scores": normalized_scores,
                "method": "rule_based"
            }

        # Find category with highest score
        best_category = max(normalized_scores, key=normalized_scores.get)
        confidence = normalized_scores[best_category]

        # Apply confidence threshold
        from config.settings import CONFIDENCE_THRESHOLD
        if confidence < CONFIDENCE_THRESHOLD:
            best_category = "other"

        return {
            "category": best_category,
            "confidence": round(confidence, 3),
            "all_scores": normalized_scores,
            "matched_keywords": total_matches.get(best_category, []),
            "method": "rule_based"
        }

    def classify_batch(self, articles: List[Dict]) -> List[Dict]:
        """
        Classify multiple articles.

        Args:
            articles: List of article dictionaries with title and content

        Returns:
            List of articles with classification added
        """
        classified_articles = []

        for article in articles:
            result = self.classify(
                title=article.get("title", ""),
                content=article.get("content", "")
            )

            # Merge classification result
            classified_article = {
                **article,
                "category": result["category"],
                "confidence": result["confidence"],
                "classification_method": result["method"]
            }

            classified_articles.append(classified_article)

            logger.debug(f"Classified: {article.get('title', 'N/A')[:50]}... "
                        f"-> {result['category']} ({result['confidence']:.2f})")

        return classified_articles

    def get_category_name(self, category_key: str) -> str:
        """
        Get display name for category key.

        Args:
            category_key: Category key (psychology, management, etc.)

        Returns:
            Display name
        """
        if category_key in self.keyword_rules:
            return self.keyword_rules[category_key]["name"]
        elif category_key == "other":
            return "其他"
        else:
            return category_key

    def should_filter(self, title: str, content: str) -> Tuple[bool, List[str]]:
        """
        Check if content should be filtered based on exclusion keywords.

        Args:
            title: Article title
            content: Article content

        Returns:
            (should_filter, matched_keywords)
        """
        combined_text = f"{title} {content}".lower()
        matched = []

        for category, keywords in self.exclusion_keywords.items():
            for keyword in keywords:
                if keyword.lower() in combined_text:
                    matched.append(f"{category}:{keyword}")

        return len(matched) > 0, matched

    def explain_classification(self, title: str, content: str) -> Dict:
        """
        Provide detailed explanation of classification.

        Args:
            title: Article title
            content: Article content

        Returns:
            Detailed classification explanation
        """
        result = self.classify(title, content)

        explanation = {
            "category": result["category"],
            "category_name": self.get_category_name(result["category"]),
            "confidence": result["confidence"],
            "method": result["method"],
            "all_scores": result["all_scores"],
            "matched_keywords": result["matched_keywords"],
            "recommendation": "accept" if result["confidence"] > 0.7 else "review"
        }

        # Check if should be filtered
        should_filter, filtered = self.should_filter(title, content)
        if should_filter:
            explanation["recommendation"] = "reject"
            explanation["filter_reasons"] = filtered

        return explanation
