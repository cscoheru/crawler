"""
Flask Web服务器 - 用于手动触发爬虫和查看状态
云端部署时提供HTTP API接口
"""
import os
import sys
import threading
from flask import Flask, jsonify, request
from loguru import logger

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)

# 配置日志
logger.remove()
logger.add(sys.stderr, level=os.getenv("LOG_LEVEL", "INFO"))

# 导入所需的类
from storage.database import DatabaseManager
from scheduler.jobs import ManualJobs, CrawlerScheduler
from utils.dify_integration import DifyBatchSyncer

# 初始化服务
db_manager = None
manual_jobs = None

def initialize_services():
    """初始化服务"""
    global db_manager, manual_jobs
    try:
        # 设置数据库路径
        data_dir = os.getenv('DATA_DIR', './data')
        os.makedirs(data_dir, exist_ok=True)

        db_manager = DatabaseManager()
        manual_jobs = ManualJobs(db_manager=db_manager)

        logger.info("✅ Services initialized successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to initialize services: {e}")
        import traceback
        traceback.print_exc()
        return False


@app.route('/health')
def health():
    """健康检查端点"""
    return jsonify({
        "status": "healthy",
        "service": "crawler-web",
        "database": os.getenv("DATABASE_URL", "sqlite:///data/crawler.db"),
        "data_dir": os.getenv('DATA_DIR', './data')
    })


