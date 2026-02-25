"""
API client for communicating with the Flask backend.
"""
import os
import sys
import requests
from typing import Dict, List, Optional, Any
from loguru import logger

# Add project path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import API_BASE_URL


class BackendAPI:
    """Client for Flask backend API calls."""

    def __init__(self, base_url: str = None):
        self.base_url = base_url or API_BASE_URL

    def get_health(self) -> Dict:
        """Check backend health."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "error", "error": str(e)}

    def get_statistics(self) -> Dict:
        """Get database statistics."""
        try:
            response = requests.get(f"{self.base_url}/api/stats", timeout=10)
            response.raise_for_status()
            result = response.json()
            if result.get('success'):
                return result.get('data', {})
            return {"error": result.get('error')}
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {"error": str(e)}

    def trigger_crawl(self, source: str = 'zhihu', max_pages: int = 1) -> Dict:
        """Trigger a crawl job."""
        try:
            payload = {"source": source, "max_pages": max_pages}
            response = requests.post(
                f"{self.base_url}/api/crawl",
                json=payload,
                timeout=300
            )
            response.raise_for_status()
            result = response.json()
            if result.get('success'):
                return result.get('data', {})
            return {"error": result.get('error')}
        except Exception as e:
            logger.error(f"Failed to trigger crawl: {e}")
            return {"error": str(e)}

    def export_articles(
        self,
        format_type: str = 'txt',
        category: Optional[str] = None,
        min_quality: float = 0.5
    ) -> Dict:
        """Export articles."""
        try:
            payload = {
                "format": format_type,
                "category": category,
                "min_quality": min_quality
            }
            response = requests.post(
                f"{self.base_url}/api/export",
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            result = response.json()
            if result.get('success'):
                return result.get('data', {})
            return {"error": result.get('error')}
        except Exception as e:
            logger.error(f"Failed to export articles: {e}")
            return {"error": str(e)}

    def sync_dify(self, hours: int = 24, min_quality: float = 0.6) -> Dict:
        """Sync articles to Dify knowledge base."""
        try:
            payload = {"hours": hours, "min_quality": min_quality}
            response = requests.post(
                f"{self.base_url}/api/sync-dify",
                json=payload,
                timeout=300
            )
            response.raise_for_status()
            result = response.json()
            if result.get('success'):
                return result.get('data', {})
            return {"error": result.get('error')}
        except Exception as e:
            logger.error(f"Failed to sync to Dify: {e}")
            return {"error": str(e)}

    def run_full_sync(self) -> Dict:
        """Run full sync workflow."""
        try:
            response = requests.post(
                f"{self.base_url}/api/run-full-sync",
                timeout=600
            )
            response.raise_for_status()
            result = response.json()
            if result.get('success'):
                return result.get('data', {})
            return {"error": result.get('error')}
        except Exception as e:
            logger.error(f"Failed to run full sync: {e}")
            return {"error": str(e)}


class DatabaseAPI:
    """Direct database access for operations not available via API."""

    def __init__(self):
        from storage.database import DatabaseManager
        self.db = DatabaseManager()

    def get_articles(
        self,
        source: Optional[str] = None,
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
        min_quality: Optional[float] = None,
        search: Optional[str] = None,
        is_valid: Optional[bool] = None,
        is_spam: Optional[bool] = None,
        sort_by: str = 'publish_time',
        sort_order: str = 'desc',
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        Get articles with filters and pagination.

        Returns dict with articles list and pagination info.
        """
        from sqlalchemy import and_, or_, desc, asc
        from storage.models import Article
        import json

        offset = (page - 1) * page_size

        with self.db.get_session() as session:
            query = session.query(Article)

            # Apply filters
            if is_valid is not None:
                query = query.filter(Article.is_valid == is_valid)
            if is_spam is not None:
                query = query.filter(Article.is_spam == is_spam)
            if source:
                query = query.filter(Article.source == source)
            if category:
                query = query.filter(Article.category == category)
            if subcategory:
                query = query.filter(Article.subcategory == subcategory)
            if min_quality is not None:
                query = query.filter(Article.quality_score >= min_quality)
            if search:
                search_pattern = f"%{search}%"
                query = query.filter(
                    or_(
                        Article.title.like(search_pattern),
                        Article.content.like(search_pattern),
                        Article.author.like(search_pattern)
                    )
                )

            # Get total count
            total = query.count()

            # Apply sorting
            order_col = getattr(Article, sort_by, Article.publish_time)
            if sort_order == 'desc':
                query = query.order_by(desc(order_col))
            else:
                query = query.order_by(asc(order_col))

            # Apply pagination
            articles = query.limit(page_size).offset(offset).all()

            # Convert to dict
            articles_data = []
            for article in articles:
                article_dict = article.to_dict()
                articles_data.append(article_dict)

            return {
                "articles": articles_data,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }

    def get_article_by_id(self, article_id: int) -> Optional[Dict]:
        """Get a single article by ID."""
        from storage.models import Article

        with self.db.get_session() as session:
            article = session.query(Article).filter(Article.id == article_id).first()
            if article:
                return article.to_dict()
            return None

    def update_article(self, article_id: int, data: Dict) -> bool:
        """Update an article."""
        from storage.models import Article

        with self.db.get_session() as session:
            article = session.query(Article).filter(Article.id == article_id).first()
            if not article:
                return False

            # Update allowed fields
            updatable_fields = [
                'title', 'content', 'author', 'category', 'subcategory',
                'sub_subcategory', 'quality_score', 'is_valid', 'is_spam'
            ]

            for field in updatable_fields:
                if field in data:
                    setattr(article, field, data[field])

            session.commit()
            return True

    def delete_articles(self, article_ids: List[int]) -> int:
        """Delete multiple articles."""
        from storage.models import Article

        with self.db.get_session() as session:
            deleted = session.query(Article).filter(
                Article.id.in_(article_ids)
            ).delete(synchronize_session=False)
            session.commit()
            return deleted

    def get_crawl_logs(self, limit: int = 50) -> List[Dict]:
        """Get recent crawl logs."""
        from storage.models import CrawlLog
        from sqlalchemy import desc

        with self.db.get_session() as session:
            logs = session.query(CrawlLog).order_by(
                desc(CrawlLog.start_time)
            ).limit(limit).all()

            return [log.to_dict() for log in logs]

    def get_categories(self) -> List[str]:
        """Get all unique categories."""
        from storage.models import Article
        from sqlalchemy import func

        with self.db.get_session() as session:
            categories = session.query(Article.category).filter(
                Article.category.isnot(None)
            ).distinct().all()
            return [c[0] for c in categories if c[0]]

    def get_subcategories(self, category: str = None) -> List[str]:
        """Get all unique subcategories, optionally filtered by category."""
        from storage.models import Article
        from sqlalchemy import func

        with self.db.get_session() as session:
            query = session.query(Article.subcategory).filter(
                Article.subcategory.isnot(None)
            )
            if category:
                query = query.filter(Article.category == category)
            subcategories = query.distinct().all()
            return [s[0] for s in subcategories if s[0]]


# Singleton instances
backend_api = BackendAPI()
database_api = DatabaseAPI()
