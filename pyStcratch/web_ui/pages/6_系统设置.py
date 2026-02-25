"""
系统设置页 - 系统信息和配置
"""
import streamlit as st
import os
from utils.api import backend_api
from utils.config import API_BASE_URL, DATABASE_URL, CATEGORIES, CATEGORIES_LABELS


def show():
    """Display the system settings page."""
    st.title("⚙️ 系统设置")

    tab1, tab2, tab3, tab4 = st.tabs(["系统状态", "运行任务", "配置信息", "关于"])

    with tab1:
        _show_system_status()

    with tab2:
        _show_run_tasks()

    with tab3:
        _show_config()

    with tab4:
        _show_about()


def _show_system_status():
    """Show system status."""
    st.subheader("系统状态")

    # Health check
    with st.spinner("检查系统健康..."):
        health = backend_api.get_health()
        stats = backend_api.get_statistics()

    col1, col2 = st.columns(2)

    with col1:
        st.write("**服务状态**")
        if health.get('status') == 'healthy':
            st.success("✅ 服务运行正常")
        else:
            st.error("❌ 服务异常")

        st.write(f"- 服务: {health.get('service', 'N/A')}")
        st.write(f"- 数据库: {health.get('database', 'N/A')}")

    with col2:
        st.write("**数据库统计**")
        if 'error' not in stats:
            st.metric("文章总数", f"{stats.get('total_articles', 0):,}")
            st.metric("有效文章", f"{stats.get('valid_articles', 0):,}")
            st.metric("平均质量", f"{stats.get('average_quality_score', 0):.2f}")
        else:
            st.error(f"获取统计失败: {stats.get('error')}")

    st.divider()

    # Database connection test
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔄 刷新状态", use_container_width=True):
            st.rerun()

    with col2:
        if st.button("🧪 测试数据库", use_container_width=True):
            _test_database()


def _show_run_tasks():
    """Show runnable tasks."""
    st.subheader("运行任务")

    st.write("**预设任务**")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**数据同步**")
        if st.button("🔄 完整同步", use_container_width=True):
            _run_full_sync()

        st.caption("执行完整流程：爬取→分类→导出→Dify同步")

    with col2:
        st.write("**爬虫任务**")
        if st.button("📘 快速爬取知乎", use_container_width=True):
            _quick_crawl('zhihu')

        if st.button("📰 快速爬取头条", use_container_width=True):
            _quick_crawl('toutiao')

    st.divider()

    st.write("**任务说明**")
    st.info("""
    - **完整同步**: 执行完整的数据同步流程，包括爬取、分类、导出和Dify同步
    - **快速爬取**: 仅执行单个数据源的快速爬取（1页）
    - 所有任务都在后台执行，可以查看执行记录了解进度
    """)


def _show_config():
    """Show system configuration."""
    st.subheader("配置信息")

    st.write("**环境配置**")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**前端**")
        st.write(f"- API地址: `{API_BASE_URL}`")
        st.write(f"- 数据库: `{DATABASE_URL}`")

    with col2:
        st.write("**数据目录**")
        data_dir = os.getenv('DATA_DIR', './data')
        st.write(f"- 数据目录: `{data_dir}`")

        if os.path.exists(data_dir):
            files = os.listdir(data_dir)
            st.write(f"- 子目录: {', '.join(files)}")
        else:
            st.warning("数据目录不存在")

    st.divider()

    st.write("**分类配置**")

    for cat in CATEGORIES:
        label = CATEGORIES_LABELS.get(cat, cat)
        st.write(f"- `{cat}`: {label}")

    st.divider()

    st.write("**环境变量**")

    env_vars = [
        'DATABASE_URL',
        'DATA_DIR',
        'LOG_LEVEL',
        'DIFY_API_KEY',
        'DIFY_BASE_URL',
        'DIFY_DATASET_ID',
        'API_BASE_URL'
    ]

    for var in env_vars:
        value = os.getenv(var)
        if value is None:
            continue

        # Hide sensitive values
        if 'KEY' in var or 'SECRET' in var:
            display_value = '*' * 10
        else:
            display_value = value

        st.write(f"- `{var}`: {display_value}")


def _show_about():
    """Show about information."""
    st.subheader("关于")

    st.write("**爬虫数据管理与内容创作系统**")

    st.write("""
    这是一个用于爬取、管理和分析网络内容的系统。

    **主要功能**:
    - 🕷️ 多平台内容爬取（知乎、今日头条、微信公众号等）
    - 📊 数据统计和可视化
    - 🧹 数据清洗和质量控制
    - 📤 多格式导出（TXT、JSON、CSV）
    - 🔄 Dify 知识库同步

    **技术栈**:
    - 后端: Python + Flask + SQLAlchemy
    - 前端: Streamlit
    - 数据库: SQLite / PostgreSQL
    - 爬虫: Scrapy + aiohttp
    """)

    st.divider()

    st.write("**版本信息**")
    st.write("- 版本: 1.0.0")
    st.write("- 最后更新: 2024")

    st.divider()

    st.write("**相关链接**")
    st.write("- GitHub: [项目仓库](https://github.com/cscoheru/crawler)")
    st.write("- 文档: `docs/` 目录")


def _test_database():
    """Test database connection."""
    from utils.api import database_api

    with st.spinner("测试数据库连接..."):
        try:
            result = database_api.get_articles(page=1, page_size=1)
            st.success(f"数据库连接正常！共 {result['total']} 篇文章")
        except Exception as e:
            st.error(f"数据库连接失败: {e}")


def _run_full_sync():
    """Run full sync workflow."""
    with st.spinner("执行完整同步流程..."):
        result = backend_api.run_full_sync()

    if 'error' in result:
        st.error(f"同步失败: {result.get('error')}")
    else:
        st.success("同步完成！")
        st.json(result)


def _quick_crawl(source: str):
    """Quick crawl for a source."""
    with st.spinner(f"正在爬取 {source}..."):
        result = backend_api.trigger_crawl(source=source, max_pages=1)

    if 'error' in result:
        st.error(f"爬取失败: {result.get('error')}")
    else:
        st.success(f"爬取完成！")
        st.json(result)