@app.route('/api/init', methods=['POST'])
def init_services():
    """初始化服务端点"""
    try:
        success = initialize_services()
        if success:
            return jsonify({"success": True, "message": "Services initialized"})
        else:
            return jsonify({"success": False, "error": "Initialization failed"}), 500
    except Exception as e:
        logger.error(f"Init failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/stats')
def get_stats():
    """获取数据库统计信息"""
    try:
        stats = db_manager.get_statistics()
        return jsonify({
            "success": True,
            "data": stats
        })
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/crawl', methods=['POST'])
def trigger_crawl():
    """
    手动触发爬虫

    请求体:
    {
        "source": "zhihu",  // 可选: all, zhihu, toutiao, wechat, bilibili, dedao, ximalaya
        "max_pages": 1       // 可选: 默认1
    }
    """
    try:
        data = request.json or {}
        source = data.get('source', 'zhihu')
        max_pages = data.get('max_pages', 1)

        logger.info(f"Manual crawl triggered: source={source}, max_pages={max_pages}")

        jobs = ManualJobs(db_manager=db_manager)
        result = jobs.crawl_source(source, max_pages=max_pages)

        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        logger.error(f"Failed to trigger crawl: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/export', methods=['POST'])
def export_data():
    """
    导出数据

    请求体:
    {
        "format": "txt",      // txt, json, csv
        "category": null,     // 可选: psychology, management, finance
        "min_quality": 0.5    // 可选: 最低质量分数
    }
    """
    try:
        data = request.json or {}
        format_type = data.get('format', 'txt')
        category = data.get('category')
        min_quality = data.get('min_quality', 0.5)

        logger.info(f"Export triggered: format={format_type}, category={category}")

        # 导出目录
        export_dir = os.path.join(os.getenv('DATA_DIR', './data'), 'exports')
        os.makedirs(export_dir, exist_ok=True)

        # 执行导出
        if format_type == 'txt':
            path = db_manager.export_articles_to_txt(
                export_dir,
                category=category,
                min_quality=min_quality
            )
        elif format_type == 'json':
            import datetime
            filename = f"articles_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            path = os.path.join(export_dir, filename)
            path = db_manager.export_articles_to_json(
                path,
                category=category,
                min_quality=min_quality
            )
        elif format_type == 'csv':
            import datetime
            filename = f"articles_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            path = os.path.join(export_dir, filename)
            path = db_manager.export_articles_to_csv(
                path,
                category=category,
                min_quality=min_quality
            )
        else:
            return jsonify({
                "success": False,
                "error": f"Unsupported format: {format_type}"
            }), 400

        return jsonify({
            "success": True,
            "data": {
                "export_path": path,
                "format": format_type
            }
        })
    except Exception as e:
        logger.error(f"Failed to export data: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/sync-dify', methods=['POST'])
def sync_to_dify():
    """
    同步数据到Dify知识库

    请求体:
    {
        "hours": 24,          // 最近N小时的文章
        "min_quality": 0.6    // 最低质量分数
    }
    """
    try:
        data = request.json or {}
        hours = data.get('hours', 24)
        min_quality = data.get('min_quality', 0.6)

        logger.info(f"Dify sync triggered: hours={hours}, min_quality={min_quality}")

        syncer = DifyBatchSyncer()
        result = syncer.sync_recent_articles(
            db_manager=db_manager,
            hours=hours,
            min_quality=min_quality
        )

        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        logger.error(f"Failed to sync to Dify: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


def _run_full_sync_task():
    """后台执行完整同步任务"""
    try:
        logger.info("Background sync task started...")
        results = {}

        # 1. 爬取数据（限制页面数以避免超时）
        logger.info("Step 1: Crawling data...")
        jobs = ManualJobs(db_manager=db_manager)

        # 依次爬取各平台
        sources = ['zhihu', 'toutiao', 'wechat']
        crawl_results = {}
        for source in sources:
            try:
                result = jobs.crawl_source(source, max_pages=1)
                crawl_results[source] = result
                logger.info(f"Crawled {source}: {result}")
            except Exception as e:
                logger.error(f"Failed to crawl {source}: {e}")
                crawl_results[source] = {"error": str(e)}

        results['crawl'] = crawl_results

        # 2. 分类未分类的文章
        logger.info("Step 2: Classifying articles...")
        try:
            scheduler = CrawlerScheduler(db_manager=db_manager)
            # 运行分类任务
            import asyncio
            asyncio.run(scheduler._classify_articles_job())
            results['classify'] = {"success": True}
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            results['classify'] = {"error": str(e)}

        # 3. 导出到TXT
        logger.info("Step 3: Exporting to TXT...")
        try:
            export_dir = os.path.join(os.getenv('DATA_DIR', './data'), 'exports')
            os.makedirs(export_dir, exist_ok=True)
            export_path = db_manager.export_articles_to_txt(export_dir, min_quality=0.6)
            results['export'] = {"success": True, "path": export_path}
        except Exception as e:
            logger.error(f"Export failed: {e}")
            results['export'] = {"error": str(e)}

        # 4. 同步到Dify（如果配置了API密钥）
        if os.getenv('DIFY_API_KEY'):
            logger.info("Step 4: Syncing to Dify...")
            try:
                syncer = DifyBatchSyncer()
                sync_result = syncer.sync_recent_articles(
                    db_manager=db_manager,
                    hours=24,
                    min_quality=0.6
                )
                results['dify_sync'] = sync_result
            except Exception as e:
                logger.error(f"Dify sync failed: {e}")
                results['dify_sync'] = {"error": str(e)}
        else:
            logger.info("Dify API key not configured, skipping sync")
            results['dify_sync'] = {"skipped": True, "reason": "No API key"}

        # 5. 获取最终统计
        logger.info("Step 5: Getting final stats...")
        try:
            stats = db_manager.get_statistics()
            results['stats'] = stats
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            results['stats'] = {"error": str(e)}

        logger.info(f"Background sync completed: {results}")
    except Exception as e:
        logger.error(f"Background sync failed: {e}")
        import traceback
        traceback.print_exc()


@app.route('/api/run-full-sync', methods=['POST'])
def run_full_sync():
    """
    运行完整同步流程：爬取→分类→导出→Dify同步
    异步执行，立即返回 202
    """
    try:
        logger.info("Full sync request received, starting in background...")

        # 使用线程池异步执行
        thread = threading.Thread(target=_run_full_sync_task, daemon=True)
        thread.start()

        # 立即返回 202 Accepted
        return jsonify({
            "success": True,
            "message": "Full sync started in background",
            "status": "processing"
        }), 202
    except Exception as e:
        logger.error(f"Failed to start sync: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ===== New HuggingFace Dataset API Endpoints =====

@app.route('/api/articles')
def get_articles():
    """
    Get articles with optional filters.

    Query parameters:
    - source: Filter by source
    - category: Filter by category
    - content_type: Filter by content type (article/review/qa/social/news)
    - sentiment: Filter by sentiment (positive/negative/neutral)
    - dataset_source: Filter by dataset source
    - min_quality: Minimum quality score
    - limit: Maximum results (default: 100)
    - offset: Pagination offset (default: 0)
    """
    try:
        source = request.args.get('source')
        category = request.args.get('category')
        content_type = request.args.get('content_type')
        sentiment = request.args.get('sentiment')
        dataset_source = request.args.get('dataset_source')
        min_quality = request.args.get('min_quality', type=float)
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)

        articles = db_manager.get_articles(
            source=source,
            category=category,
            content_type=content_type,
            sentiment=sentiment,
            dataset_source=dataset_source,
            min_quality=min_quality,
            limit=limit,
            offset=offset
        )

        return jsonify({
            "success": True,
            "data": {
                "articles": [article.to_dict() for article in articles],
                "count": len(articles),
                "limit": limit,
                "offset": offset
            }
        })
    except Exception as e:
        logger.error(f"Failed to get articles: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/stats/detailed')
def get_detailed_stats():
    """
    Get detailed statistics including:
    - Distribution by content type
    - Distribution by sentiment
    - Distribution by dataset source
    """
    try:
        # Get basic stats
        basic_stats = db_manager.get_statistics()

        # Get detailed dataset stats
        dataset_stats = db_manager.get_dataset_statistics()

        return jsonify({
            "success": True,
            "data": {
                "basic": basic_stats,
                "by_content_type": dataset_stats["by_content_type"],
                "by_sentiment": dataset_stats["by_sentiment"],
                "by_dataset_source": dataset_stats["by_dataset_source"],
            }
        })
    except Exception as e:
        logger.error(f"Failed to get detailed stats: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/datasets')
def get_datasets():
    """Get list of datasets and their sync status."""
    try:
        datasets = db_manager.get_dataset_statistics()

        # Convert to list format
        dataset_list = []
        for source, count in datasets["by_dataset_source"].items():
            dataset_list.append({
                "name": source,
                "count": count,
                "last_sync": None  # Could be added from DatasetMetadata table
            })

        return jsonify({
            "success": True,
            "data": {
                "datasets": dataset_list,
                "total": len(dataset_list)
            }
        })
    except Exception as e:
        logger.error(f"Failed to get datasets: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/datasets/<dataset_name>/sync', methods=['POST'])
def sync_dataset(dataset_name):
    """
    Manually trigger sync for a specific dataset.

    Path parameters:
    - dataset_name: Name of the dataset (chnsenticorp, lcqmc, weibo, etc.)
    """
    try:
        # Map dataset name to source
        dataset_source_map = {
            "chnsenticorp": "chnsenticorp",
            "lcqmc": "lcqmc",
            "weibo": "weibo",
            "thucnews": "toutiao",
            "cmnlu": "cmnlu",
            "c3": "c3",
        }

        source = dataset_source_map.get(dataset_name)
        if not source:
            return jsonify({
                "success": False,
                "error": f"Unknown dataset: {dataset_name}"
            }), 400

        logger.info(f"Manual dataset sync triggered: {dataset_name} (source: {source})")

        jobs = ManualJobs(db_manager=db_manager)
        result = jobs.crawl_source(source, max_pages=2)

        return jsonify({
            "success": True,
            "data": {
                "dataset": dataset_name,
                "source": source,
                "result": result
            }
        })
    except Exception as e:
        logger.error(f"Failed to sync dataset: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/export/qa', methods=['POST'])
def export_qa_pairs():
    """
    Export QA pairs to CSV format.

    Request body:
    {
        "category": null,     // Optional: filter by category
        "min_quality": 0.5    // Optional: minimum quality score
    }
    """
    try:
        data = request.json or {}
        category = data.get('category')
        min_quality = data.get('min_quality', 0.5)

        export_dir = os.path.join(os.getenv('DATA_DIR', './data'), 'exports')
        os.makedirs(export_dir, exist_ok=True)

        import datetime
        filename = f"qa_pairs_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        output_file = os.path.join(export_dir, filename)

        path = db_manager.export_qa_pairs_to_csv(
            output_file,
            category=category,
            min_quality=min_quality
        )

        return jsonify({
            "success": True,
            "data": {
                "export_path": path,
                "format": "csv"
            }
        })
    except Exception as e:
        logger.error(f"Failed to export QA pairs: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/export/reviews', methods=['POST'])
def export_reviews():
    """
    Export reviews with sentiment to CSV format.

    Request body:
    {
        "sentiment": "positive",  // Optional: positive/negative/neutral
        "min_quality": 0.5        // Optional: minimum quality score
    }
    """
    try:
        data = request.json or {}
        sentiment = data.get('sentiment')
        min_quality = data.get('min_quality', 0.5)

        export_dir = os.path.join(os.getenv('DATA_DIR', './data'), 'exports')
        os.makedirs(export_dir, exist_ok=True)

        import datetime
        filename = f"reviews_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        output_file = os.path.join(export_dir, filename)

        path = db_manager.export_reviews_with_sentiment(
            output_file,
            sentiment=sentiment,
            min_quality=min_quality
        )

        return jsonify({
            "success": True,
            "data": {
                "export_path": path,
                "format": "csv"
            }
        })
    except Exception as e:
        logger.error(f"Failed to export reviews: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


if __name__ == '__main__':
    # 初始化服务
    if not initialize_services():
        logger.warning("⚠️ Service initialization failed, some endpoints may not work")

    # 开发环境直接运行
    port = int(os.getenv('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
