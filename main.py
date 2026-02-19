"""
Main entry point for the web scraping system.
"""
import sys
import os
import asyncio
from loguru import logger
from config.settings import LOG_DIR, LOG_FILE, LOG_LEVEL, LOG_ROTATION, LOG_RETENTION, RAW_DATA_DIR, PROCESSED_DATA_DIR

# Configure logging
logger.remove()
logger.add(
    sys.stderr,
    level=LOG_LEVEL,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
)
logger.add(
    LOG_FILE,
    rotation=LOG_ROTATION,
    retention=LOG_RETENTION,
    level=LOG_LEVEL,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
)

# Ensure directories exist
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(RAW_DATA_DIR, exist_ok=True)
os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)


def run_crawler(source: str = None, keywords: list = None, max_pages: int = 2):
    """
    Run manual crawling task.

    Args:
        source: Source to crawl (zhihu, toutiao, wechat, or all)
        keywords: Keywords to search (default: use config)
        max_pages: Maximum pages per keyword
    """
    from scheduler.jobs import ManualJobs

    jobs = ManualJobs()

    if source == "all":
        sources = ["zhihu", "toutiao", "wechat", "bilibili", "dedao", "ximalaya"]
    else:
        sources = [source] if source else ["zhihu"]

    results = {}
    for s in sources:
        try:
            result = jobs.crawl_source(s, keywords, max_pages)
            results[s] = result
        except Exception as e:
            logger.error(f"Failed to crawl {s}: {e}")
            results[s] = {"error": str(e)}

    return results


def classify_articles():
    """Classify unclassified articles."""
    from scheduler.jobs import CrawlerScheduler

    scheduler = CrawlerScheduler()
    asyncio.run(scheduler._classify_articles_job())


def export_data(output_dir: str, format: str = "txt", source: str = None, category: str = None):
    """
    Export articles to files.

    Args:
        output_dir: Output directory
        format: Export format (txt, json, csv)
        source: Filter by source
        category: Filter by category
    """
    from scheduler.jobs import ManualJobs

    jobs = ManualJobs()
    return jobs.export_data(output_dir, format, source, category)


def start_scheduler():
    """Start the scheduler daemon."""
    from scheduler.jobs import CrawlerScheduler

    scheduler = CrawlerScheduler()
    scheduler.start()

    logger.info("Scheduler is running. Press Ctrl+C to stop.")

    try:
        # Keep the script running
        import asyncio
        asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("Shutting down scheduler...")
        scheduler.stop()


def show_stats():
    """Display database statistics."""
    from storage.database import DatabaseManager

    db = DatabaseManager()
    stats = db.get_statistics()

    print("\n" + "=" * 60)
    print("DATABASE STATISTICS")
    print("=" * 60)
    print(f"Total articles: {stats['total_articles']}")
    print(f"Valid articles: {stats['valid_articles']}")
    print(f"\nBy source:")
    for source, count in stats['by_source'].items():
        print(f"  {source}: {count}")
    print(f"\nBy category:")
    for category, count in stats['by_category'].items():
        print(f"  {category}: {count}")
    print(f"\nAverage quality score: {stats['average_quality_score']}")
    print("=" * 60 + "\n")


def main():
    """Main CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Web scraping system for content collection")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Crawl command
    crawl_parser = subparsers.add_parser("crawl", help="Run manual crawling")
    crawl_parser.add_argument("--source", choices=["zhihu", "toutiao", "wechat", "bilibili", "dedao", "ximalaya", "all"],
                            default="zhihu", help="Source to crawl")
    crawl_parser.add_argument("--keywords", nargs="+", help="Keywords to search")
    crawl_parser.add_argument("--max-pages", type=int, default=2,
                            help="Maximum pages per keyword")

    # Classify command
    subparsers.add_parser("classify", help="Classify unclassified articles")

    # Export command
    export_parser = subparsers.add_parser("export", help="Export articles")
    export_parser.add_argument("--output", "-o", required=True, help="Output directory")
    export_parser.add_argument("--format", "-f", choices=["txt", "json", "csv"],
                             default="txt", help="Export format")
    export_parser.add_argument("--source", help="Filter by source")
    export_parser.add_argument("--category", help="Filter by category")

    # Scheduler command
    subparsers.add_parser("scheduler", help="Start the scheduler daemon")

    # Stats command
    subparsers.add_parser("stats", help="Show database statistics")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        if args.command == "crawl":
            run_crawler(args.source, args.keywords, args.max_pages)

        elif args.command == "classify":
            classify_articles()

        elif args.command == "export":
            export_data(args.output, args.format, args.source, args.category)

        elif args.command == "scheduler":
            start_scheduler()

        elif args.command == "stats":
            show_stats()

    except Exception as e:
        logger.error(f"Command failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
