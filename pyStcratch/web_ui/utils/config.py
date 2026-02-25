"""
Configuration module for the Streamlit frontend.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Backend API configuration
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000')

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///data/crawler.db')

# Frontend configuration
STREAMLIT_PORT = int(os.getenv('STREAMLIT_SERVER_PORT', 8501))
STREAMLIT_ADDRESS = os.getenv('STREAMLIT_SERVER_ADDRESS', 'localhost')

# Pagination
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Categories
CATEGORIES = ['psychology', 'management', 'finance', 'other']
CATEGORIES_LABELS = {
    'psychology': '心理学',
    'management': '管理学',
    'finance': '金融学',
    'other': '其他'
}

# Sources
SOURCES = ['zhihu', 'toutiao', 'wechat', 'bilibili', 'dedao', 'ximalaya']
SOURCES_LABELS = {
    'zhihu': '知乎',
    'toutiao': '今日头条',
    'wechat': '微信公众号',
    'bilibili': '哔哩哔哩',
    'dedao': '得到',
    'ximalaya': '喜马拉雅'
}

# Quality score ranges
QUALITY_RANGES = {
    'high': (0.8, 1.0),
    'medium': (0.6, 0.8),
    'low': (0.0, 0.6)
}
