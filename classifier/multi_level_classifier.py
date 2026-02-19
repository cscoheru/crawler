"""
Multi-level rule-based classifier supporting 3-level taxonomy.
"""
import re
from typing import Dict, List, Optional, Tuple
from loguru import logger

from config.category_taxonomy import (
    CATEGORY_TAXONOMY,
    get_category_path,
    flatten_taxonomy,
    get_keywords_for_level
)


class MultiLevelClassifier:
    """
    Classify content into 3-level hierarchy:
    - Level 1: Category (psychology, management, finance)
    - Level 2: Subcategory (e.g., hr, strategy)
    - Level 3: Sub-subcategory (e.g., talent_management, blue_ocean)
    """

    def __init__(self, taxonomy: Dict = None):
        self.taxonomy = taxonomy or CATEGORY_TAXONOMY
        self.flat_taxonomy = flatten_taxonomy()

        logger.info(f"Initialized multi-level classifier with {len(self.flat_taxonomy)} leaf categories")

    def classify(self, title: str, content: str) -> Dict:
        """
        Classify article at all three levels.

        Args:
            title: Article title
            content: Article content

        Returns:
            Dictionary with classification at all levels
        """
        # Combine title and content (title gets higher weight)
        text = f"{title} {title} {content}"

        # Step 1: Classify at level 1 (category)
        category_result = self._classify_level_1(text)
        category = category_result["category"]

        # Step 2: Classify at level 2 (subcategory)
        subcategory_result = self._classify_level_2(text, category)

        # Step 3: Classify at level 3 (sub-subcategory)
        sub_subcategory_result = self._classify_level_3(
            text,
            category,
            subcategory_result["subcategory"]
        )

        # Assemble result
        result = {
            "category": category,
            "category_name": self.taxonomy[category]["name"],
            "category_confidence": category_result["confidence"],

            "subcategory": subcategory_result["subcategory"],
            "subcategory_name": subcategory_result.get("name", ""),
            "subcategory_confidence": subcategory_result["confidence"],

            "sub_subcategory": sub_subcategory_result["sub_subcategory"],
            "sub_subcategory_name": sub_subcategory_result.get("name", ""),
            "sub_subcategory_confidence": sub_subcategory_result["confidence"],

            "full_path": get_category_path(
                category,
                subcategory_result["subcategory"],
                sub_subcategory_result["sub_subcategory"]
            ),

            "method": "multi_level_rule_based"
        }

        # Calculate overall confidence (weighted average)
        result["overall_confidence"] = (
            category_result["confidence"] * 0.3 +
            subcategory_result["confidence"] * 0.3 +
            sub_subcategory_result["confidence"] * 0.4
        )

        return result

    def _classify_level_1(self, text: str) -> Dict:
        """
        Classify at level 1 (top-level category).

        Args:
            text: Text content

        Returns:
            Dictionary with category and confidence
        """
        scores = {}

        for category_key, category_data in self.taxonomy.items():
            score = 0.0
            total_keywords = 0

            # Collect all keywords at this level
            for sub_data in category_data["subcategories"].values():
                for sub_sub_data in sub_data["sub_subcategories"].values():
                    for keyword in sub_sub_data["keywords"]:
                        total_keywords += 1
                        count = text.lower().count(keyword.lower())
                        if count > 0:
                            score += min(count, 3)  # Diminishing returns

            scores[category_key] = score

        # Normalize
        max_score = max(scores.values()) if scores else 0
        if max_score > 0:
            scores = {k: v / max_score for k, v in scores.items()}

        best_category = max(scores, key=scores.get) if scores else "other"
        confidence = scores.get(best_category, 0.0)

        return {
            "category": best_category,
            "confidence": round(confidence, 3),
            "all_scores": scores
        }

    def _classify_level_2(self, text: str, category: str) -> Dict:
        """
        Classify at level 2 (subcategory).

        Args:
            text: Text content
            category: Parent category

        Returns:
            Dictionary with subcategory and confidence
        """
        if category not in self.taxonomy:
            return {
                "subcategory": None,
                "confidence": 0.0,
                "name": ""
            }

        subcategories = self.taxonomy[category]["subcategories"]
        scores = {}

        for sub_key, sub_data in subcategories.items():
            score = 0.0

            for sub_sub_data in sub_data["sub_subcategories"].values():
                for keyword in sub_sub_data["keywords"]:
                    count = text.lower().count(keyword.lower())
                    if count > 0:
                        score += min(count, 3)

            scores[sub_key] = score

        # Normalize
        max_score = max(scores.values()) if scores else 0
        if max_score > 0:
            scores = {k: v / max_score for k, v in scores.items()}

        best_subcategory = max(scores, key=scores.get) if scores else None
        confidence = scores.get(best_subcategory, 0.0) if best_subcategory else 0.0

        return {
            "subcategory": best_subcategory,
            "confidence": round(confidence, 3),
            "name": subcategories[best_subcategory]["name"] if best_subcategory else "",
            "all_scores": scores
        }

    def _classify_level_3(
        self,
        text: str,
        category: str,
        subcategory: str
    ) -> Dict:
        """
        Classify at level 3 (sub-subcategory).

        Args:
            text: Text content
            category: Parent category
            subcategory: Parent subcategory

        Returns:
            Dictionary with sub-subcategory and confidence
        """
        if category not in self.taxonomy:
            return {
                "sub_subcategory": None,
                "confidence": 0.0,
                "name": ""
            }

        subcategories = self.taxonomy[category]["subcategories"]

        if subcategory not in subcategories:
            return {
                "sub_subcategory": None,
                "confidence": 0.0,
                "name": ""
            }

        sub_subcategories = subcategories[subcategory]["sub_subcategories"]
        scores = {}

        for sub_sub_key, sub_sub_data in sub_subcategories.items():
            score = 0.0

            for keyword in sub_sub_data["keywords"]:
                count = text.lower().count(keyword.lower())
                if count > 0:
                    # More weight for exact matches
                    if keyword.lower() in text.lower():
                        score += min(count * 1.5, 5)

            scores[sub_sub_key] = score

        # Normalize
        max_score = max(scores.values()) if scores else 0
        if max_score > 0:
            scores = {k: v / max_score for k, v in scores.items()}

        best_sub_subcategory = max(scores, key=scores.get) if scores else None
        confidence = scores.get(best_sub_subcategory, 0.0) if best_sub_subcategory else 0.0

        return {
            "sub_subcategory": best_sub_subcategory,
            "confidence": round(confidence, 3),
            "name": sub_subcategories[best_sub_subcategory]["name"] if best_sub_subcategory else "",
            "all_scores": scores,
            "matched_keywords": self._get_matched_keywords(
                text,
                sub_subcategories[best_sub_subcategory]["keywords"]
            ) if best_sub_subcategory else []
        }

    def _get_matched_keywords(self, text: str, keywords: List[str]) -> List[str]:
        """Get list of keywords that matched in text."""
        matched = []
        text_lower = text.lower()

        for keyword in keywords:
            if keyword.lower() in text_lower:
                matched.append(keyword)

        return matched

    def classify_batch(self, articles: List[Dict]) -> List[Dict]:
        """
        Classify multiple articles.

        Args:
            articles: List of article dictionaries

        Returns:
            List of articles with multi-level classification added
        """
        classified_articles = []

        for i, article in enumerate(articles):
            result = self.classify(
                title=article.get("title", ""),
                content=article.get("content", "")
            )

            # Merge classification result
            classified_article = {
                **article,
                "category": result["category"],
                "subcategory": result["subcategory"],
                "sub_subcategory": result["sub_subcategory"],
                "category_path": result["full_path"],
                "confidence": result["overall_confidence"],
                "classification_method": result["method"]
            }

            classified_articles.append(classified_article)

            if (i + 1) % 10 == 0:
                logger.info(f"Classified {i + 1}/{len(articles)} articles")

        return classified_articles

    def explain_classification(self, title: str, content: str) -> Dict:
        """
        Provide detailed explanation of multi-level classification.

        Args:
            title: Article title
            content: Article content

        Returns:
            Detailed classification explanation
        """
        result = self.classify(title, content)

        explanation = {
            "article_title": title,
            "classification": result,
            "recommendation": "accept" if result["overall_confidence"] > 0.7 else "review"
        }

        # Add confidence assessment
        if result["overall_confidence"] > 0.8:
            explanation["confidence_level"] = "high"
            explanation["note"] = "分类置信度高，可直接使用"
        elif result["overall_confidence"] > 0.5:
            explanation["confidence_level"] = "medium"
            explanation["note"] = "分类置信度中等，建议人工复核"
        else:
            explanation["confidence_level"] = "low"
            explanation["note"] = "分类置信度低，建议人工分类或使用AI分类"

        return explanation

    def get_taxonomy_stats(self) -> Dict:
        """
        Get statistics about the taxonomy.

        Returns:
            Taxonomy statistics
        """
        stats = {
            "total_categories": len(self.taxonomy),
            "categories": {}
        }

        for cat_key, cat_data in self.taxonomy.items():
            sub_count = len(cat_data["subcategories"])
            sub_sub_count = sum(
                len(sub_data["sub_subcategories"])
                for sub_data in cat_data["subcategories"].values()
            )

            stats["categories"][cat_key] = {
                "name": cat_data["name"],
                "subcategories": sub_count,
                "sub_subcategories": sub_sub_count
            }

        return stats


# Convenience function for backward compatibility
def classify_article(title: str, content: str) -> Dict:
    """
    Quick classification function.

    Args:
        title: Article title
        content: Article content

    Returns:
        Classification result
    """
    classifier = MultiLevelClassifier()
    return classifier.classify(title, content)
