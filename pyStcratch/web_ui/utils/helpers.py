"""
Helper functions for the Streamlit frontend.
"""
from datetime import datetime, timedelta
from typing import Optional


def format_time(time_str: str) -> str:
    """Format ISO time string to relative time."""
    if not time_str:
        return "未知"

    try:
        # Parse ISO format
        dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
        now = datetime.now(dt.tzinfo)
        delta = now - dt

        if delta.seconds < 60:
            return f"{delta.seconds}秒前"
        elif delta.seconds < 3600:
            return f"{delta.seconds // 60}分钟前"
        elif delta.seconds < 86400:
            return f"{delta.seconds // 3600}小时前"
        elif delta.days < 7:
            return f"{delta.days}天前"
        else:
            return dt.strftime("%Y-%m-%d")
    except Exception:
        return time_str


def format_datetime(dt: Optional[datetime]) -> str:
    """Format datetime to readable string."""
    if not dt:
        return "未知"
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def format_number(num: int) -> str:
    """Format large numbers with commas."""
    return f"{num:,}"


def get_quality_color(score: float) -> str:
    """Get color indicator for quality score."""
    if score >= 0.8:
        return "🟢"
    elif score >= 0.6:
        return "🟡"
    else:
        return "🔴"


def get_quality_label(score: float) -> str:
    """Get label for quality score."""
    if score >= 0.8:
        return "高质量"
    elif score >= 0.6:
        return "中等"
    else:
        return "低质量"


def truncate_text(text: str, max_length: int = 200) -> str:
    """Truncate text to max length."""
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def safe_divide(numerator: float, denominator: float) -> float:
    """Safely divide two numbers."""
    if denominator == 0:
        return 0.0
    return numerator / denominator


def get_source_emoji(source: str) -> str:
    """Get emoji for source."""
    emojis = {
        'zhihu': '📘',
        'toutiao': '📰',
        'wechat': '💬',
        'bilibili': '📺',
        'dedao': '🎧',
        'ximalaya': '🎙️'
    }
    return emojis.get(source, '📄')


def get_category_emoji(category: str) -> str:
    """Get emoji for category."""
    emojis = {
        'psychology': '🧠',
        'management': '💼',
        'finance': '💰',
        'other': '📁'
    }
    return emojis.get(category, '📁')
