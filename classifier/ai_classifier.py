"""
AI-powered content classification using LLM APIs.
"""
import json
import time
from typing import Dict, List, Optional
from loguru import logger

try:
    from zhipuai import ZhipuAI
except ImportError:
    ZhipuAI = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from config.settings import (
    ZHIPUAI_API_KEY,
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL,
    AI_CLASSIFIER_MODEL,
    AI_API_TIMEOUT
)


class AIClassifier:
    """Classify content using AI models (ZhipuAI or DeepSeek)."""

    def __init__(
        self,
        model: str = None,
        api_key: str = None,
        base_url: str = None,
        max_retries: int = 3
    ):
        self.model = model or AI_CLASSIFIER_MODEL
        self.max_retries = max_retries
        self.api_key = api_key
        self.base_url = base_url

        # Initialize client based on model
        if self.model == "zhipu":
            if not ZHIPUAI:
                raise ImportError("zhipuai package not installed")
            self.client = ZhipuAI(api_key=api_key or ZHIPUAI_API_KEY)
        elif self.model == "deepseek":
            if not OpenAI:
                raise ImportError("openai package not installed")
            self.client = OpenAI(
                api_key=api_key or DEEPSEEK_API_KEY,
                base_url=base_url or DEEPSEEK_BASE_URL
            )
        else:
            raise ValueError(f"Unsupported model: {self.model}")

        logger.info(f"Initialized AI classifier with model: {self.model}")

    def _create_prompt(self, title: str, content: str, max_length: int = 3000) -> str:
        """
        Create classification prompt.

        Args:
            title: Article title
            content: Article content
            max_length: Maximum content length

        Returns:
            Prompt string
        """
        # Truncate content if too long
        if len(content) > max_length:
            content = content[:max_length] + "..."

        prompt = f"""请分析以下文章内容，判断其所属类别。

文章标题: {title}

文章内容:
{content}

请从以下类别中选择最合适的一个：
1. 心理咨询 - 包括心理健康、心理治疗、心理咨询、情绪管理等内容
2. 企业管理 - 包括企业管理、战略管理、团队建设、领导力等内容
3. 财务会计税务 - 包括会计、税务、财务、审计等内容
4. 其他 - 不属于以上任何类别的文章

请以JSON格式返回结果，格式如下：
{{
    "category": "类别名称（心理咨询/企业管理/财务会计税务/其他）",
    "confidence": 0.95,
    "reasoning": "简要说明分类理由"
}}

注意：confidence应该是0到1之间的数值，表示分类的置信度。"""

        return prompt

    def _parse_response(self, response_text: str) -> Dict:
        """
        Parse AI response.

        Args:
            response_text: Response text from AI

        Returns:
            Parsed classification result
        """
        # Try to extract JSON from response
        try:
            # Find JSON in response
            start = response_text.find("{")
            end = response_text.rfind("}") + 1

            if start >= 0 and end > start:
                json_str = response_text[start:end]
                result = json.loads(json_str)

                # Validate result
                if "category" in result:
                    # Map Chinese category names to keys
                    category_mapping = {
                        "心理咨询": "psychology",
                        "企业管理": "management",
                        "财务会计税务": "finance",
                        "其他": "other"
                    }

                    category_key = category_mapping.get(result["category"], "other")

                    return {
                        "category": category_key,
                        "confidence": float(result.get("confidence", 0.5)),
                        "reasoning": result.get("reasoning", ""),
                        "method": f"ai_{self.model}"
                    }
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse AI response: {e}")

        # Fallback: try to extract category from text
        if "心理咨询" in response_text:
            category = "psychology"
        elif "企业管理" in response_text:
            category = "management"
        elif "财务会计税务" in response_text or "财务" in response_text:
            category = "finance"
        else:
            category = "other"

        return {
            "category": category,
            "confidence": 0.5,  # Low confidence for fallback
            "reasoning": "Parsed from non-JSON response",
            "method": f"ai_{self.model}_fallback"
        }

    def classify(self, title: str, content: str, max_retries: int = None) -> Dict:
        """
        Classify article using AI.

        Args:
            title: Article title
            content: Article content
            max_retries: Maximum number of retries

        Returns:
            Classification result dictionary
        """
        max_retries = max_retries or self.max_retries
        prompt = self._create_prompt(title, content)

        for attempt in range(max_retries):
            try:
                if self.model == "zhipu":
                    response = self.client.chat.completions.create(
                        model="glm-4",
                        messages=[
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.3,
                    )
                    result_text = response.choices[0].message.content

                elif self.model == "deepseek":
                    response = self.client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.3,
                    )
                    result_text = response.choices[0].message.content

                # Parse response
                result = self._parse_response(result_text)

                logger.debug(f"AI classified: {title[:50]}... -> {result['category']} ({result['confidence']:.2f})")

                return result

            except Exception as e:
                logger.warning(f"AI classification attempt {attempt + 1} failed: {e}")

                if attempt < max_retries - 1:
                    # Exponential backoff
                    wait_time = (2 ** attempt) + 1
                    logger.debug(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    # Return fallback result
                    logger.error(f"All AI classification attempts failed for: {title[:50]}")
                    return {
                        "category": "other",
                        "confidence": 0.0,
                        "reasoning": f"API error: {str(e)}",
                        "method": f"ai_{self.model}_error"
                    }

    def classify_batch(self, articles: List[Dict], delay: float = 1.0) -> List[Dict]:
        """
        Classify multiple articles with rate limiting.

        Args:
            articles: List of article dictionaries
            delay: Delay between requests in seconds

        Returns:
            List of articles with classification added
        """
        classified_articles = []

        for i, article in enumerate(articles):
            if i > 0 and delay > 0:
                time.sleep(delay)

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

            logger.info(f"Classified {i + 1}/{len(articles)}: {article.get('title', 'N/A')[:50]}... "
                       f"-> {result['category']} ({result['confidence']:.2f})")

        return classified_articles


class HybridClassifier:
    """Hybrid classifier combining rule-based and AI classification."""

    def __init__(
        self,
        rule_classifier=None,
        ai_classifier=None,
        confidence_threshold: float = 0.7
    ):
        from classifier.rule_based import RuleBasedClassifier

        self.rule_classifier = rule_classifier or RuleBasedClassifier()
        self.ai_classifier = ai_classifier
        self.confidence_threshold = confidence_threshold

        logger.info("Initialized hybrid classifier")

    def classify(self, title: str, content: str) -> Dict:
        """
        Classify using rule-based first, fall back to AI if confidence low.

        Args:
            title: Article title
            content: Article content

        Returns:
            Classification result
        """
        # Try rule-based first
        rule_result = self.rule_classifier.classify(title, content)

        # If confidence is high enough, return rule-based result
        if rule_result["confidence"] >= self.confidence_threshold:
            logger.debug(f"Rule-based classification accepted (confidence: {rule_result['confidence']:.2f})")
            return rule_result

        # Otherwise, use AI if available
        if self.ai_classifier:
            logger.debug(f"Rule-based confidence low ({rule_result['confidence']:.2f}), using AI")
            return self.ai_classifier.classify(title, content)
        else:
            logger.warning("AI classifier not available, returning rule-based result")
            return rule_result

    def classify_batch(self, articles: List[Dict]) -> List[Dict]:
        """
        Classify batch using hybrid approach.

        Args:
            articles: List of article dictionaries

        Returns:
            List of classified articles
        """
        classified = []

        for article in articles:
            result = self.classify(
                title=article.get("title", ""),
                content=article.get("content", "")
            )

            classified_article = {
                **article,
                "category": result["category"],
                "confidence": result["confidence"],
                "classification_method": result["method"]
            }

            classified.append(classified_article)

        return classified
