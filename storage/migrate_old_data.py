"""
Migration script to update old articles with default values for new HuggingFace fields.
Run this script after updating the database schema to set default values for existing records.
"""
import sys
import os

# Add project path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
from storage.database import DatabaseManager
from storage.models import Article


def migrate_old_articles():
    """
    Migrate existing articles to set default values for new fields.

    Sets:
    - content_type: Based on source (article/social/news)
    - language: Default to "zh"
    """
    db = DatabaseManager()

    try:
        with db.get_session() as session:
            # Find articles without content_type set
            old_articles = session.query(Article).filter(
                Article.content_type == None
            ).all()

            logger.info(f"Found {len(old_articles)} articles to migrate")

            updated_count = 0
            for article in old_articles:
                # Set content_type based on source
                if article.source == "weibo":
                    article.content_type = "social"
                elif article.source == "toutiao":
                    article.content_type = "news"
                elif article.source in ["chnsenticorp", "lcqmc"]:
                    article.content_type = "review" if article.source == "chnsenticorp" else "qa"
                else:
                    article.content_type = "article"

                # Set default language
                article.language = article.language or "zh"

                updated_count += 1

                if updated_count % 100 == 0:
                    logger.info(f"Updated {updated_count}/{len(old_articles)} articles")

            session.commit()
            logger.info(f"Migration completed: {updated_count} articles updated")

            # Summary statistics
            summary = session.query(Article.content_type, func.count(Article.id)).group_by(Article.content_type).all()
            logger.info("Summary by content_type:")
            for content_type, count in summary:
                logger.info(f"  {content_type}: {count}")

            return updated_count

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise


if __name__ == "__main__":
    from sqlalchemy import func

    logger.info("Starting migration...")
    count = migrate_old_articles()
    logger.info(f"Migration completed successfully: {count} articles updated")
