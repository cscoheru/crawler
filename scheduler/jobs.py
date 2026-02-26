"""
Scheduled jobs for automated crawling and processing.
"""
import os
from datetime import datetime
from typing import Dict, List
from loguru import logger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from config.settings import SCHEDULER_TIMEZONE, SCHEDULER_JOBS, SEARCH_KEYWORDS
from storage.database import DatabaseManager
from classifier.multi_level_classifier import MultiLevelClassifier
from classifier.ai_classifier import HybridClassifier


class CrawlerScheduler:
    """Manage scheduled crawling tasks."""

    def __init__(self, db_manager: DatabaseManager = None, use_multi_level: bool = True):
        self.db_manager = db_manager or DatabaseManager()
        self.scheduler = AsyncIOScheduler(timezone=SCHEDULER_TIMEZONE)

        # Use multi-level classifier by default
        if use_multi_level:
            self.classifier = MultiLevelClassifier()
            logger.info("Using multi-level classifier (3-level hierarchy)")
        else:
            from classifier.rule_based import RuleBasedClassifier
            self.classifier = RuleBasedClassifier()
            logger.info("Using single-level classifier")

        logger.info("Initialized crawler scheduler")

    def setup_jobs(self):
        """Setup all scheduled jobs."""
        # Zhihu crawling job
        self.scheduler.add_job(
            self._crawl_zhihu_job,
            trigger=CronTrigger(
                hour=SCHEDULER_JOBS["zhihu"]["hour"],
                minute=SCHEDULER_JOBS["zhihu"]["minute"],
                timezone=SCHEDULER_TIMEZONE
            ),
            id="crawl_zhihu",
            name="Crawl Zhihu articles",
            replace_existing=True
        )

        # Toutiao crawling job
        self.scheduler.add_job(
            self._crawl_toutiao_job,
            trigger=CronTrigger(
                hour=SCHEDULER_JOBS["toutiao"]["hour"],
                minute=SCHEDULER_JOBS["toutiao"]["minute"],
                timezone=SCHEDULER_TIMEZONE
            ),
            id="crawl_toutiao",
            name="Crawl Toutiao articles",
            replace_existing=True
        )

        # WeChat crawling job
        self.scheduler.add_job(
            self._crawl_wechat_job,
            trigger=CronTrigger(
                hour=SCHEDULER_JOBS["wechat"]["hour"],
                minute=SCHEDULER_JOBS["wechat"]["minute"],
                timezone=SCHEDULER_TIMEZONE
            ),
            id="crawl_wechat",
            name="Crawl WeChat articles",
            replace_existing=True
        )

        # Bilibili crawling job
        if "bilibili" in SCHEDULER_JOBS:
            self.scheduler.add_job(
                self._crawl_bilibili_job,
                trigger=CronTrigger(
                    hour=SCHEDULER_JOBS["bilibili"]["hour"],
                    minute=SCHEDULER_JOBS["bilibili"]["minute"],
                    timezone=SCHEDULER_TIMEZONE
                ),
                id="crawl_bilibili",
                name="Crawl Bilibili videos",
                replace_existing=True
            )

        # Dedao crawling job
        if "dedao" in SCHEDULER_JOBS:
            self.scheduler.add_job(
                self._crawl_dedao_job,
                trigger=CronTrigger(
                    hour=SCHEDULER_JOBS["dedao"]["hour"],
                    minute=SCHEDULER_JOBS["dedao"]["minute"],
                    timezone=SCHEDULER_TIMEZONE
                ),
                id="crawl_dedao",
                name="Crawl Dedao courses",
                replace_existing=True
            )

        # Ximalaya crawling job
        if "ximalaya" in SCHEDULER_JOBS:
            self.scheduler.add_job(
                self._crawl_ximalaya_job,
                trigger=CronTrigger(
                    hour=SCHEDULER_JOBS["ximalaya"]["hour"],
                    minute=SCHEDULER_JOBS["ximalaya"]["minute"],
                    timezone=SCHEDULER_TIMEZONE
                ),
                id="crawl_ximalaya",
                name="Crawl Ximalaya albums",
                replace_existing=True
            )

        # Weibo dataset crawling job
        if "weibo" in SCHEDULER_JOBS:
            self.scheduler.add_job(
                self._crawl_weibo_job,
                trigger=CronTrigger(
                    hour=SCHEDULER_JOBS["weibo"]["hour"],
                    minute=SCHEDULER_JOBS["weibo"]["minute"],
                    timezone=SCHEDULER_TIMEZONE
                ),
                id="crawl_weibo",
                name="Crawl Weibo dataset",
                replace_existing=True
            )

        # Dify sync job
        if "dify_sync" in SCHEDULER_JOBS:
            self.scheduler.add_job(
                self._dify_sync_job,
                trigger=CronTrigger(
                    hour=SCHEDULER_JOBS["dify_sync"]["hour"],
                    minute=SCHEDULER_JOBS["dify_sync"]["minute"],
                    timezone=SCHEDULER_TIMEZONE
                ),
                id="dify_sync",
                name="Sync articles to Dify knowledge base",
                replace_existing=True
            )

        # Classification job
        self.scheduler.add_job(
            self._classify_articles_job,
            trigger=CronTrigger(
                hour=SCHEDULER_JOBS["classify"]["hour"],
                minute=SCHEDULER_JOBS["classify"]["minute"],
                timezone=SCHEDULER_TIMEZONE
            ),
            id="classify_articles",
            name="Classify unclassified articles",
            replace_existing=True
        )

        # Quality check job
        self.scheduler.add_job(
            self._quality_check_job,
            trigger=CronTrigger(
                hour=SCHEDULER_JOBS["quality_check"]["hour"],
                minute=SCHEDULER_JOBS["quality_check"]["minute"],
                timezone=SCHEDULER_TIMEZONE
            ),
            id="quality_check",
            name="Check data quality",
            replace_existing=True
        )

        logger.info(f"Setup {len(self.scheduler.get_jobs())} scheduled jobs")

    def start(self):
        """Start the scheduler."""
        self.setup_jobs()
        self.scheduler.start()
        logger.info("Scheduler started")

    def stop(self):
        """Stop the scheduler."""
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")

    async def _crawl_zhihu_job(self):
        """Execute Zhihu crawling job using Hugging Face dataset."""
        logger.info("=" * 60)
        logger.info(f"Starting Zhihu data collection from Hugging Face: {datetime.now()}")
        logger.info("=" * 60)

        # Use Hugging Face dataset instead of web scraping
        from crawler.huggingface_zhihu import HuggingFaceZhihuCrawler

        crawler = HuggingFaceZhihuCrawler()
        log = self.db_manager.create_crawl_log("zhihu")

        try:
            all_articles = []

            # Collect for each keyword category
            for category, keywords in SEARCH_KEYWORDS.items():
                logger.info(f"Fetching from Hugging Face for category: {category}")

                articles = crawler.crawl_by_keywords(keywords[:5], max_pages=5)
                all_articles.extend(articles)

            # Also get some random samples for diversity
            logger.info("Fetching random samples for diversity...")
            random_samples = crawler.get_random_samples(n=50)
            all_articles.extend(random_samples)

            # Clean and classify
            from utils.text_cleaner import clean_batch
            cleaned_articles = clean_batch(all_articles)
            classified_articles = self.classifier.classify_batch(cleaned_articles)

            # Save to database
            result = self.db_manager.save_articles_batch(classified_articles)

            # Update log
            self.db_manager.update_crawl_log(
                log.id,
                success_count=result["success"],
                failed_count=result["failed"]
            )

            logger.info(f"Zhihu data collection completed: {result['success']} articles saved, "
                       f"{result['duplicate']} duplicates, {result['failed']} failed")

        except Exception as e:
            logger.error(f"Zhihu data collection job failed: {e}")
            self.db_manager.update_crawl_log(log.id, error_msg=str(e))

        finally:
            crawler.close()

    async def _crawl_toutiao_job(self):
        """Execute Toutiao crawling job using THUCNews dataset."""
        logger.info("=" * 60)
        logger.info(f"Starting scheduled THUCNews dataset crawling: {datetime.now()}")
        logger.info("=" * 60)

        from crawler.huggingface_thucnews import HuggingFaceTHUCNewsCrawler

        crawler = HuggingFaceTHUCNewsCrawler()
        log = self.db_manager.create_crawl_log("toutiao")

        try:
            all_articles = []

            for category, keywords in SEARCH_KEYWORDS.items():
                logger.info(f"Searching THUCNews dataset for category: {category}")

                articles = crawler.crawl_by_keywords(keywords[:5], max_pages=20)
                all_articles.extend(articles)

            # Clean and classify
            from utils.text_cleaner import clean_batch
            cleaned_articles = clean_batch(all_articles)
            classified_articles = self.classifier.classify_batch(cleaned_articles)

            # Save
            result = self.db_manager.save_articles_batch(classified_articles)

            self.db_manager.update_crawl_log(
                log.id,
                success_count=result["success"],
                failed_count=result["failed"]
            )

            logger.info(f"THUCNews dataset crawling completed: {result['success']} articles saved")

        except Exception as e:
            logger.error(f"THUCNews dataset crawling job failed: {e}")
            self.db_manager.update_crawl_log(log.id, error_msg=str(e))

    async def _crawl_wechat_job(self):
        """Execute WeChat crawling job."""
        logger.info("=" * 60)
        logger.info(f"Starting scheduled WeChat crawling: {datetime.now()}")
        logger.info("=" * 60)

        from crawler.wechat import WeChatCrawler

        crawler = WeChatCrawler()
        log = self.db_manager.create_crawl_log("wechat")

        try:
            all_articles = []

            for category, keywords in SEARCH_KEYWORDS.items():
                logger.info(f"Searching WeChat for category: {category}")

                articles = crawler.crawl_by_keywords(keywords[:3], max_pages=2)
                all_articles.extend(articles)

            # Clean and classify
            from utils.text_cleaner import clean_batch
            cleaned_articles = clean_batch(all_articles)
            classified_articles = self.classifier.classify_batch(cleaned_articles)

            # Save
            result = self.db_manager.save_articles_batch(classified_articles)

            self.db_manager.update_crawl_log(
                log.id,
                success_count=result["success"],
                failed_count=result["failed"]
            )

            logger.info(f"WeChat crawling completed: {result['success']} articles saved")

        except Exception as e:
            logger.error(f"WeChat crawling job failed: {e}")
            self.db_manager.update_crawl_log(log.id, error_msg=str(e))

    async def _crawl_bilibili_job(self):
        """Execute Bilibili crawling job."""
        logger.info("=" * 60)
        logger.info(f"Starting scheduled Bilibili crawling: {datetime.now()}")
        logger.info("=" * 60)

        from crawler.bilibili import BilibiliCrawler

        crawler = BilibiliCrawler()
        log = self.db_manager.create_crawl_log("bilibili")

        try:
            all_articles = []

            for category, keywords in SEARCH_KEYWORDS.items():
                logger.info(f"Searching Bilibili for category: {category}")

                articles = crawler.crawl_by_keywords(keywords[:3], max_pages=2)
                all_articles.extend(articles)

            # Clean and classify
            from utils.text_cleaner import clean_batch
            cleaned_articles = clean_batch(all_articles)
            classified_articles = self.classifier.classify_batch(cleaned_articles)

            # Save
            result = self.db_manager.save_articles_batch(classified_articles)

            self.db_manager.update_crawl_log(
                log.id,
                success_count=result["success"],
                failed_count=result["failed"]
            )

            logger.info(f"Bilibili crawling completed: {result['success']} articles saved")

        except Exception as e:
            logger.error(f"Bilibili crawling job failed: {e}")
            self.db_manager.update_crawl_log(log.id, error_msg=str(e))

    async def _classify_articles_job(self):
        """Classify articles that haven't been classified yet."""
        logger.info("=" * 60)
        logger.info(f"Starting classification job: {datetime.now()}")
        logger.info("=" * 60)

        try:
            from storage.models import Article
            from storage.database import DatabaseManager

            # Get unclassified articles
            with self.db_manager.get_session() as session:
                unclassified = session.query(Article).filter(
                    (Article.category == None) | (Article.category == "")
                ).limit(100).all()

                logger.info(f"Found {len(unclassified)} unclassified articles")

                # Prepare for classification
                articles_to_classify = [article.to_dict() for article in unclassified]

            # Classify
            classified = self.classifier.classify_batch(articles_to_classify)

            # Update database
            updated_count = 0
            for article_data in classified:
                with self.db_manager.get_session() as session:
                    article = session.query(Article).filter(
                        Article.source == article_data["source"],
                        Article.article_id == article_data["article_id"]
                    ).first()

                    if article:
                        article.category = article_data["category"]
                        article.confidence = article_data["confidence"]
                        updated_count += 1
                        session.commit()

            logger.info(f"Classification completed: {updated_count} articles updated")

        except Exception as e:
            logger.error(f"Classification job failed: {e}")

    async def _crawl_dedao_job(self):
        """Execute Dedao crawling job using Playwright."""
        logger.info("=" * 60)
        logger.info(f"Starting scheduled Dedao crawling: {datetime.now()}")
        logger.info("=" * 60)

        from crawler.dedao_playwright import DedaoCrawlerPlaywright

        crawler = DedaoCrawlerPlaywright()
        log = self.db_manager.create_crawl_log("dedao")

        try:
            all_articles = []

            for category, keywords in SEARCH_KEYWORDS.items():
                logger.info(f"Searching Dedao (Playwright) for category: {category}")

                # Limit to fewer keywords due to Playwright overhead
                for keyword in keywords[:2]:
                    articles = list(crawler.search(keyword, max_pages=1))
                    all_articles.extend(articles)

            # Clean and classify
            from utils.text_cleaner import clean_batch
            cleaned_articles = clean_batch(all_articles)
            classified_articles = self.classifier.classify_batch(cleaned_articles)

            # Save
            result = self.db_manager.save_articles_batch(classified_articles)

            self.db_manager.update_crawl_log(
                log.id,
                success_count=result["success"],
                failed_count=result["failed"]
            )

            logger.info(f"Dedao crawling completed: {result['success']} articles saved")

        except Exception as e:
            logger.error(f"Dedao crawling job failed: {e}")
            self.db_manager.update_crawl_log(log.id, error_msg=str(e))

        finally:
            await crawler.close()

    async def _crawl_ximalaya_job(self):
        """Execute Ximalaya crawling job using category browsing."""
        logger.info("=" * 60)
        logger.info(f"Starting scheduled Ximalaya crawling: {datetime.now()}")
        logger.info("=" * 60)

        from crawler.ximalaya_fixed import XimalayaCrawlerFixed

        crawler = XimalayaCrawlerFixed()
        log = self.db_manager.create_crawl_log("ximalaya")

        try:
            all_articles = []

            for category, keywords in SEARCH_KEYWORDS.items():
                logger.info(f"Searching Ximalaya (category browsing) for category: {category}")

                # Limit to fewer keywords for efficiency
                for keyword in keywords[:2]:
                    articles = crawler.search(keyword, max_pages=1)
                    all_articles.extend(articles)

            # Clean and classify
            from utils.text_cleaner import clean_batch
            cleaned_articles = clean_batch(all_articles)
            classified_articles = self.classifier.classify_batch(cleaned_articles)

            # Save
            result = self.db_manager.save_articles_batch(classified_articles)

            self.db_manager.update_crawl_log(
                log.id,
                success_count=result["success"],
                failed_count=result["failed"]
            )

            logger.info(f"Ximalaya crawling completed: {result['success']} articles saved")

        except Exception as e:
            logger.error(f"Ximalaya crawling job failed: {e}")
            self.db_manager.update_crawl_log(log.id, error_msg=str(e))

        finally:
            await crawler.close()

    async def _crawl_weibo_job(self):
        """Execute Weibo dataset crawling job."""
        logger.info("=" * 60)
        logger.info(f"Starting scheduled Weibo dataset crawling: {datetime.now()}")
        logger.info("=" * 60)

        from crawler.huggingface_thucnews import HuggingFaceWeiboCrawler

        crawler = HuggingFaceWeiboCrawler()
        log = self.db_manager.create_crawl_log("weibo")

        try:
            all_articles = []

            for category, keywords in SEARCH_KEYWORDS.items():
                logger.info(f"Searching Weibo dataset for category: {category}")

                articles = crawler.crawl_by_keywords(keywords[:5], max_pages=20)
                all_articles.extend(articles)

            # Clean and classify
            from utils.text_cleaner import clean_batch
            cleaned_articles = clean_batch(all_articles)
            classified_articles = self.classifier.classify_batch(cleaned_articles)

            # Save
            result = self.db_manager.save_articles_batch(classified_articles)

            self.db_manager.update_crawl_log(
                log.id,
                success_count=result["success"],
                failed_count=result["failed"]
            )

            logger.info(f"Weibo dataset crawling completed: {result['success']} articles saved")

        except Exception as e:
            logger.error(f"Weibo dataset crawling job failed: {e}")
            self.db_manager.update_crawl_log(log.id, error_msg=str(e))

        finally:
            crawler.close()

    async def _crawl_chnsenticorp_job(self):
        """Execute ChnSentiCorp review dataset crawling job."""
        logger.info("=" * 60)
        logger.info(f"Starting scheduled ChnSentiCorp dataset crawling: {datetime.now()}")
        logger.info("=" * 60)

        from crawler.huggingface_chinese import HuggingFaceChnSentiCorpCrawler

        crawler = HuggingFaceChnSentiCorpCrawler()
        log = self.db_manager.create_crawl_log("chnsenticorp")

        try:
            all_articles = []

            # Use general keywords for reviews
            review_keywords = ["服务", "质量", "体验", "酒店", "产品", "购物"]
            for keyword in review_keywords:
                logger.info(f"Searching ChnSentiCorp for keyword: {keyword}")
                articles = crawler.search(keyword, max_pages=20)
                all_articles.extend(articles)

            # Clean and classify
            from utils.text_cleaner import clean_batch
            cleaned_articles = clean_batch(all_articles)
            classified_articles = self.classifier.classify_batch(cleaned_articles)

            # Save
            result = self.db_manager.save_articles_batch(classified_articles)

            self.db_manager.update_crawl_log(
                log.id,
                success_count=result["success"],
                failed_count=result["failed"]
            )

            logger.info(f"ChnSentiCorp dataset crawling completed: {result['success']} articles saved")

        except Exception as e:
            logger.error(f"ChnSentiCorp dataset crawling job failed: {e}")
            self.db_manager.update_crawl_log(log.id, error_msg=str(e))

        finally:
            crawler.close()

    async def _dify_sync_job(self):
        """Execute Dify knowledge base sync job."""
        logger.info("=" * 60)
        logger.info(f"Starting Dify sync job: {datetime.now()}")
        logger.info("=" * 60)

        try:
            from utils.dify_integration import DifyBatchSyncer

            syncer = DifyBatchSyncer()

            # Sync recent articles (last 24 hours)
            result = syncer.sync_recent_articles(
                db_manager=self.db_manager,
                hours=24,
                min_quality=0.6
            )

            logger.info(f"Dify sync completed: {result['success']} articles synced, "
                       f"{result['failed']} failed")

        except Exception as e:
            logger.error(f"Dify sync job failed: {e}")

    async def _quality_check_job(self):
        """Check data quality and generate report."""
        logger.info("=" * 60)
        logger.info(f"Starting quality check job: {datetime.now()}")
        logger.info("=" * 60)

        try:
            # Get statistics
            stats = self.db_manager.get_statistics()

            logger.info(f"Database Statistics:")
            logger.info(f"  Total articles: {stats['total_articles']}")
            logger.info(f"  Valid articles: {stats['valid_articles']}")
            logger.info(f"  By source:")
            for source, count in stats['by_source'].items():
                logger.info(f"    {source}: {count}")
            logger.info(f"  By category:")
            for category, count in stats['by_category'].items():
                logger.info(f"    {category}: {count}")
            logger.info(f"  Average quality score: {stats['average_quality_score']}")

            # Check for low-quality articles
            from storage.models import Article
            with self.db_manager.get_session() as session:
                low_quality = session.query(Article).filter(
                    Article.quality_score < 0.5
                ).count()

                if low_quality > 0:
                    logger.warning(f"Found {low_quality} low-quality articles (score < 0.5)")

                spam_articles = session.query(Article).filter(
                    Article.is_spam == True
                ).count()

                if spam_articles > 0:
                    logger.warning(f"Found {spam_articles} spam articles")

            logger.info("Quality check completed")

        except Exception as e:
            logger.error(f"Quality check job failed: {e}")


