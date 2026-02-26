# 任务卡 1: 后端开发

## 任务概述

扩展数据库和后端API以支持 HuggingFace 数据集的新数据类型（评论、问答、社交内容等）

## 关键文件

| 文件 | 操作 | 优先级 |
|------|------|--------|
| `storage/models.py` | 添加新字段、新表 | P0 |
| `storage/database.py` | 新增查询方法、更新保存逻辑 | P0 |
| `crawler/huggingface_thucnews.py` | 返回新字段 | P0 |
| `crawler/huggingface_chinese.py` | 返回新字段 | P0 |
| `web_server.py` | 新增API端点 | P1 |
| `config/settings.py` | 添加配置 | P2 |

---

## 任务清单

### P0 - 数据库扩展

**文件: `storage/models.py`**

在 `Article` 模型中添加以下字段：

```python
# 内容类型
content_type = Column(String(50), default="article")  # article/review/qa/social/news

# 情感标注
sentiment = Column(String(20))  # positive/negative/neutral
sentiment_label = Column(Integer)  # 0/1/2 原始标签

# 问答相关
question = Column(Text)  # QA类型的问题
answer = Column(Text)  # QA类型的答案
choices = Column(Text)  # JSON: 选择题选项
similarity = Column(String(20))  # similar/not_similar (LCQMC)

# 数据集来源
dataset_source = Column(String(100))  # 数据集名称 e.g. "lansinuote/ChnSentiCorp"
language = Column(String(10), default="zh")  # 语言标签
```

新增 `DatasetMetadata` 表：

```python
class DatasetMetadata(Base):
    """HuggingFace 数据集元数据"""
    __tablename__ = "dataset_metadata"

    id = Column(Integer, primary_key=True)
    dataset_name = Column(String(100))
    source = Column(String(50))
    content_type = Column(String(50))
    description = Column(Text)
    total_samples = Column(Integer)
    last_sync_at = Column(DateTime)
    config = Column(Text)
    created_at = Column(DateTime, default=func.now())
```

更新 `to_dict()` 方法包含新字段：

```python
def to_dict(self):
    return {
        # ... 现有字段
        "content_type": self.content_type,
        "sentiment": self.sentiment,
        "sentiment_label": self.sentiment_label,
        "question": self.question,
        "answer": self.answer,
        "choices": json.loads(self.choices) if self.choices else None,
        "similarity": self.similarity,
        "dataset_source": self.dataset_source,
        "language": self.language,
    }
```

创建数据库迁移脚本 `storage/migration_add_huggingface_fields.py`。

---

### P0 - 爬虫更新

**文件: `crawler/huggingface_chinese.py`**

修改 `HuggingFaceChnSentiCorpCrawler._parse_dataset_item()`：

```python
def _parse_dataset_item(self, item, keyword):
    text = item.get('text', '')
    label = item.get('label', 0)

    sentiment_map = {0: "negative", 1: "positive", 2: "neutral"}

    return {
        "content_type": "review",
        "sentiment": sentiment_map.get(label, "neutral"),
        "sentiment_label": label,
        "dataset_source": "lansinuote/ChnSentiCorp",
        # ... 其他现有字段
    }
```

修改 `HuggingFaceLCQMCrawler._parse_dataset_item()`：

```python
def _parse_dataset_item(self, item, keyword):
    question1 = item.get('question1', '')
    question2 = item.get('question2', '')
    label = item.get('label', 0)

    return {
        "content_type": "qa",
        "question": question1,
        "answer": question2,
        "similarity": "similar" if label == 1 else "not_similar",
        "dataset_source": "clue/lcqmc",
        # ... 其他现有字段
    }
```

**文件: `crawler/huggingface_thucnews.py`**

修改 `HuggingFaceWeiboCrawler._parse_dataset_item()`：

```python
return {
    "content_type": "social",
    "sentiment": sentiment_map.get(label, "neutral"),
    # ... 其他字段
}
```

修改 `HuggingFaceTHUCNewsCrawler._parse_dataset_item()`：

```python
return {
    "content_type": "news",
    # ... 其他字段
}
```

**文件: `crawler/huggingface_chinese.py` - 补充其他爬虫**

修改 `HuggingFaceCMNLUCrawler._parse_dataset_item()`：

```python
return {
    "content_type": "article",  # 通用NLP作为文章
    "dataset_source": "clue/cmnlu",
    # ... 其他字段
}
```

修改 `HuggingFaceC3Crawler._parse_dataset_item()`：

```python
return {
    "content_type": "qa",  # 儿童问答
    "question": question,
    "choices": choices,  # 列表
    "answer": answer,
    "dataset_source": "cmnli/c3",
    # ... 其他字段
}
```

---

### P0 - 数据库操作

**文件: `storage/database.py`**

更新 `save_article()` 方法：

