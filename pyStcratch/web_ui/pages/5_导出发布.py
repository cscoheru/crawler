"""
导出发布页 - 导出文章到各种格式
"""
import streamlit as st
import os
from datetime import datetime
from utils.api import backend_api, database_api
from utils.config import CATEGORIES, CATEGORIES_LABELS


def show():
    """Display the export page."""
    st.title("📤 导出发布")

    tab1, tab2 = st.tabs(["导出文章", "同步设置"])

    with tab1:
        _show_export_articles()

    with tab2:
        _show_sync_settings()


def _show_export_articles():
    """Show article export interface."""
    st.subheader("导出文章")

    # Export settings
    col1, col2, col3 = st.columns(3)

    with col1:
        format_type = st.selectbox(
            "导出格式",
            ["txt", "json", "csv"],
            format_func=lambda x: {
                'txt': 'TXT 文本文件',
                'json': 'JSON 数据文件',
                'csv': 'CSV 表格文件'
            }.get(x, x)
        )

    with col2:
        all_categories = ["全部"] + list(CATEGORIES)
        category = st.selectbox(
            "筛选分类",
            all_categories,
            format_func=lambda x: CATEGORIES_LABELS.get(x, x) if x != '全部' else '全部'
        )
        category = None if category == '全部' else category

    with col3:
        min_quality = st.slider(
            "最低质量分数",
            0.0, 1.0, 0.5, 0.05
        )

    st.divider()

    # Export buttons
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📤 开始导出", type="primary", use_container_width=True):
            _do_export(format_type, category, min_quality)

    with col2:
        if st.button("📊 查看预览", use_container_width=True):
            _preview_export(category, min_quality)

    with col3:
        if st.button("📁 打开导出目录", use_container_width=True):
            _open_export_dir()

    st.divider()

    # Recent exports
    _show_recent_exports()


def _show_sync_settings():
    """Show Dify sync settings."""
    st.subheader("Dify 知识库同步")

    # Settings
    col1, col2 = st.columns(2)

    with col1:
        hours = st.number_input("同步最近N小时的文章", 1, 168, 24)

    with col2:
        min_quality = st.slider("最低质量分数", 0.0, 1.0, 0.6, 0.05)

    st.divider()

    # Actions
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔄 同步到 Dify", type="primary", use_container_width=True):
            _do_sync_dify(hours, min_quality)

    with col2:
        if st.button("📊 查看配置", use_container_width=True):
            _show_dify_config()

    with col3:
        if st.button("🧪 测试连接", use_container_width=True):
            _test_dify_connection()

    st.divider()

    # Info
    st.info("""
    **Dify 同步说明**:
    - 将最近的高质量文章同步到 Dify 知识库
    - 需要在 .env 文件中配置 DIFY_API_KEY 和 DIFY_BASE_URL
    - 同步操作可能需要较长时间，请耐心等待
    """)


def _do_export(format_type: str, category: str, min_quality: float):
    """Execute the export."""
    with st.spinner(f"正在导出为 {format_type.upper()} 格式..."):
        result = backend_api.export_articles(
            format_type=format_type,
            category=category,
            min_quality=min_quality
        )

    if 'error' in result:
        st.error(f"导出失败: {result.get('error')}")
    else:
        st.success(f"导出成功！")
        st.write(f"导出路径: `{result.get('export_path')}`")

        # Show file info
        export_path = result.get('export_path')
        if export_path and os.path.exists(export_path):
            if os.path.isfile(export_path):
                size = os.path.getsize(export_path)
                st.caption(f"文件大小: {size / 1024:.1f} KB")
            else:
                # Directory - count files
                files = os.listdir(export_path)
                st.caption(f"导出了 {len(files)} 个文件")


