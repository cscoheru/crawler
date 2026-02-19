"""
Dify knowledge base integration module.
Automatically syncs crawled articles to Dify knowledge base via API.
"""
import os
import json
import time
from typing import List, Dict, Optional
from loguru import logger
import requests

from config.settings import PROCESSED_DATA_DIR


class DifyKnowledgeBase:
    """Client for Dify knowledge base API."""

    def __init__(self, api_key: str = None, base_url: str = None):
        """
        Initialize Dify KB client.

        Args:
            api_key: Dify API key (default: from env var DIFY_API_KEY)
            base_url: Dify base URL (default: from env var DIFY_BASE_URL)
        """
        self.api_key = api_key or os.getenv("DIFY_API_KEY", "")
        self.base_url = base_url or os.getenv("DIFY_BASE_URL", "http://localhost:3001")
        self.dataset_api = f"{self.base_url}/api/v1"

        if not self.api_key:
            logger.warning("No Dify API key provided. Set DIFY_API_KEY environment variable.")

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        logger.info("Initialized Dify knowledge base client")

    def create_document_from_text(
        self,
        title: str,
        content: str,
        metadata: Dict = None
    ) -> Optional[Dict]:
        """
        Create a document in Dify knowledge base from text.

        Args:
            title: Document title
            content: Document content
            metadata: Optional metadata dictionary

        Returns:
            API response or None if failed
        """
        if not self.api_key:
            logger.error("Cannot create document: No API key configured")
            return None

        try:
            # Prepare document data
            document_data = {
                "name": title,
                "text": content,
                "indexing_technique": "high_quality",
                "process_rule": {
                    "mode": "automatic"
                }
            }

            if metadata:
                document_data["metadata"] = metadata

            # Create document via API
            url = f"{self.dataset_api}/datasets/{os.getenv('DIFY_DATASET_ID', '')}/documents/create-by-text"

            response = requests.post(
                url,
                headers=self.headers,
                json=document_data,
                timeout=30
            )

            if response.status_code in (200, 201):
                result = response.json()
                logger.info(f"Created document in Dify: {title}")
                return result
            else:
                logger.warning(f"Failed to create document: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"Error creating document in Dify: {e}")
            return None

    def create_document_from_file(self, filepath: str, metadata: Dict = None) -> Optional[Dict]:
        """
        Create a document in Dify knowledge base from file.

        Args:
            filepath: Path to the file
            metadata: Optional metadata dictionary

        Returns:
            API response or None if failed
        """
        if not self.api_key:
            logger.error("Cannot create document: No API key configured")
            return None

        if not os.path.exists(filepath):
            logger.error(f"File not found: {filepath}")
            return None

        try:
            with open(filepath, 'rb') as f:
                files = {'file': f}

                data = {
                    "indexing_technique": "high_quality",
                    "process_rule": json.dumps({"mode": "automatic"})
                }

                if metadata:
                    data["metadata"] = json.dumps(metadata)

                url = f"{self.dataset_api}/datasets/{os.getenv('DIFY_DATASET_ID', '')}/documents/create-by-file"

                response = requests.post(
                    url,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    data=data,
                    files=files,
                    timeout=60
                )

                if response.status_code in (200, 201):
                    result = response.json()
                    logger.info(f"Created document from file in Dify: {filepath}")
                    return result
                else:
                    logger.warning(f"Failed to create document from file: {response.status_code}")
                    return None

        except Exception as e:
            logger.error(f"Error creating document from file in Dify: {e}")
            return None

    def sync_articles_to_dify(
        self,
        articles: List[Dict],
        batch_size: int = 10,
        delay: float = 1.0
    ) -> Dict[str, int]:
        """
        Sync multiple articles to Dify knowledge base.

        Args:
            articles: List of article dictionaries
            batch_size: Number of articles to process in each batch
            delay: Delay between API calls (seconds)

        Returns:
            Dictionary with success and failure counts
        """
        success_count = 0
        failed_count = 0

        logger.info(f"Starting sync of {len(articles)} articles to Dify")

        for i, article in enumerate(articles):
            try:
                # Prepare metadata
                metadata = {
                    "source": article.get("source", ""),
                    "category": article.get("category", ""),
                    "subcategory": article.get("subcategory", ""),
                    "author": article.get("author", ""),
                    "url": article.get("url", "")
                }

                # Create document from text
                result = self.create_document_from_text(
                    title=article.get("title", "Untitled"),
                    content=article.get("content", ""),
                    metadata=metadata
                )

                if result:
                    success_count += 1
                else:
                    failed_count += 1

                # Rate limiting
                if (i + 1) % batch_size == 0:
                    logger.info(f"Processed {i + 1}/{len(articles)} articles")
                    time.sleep(delay * 5)  # Longer pause between batches

                time.sleep(delay)

            except Exception as e:
                logger.error(f"Failed to sync article {article.get('title', 'Unknown')}: {e}")
                failed_count += 1

        logger.info(f"Sync completed: {success_count} succeeded, {failed_count} failed")

        return {
            "success": success_count,
            "failed": failed_count,
            "total": len(articles)
        }

    def sync_exported_files_to_dify(
        self,
        export_dir: str,
        file_pattern: str = "*.txt",
        metadata_filter: Dict = None
    ) -> Dict[str, int]:
        """
        Sync exported TXT files to Dify knowledge base.

        Args:
            export_dir: Directory containing exported files
            file_pattern: File pattern to match (default: *.txt)
            metadata_filter: Optional metadata filter

        Returns:
            Dictionary with success and failure counts
        """
        import glob

        files = glob.glob(os.path.join(export_dir, file_pattern))
        logger.info(f"Found {len(files)} files to sync")

        success_count = 0
        failed_count = 0

        for filepath in files:
            try:
                # Extract metadata from filename
                filename = os.path.basename(filepath)
                parts = filename.split('_')

                metadata = {
                    "source": parts[0] if len(parts) > 0 else "",
                    "article_id": parts[1].replace('.txt', '') if len(parts) > 1 else ""
                }

                if metadata_filter:
                    metadata.update(metadata_filter)

                result = self.create_document_from_file(filepath, metadata)

                if result:
                    success_count += 1
                else:
                    failed_count += 1

                time.sleep(1)  # Rate limiting

            except Exception as e:
                logger.error(f"Failed to sync file {filepath}: {e}")
                failed_count += 1

        logger.info(f"File sync completed: {success_count} succeeded, {failed_count} failed")

        return {
            "success": success_count,
            "failed": failed_count,
            "total": len(files)
        }


class DifyBatchSyncer:
    """Batch sync articles from database to Dify."""

    def __init__(self, dify_client: DifyKnowledgeBase = None):
        self.dify = dify_client or DifyKnowledgeBase()

    def sync_recent_articles(
        self,
        db_manager,
        hours: int = 24,
        min_quality: float = 0.6
    ) -> Dict[str, int]:
        """
        Sync recent articles from database to Dify.

        Args:
            db_manager: DatabaseManager instance
            hours: Only sync articles from last N hours
            min_quality: Minimum quality score

        Returns:
            Sync result dictionary
        """
        from datetime import datetime, timedelta

        # Get recent articles
        cutoff_time = datetime.now() - timedelta(hours=hours)

        with db_manager.get_session() as session:
            from storage.models import Article

            articles = session.query(Article).filter(
                Article.created_at >= cutoff_time,
                Article.quality_score >= min_quality,
                Article.is_valid == True
            ).limit(500).all()

            logger.info(f"Found {len(articles)} articles to sync from last {hours} hours")

            # Convert to dictionaries
            article_dicts = [article.to_dict() for article in articles]

        # Sync to Dify
        return self.dify.sync_articles_to_dify(article_dicts)

    def export_and_sync(
        self,
        db_manager,
        output_dir: str = None,
        category: str = None,
        min_quality: float = 0.6
    ) -> str:
        """
        Export articles to files and sync to Dify.

        Args:
            db_manager: DatabaseManager instance
            output_dir: Output directory for exports
            category: Filter by category
            min_quality: Minimum quality score

        Returns:
            Path to exported files
        """
        output_dir = output_dir or os.path.join(PROCESSED_DATA_DIR, "dify_export")
        os.makedirs(output_dir, exist_ok=True)

        # Export to TXT
        logger.info(f"Exporting articles to {output_dir}")
        db_manager.export_articles_to_txt(
            output_dir=output_dir,
            category=category,
            min_quality=min_quality
        )

        # Sync to Dify
        logger.info("Syncing exported files to Dify")
        self.dify.sync_exported_files_to_dify(output_dir)

        return output_dir
