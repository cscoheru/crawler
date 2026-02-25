"""
文章列表页 - 显示和筛选文章
"""
import streamlit as st
from utils.api import database_api
from utils.config import DEFAULT_PAGE_SIZE
from utils.helpers import format_number
from components.filters import article_filters
from components.article_card import article_card


def show():
    """Display the article list page."""
    st.title("📋 文章列表")

    # Initialize session state
    if 'selected_articles' not in st.session_state:
        st.session_state.selected_articles = []
    if 'page' not in st.session_state:
        st.session_state.page = 1
    if 'search_query' not in st.session_state:
        st.session_state.search_query = ""

    # Filters section
    with st.expander("🔍 筛选条件", expanded=False):
        filters = article_filters()

    # Search bar
    col1, col2 = st.columns([4, 1])
    with col1:
        search = st.text_input(
            "搜索文章",
            value=st.session_state.search_query,
            placeholder="输入关键词搜索标题、内容或作者...",
            key="article_search"
        )
    with col2:
        if st.button("🔍 搜索", use_container_width=True):
            st.session_state.search_query = search
            st.session_state.page = 1
            st.rerun()

    # Get articles
    with st.spinner("加载中..."):
        # Prepare filter parameters
        params = {
            'page': st.session_state.page,
            'page_size': DEFAULT_PAGE_SIZE,
            'sort_by': st.session_state.get('filter_sort_by', 'publish_time'),
            'sort_order': st.session_state.get('filter_sort_order', 'desc'),
            'search': search if search else None
        }

        # Add filters
        if 'source' in filters:
            params['source'] = filters['source']
        if 'category' in filters:
            params['category'] = filters['category']
        if 'min_quality' in filters:
            params['min_quality'] = filters['min_quality']
        if 'is_valid' in filters:
            params['is_valid'] = filters['is_valid']
        if 'is_spam' in filters:
            params['is_spam'] = filters['is_spam']

        result = database_api.get_articles(**params)

    # Statistics header
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("总文章数", format_number(result['total']))
    with col2:
        current_page = result['page']
        total_pages = result['total_pages']
        st.metric(f"当前页", f"{current_page} / {total_pages}")
    with col3:
        selected_count = len(st.session_state.get('selected_articles', []))
        st.metric("已选择", format_number(selected_count))

    st.divider()

    # Batch operations
    if st.session_state.get('selected_articles'):
        st.info(f"已选择 {selected_count} 篇文章")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📤 批量导出", use_container_width=True):
                st.session_state.export_article_ids = st.session_state.selected_articles
                st.success("已选择要导出的文章！请在导出页面完成导出。")

        with col2:
            if st.button("🔄 批量标记为有效", use_container_width=True):
                _batch_update_valid(True)

        with col3:
            if st.button("🗑️ 批量删除", type="secondary", use_container_width=True):
                if st.confirm(f"确定要删除选中的 {selected_count} 篇文章吗？此操作不可恢复。"):
                    _batch_delete()
                else:
                    st.info("已取消删除")

        st.divider()

    # Article list
    if not result['articles']:
        st.info("没有找到符合条件的文章")
    else:
        for article in result['articles']:
            article_card(article, show_select=True)
            st.divider()

        # Pagination
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("← 上一页", disabled=current_page <= 1, use_container_width=True):
                st.session_state.page = current_page - 1
                st.rerun()

        with col2:
            # Page input
            new_page = st.number_input(
                "跳转到页",
                min_value=1,
                max_value=total_pages,
                value=current_page,
                step=1
            )
            if new_page != current_page:
                st.session_state.page = int(new_page)
                st.rerun()

        with col3:
            if st.button("下一页 →", disabled=current_page >= total_pages, use_container_width=True):
                st.session_state.page = current_page + 1
                st.rerun()


def _batch_update_valid(is_valid: bool):
    """Batch update article validity."""
    import streamlit as st
    from utils.api import database_api

    article_ids = st.session_state.get('selected_articles', [])
    if not article_ids:
        return

    with st.spinner("更新中..."):
        for article_id in article_ids:
            database_api.update_article(article_id, {'is_valid': is_valid})

    st.success(f"已更新 {len(article_ids)} 篇文章！")
    st.session_state.selected_articles = []
    st.rerun()


def _batch_delete():
    """Batch delete articles."""
    import streamlit as st
    from utils.api import database_api

    article_ids = st.session_state.get('selected_articles', [])
    if not article_ids:
        return

    with st.spinner("删除中..."):
        deleted = database_api.delete_articles(article_ids)

    st.success(f"已删除 {deleted} 篇文章！")
    st.session_state.selected_articles = []
    st.rerun()
