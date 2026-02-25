"""
Chart components for data visualization.
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from utils.helpers import format_number


def metric_card(title: str, value: any, delta: any = None, help_text: str = None):
    """
    Display a metric card with title, value, and optional delta.

    Args:
        title: Card title
        value: Metric value
        delta: Optional change indicator
        help_text: Optional help text tooltip
    """
    if help_text:
        st.metric(title, value, delta, help=help_text)
    else:
        st.metric(title, value, delta)


def category_distribution_chart(data: dict, title: str = "分类分布"):
    """
    Display a pie chart for category distribution.

    Args:
        data: Dictionary with categories as keys and counts as values
        title: Chart title
    """
    categories = list(data.keys())
    counts = list(data.values())

    fig = px.pie(
        values=counts,
        names=categories,
        title=title,
        color_discrete_sequence=px.colors.qualitative.Set2
    )

    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br>数量: %{value}<br>占比: %{percent}<extra></extra>'
    )

    st.plotly_chart(fig, use_container_width=True)


def source_distribution_chart(data: dict, title: str = "来源分布"):
    """
    Display a horizontal bar chart for source distribution.

    Args:
        data: Dictionary with sources as keys and counts as values
        title: Chart title
    """
    sources = list(data.keys())
    counts = list(data.values())

    fig = px.bar(
        x=counts,
        y=sources,
        orientation='h',
        title=title,
        labels={'x': '文章数量', 'y': '来源'},
        color=counts,
        color_continuous_scale='Blues'
    )

    fig.update_layout(
        yaxis={'categoryorder': 'total ascending'},
        height=300
    )

    st.plotly_chart(fig, use_container_width=True)


def quality_distribution_chart(quality_scores: list, title: str = "质量分数分布"):
    """
    Display a histogram for quality score distribution.

    Args:
        quality_scores: List of quality scores
        title: Chart title
    """
    if not quality_scores:
        st.info("暂无质量分数数据")
        return

    fig = px.histogram(
        x=quality_scores,
        nbins=20,
        title=title,
        labels={'x': '质量分数', 'y': '文章数量'},
        color_discrete_sequence=['#3B82F6']
    )

    fig.update_layout(
        bargap=0.1,
        xaxis=dict(tick0=0, dtick=0.1)
    )

    st.plotly_chart(fig, use_container_width=True)


def trend_chart(data: list, title: str = "趋势图", x_label: str = "日期", y_label: str = "数量"):
    """
    Display a line chart for trends over time.

    Args:
        data: List of dictionaries with 'date' and 'count' keys
        title: Chart title
        x_label: X-axis label
        y_label: Y-axis label
    """
    if not data:
        st.info("暂无趋势数据")
        return

    dates = [item.get('date', item.get('created_at', '')) for item in data]
    counts = [item.get('count', item.get('total', 0)) for item in data]

    fig = px.line(
        x=dates,
        y=counts,
        title=title,
        labels={'x': x_label, 'y': y_label},
        markers=True
    )

    fig.update_traces(
        line_color='#3B82F6',
        marker_size=8
    )

    fig.update_layout(
        xaxis=dict(tickangle=-45),
        hovermode='x unified'
    )

    st.plotly_chart(fig, use_container_width=True)


def statistics_overview(stats: dict):
    """
    Display overview statistics cards.

    Args:
        stats: Statistics dictionary with various metrics
    """
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        metric_card(
            "📚 文章总数",
            format_number(stats.get('total_articles', 0)),
            help_text="数据库中的文章总数"
        )

    with col2:
        metric_card(
            "✅ 有效文章",
            format_number(stats.get('valid_articles', 0)),
            delta=f"{stats.get('valid_articles', 0) / max(stats.get('total_articles', 1), 1) * 100:.1f}%",
            help_text="标记为有效的文章数量"
        )

    with col3:
        metric_card(
            "⭐ 平均质量",
            f"{stats.get('average_quality_score', 0):.2f}",
            help_text="所有文章的平均质量分数"
        )

    with col4:
        source_count = len([k for k, v in stats.get('by_source', {}).items() if v > 0])
        metric_card(
            "🌐 数据来源",
            source_count,
            help_text="有文章的数据源数量"
        )


def category_quality_chart(data: dict, title: str = "分类质量对比"):
    """
    Display a bar chart comparing quality scores across categories.

    Args:
        data: Dictionary with categories as keys and avg quality as values
        title: Chart title
    """
    categories = list(data.keys())
    qualities = list(data.values())

    fig = px.bar(
        x=categories,
        y=qualities,
        title=title,
        labels={'x': '分类', 'y': '平均质量分数'},
        color=qualities,
        color_continuous_scale='RdYlGn',
        range_color=[0, 1]
    )

    fig.update_layout(
        yaxis=dict(range=[0, 1])
    )

    st.plotly_chart(fig, use_container_width=True)


def crawl_logs_chart(logs: list, title: str = "爬虫执行记录"):
    """
    Display a summary of recent crawl logs.

    Args:
        logs: List of crawl log dictionaries
        title: Chart title
    """
    if not logs:
        st.info("暂无爬虫记录")
        return

    # Group by source
    source_stats = {}
    for log in logs:
        source = log.get('source', 'unknown')
        if source not in source_stats:
            source_stats[source] = {'success': 0, 'failed': 0}

        source_stats[source]['success'] += log.get('success_count', 0)
        source_stats[source]['failed'] += log.get('failed_count', 0)

    # Create stacked bar chart
    sources = list(source_stats.keys())
    success_counts = [source_stats[s]['success'] for s in sources]
    failed_counts = [source_stats[s]['failed'] for s in sources]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name='成功',
        x=sources,
        y=success_counts,
        marker_color='#10B981'
    ))
    fig.add_trace(go.Bar(
        name='失败',
        x=sources,
        y=failed_counts,
        marker_color='#EF4444'
    ))

    fig.update_layout(
        title=title,
        barmode='stack',
        xaxis_title='数据源',
        yaxis_title='文章数量'
    )

    st.plotly_chart(fig, use_container_width=True)
