# 任务卡 2: 前端开发 (Streamlit)

## 任务概述

创建 Streamlit 前端应用，支持文章管理、数据统计、数据集管理等功能。与 Flask API (端口8000) 并行运行。

---

## 项目结构

```
web_ui/
├── __init__.py             # 包初始化
├── app.py                 # 主应用入口
├── pages/
│   ├── __init__.py        # 包初始化（使 pages 成为 Python 包）
│   ├── 1_文章列表.py      # 文章列表和筛选
│   ├── 2_数据统计.py      # 数据可视化统计
│   ├── 3_数据清洗.py      # 数据质量检查和清洗
│   ├── 4_导出.py          # 数据导出功能
│   └── 5_数据集管理.py    # 数据集同步管理
└── components/
    ├── __init__.py        # 包初始化
    ├── filters.py         # 筛选器组件
    └── charts.py          # 图表组件
```

**注意**: 每个 `__init__.py` 文件可以为空，或包含包级别的初始化代码。

---

## 依赖配置

**文件: `requirements.txt` 添加**

```
streamlit>=1.28.0
plotly>=5.17.0
altair>=5.0.0
pandas>=2.0.0
```

---

## 任务清单

### P2 - 基础框架

**文件: `web_ui/app.py`**

```python
"""
Streamlit 前端主应用
运行: streamlit run web_ui/app.py --server.port 8501
"""
import streamlit as st
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(
    page_title="爬虫数据管理系统",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🕷️"
)

# 侧边栏导航
page = st.sidebar.selectbox(
    "选择功能",
    ["文章列表", "数据统计", "数据清洗", "导出", "数据集管理"],
    icons=["📄", "📊", "🧹", "📦", "🗄️"]
)

# 路由到各页面
if page == "文章列表":
    from web_ui.pages.article_list import show_page
    show_page()
elif page == "数据统计":
    from web_ui.pages.statistics import show_page
    show_page()
elif page == "数据清洗":
    from web_ui.pages.cleaning import show_page
    show_page()
elif page == "导出":
    from web_ui.pages.export import show_page
    show_page()
elif page == "数据集管理":
    from web_ui.pages.dataset_manager import show_page
    show_page()
```

---

### P2 - 文章列表页

**文件: `web_ui/pages/1_文章列表.py`**

功能要求：

- [ ] 显示文章表格（支持分页，每页20条）
- [ ] 筛选器（侧边栏）：
  - [ ] 来源（zhihu, toutiao, wechat, bilibili, chnsenticorp, lcqmc...）
  - [ ] 分类（psychology, management, finance...）
  - [ ] 质量评分（滑块 0-1）
  - [ ] **内容类型**（article, review, qa, social, news）← 新增
  - [ ] **情感标签**（positive, negative, neutral）← 新增
- [ ] 搜索框（标题/内容关键词）
- [ ] 点击行展开查看详情
- [ ] 详情页面根据 `content_type` 显示不同格式：
  - `qa`: 显示问题和答案对照
  - `review`: 显示情感标签（正面/负面/中性）
  - `social`: 短文本格式
  - `article/news`: 标准文章格式

示例代码：

```python
import streamlit as st
from storage.database import DatabaseManager
import pandas as pd

def show_page():
    st.title("📄 文章列表")

    # 筛选器
    with st.sidebar:
        st.subheader("筛选条件")
        source = st.selectbox("来源", ["全部", "zhihu", "toutiao", "chnsenticorp", "lcqmc"])
        content_type = st.selectbox("内容类型", ["全部", "article", "review", "qa", "social", "news"])  # 新增
        sentiment = st.selectbox("情感标签", ["全部", "positive", "negative", "neutral"])  # 新增
        min_quality = st.slider("最低质量", 0.0, 1.0, 0.5)

    # 获取数据
    db = DatabaseManager()
    articles = db.get_articles(
        source=source if source != "全部" else None,
        content_type=content_type if content_type != "全部" else None,  # 新增
        sentiment=sentiment if sentiment != "全部" else None,  # 新增
        min_quality=min_quality,
        limit=100
    )

    # 显示表格
    data = [{
        "ID": a.id,
        "标题": a.title[:50] + "...",
        "来源": a.source,
        "类型": a.content_type,  # 新增
        "情感": a.sentiment,  # 新增
        "分类": a.category,
        "质量": f"{a.quality_score:.2f}"
    } for a in articles]

    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)

    # 详情展示
    selected_id = st.selectbox("查看详情", options=[a.id for a in articles])
    if selected_id:
        article = next(a for a in articles if a.id == selected_id)
        show_article_detail(article)

def show_article_detail(article):
    """根据 content_type 显示不同格式"""
    st.subheader(article.title)

    if article.content_type == "qa":
        col1, col2 = st.columns(2)
        with col1:
            st.write("**问题:**")
            st.write(article.question)
        with col2:
            st.write("**答案:**")
            st.write(article.answer)
        if article.similarity:
            st.info(f"相似度: {article.similarity}")

    elif article.content_type == "review":
        sentiment_emoji = {"positive": "😊", "negative": "😞", "neutral": "😐"}
        st.markdown(f"**情感:** {sentiment_emoji.get(article.sentiment, '')} {article.sentiment}")
        st.write(article.content)

    else:
        st.write(article.content)
```

