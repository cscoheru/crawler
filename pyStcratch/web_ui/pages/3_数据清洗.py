"""
数据清洗页 - 管理无效和垃圾文章
"""
import streamlit as st
from utils.api import database_api
from utils.helpers import format_time
from components.filters import status_filters
from components.article_card import article_card


def show():
    """Display the data cleaning page."""
    st.title("🧹 数据清洗")

    tab1, tab2, tab3 = st.tabs(["无效文章", "垃圾文章", "质量检查"])

    with tab1:
        _show_invalid_articles()

    with tab2:
        _show_spam_articles()

    with tab3:
        _show_quality_check()


def _show_invalid_articles():
    """Show articles marked as invalid."""
    st.subheader("无效文章列表")

    # Get invalid articles
    with st.spinner("加载中..."):
        result = database_api.get_articles(
            is_valid=False,
            page=st.session_state.get('clean_page', 1),
            page_size=50,
            sort_by='created_at',
            sort_order='desc'
        )

    if not result['articles']:
        st.info("没有无效文章")
        return

    col1, col2 = st.columns(2)
    with col1:
        st.metric("无效文章数", result['total'])

    with col2:
        if st.button("✅ 全部标记为有效", use_container_width=True):
            if st.confirm(f"确定要将所有 {result['total']} 篇无效文章标记为有效吗？"):
                _batch_mark_valid(result['articles'])
                st.rerun()

    st.divider()

    # Display articles
    for article in result['articles']:
        with st.container():
            st.write(f"**{article['title']}**")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.caption(f"📍 {article['source']}")
            with col2:
                st.caption(f"🕒 {format_time(article['created_at'])}")
            with col3:
                st.caption(f"⭐ {article['quality_score']:.2f}")

            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("✅ 标记为有效", key=f"valid_{article['id']}", use_container_width=True):
                    database_api.update_article(article['id'], {'is_valid': True})
                    st.success("已标记为有效！")
                    st.rerun()

            with col2:
                if st.button("👀 查看", key=f"view_invalid_{article['id']}", use_container_width=True):
                    st.json(article)

            with col3:
                if st.button("🗑️ 删除", key=f"del_invalid_{article['id']}", use_container_width=True):
                    database_api.delete_articles([article['id']])
                    st.success("已删除！")
                    st.rerun()

            st.divider()


def _show_spam_articles():
    """Show articles marked as spam."""
    st.subheader("垃圾文章列表")

    # Get spam articles
    with st.spinner("加载中..."):
        result = database_api.get_articles(
            is_spam=True,
            page=st.session_state.get('spam_page', 1),
            page_size=50,
            sort_by='created_at',
            sort_order='desc'
        )

    if not result['articles']:
        st.info("没有垃圾文章")
        return

    col1, col2 = st.columns(2)
    with col1:
        st.metric("垃圾文章数", result['total'])

    with col2:
        if st.button("🗑️ 删除全部垃圾文章", type="secondary", use_container_width=True):
            if st.confirm(f"确定要删除所有 {result['total']} 篇垃圾文章吗？此操作不可恢复。"):
                _batch_delete_spam(result['articles'])
                st.rerun()

    st.divider()

    # Display articles
    for article in result['articles']:
        with st.container():
            st.write(f"**{article['title']}**")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.caption(f"📍 {article['source']}")
            with col2:
                st.caption(f"🕒 {format_time(article['created_at'])}")
            with col3:
                st.caption(f"⭐ {article['quality_score']:.2f}")

            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🔄 取消垃圾标记", key=f"unspam_{article['id']}", use_container_width=True):
                    database_api.update_article(article['id'], {'is_spam': False})
                    st.success("已取消垃圾标记！")
                    st.rerun()

            with col2:
                if st.button("👀 查看", key=f"view_spam_{article['id']}", use_container_width=True):
                    st.json(article)

            with col3:
                if st.button("🗑️ 删除", key=f"del_spam_{article['id']}", use_container_width=True):
                    database_api.delete_articles([article['id']])
                    st.success("已删除！")
                    st.rerun()

            st.divider()


def _show_quality_check():
    """Show articles with low quality scores for review."""
    st.subheader("质量检查")

    # Quality threshold
    col1, col2 = st.columns(2)
    with col1:
        min_quality = st.slider("最低质量分数", 0.0, 1.0, 0.5, 0.05)
    with col2:
        limit = st.number_input("显示数量", 1, 100, 20)

    # Get low quality articles
    with st.spinner("加载中..."):
        result = database_api.get_articles(
            is_valid=True,
            is_spam=False,
            min_quality=0.0,
            page=1,
            page_size=limit,
            sort_by='quality_score',
            sort_order='asc'
        )

        # Filter by max quality for display
        filtered_articles = [a for a in result['articles'] if a['quality_score'] <= min_quality]

    if not filtered_articles:
        st.info(f"没有质量分数低于 {min_quality} 的文章")
        return

    col1, col2 = st.columns(2)
    with col1:
        st.metric("低质量文章数", len(filtered_articles))

    with col2:
        if st.button("📊 分析质量分布", use_container_width=True):
            st.info("质量分析功能开发中...")

    st.divider()

    # Display articles
    for article in filtered_articles:
        with st.container():
            col1, col2 = st.columns([1, 20])
            with col1:
                st.write(f"⭐ {article['quality_score']:.2f}")
            with col2:
                st.write(f"**{article['title']}**")

            st.caption(f"📍 {article['source']} | 📂 {article.get('category', '未分类')}")

            col1, col2, col3 = st.columns(3)
            with col1:
                new_score = st.slider(
                    "调整质量分数",
                    0.0, 1.0,
                    float(article['quality_score']),
                    0.05,
                    key=f"quality_{article['id']}"
                )
                if st.button("更新", key=f"update_quality_{article['id']}", use_container_width=True):
                    database_api.update_article(article['id'], {'quality_score': new_score})
                    st.success("已更新！")
                    st.rerun()

            with col2:
                if st.button("👀 查看", key=f"view_quality_{article['id']}", use_container_width=True):
                    with st.expander("文章内容", expanded=True):
                        st.write(article['content'])

            with col3:
                if st.button("🗑️ 删除", key=f"del_quality_{article['id']}", type="secondary", use_container_width=True):
                    database_api.delete_articles([article['id']])
                    st.success("已删除！")
                    st.rerun()

            st.divider()


def _batch_mark_valid(articles: list):
    """Mark all articles as valid."""
    for article in articles:
        database_api.update_article(article['id'], {'is_valid': True})
    st.success(f"已将 {len(articles)} 篇文章标记为有效！")


def _batch_delete_spam(articles: list):
    """Delete all spam articles."""
    article_ids = [a['id'] for a in articles]
    deleted = database_api.delete_articles(article_ids)
    st.success(f"已删除 {deleted} 篇垃圾文章！")
