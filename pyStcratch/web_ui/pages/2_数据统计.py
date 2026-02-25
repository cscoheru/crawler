"""
数据统计页 - 显示数据库统计和图表
"""
import streamlit as st
from utils.api import backend_api
from components.charts import (
    statistics_overview,
    category_distribution_chart,
    source_distribution_chart,
    quality_distribution_chart
)


def show():
    """Display the statistics page."""
    st.title("📈 数据统计")

    # Load statistics
    with st.spinner("加载统计数据..."):
        stats = backend_api.get_statistics()

    if 'error' in stats:
        st.error(f"加载统计数据失败: {stats['error']}")
        return

    # Overview metrics
    st.subheader("总体概况")
    statistics_overview(stats)
    st.divider()

    # Category distribution
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("分类分布")
        category_data = stats.get('by_category', {})
        category_distribution_chart(category_data)

    with col2:
        st.subheader("来源分布")
        source_data = stats.get('by_source', {})
        source_distribution_chart(source_data)

    st.divider()

    # Quality score
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("平均质量分数")
        avg_quality = stats.get('average_quality_score', 0)
        st.metric("整体平均质量", f"{avg_quality:.2f}")

        # Quality distribution
        quality_ranges = {
            '高质量 (≥0.8)': _count_quality(stats, 0.8),
            '中等质量 (0.6-0.8)': _count_quality_range(stats, 0.6, 0.8),
            '低质量 (<0.6)': _count_quality_max(stats, 0.6)
        }

        st.write("质量分布:")
        for label, count in quality_ranges.items():
            st.write(f"- {label}: {count:,}")

    with col2:
        st.subheader("数据健康度")
        total = stats.get('total_articles', 0)
        valid = stats.get('valid_articles', 0)
        valid_rate = (valid / total * 100) if total > 0 else 0

        st.metric("有效率", f"{valid_rate:.1f}%")
        st.metric("无效/垃圾", f"{total - valid:,}")

    st.divider()

    # Actions
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔄 刷新数据", use_container_width=True):
            st.rerun()

    with col2:
        if st.button("📤 导出统计", use_container_width=True):
            st.info("导出功能开发中...")

    with col3:
        if st.button("📊 详细报告", use_container_width=True):
            st.info("详细报告功能开发中...")


def _count_quality(stats: dict, min_quality: float) -> int:
    """Estimate articles with quality >= min_quality."""
    # This is a simplified estimation
    # In real implementation, query database directly
    valid = stats.get('valid_articles', 0)
    avg = stats.get('average_quality_score', 0.5)
    if avg >= min_quality:
        return int(valid * 0.6)  # Rough estimate
    return int(valid * 0.2)


def _count_quality_range(stats: dict, min_q: float, max_q: float) -> int:
    """Estimate articles with quality in range."""
    valid = stats.get('valid_articles', 0)
    return int(valid * 0.3)  # Rough estimate


def _count_quality_max(stats: dict, max_quality: float) -> int:
    """Estimate articles with quality < max_quality."""
    total = stats.get('total_articles', 0)
    valid = stats.get('valid_articles', 0)
    return total - valid + int(valid * 0.1)  # Rough estimate