```python
def save_article(self, article_data: Dict) -> Optional[Article]:
    # ... 现有代码

    article = Article(
        # ... 现有字段
        content_type=article_data.get("content_type", "article"),
        sentiment=article_data.get("sentiment"),
        sentiment_label=article_data.get("sentiment_label"),
        question=article_data.get("question"),
        answer=article_data.get("answer"),
        choices=json.dumps(article_data.get("choices", [])) if article_data.get("choices") else None,
        similarity=article_data.get("similarity"),
        dataset_source=article_data.get("dataset_source"),
        language=article_data.get("language", "zh"),
    )
```

新增查询方法：

```python
def get_articles_by_content_type(
    self, content_type: str, **filters
) -> List[Article]:
    """按内容类型筛选文章"""

def get_dataset_statistics(self) -> Dict:
    """获取数据集统计信息
    返回: {
        "by_content_type": {"article": 1000, "review": 500, ...},
        "by_sentiment": {"positive": 300, "negative": 150, ...},
        "by_dataset_source": {"lansinuote/ChnSentiCorp": 800, ...}
    }
    """

def get_qa_pairs(self, **filters) -> List[Article]:
    """获取问答对数据"""

def get_reviews_by_sentiment(self, sentiment: str, **filters) -> List[Article]:
    """按情感筛选评论"""
```

---

### P1 - Flask API

**文件: `web_server.py`**

新增端点：

```python
@app.route('/api/articles')
def get_articles():
    """获取文章列表，支持新筛选参数
    参数:
    - content_type: article/review/qa/social
    - sentiment: positive/negative/neutral
    - dataset_source: 数据集名称
    """

@app.route('/api/stats/detailed')
def get_detailed_stats():
    """获取详细统计，包含:
    - 按内容类型分布
    - 按情感分布
    - 按数据集来源分布
    """

@app.route('/api/datasets')
def get_datasets():
    """获取数据集列表和同步状态"""

@app.route('/api/datasets/<dataset_name>/sync', methods=['POST'])
def sync_dataset(dataset_name):
    """手动同步指定数据集"""
```

---

### P2 - 配置和导出

**文件: `config/settings.py`**

添加配置：

```python
# 内容类型
CONTENT_TYPES = {
    "article": "文章",
    "review": "评论",
    "qa": "问答",
    "social": "社交内容",
    "news": "新闻",
}

# 情感标签
SENTIMENT_LABELS = {0: "negative", 1: "positive", 2: "neutral"}

# HuggingFace 数据集
HUGGINGFACE_DATASETS = {
    "thucnews": {"name": "lansinuote/ChnSentiCorp", "source": "toutiao"},
    "chnsenticorp": {"name": "lansinuote/ChnSentiCorp", "source": "chnsenticorp"},
    "lcqmc": {"name": "clue/lcqmc", "source": "lcqmc"},
}
```

新增导出方法：

```python
def export_qa_pairs_to_csv(self, output_file: str, **filters) -> str:
    """导出问答对为 CSV 格式
    格式: question, answer, similarity, category
    """

def export_reviews_with_sentiment(self, output_file: str, **filters) -> str:
    """导出评论带情感标注
    格式: content, sentiment, label, source
    """
```

创建迁移脚本 `storage/migrate_old_data.py`：

```python
def migrate_old_articles():
    """为现有文章设置默认的新字段值"""
    db = DatabaseManager()
    with db.get_session() as session:
        old_articles = session.query(Article).filter(
            Article.content_type == None
        ).all()

        for article in old_articles:
            article.content_type = "article"
            article.language = "zh"
            if article.source == "weibo":
                article.content_type = "social"
            elif article.source == "toutiao":
                article.content_type = "news"

        session.commit()
```

---

## 验收标准

- [ ] 爬取 chnsenticorp 数据后，文章的 `content_type="review"`, `sentiment` 有值
- [ ] 爬取 lcqmc 数据后，文章的 `content_type="qa"`, `question`, `answer` 有值
- [ ] API `/api/stats/detailed` 返回按内容类型、情感、数据集的统计
- [ ] API `/api/articles?content_type=review&sentiment=positive` 正确筛选
- [ ] 旧数据自动设置默认值 `content_type="article"`, `language="zh"`
- [ ] 导出 QA CSV 格式正确（包含 question, answer, similarity 列）

---

## 测试命令

```bash
# 测试爬虫
cd /Users/kjonekong/temp-crawler-repo
python -c "
from scheduler.jobs import ManualJobs
jobs = ManualJobs()
jobs.crawl_source('chnsenticorp', keywords=['服务'], max_pages=5)
jobs.crawl_source('lcqmc', keywords=['怎么'], max_pages=5)
"

# 验证数据库字段
python -c "
from storage.database import DatabaseManager
db = DatabaseManager()
articles = db.get_articles(source='chnsenticorp', limit=1)
if articles:
    print(f'content_type: {articles[0].content_type}')
    print(f'sentiment: {articles[0].sentiment}')
"

# 测试 API
curl http://localhost:8000/api/stats/detailed
curl "http://localhost:8000/api/articles?content_type=review"
```