---

### P3 - 数据统计页

**文件: `web_ui/pages/2_数据统计.py`**

功能要求：

- [ ] 显示数据库统计卡片：
  - [ ] 总文章数
  - [ ] 有效文章数
  - [ ] 平均质量分
- [ ] **内容类型分布图**（饼图）← 新增
- [ ] **情感分布图**（饼图/柱状图）← 新增
- [ ] **数据集来源分布图**（柱状图）← 新增
- [ ] 分类分布图
- [ ] 来源分布图
- [ ] 质量评分分布图（直方图）

示例代码：

```python
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from storage.database import DatabaseManager

def show_page():
    st.title("📊 数据统计")

    db = DatabaseManager()
    stats = db.get_dataset_statistics()  # 调用新增的方法

    # 统计卡片
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("总文章数", stats["total_articles"])
    with col2:
        st.metric("有效文章", stats["valid_articles"])
    with col3:
        st.metric("平均质量", f"{stats['average_quality_score']:.2f}")
    with col4:
        st.metric("数据集数量", len(stats.get("by_dataset_source", {})))

    # 内容类型分布（新增）
    st.subheader("内容类型分布")
    fig_content_type = px.pie(
        values=list(stats["by_content_type"].values()),
        names=list(stats["by_content_type"].keys()),
        title="按内容类型"
    )
    st.plotly_chart(fig_content_type, use_container_width=True)

    # 情感分布（新增）
    st.subheader("情感分布")
    fig_sentiment = px.bar(
        x=list(stats["by_sentiment"].keys()),
        y=list(stats["by_sentiment"].values()),
        title="按情感标签"
    )
    st.plotly_chart(fig_sentiment, use_container_width=True)

    # 数据集来源分布（新增）
    st.subheader("数据集来源分布")
    fig_dataset = px.bar(
        x=list(stats["by_dataset_source"].keys()),
        y=list(stats["by_dataset_source"].values()),
        title="按数据集来源"
    )
    st.plotly_chart(fig_dataset, use_container_width=True)
```

---

### P3 - 数据清洗页

**文件: `web_ui/pages/3_数据清洗.py`**

功能要求：

- [ ] 显示低质量文章列表（quality_score < 0.5）
- [ ] 显示未分类文章（category 为空）
- [ ] 显示垃圾文章（is_spam = True）
- [ ] 重新清洗按钮（调用 text_cleaner）
- [ ] 批量重新分类按钮
- [ ] 更新质量评分按钮

示例代码：

```python
import streamlit as st
from storage.database import DatabaseManager
from utils.text_cleaner import clean_batch
from classifier.multi_level_classifier import MultiLevelClassifier

def show_page():
    st.title("🧹 数据清洗")

    db = DatabaseManager()

    # 低质量文章
    st.subheader("低质量文章 (质量 < 0.5)")
    low_quality = db.get_articles(min_quality=0.0, limit=100)
    low_quality_filtered = [a for a in low_quality if a.quality_score < 0.5]

    if st.button(f"重新清洗 ({len(low_quality_filtered)} 篇)"):
        with st.spinner("正在清洗..."):
            cleaned = clean_batch([a.to_dict() for a in low_quality_filtered])
            st.success(f"已清洗 {len(cleaned)} 篇")

    # 未分类文章
    st.subheader("未分类文章")
    with db.get_session() as session:
        from storage.models import Article
        unclassified = session.query(Article).filter(
            (Article.category == None) | (Article.category == "")
        ).limit(50).all()

    if st.button(f"重新分类 ({len(unclassified)} 篇)"):
        with st.spinner("正在分类..."):
            classifier = MultiLevelClassifier()
            classified = classifier.classify_batch([a.to_dict() for a in unclassified])
            st.success(f"已分类 {len(classified)} 篇")
```

---

### P3 - 数据集管理页

**文件: `web_ui/pages/5_数据集管理.py`**

功能要求：

- [ ] 显示数据集列表表格：
  - [ ] 数据集名称
  - [ ] 来源
  - [ ] 内容类型
  - [ ] 文章数量
  - [ ] 最后同步时间
- [ ] 手动触发同步按钮
- [ ] 显示同步进度和日志
- [ ] 数据集样本预览

示例代码：

