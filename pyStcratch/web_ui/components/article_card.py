"""
Article card component for displaying article information.
"""
import streamlit as st
from utils.helpers import format_time, get_quality_color, get_source_emoji, get_category_emoji


def article_card(article: dict, show_select: bool = True):
    """
    Display an article card with title, metadata, and actions.

    Args:
        article: Article dictionary
        show_select: Whether to show selection checkbox
    """
    # Selection checkbox
    if show_select:
        col1, col2 = st.columns([1, 20])
        with col1:
            selected = st.checkbox(
                "",
                key=f"select_{article['id']}",
                value=article['id'] in st.session_state.get('selected_articles', []),
                on_change=_toggle_select,
                args=(article['id'],),
                label_visibility="collapsed"
            )
    else:
        col1 = st.container()
        col2 = st.container()

    with col2:
        # Title with source and category
        title_col1, title_col2 = st.columns([1, 10])
        with title_col1:
            st.markdown(f"{get_source_emoji(article.get('source', ''))}")
        with title_col2:
            st.markdown(f"**{article.get('title', '无标题')}**")

        # Metadata row
        meta_col1, meta_col2, meta_col3, meta_col4, meta_col5 = st.columns(5)
        with meta_col1:
            st.caption(f"📍 {article.get('source', '未知')}")
        with meta_col2:
            category = article.get('category', '未分类')
            st.caption(f"{get_category_emoji(category)} {category}")
        with meta_col3:
            score = article.get('quality_score', 0)
            st.caption(f"{get_quality_color(score)} {score:.2f}")
        with meta_col4:
            author = article.get('author', '未知')
            st.caption(f"👤 {author[:20]}..." if len(author) > 20 else f"👤 {author}")
        with meta_col5:
            st.caption(f"🕒 {format_time(article.get('created_at', ''))}")

        # Content preview
        with st.expander("查看摘要"):
            content = article.get('content', '')
            st.write(content[:500] + "..." if len(content) > 500 else content)

        # Action buttons
        action_col1, action_col2, action_col3, action_col4 = st.columns(4)
        with action_col1:
            if st.button("👀 查看", key=f"view_{article['id']}", use_container_width=True):
                st.session_state.view_article_id = article['id']
                st.rerun()

        with action_col2:
            if st.button("✏️ 编辑", key=f"edit_{article['id']}", use_container_width=True):
                st.session_state.edit_article_id = article['id']
                st.rerun()

        with action_col3:
            if st.button("📋 复制", key=f"copy_{article['id']}", use_container_width=True):
                _copy_to_clipboard(article)
                st.success("已复制内容！")

        with action_col4:
            if st.button("🗑️ 删除", key=f"delete_{article['id']}", use_container_width=True):
                st.session_state.delete_article_id = article['id']
                st.rerun()


def _toggle_select(article_id: int):
    """Toggle article selection state."""
    selected = st.session_state.get('selected_articles', [])
    if article_id in selected:
        selected.remove(article_id)
    else:
        selected.append(article_id)
    st.session_state.selected_articles = selected


def _copy_to_clipboard(article: dict):
    """Copy article content to clipboard."""
    content = f"{article.get('title', '')}\n\n{article.get('content', '')}"
    st.session_state.clipboard_content = content
    # Note: Actual clipboard copying requires JavaScript
    # This stores in session state for user to copy manually
