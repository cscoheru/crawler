"""
Database models for scraped content.
"""
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class Article(Base):
    """Article model for storing scraped content."""

    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(50), nullable=False)  # zhihu, toutiao, wechat
    article_id = Column(String(100), nullable=False)  # Unique ID from source
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    author = Column(String(200))
    publish_time = Column(DateTime)
    url = Column(Text)
    # Multi-level classification
    category = Column(String(50))  # psychology, management, finance, other
    subcategory = Column(String(50))  # hr, strategy, clinical, etc.
    sub_subcategory = Column(String(50))  # talent_management, blue_ocean, depression, etc.
    category_path = Column(Text)  # JSON array of full category path

    confidence = Column(Float, default=0.0)  # Classification confidence
    quality_score = Column(Float, default=0.0)  # Content quality score
    is_valid = Column(Boolean, default=True)
    is_spam = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Unique constraint
    __table_args__ = (
        Index('idx_source_article_id', 'source', 'article_id', unique=True),
        Index('idx_category', 'category'),
        Index('idx_publish_time', 'publish_time'),
        Index('idx_quality_score', 'quality_score'),
    )

    def to_dict(self):
        """Convert model to dictionary."""
        import json
        return {
            "id": self.id,
            "source": self.source,
            "article_id": self.article_id,
            "title": self.title,
            "content": self.content,
            "author": self.author,
            "publish_time": self.publish_time.isoformat() if self.publish_time else None,
            "url": self.url,
            "category": self.category,
            "subcategory": self.subcategory,
            "sub_subcategory": self.sub_subcategory,
            "category_path": json.loads(self.category_path) if self.category_path else [],
            "confidence": self.confidence,
            "quality_score": self.quality_score,
            "is_valid": self.is_valid,
            "is_spam": self.is_spam,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class CrawlLog(Base):
    """Crawl execution log."""

    __tablename__ = "crawl_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(50), nullable=False)  # zhihu, toutiao, wechat
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    success_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    error_msg = Column(Text)
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        Index('idx_source_start_time', 'source', 'start_time'),
    )

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "source": self.source,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "success_count": self.success_count,
            "failed_count": self.failed_count,
            "error_msg": self.error_msg,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Keyword(Base):
    """Keyword configuration for classification."""

    __tablename__ = "keywords"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(50), nullable=False)
    keyword = Column(String(100), nullable=False)
    weight = Column(Float, default=1.0)

    __table_args__ = (
        Index('idx_category_keyword', 'category', 'keyword', unique=True),
    )

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "category": self.category,
            "keyword": self.keyword,
            "weight": self.weight,
        }
