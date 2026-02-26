"""
Configuration settings for the web scraping system.
"""
import os
from dotenv import load_dotenv

load_dotenv()


# Database configuration
# Supports SQLite (default) or PostgreSQL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///data/crawler.db"  # Default to SQLite for easier setup
)

# AI API configuration
ZHIPUAI_API_KEY = os.getenv("ZHIPUAI_API_KEY", "")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")

# Proxy configuration
PROXY_ENABLED = os.getenv("PROXY_ENABLED", "False").lower() == "true"
PROXY_API_URL = os.getenv("PROXY_API_URL", "")
PROXY_POOL = [
    "http://proxy1.example.com:8080",
    "http://proxy2.example.com:8080",
]

# Scraping configuration
REQUEST_DELAY = (3, 10)  # Random delay between requests (seconds)
MAX_RETRIES = 3
CONCURRENT_REQUESTS = 5
DOWNLOAD_TIMEOUT = 30
USER_AGENT_ROTATION = True

# Platform-specific configurations
PLATFORM_CONFIG = {
    "zhihu": {
        "base_url": "https://www.zhihu.com",
        "search_url": "https://www.zhihu.com/api/v4/search_v3",
        "max_pages": 5,
        "delay_range": (5, 15),
    },
    "toutiao": {
        "base_url": "https://www.toutiao.com",
        "api_url": "https://www.toutiao.com/api/search/content/",
        "max_pages": 5,
        "delay_range": (3, 10),
    },
    "wechat": {
        "sogou_url": "https://weixin.sogou.com",
        "max_pages": 3,
        "delay_range": (5, 12),
    },
    "bilibili": {
        "base_url": "https://www.bilibili.com",
        "search_url": "https://api.bilibili.com/x/web-interface/search/type",
        "max_pages": 5,
        "delay_range": (5, 15),
    },
    "dedao": {
        "base_url": "https://www.dedao.cn",
        "api_url": "https://www.dedao.cn/mobile/api",
        "max_pages": 3,
        "delay_range": (5, 10),
    },
    "ximalaya": {
        "base_url": "https://www.ximalaya.com",
        "search_url": "https://www.ximalaya.com/search",
        "max_pages": 3,
        "delay_range": (5, 10),
    },
}

# Classification configuration
CONFIDENCE_THRESHOLD = 0.7
AI_CLASSIFIER_MODEL = os.getenv("AI_CLASSIFIER_MODEL", "deepseek")  # zhipu or deepseek
AI_API_MAX_RETRIES = 3
AI_API_TIMEOUT = 30

# Data storage
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")

# Logging
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.path.join(LOG_DIR, "crawler.log")
LOG_ROTATION = "100 MB"
LOG_RETENTION = "30 days"

# Scheduler configuration
SCHEDULER_TIMEZONE = "Asia/Shanghai"
SCHEDULER_JOBS = {
    "zhihu": {"hour": 6, "minute": 0},
    "toutiao": {"hour": 8, "minute": 0},  # Now using THUCNews dataset
    "wechat": {"hour": 10, "minute": 0},
    "bilibili": {"hour": 12, "minute": 0},
    "dedao": {"hour": 13, "minute": 0},
    "ximalaya": {"hour": 13, "minute": 30},
    "weibo": {"hour": 14, "minute": 0},  # New: Weibo dataset
    "chnsenticorp": {"hour": 14, "minute": 30},  # New: Hotel reviews
    "classify": {"hour": 15, "minute": 0},
    "dify_sync": {"hour": 16, "minute": 0},
    "quality_check": {"hour": 20, "minute": 0},
}

# Search keywords for each category
SEARCH_KEYWORDS = {
    "psychology": [
        "心理咨询", "抑郁症", "焦虑症", "心理治疗", "心理健康",
        "情绪管理", "压力缓解", "心理咨询师", "认知行为疗法",
        "心理咨询中心", "心理辅导", "心理障碍", "心理咨询师培训"
    ],
    "management": [
        "企业管理", "战略管理", "团队建设", "领导力", "管理技能",
        "组织管理", "人力资源", "绩效管理", "企业文化",
        "管理咨询", "项目管理", "商业模式", "企业战略"
    ],
    "finance": [
        "会计", "税务", "财务", "审计", "报税",
        "财务报表", "成本会计", "管理会计", "税务筹划",
        "财务分析", "会计准则", "企业税务", "财务管理"
    ]
}

# Data quality thresholds
MIN_CONTENT_LENGTH = 200  # Minimum characters for valid content
MAX_CONTENT_LENGTH = 50000  # Maximum characters to avoid spam
MIN_QUALITY_SCORE = 0.5

# Export configuration
EXPORT_FORMATS = ["csv", "json", "excel"]
EXPORT_BATCH_SIZE = 1000
