#!/usr/bin/env python3
"""
Comprehensive test script for all crawlers.
Tests basic functionality of each crawler.
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
from storage.database import DatabaseManager


def test_database():
    """Test database connection and initialization."""
    logger.info("=" * 60)
    logger.info("Testing Database Connection")
    logger.info("=" * 60)

    try:
        db = DatabaseManager()
        stats = db.get_statistics()
        logger.info(f"✓ Database initialized successfully")
        logger.info(f"  - Total articles: {stats['total_articles']}")
        return True
    except Exception as e:
        logger.error(f"✗ Database test failed: {e}")
        return False


def test_crawler_imports():
    """Test that all crawlers can be imported."""
    logger.info("=" * 60)
    logger.info("Testing Crawler Imports")
    logger.info("=" * 60)

    crawlers = [
        ("ZhihuCrawler", "crawler.zhihu"),
        ("ToutiaoCrawler", "crawler.toutiao"),
        ("WeChatCrawler", "crawler.wechat"),
        ("BilibiliCrawler", "crawler.bilibili"),
        ("DedaoCrawler", "crawler.dedao"),
        ("XimalayaCrawler", "crawler.ximalaya"),
    ]

    success = True
    for name, module_path in crawlers:
        try:
            module = __import__(module_path, fromlist=[name])
            crawler_class = getattr(module, name)
            logger.info(f"✓ {name} imported successfully")
        except Exception as e:
            logger.error(f"✗ Failed to import {name}: {e}")
            success = False

    return success


def test_crawler_initialization():
    """Test that all crawlers can be initialized."""
    logger.info("=" * 60)
    logger.info("Testing Crawler Initialization")
    logger.info("=" * 60)

    from crawler.zhihu import ZhihuCrawler
    from crawler.toutiao import ToutiaoCrawler
    from crawler.wechat import WeChatCrawler
    from crawler.bilibili import BilibiliCrawler
    from crawler.dedao import DedaoCrawler
    from crawler.ximalaya import XimalayaCrawler

    crawlers = [
        ("ZhihuCrawler", ZhihuCrawler),
        ("ToutiaoCrawler", ToutiaoCrawler),
        ("WeChatCrawler", WeChatCrawler),
        ("BilibiliCrawler", BilibiliCrawler),
        ("DedaoCrawler", DedaoCrawler),
        ("XimalayaCrawler", XimalayaCrawler),
    ]

    success = True
    for name, crawler_class in crawlers:
        try:
            crawler = crawler_class()
            logger.info(f"✓ {name} initialized successfully")
            crawler.close()
        except Exception as e:
            logger.error(f"✗ Failed to initialize {name}: {e}")
            success = False

    return success


def test_basic_search():
    """Test basic search functionality with minimal pages."""
    logger.info("=" * 60)
    logger.info("Testing Basic Search Functionality")
    logger.info("=" * 60)

    from crawler.zhihu import ZhihuCrawler
    from crawler.toutiao import ToutiaoCrawler

    test_keyword = "心理咨询"

    # Test Zhihu
    try:
        crawler = ZhihuCrawler()
        results = list(crawler.search(test_keyword, max_pages=1))
        logger.info(f"✓ Zhihu search: found {len(results)} results")
        crawler.close()
    except Exception as e:
        logger.warning(f"⚠ Zhihu search test: {e}")

    # Test Toutiao
    try:
        crawler = ToutiaoCrawler()
        results = list(crawler.search(test_keyword, max_pages=1))
        logger.info(f"✓ Toutiao search: found {len(results)} results")
        crawler.close()
    except Exception as e:
        logger.warning(f"⚠ Toutiao search test: {e}")

    return True


def test_classifier():
    """Test classifier functionality."""
    logger.info("=" * 60)
    logger.info("Testing Classifier")
    logger.info("=" * 60)

    from classifier.rule_based import RuleBasedClassifier

    try:
        classifier = RuleBasedClassifier()

        test_articles = [
            {
                "title": "企业管理中的领导力培养",
                "content": "在企业管理中，领导力是核心竞争力之一...",
                "source": "zhihu",
            },
            {
                "title": "抑郁症的心理治疗方法",
                "content": "认知行为疗法是治疗抑郁症的有效方法...",
                "source": "zhihu",
            },
        ]

        classified = classifier.classify_batch(test_articles)

        for article in classified:
            logger.info(f"  - {article['title'][:30]}... -> {article['category']} ({article['confidence']:.2f})")

        logger.info(f"✓ Classifier tested successfully")
        return True
    except Exception as e:
        logger.error(f"✗ Classifier test failed: {e}")
        return False


def test_export():
    """Test export functionality."""
    logger.info("=" * 60)
    logger.info("Testing Export Functionality")
    logger.info("=" * 60)

    from storage.database import DatabaseManager
    import tempfile
    import shutil

    try:
        db = DatabaseManager()

        # Create temp directory
        temp_dir = tempfile.mkdtemp()

        # Test TXT export
        db.export_articles_to_txt(temp_dir)

        # Count exported files
        import os
        files = [f for f in os.listdir(temp_dir) if f.endswith('.txt')]

        logger.info(f"✓ Exported {len(files)} articles to TXT")

        # Cleanup
        shutil.rmtree(temp_dir)

        return True
    except Exception as e:
        logger.error(f"✗ Export test failed: {e}")
        return False


def main():
    """Run all tests."""
    logger.info("Starting comprehensive crawler tests")
    logger.info("")

    tests = [
        ("Database", test_database),
        ("Imports", test_crawler_imports),
        ("Initialization", test_crawler_initialization),
        ("Basic Search", test_basic_search),
        ("Classifier", test_classifier),
        ("Export", test_export),
    ]

    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            logger.error(f"Test {name} crashed: {e}")
            results[name] = False
        logger.info("")

    # Summary
    logger.info("=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status}: {name}")

    logger.info("")
    logger.info(f"Total: {passed}/{total} tests passed")

    if passed == total:
        logger.info("All tests passed!")
        return 0
    else:
        logger.warning(f"Some tests failed. Check logs for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