```python
import streamlit as st
import pandas as pd
from storage.database import DatabaseManager
from scheduler.jobs import ManualJobs

def show_page():
    st.title("🗄️ 数据集管理")

    # 数据集列表
    datasets = [
        {"name": "THUCNews", "source": "toutiao", "type": "news", "dataset": "lansinuote/ChnSentiCorp"},
        {"name": "ChnSentiCorp", "source": "chnsenticorp", "type": "review", "dataset": "lansinuote/ChnSentiCorp"},
        {"name": "LCQMC", "source": "lcqmc", "type": "qa", "dataset": "clue/lcqmc"},
    ]

    # 显示数据集表格
    for ds in datasets:
        with st.expander(f"📦 {ds['name']} ({ds['type']})"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**数据集:** `{ds['dataset']}`")
            with col2:
                st.write(f"**来源:** {ds['source']}")
            with col3:
                if st.button(f"同步 {ds['name']}", key=f"sync_{ds['name']}"):
                    sync_dataset(ds['source'])

    # 同步日志
    if "sync_logs" in st.session_state:
        st.code(st.session_state.sync_logs, language="text")

def sync_dataset(source):
    """手动触发数据集同步"""
    st.info(f"正在同步 {source}...")
    jobs = ManualJobs()
    result = jobs.crawl_source(source, max_pages=5)
    st.success(f"同步完成: {result['success']} 篇文章")
    st.rerun()
```

---

### P4 - 导出页增强

**文件: `web_ui/pages/4_导出.py`**

新增功能：

- [ ] 现有导出格式（TXT, JSON, CSV）
- [ ] **QA CSV 导出** ← 新增
  - 格式: question, answer, similarity, category
- [ ] **评论情感 JSON 导出** ← 新增
  - 格式: content, sentiment, label, source

示例代码：

```python
# QA CSV 导出
if st.button("导出 QA 对为 CSV"):
    import tempfile
    from storage.database import DatabaseManager

    db = DatabaseManager()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as f:
        output_path = db.export_qa_pairs_to_csv(f.name)
        with open(output_path, "r") as file:
            st.download_button(
                label="下载 QA CSV",
                data=file,
                file_name="qa_pairs.csv",
                mime="text/csv"
            )
```

---

### P4 - 组件开发

**文件: `web_ui/components/filters.py`**

```python
"""筛选器组件"""
import streamlit as st

def content_type_filter(default="全部"):
    """内容类型筛选器"""
    return st.selectbox(
        "内容类型",
        ["全部", "article", "review", "qa", "social", "news"],
        index=["全部", "article", "review", "qa", "social", "news"].index(default) if default in ["全部", "article", "review", "qa", "social", "news"] else 0
    )

def sentiment_filter(default="全部"):
    """情感标签筛选器"""
    return st.selectbox(
        "情感标签",
        ["全部", "positive", "negative", "neutral"],
        index=["全部", "positive", "negative", "neutral"].index(default) if default in ["全部", "positive", "negative", "neutral"] else 0
    )
```

**文件: `web_ui/components/charts.py`**

```python
"""图表组件"""
import plotly.express as px
import plotly.graph_objects as go

def sentiment_pie_chart(sentiment_data):
    """情感分布饼图"""
    colors = {"positive": "#00CC96", "negative": "#EF553B", "neutral": "#636EFA"}

    fig = go.Figure(data=[go.Pie(
        labels=list(sentiment_data.keys()),
        values=list(sentiment_data.values()),
        marker=dict(colors=[colors.get(k, "#636EFA") for k in sentiment_data.keys()]),
        textinfo='label+percent'
    )])

    fig.update_layout(
        title="情感分布",
        height=400
    )
    return fig

def content_type_bar_chart(content_type_data):
    """内容类型分布柱状图"""
    fig = px.bar(
        x=list(content_type_data.keys()),
        y=list(content_type_data.values()),
        labels={"x": "内容类型", "y": "文章数量"},
        title="内容类型分布"
    )
    return fig
```

---

## 验收标准

- [ ] 启动 `streamlit run web_ui/app.py --server.port 8501` 成功运行
- [ ] 文章列表页可按 `content_type` 和 `sentiment` 筛选
- [ ] QA 类型文章显示问题和答案对照
- [ ] 评论类型文章显示情感标签（带表情）
- [ ] 数据统计页显示内容类型分布饼图
- [ ] 数据统计页显示情感分布饼图
- [ ] 数据集管理页显示各数据集状态
- [ ] 可手动触发数据集同步
- [ ] 导出页支持 QA CSV 和评论情感 JSON 格式

---

## 启动命令

```bash
# 进入项目目录
cd /Users/kjonekong/temp-crawler-repo

# 安装依赖
pip install streamlit plotly altair

# 启动前端
streamlit run web_ui/app.py --server.port 8501

# 访问 http://localhost:8501
```

---

## 开发注意事项

1. **数据访问**: 前端直接访问 `DatabaseManager`，不经过 Flask API
2. **会话状态**: 使用 `st.session_state` 存储筛选条件和数据
3. **性能**: 大数据量时使用 `st.cache_data` 缓存查询结果
4. **错误处理**: 使用 `try-except` 捕获数据库错误，用 `st.error()` 显示
5. **响应式**: 使用 `st.columns()` 实现响应式布局