class ManualJobs:
    """Manually trigger jobs for testing."""

    def __init__(self, db_manager: DatabaseManager = None):
        self.db_manager = db_manager or DatabaseManager()

    def crawl_source(self, source: str, keywords: List[str] = None, max_pages: int = 2):
        """
        Manually trigger crawling for a specific source.

        Args:
            source: Source name (zhihu, toutiao, wechat, bilibili)
            keywords: Keywords to search (default: use config)
            max_pages: Maximum pages to crawl
        """
        from config.settings import SEARCH_KEYWORDS

        if keywords is None:
            # Flatten all keywords
            keywords = []
            for kw_list in SEARCH_KEYWORDS.values():
                keywords.extend(kw_list[:3])  # Use first 3 per category

        logger.info(f"Manual crawling: source={source}, keywords={len(keywords)}, max_pages={max_pages}")

        # Import appropriate crawler
        if source == "zhihu":
            from crawler.huggingface_zhihu import HuggingFaceZhihuCrawler
            crawler = HuggingFaceZhihuCrawler()
        elif source == "toutiao":
            from crawler.huggingface_thucnews import HuggingFaceTHUCNewsCrawler
            crawler = HuggingFaceTHUCNewsCrawler()
        elif source == "wechat":
            from crawler.wechat import WeChatCrawler
            crawler = WeChatCrawler()
        elif source == "bilibili":
            from crawler.bilibili import BilibiliCrawler
            crawler = BilibiliCrawler()
        elif source == "weibo":
            from crawler.huggingface_thucnews import HuggingFaceWeiboCrawler
            crawler = HuggingFaceWeiboCrawler()
        elif source == "chnsenticorp":
            from crawler.huggingface_chinese import HuggingFaceChnSentiCorpCrawler
            crawler = HuggingFaceChnSentiCorpCrawler()
        elif source == "dedao":
            from crawler.dedao_playwright import DedaoCrawlerPlaywright
            crawler = DedaoCrawlerPlaywright()
        elif source == "ximalaya":
            from crawler.ximalaya_fixed import XimalayaCrawlerFixed
            crawler = XimalayaCrawlerFixed()
        else:
            raise ValueError(f"Unknown source: {source}")

        log = self.db_manager.create_crawl_log(source)

        try:
            # Check if using Playwright crawler (async)
            is_playwright = source == "dedao"  # Only Dedao still uses Playwright
            is_fixed_async = source == "ximalaya"  # Ximalaya uses fixed crawler (returns list)

            if is_playwright:
                # Playwright crawlers use async search method
                articles = []
                for keyword in keywords[:3]:  # Limit keywords for Playwright
                    for article in crawler.search(keyword, max_pages=max_pages):
                        articles.append(article)
            elif is_fixed_async:
                # Ximalaya fixed crawler returns list directly
                articles = []
                for keyword in keywords[:3]:
                    articles.extend(crawler.search(keyword, max_pages=max_pages))
            else:
                # Regular crawlers
                articles = crawler.crawl_by_keywords(keywords, max_pages)

            # Clean and classify
            from utils.text_cleaner import clean_batch
            from classifier.rule_based import RuleBasedClassifier

            cleaned = clean_batch(articles)
            classifier = RuleBasedClassifier()
            classified = classifier.classify_batch(cleaned)

            # Save
            result = self.db_manager.save_articles_batch(classified)

            self.db_manager.update_crawl_log(
                log.id,
                success_count=result["success"],
                failed_count=result["failed"]
            )

            logger.info(f"Manual crawling completed: {result['success']} saved")

            return result

        except Exception as e:
            logger.error(f"Manual crawling failed: {e}")
            self.db_manager.update_crawl_log(log.id, error_msg=str(e))
            raise

        finally:
            # Close Playwright browsers if needed
            if source == "dedao":  # Only Dedao uses Playwright now
                import asyncio
                asyncio.run(crawler.close())
            elif source == "ximalaya":
                crawler.close()  # Fixed crawler has simple close()
            else:
                crawler.close()

    async def vectorize_articles(self, articles: List[Dict]) -> bool:
        """
        Vectorize articles and add to Pinecone.

        Args:
            articles: List of article dicts

        Returns:
            True if successful
        """
        try:
            from storage.pinecone_store import PineconeStore
            from storage.supabase_client import SupabaseClient
            from utils.embedding import QwenEmbedder

            pinecone = PineconeStore()
            embedder = QwenEmbedder()
            supabase = SupabaseClient()

            if not pinecone.index or not embedder.api_key:
                logger.warning("Pinecone or Qwen not configured, skipping vectorization")
                return False

            # Generate embeddings
            logger.info(f"Generating embeddings for {len(articles)} articles")
            embeddings = await embedder.vectorize_articles(articles, batch_size=10)

            # Add to Pinecone
            logger.info("Adding vectors to Pinecone")
            result = await pinecone.add_vectors(articles, embeddings)

            if result:
                logger.info(f"Successfully vectorized {len(articles)} articles")
            return result

        except Exception as e:
            logger.error(f"Vectorization failed: {e}")
            return False

    def export_data(
        self,
        output_dir: str,
        format: str = "txt",
        source: str = None,
        category: str = None
    ):
        """
        Export articles from database.

        Args:
            output_dir: Output directory path
            format: Export format (txt, json, csv)
            source: Filter by source
            category: Filter by category
        """
        logger.info(f"Exporting data: format={format}, source={source}, category={category}")

        if format == "txt":
            path = self.db_manager.export_articles_to_txt(output_dir, source, category)
        elif format == "json":
            output_file = os.path.join(output_dir, f"articles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            path = self.db_manager.export_articles_to_json(output_file, source, category)
        elif format == "csv":
            output_file = os.path.join(output_dir, f"articles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
            path = self.db_manager.export_articles_to_csv(output_file, source, category)
        else:
            raise ValueError(f"Unsupported format: {format}")

        logger.info(f"Data exported to: {path}")
        return path
