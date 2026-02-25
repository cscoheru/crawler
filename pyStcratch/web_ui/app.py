"""
Streamlit 主应用 - 爬虫数据管理与内容创作系统
"""
import os
import sys

# Add project path to imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="爬虫数据管理",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
css_path = os.path.join(os.path.dirname(__file__), 'styles', 'custom.css')
try:
    with open(css_path, 'r', encoding='utf-8') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
except FileNotFoundError:
    pass

# Initialize session state
def init_session_state():
    """Initialize session state variables."""
    if 'api_base_url' not in st.session_state:
        st.session_state.api_base_url = os.getenv('API_BASE_URL', 'http://localhost:8000')
    if 'selected_articles' not in st.session_state:
        st.session_state.selected_articles = []
    if 'page' not in st.session_state:
        st.session_state.page = 1
    if 'filter_source' not in st.session_state:
        st.session_state.filter_source = '全部'
    if 'filter_category' not in st.session_state:
        st.session_state.filter_category = '全部'
    if 'filter_min_quality' not in st.session_state:
        st.session_state.filter_min_quality = 0.0
    if 'filter_show_invalid' not in st.session_state:
        st.session_state.filter_show_invalid = False
    if 'filter_show_spam' not in st.session_state:
        st.session_state.filter_show_spam = False
    if 'filter_sort_by' not in st.session_state:
        st.session_state.filter_sort_by = 'publish_time'
    if 'filter_sort_order' not in st.session_state:
        st.session_state.filter_sort_order = 'desc'

init_session_state()

# Sidebar
with st.sidebar:
    st.title("📊 爬虫数据管理")
    st.markdown("---")

    page = st.radio(
        "选择功能",
        ["文章列表", "数据统计", "数据清洗", "爬虫管理", "导出发布", "系统设置"],
        label_visibility="collapsed",
        icons=["📋", "📈", "🧹", "🕷️", "📤", "⚙️"]
    )

    st.markdown("---")

    # Quick stats
    st.subheader("快速统计")

    try:
        from utils.api import backend_api
        stats = backend_api.get_statistics()

        if 'error' not in stats:
            st.metric("文章总数", f"{stats.get('total_articles', 0):,}")
            st.metric("有效文章", f"{stats.get('valid_articles', 0):,}")
    except Exception as e:
        st.caption(f"统计加载失败: {e}")

    st.markdown("---")

    # System status
    st.caption(f"**API**: {st.session_state.api_base_url}")

    try:
        health = backend_api.get_health()
        if health.get('status') == 'healthy':
            st.success("✅ 系统在线")
        else:
            st.error("❌ 系统离线")
    except:
        st.warning("⚠️ 无法连接")

# Main content
if page == "文章列表":
    from pages._1_文章列表 import show
    show()

elif page == "数据统计":
    from pages._2_数据统计 import show
    show()

elif page == "数据清洗":
    from pages._3_数据清洗 import show
    show()

elif page == "爬虫管理":
    from pages._4_爬虫管理 import show
    show()

elif page == "导出发布":
    from pages._5_导出发布 import show
    show()

elif page == "系统设置":
    from pages._6_系统设置 import show
    show()

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #6b7280; font-size: 0.875rem;'>
    爬虫数据管理系统 v1.0.0 | Built with Streamlit
</div>
""", unsafe_allow_html=True)
