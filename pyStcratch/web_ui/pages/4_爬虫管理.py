"""
爬虫管理页 - 触发和监控爬虫任务
"""
import streamlit as st
from utils.api import backend_api, database_api
from utils.config import SOURCES, SOURCES_LABELS
from components.charts import crawl_logs_chart


def show():
    """Display the crawler management page."""
    st.title("🕷️ 爬虫管理")

    tab1, tab2 = st.tabs(["触发爬虫", "执行记录"])

    with tab1:
        _show_crawl_trigger()

    with tab2:
        _show_crawl_logs()


def _show_crawl_trigger():
    """Show crawl trigger interface."""
    st.subheader("手动触发爬虫")

    # Source selection
    st.write("**选择数据源**")
    all_sources = ["all"] + list(SOURCES)

    source_col1, source_col2 = st.columns(2)
    with source_col1:
        selected_source = st.selectbox(
            "数据源",
            all_sources,
            format_func=lambda x: "全部" if x == "all" else SOURCES_LABELS.get(x, x),
            index=0
        )

    # Max pages
    col1, col2 = st.columns(2)
    with col1:
        max_pages = st.number_input(
            "爬取页数",
            min_value=1,
            max_value=10,
            value=1,
            help="建议从少量页面开始测试"
        )

    with col2:
        st.write("**爬取设置**")
        st.caption(f"数据源: {SOURCES_LABELS.get(selected_source, selected_source)}")
        st.caption(f"最大页数: {max_pages}")

    st.divider()

    # Quick actions
    st.write("**快速操作**")

    quick_col1, quick_col2, quick_col3 = st.columns(3)

    with quick_col1:
        if st.button("📘 爬取知乎", use_container_width=True):
            _trigger_crawl('zhihu', 1)

    with quick_col2:
        if st.button("📰 爬取今日头条", use_container_width=True):
            _trigger_crawl('toutiao', 1)

    with quick_col3:
        if st.button("💬 爬取微信", use_container_width=True):
            _trigger_crawl('wechat', 1)

    st.divider()

    # Custom crawl
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🚀 开始爬取", type="primary", use_container_width=True):
            _trigger_crawl(selected_source, max_pages)

    with col2:
        if st.button("🔄 刷新状态", use_container_width=True):
            st.rerun()

    with col3:
        if st.button("📊 查看统计", use_container_width=True):
            stats = backend_api.get_statistics()
            if 'error' not in stats:
                st.json(stats)


def _show_crawl_logs():
    """Show crawl execution logs."""
    st.subheader("爬虫执行记录")

    # Get logs
    with st.spinner("加载日志..."):
        logs = database_api.get_crawl_logs(limit=100)

    if not logs:
        st.info("暂无爬虫执行记录")
        return

    # Summary chart
    st.write("**最近执行记录**")
    crawl_logs_chart(logs)

    st.divider()

    # Detailed logs
    st.write("**详细记录**")

    for log in logs:
        with st.expander(
            f"📅 {log['start_time']} | {SOURCES_LABELS.get(log['source'], log['source'])} | "
            f"✅ {log['success_count']} | ❌ {log['failed_count']}"
        ):
            col1, col2 = st.columns(2)

            with col1:
                st.write("**基本信息**")
                st.write(f"- 数据源: {SOURCES_LABELS.get(log['source'], log['source'])}")
                st.write(f"- 开始时间: {log['start_time']}")
                if log['end_time']:
                    from utils.helpers import format_time
                    st.write(f"- 结束时间: {log['end_time']}")
                    # Calculate duration
                    try:
                        from datetime import datetime
                        start = datetime.fromisoformat(log['start_time'])
                        end = datetime.fromisoformat(log['end_time'])
                        duration = (end - start).total_seconds()
                        st.write(f"- 执行时长: {duration:.1f} 秒")
                    except:
                        pass

            with col2:
                st.write("**执行结果**")
                st.metric("成功", log['success_count'])
                st.metric("失败", log['failed_count'])

                if log['error_msg']:
                    st.error(f"错误信息: {log['error_msg']}")


def _trigger_crawl(source: str, max_pages: int):
    """Trigger a crawl job."""
    with st.spinner(f"正在爬取 {source}..."):
        result = backend_api.trigger_crawl(source=source, max_pages=max_pages)

    if 'error' in result:
        st.error(f"爬取失败: {result.get('error')}")
    else:
        st.success(f"爬取完成！")
        st.json(result)

        # Show stats
        if isinstance(result, dict):
            stats_col1, stats_col2, stats_col3 = st.columns(3)
            with stats_col1:
                st.metric("成功", result.get('success', 0))
            with stats_col2:
                st.metric("失败", result.get('failed', 0))
            with stats_col3:
                st.metric("总计", result.get('total', 0))

    st.rerun()