def _preview_export(category: str, min_quality: float):
    """Preview what will be exported."""
    with st.spinner("获取预览..."):
        result = database_api.get_articles(
            category=category,
            min_quality=min_quality,
            page=1,
            page_size=10
        )

    st.write(f"**预览** (最多显示10条)")

    if not result['articles']:
        st.info("没有符合条件的文章")
        return

    for i, article in enumerate(result['articles'], 1):
        with st.expander(f"{i}. {article['title']}"):
            st.write(f"- 来源: {article['source']}")
            st.write(f"- 分类: {article.get('category', '未分类')}")
            st.write(f"- 质量: {article['quality_score']:.2f}")
            st.write(f"- 长度: {len(article['content'])} 字符")

    st.caption(f"总计约 {result['total']} 篇文章可导出")


def _open_export_dir():
    """Show export directory contents."""
    data_dir = os.getenv('DATA_DIR', './data')
    export_dir = os.path.join(data_dir, 'exports')

    if not os.path.exists(export_dir):
        st.info("导出目录不存在")
        return

    files = sorted(os.listdir(export_dir), reverse=True)[:20]

    if not files:
        st.info("导出目录为空")
        return

    st.write("**导出目录内容** (最近20个文件/文件夹)")

    for f in files:
        path = os.path.join(export_dir, f)
        if os.path.isfile(path):
            size = os.path.getsize(path)
            st.write(f"- 📄 {f} ({size / 1024:.1f} KB)")
        else:
            count = len(os.listdir(path)) if os.path.isdir(path) else 0
            st.write(f"- 📁 {f} ({count} 个文件)")


def _show_recent_exports():
    """Show recent export files."""
    data_dir = os.getenv('DATA_DIR', './data')
    export_dir = os.path.join(data_dir, 'exports')

    if not os.path.exists(export_dir):
        return

    # Get recent JSON and CSV files
    files = []
    for f in os.listdir(export_dir):
        path = os.path.join(export_dir, f)
        if os.path.isfile(path) and f.endswith(('.json', '.csv')):
            files.append((f, os.path.getmtime(path)))

    files.sort(key=lambda x: x[1], reverse=True)

    if files:
        st.write("**最近导出的文件**")

        for f, mtime in files[:10]:
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.write(f"- {f}")

            with col2:
                dt = datetime.fromtimestamp(mtime)
                st.caption(f"{dt.strftime('%Y-%m-%d %H:%M')}")

            with col3:
                if st.button("下载", key=f"download_{f}", use_container_width=True):
                    st.info(f"文件位置: {os.path.join(export_dir, f)}")


def _do_sync_dify(hours: int, min_quality: float):
    """Execute Dify sync."""
    with st.spinner(f"正在同步最近 {hours} 小时的文章..."):
        result = backend_api.sync_dify(hours=hours, min_quality=min_quality)

    if 'error' in result:
        st.error(f"同步失败: {result.get('error')}")
    else:
        st.success("同步完成！")
        st.json(result)


def _show_dify_config():
    """Show Dify configuration."""
    import os
    from dotenv import load_dotenv

    load_dotenv()

    st.write("**Dify 配置**")

    api_key = os.getenv('DIFY_API_KEY')
    base_url = os.getenv('DIFY_BASE_URL')
    dataset_id = os.getenv('DIFY_DATASET_ID')

    col1, col2 = st.columns(2)

    with col1:
        st.write(f"- API Key: {'已配置' if api_key else '未配置'}")
        st.write(f"- Base URL: {base_url or '未配置'}")

    with col2:
        st.write(f"- Dataset ID: {dataset_id or '未配置'}")


def _test_dify_connection():
    """Test Dify connection."""
    api_key = os.getenv('DIFY_API_KEY')
    base_url = os.getenv('DIFY_BASE_URL')

    if not api_key or not base_url:
        st.warning("Dify 配置不完整，请先配置 API Key 和 Base URL")
        return

    with st.spinner("测试连接..."):
        try:
            import requests
            headers = {"Authorization": f"Bearer {api_key}"}
            response = requests.get(f"{base_url}/datasets", headers=headers, timeout=10)

            if response.status_code == 200:
                st.success("连接成功！")
                st.json(response.json())
            else:
                st.error(f"连接失败: {response.status_code}")
        except Exception as e:
            st.error(f"连接失败: {e}")
