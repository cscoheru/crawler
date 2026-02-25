"""
Filter components for articles.
"""
import streamlit as st
from utils.config import SOURCES, SOURCES_LABELS, CATEGORIES, CATEGORIES_LABELS


def article_filters() -> dict:
    """
    Display article filter options.

    Returns:
        Dictionary of filter values
    """
    filters = {}

    # Source filter
    all_sources = ["全部"] + list(SOURCES)
    source_index = all_sources.index(st.session_state.get('filter_source', '全部'))
    selected_source = st.selectbox(
        "数据来源",
        all_sources,
        index=source_index,
        format_func=lambda x: SOURCES_LABELS.get(x, x) if x != '全部' else '全部'
    )
    st.session_state.filter_source = selected_source
    if selected_source != '全部':
        filters['source'] = selected_source

    # Category filter
    all_categories = ["全部"] + list(CATEGORIES)
    category_index = all_categories.index(st.session_state.get('filter_category', '全部'))
    selected_category = st.selectbox(
        "分类",
        all_categories,
        index=category_index,
        format_func=lambda x: CATEGORIES_LABELS.get(x, x) if x != '全部' else '全部'
    )
    st.session_state.filter_category = selected_category
    if selected_category != '全部':
        filters['category'] = selected_category

    # Quality score filter
    col1, col2 = st.columns(2)
    with col1:
        min_quality = st.slider(
            "最低质量分数",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.get('filter_min_quality', 0.0),
            step=0.05
        )
        st.session_state.filter_min_quality = min_quality
        if min_quality > 0:
            filters['min_quality'] = min_quality

    with col2:
        # Valid/spam filter
        show_invalid = st.checkbox("显示无效文章", value=st.session_state.get('filter_show_invalid', False))
        st.session_state.filter_show_invalid = show_invalid
        if not show_invalid:
            filters['is_valid'] = True

        show_spam = st.checkbox("显示垃圾文章", value=st.session_state.get('filter_show_spam', False))
        st.session_state.filter_show_spam = show_spam
        if not show_spam:
            filters['is_spam'] = False

    # Sort options
    col1, col2 = st.columns(2)
    with col1:
        sort_by = st.selectbox(
            "排序方式",
            ['publish_time', 'created_at', 'quality_score', 'title'],
            index=['publish_time', 'created_at', 'quality_score', 'title'].index(
                st.session_state.get('filter_sort_by', 'publish_time')
            ),
            format_func=lambda x: {
                'publish_time': '发布时间',
                'created_at': '创建时间',
                'quality_score': '质量分数',
                'title': '标题'
            }.get(x, x)
        )
        st.session_state.filter_sort_by = sort_by
        filters['sort_by'] = sort_by

    with col2:
        sort_order = st.selectbox(
            "排序顺序",
            ['desc', 'asc'],
            index=0 if st.session_state.get('filter_sort_order', 'desc') == 'desc' else 1,
            format_func=lambda x: '降序' if x == 'desc' else '升序'
        )
        st.session_state.filter_sort_order = sort_order
        filters['sort_order'] = sort_order

    # Reset filters button
    if st.button("🔄 重置筛选条件", use_container_width=True):
        for key in list(st.session_state.keys()):
            if key.startswith('filter_'):
                del st.session_state[key]
        st.rerun()

    return filters


def status_filters() -> dict:
    """
    Display status filter options for data cleaning page.

    Returns:
        Dictionary of filter values
    """
    filters = {}

    col1, col2, col3 = st.columns(3)

    with col1:
        show_invalid = st.checkbox(
            "显示无效文章",
            value=st.session_state.get('status_show_invalid', True),
            key='status_show_invalid'
        )
        if not show_invalid:
            filters['is_valid'] = True

    with col2:
        show_spam = st.checkbox(
            "显示垃圾文章",
            value=st.session_state.get('status_show_spam', True),
            key='status_show_spam'
        )
        if not show_spam:
            filters['is_spam'] = False

    with col3:
        max_quality = st.slider(
            "最高质量分数",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.get('status_max_quality', 1.0),
            step=0.05,
            key='status_max_quality'
        )
        if max_quality < 1.0:
            filters['max_quality'] = max_quality

    return filters
