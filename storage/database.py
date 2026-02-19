"""
Database operations and connection management.
"""
import os
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy import create_engine, and_, or_
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError
from contextlib import contextmanager
from loguru import logger

from config.settings import DATABASE_URL
from storage.models import Base, Article, CrawlLog, Keyword


class DatabaseManager:
    """Manage database connections and operations."""

    def __init__(self, database_url: str = None):
        self.database_url = database_url or DATABASE_URL
        self.engine = create_engine(
            self.database_url,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            echo=False
        )
        self.SessionLocal = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)

        # Create tables if they don't exist
        self.init_db()

    def init_db(self):
        """Initialize database tables."""
        try:
            Base.metadata.create_all(self.engine)
            logger.info("Database tables initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    @contextmanager
    def get_session(self) -> Session:
        """Get database session with context manager."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            session.close()

    def save_article(self, article_data: Dict) -> Optional[Article]:
        """
        Save a single article to database.

        Args:
            article_data: Article data dictionary

        Returns:
            Article object if saved successfully, None if duplicate
        """
        try:
            import json

            with self.get_session() as session:
                # Handle category_path - convert list to JSON string
                category_path = article_data.get("category_path")
                if isinstance(category_path, list):
                    category_path = json.dumps(category_path, ensure_ascii=False)

                article = Article(
                    source=article_data.get("source"),
                    article_id=article_data.get("article_id"),
                    title=article_data.get("title"),
                    content=article_data.get("content"),
                    author=article_data.get("author"),
                    publish_time=article_data.get("publish_time"),
                    url=article_data.get("url"),
                    category=article_data.get("category"),
                    subcategory=article_data.get("subcategory"),
                    sub_subcategory=article_data.get("sub_subcategory"),
                    category_path=category_path,
                    confidence=article_data.get("confidence", 0.0),
                    quality_score=article_data.get("quality_score", 0.0),
                    is_valid=article_data.get("is_valid", True),
                    is_spam=article_data.get("is_spam", False),
                )

                session.add(article)
                session.commit()
                session.refresh(article)

                logger.debug(f"Saved article: {article.title[:50]}")
                return article

        except IntegrityError:
            logger.debug(f"Duplicate article: {article_data.get('article_id')}")
            return None
        except Exception as e:
            logger.error(f"Failed to save article: {e}")
            return None

    def save_articles_batch(self, articles: List[Dict]) -> Dict[str, int]:
        """
        Save multiple articles in batch.

        Args:
            articles: List of article data dictionaries

        Returns:
            Dictionary with success and failed counts
        """
        success_count = 0
        failed_count = 0
        duplicate_count = 0

        for article_data in articles:
            result = self.save_article(article_data)
            if result:
                success_count += 1
            elif result is None:
                duplicate_count += 1
            else:
                failed_count += 1

        return {
            "success": success_count,
            "failed": failed_count,
            "duplicate": duplicate_count,
            "total": len(articles)
        }

    def get_articles(
        self,
        source: Optional[str] = None,
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
        sub_subcategory: Optional[str] = None,
        min_quality: Optional[float] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Article]:
        """
        Query articles with filters.

        Args:
            source: Filter by source
            category: Filter by category
            subcategory: Filter by subcategory
            sub_subcategory: Filter by sub-subcategory
            min_quality: Minimum quality score
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of Article objects
        """
        with self.get_session() as session:
            query = session.query(Article).filter(Article.is_valid == True, Article.is_spam == False)

            if source:
                query = query.filter(Article.source == source)
            if category:
                query = query.filter(Article.category == category)
            if subcategory:
                query = query.filter(Article.subcategory == subcategory)
            if sub_subcategory:
                query = query.filter(Article.sub_subcategory == sub_subcategory)
            if min_quality:
                query = query.filter(Article.quality_score >= min_quality)

            articles = query.order_by(Article.publish_time.desc()).limit(limit).offset(offset).all()
            return articles

    def export_articles_to_txt(
        self,
        output_dir: str,
        source: Optional[str] = None,
        category: Optional[str] = None,
        min_quality: Optional[float] = None
    ) -> str:
        """
        Export articles to TXT files (one file per article).

        Args:
            output_dir: Output directory path
            source: Filter by source
            category: Filter by category
            min_quality: Minimum quality score

        Returns:
            Path to output directory
        """
        os.makedirs(output_dir, exist_ok=True)

        # Fetch articles
        articles = self.get_articles(source=source, category=category, min_quality=min_quality, limit=10000)

        # Export to TXT files
        for article in articles:
            import json
            category_path = json.loads(article.category_path) if article.category_path else []
            category_path_str = " > ".join(category_path) if category_path else (article.category or "N/A")

            filename = f"{article.source}_{article.article_id}.txt"
            # Remove invalid characters from filename
            filename = "".join(c if c.isalnum() or c in ('-', '_', '.') else '_' for c in filename)
            filepath = os.path.join(output_dir, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"标题: {article.title}\n")
                f.write(f"来源: {article.source}\n")
                f.write(f"作者: {article.author or 'N/A'}\n")
                f.write(f"发布时间: {article.publish_time or 'N/A'}\n")
                f.write(f"URL: {article.url or 'N/A'}\n")
                f.write(f"一级分类: {article.category or 'N/A'}\n")
                f.write(f"二级分类: {article.subcategory or 'N/A'}\n")
                f.write(f"三级分类: {article.sub_subcategory or 'N/A'}\n")
                f.write(f"分类路径: {category_path_str}\n")
                f.write(f"质量评分: {article.quality_score:.2f}\n")
                f.write(f"分类置信度: {article.confidence:.2f}\n")
                f.write("\n")
                f.write("=" * 80 + "\n")
                f.write("\n")
                f.write(article.content)
                f.write("\n")
                f.write("=" * 80 + "\n")

        logger.info(f"Exported {len(articles)} articles to {output_dir}")
        return output_dir

    def export_articles_to_json(
        self,
        output_file: str,
        source: Optional[str] = None,
        category: Optional[str] = None,
        min_quality: Optional[float] = None
    ) -> str:
        """
        Export articles to JSON file.

        Args:
            output_file: Output JSON file path
            source: Filter by source
            category: Filter by category
            min_quality: Minimum quality score

        Returns:
            Path to output file
        """
        import json

        articles = self.get_articles(source=source, category=category, min_quality=min_quality, limit=10000)

        data = [article.to_dict() for article in articles]

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"Exported {len(articles)} articles to {output_file}")
        return output_file

    def export_articles_to_csv(
        self,
        output_file: str,
        source: Optional[str] = None,
        category: Optional[str] = None,
        min_quality: Optional[float] = None
    ) -> str:
        """
        Export articles to CSV file.

        Args:
            output_file: Output CSV file path
            source: Filter by source
            category: Filter by category
            min_quality: Minimum quality score

        Returns:
            Path to output file
        """
        import pandas as pd

        articles = self.get_articles(source=source, category=category, min_quality=min_quality, limit=10000)

        data = [article.to_dict() for article in articles]
        df = pd.DataFrame(data)

        df.to_csv(output_file, index=False, encoding='utf-8-sig')

        logger.info(f"Exported {len(articles)} articles to {output_file}")
        return output_file

    def create_crawl_log(self, source: str) -> CrawlLog:
        """
        Create a new crawl log entry.

        Args:
            source: Source name

        Returns:
            CrawlLog object
        """
        with self.get_session() as session:
            log = CrawlLog(
                source=source,
                start_time=datetime.now(),
                success_count=0,
                failed_count=0
            )
            session.add(log)
            session.commit()
            session.refresh(log)
            return log

    def update_crawl_log(self, log_id: int, success_count: int = 0, failed_count: int = 0, error_msg: str = None):
        """
        Update crawl log with results.

        Args:
            log_id: Log entry ID
            success_count: Number of successful articles
            failed_count: Number of failed articles
            error_msg: Error message if any
        """
        with self.get_session() as session:
            log = session.query(CrawlLog).filter(CrawlLog.id == log_id).first()
            if log:
                log.end_time = datetime.now()
                log.success_count = success_count
                log.failed_count = failed_count
                log.error_msg = error_msg
                session.commit()

    def get_statistics(self) -> Dict:
        """
        Get database statistics.

        Returns:
            Statistics dictionary
        """
        with self.get_session() as session:
            total_articles = session.query(Article).count()
            valid_articles = session.query(Article).filter(Article.is_valid == True).count()

            stats_by_source = {}
            for source in ["zhihu", "toutiao", "wechat"]:
                count = session.query(Article).filter(
                    and_(Article.source == source, Article.is_valid == True)
                ).count()
                stats_by_source[source] = count

            stats_by_category = {}
            for category in ["psychology", "management", "finance", "other"]:
                count = session.query(Article).filter(
                    and_(Article.category == category, Article.is_valid == True)
                ).count()
                stats_by_category[category] = count

            avg_quality = session.query(Article.quality_score).filter(
                Article.is_valid == True
            ).all()
            avg_quality = sum([s[0] for s in avg_quality]) / len(avg_quality) if avg_quality else 0

            return {
                "total_articles": total_articles,
                "valid_articles": valid_articles,
                "by_source": stats_by_source,
                "by_category": stats_by_category,
                "average_quality_score": round(avg_quality, 2),
            }

    def close(self):
        """Close database connection."""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connection closed")
