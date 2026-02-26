# 任务卡 3: 架构师

## 任务概述

设计整体架构，确保数据库扩展、API 更新、前端开发的协调一致，处理向后兼容性和迁移策略。

---

## 架构设计

### 系统架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                          用户界面层                                  │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐              ┌──────────────────┐            │
│  │  Streamlit Front │              │   Flask API      │            │
│  │     端口 8501     │              │    端口 8000      │            │
│  └────────┬─────────┘              └────────┬─────────┘            │
│           │                                  │                      │
└───────────┼──────────────────────────────────┼──────────────────────┘
            │                         直接数据库访问
            │                         (可选通过API)
            ↓                                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│                          业务逻辑层                                  │
├─────────────────────────────────────────────────────────────────────┤
│  DatabaseManager  │  ManualJobs  │  CrawlerScheduler  │  Classifiers │
└────────────────────┴──────────────┴───────────────────┴─────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                          数据访问层                                  │
├─────────────────────────────────────────────────────────────────────┤
│  SQLAlchemy ORM  │  Article Model  │  DatasetMetadata Model         │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                          数据存储层                                  │
├─────────────────────────────────────────────────────────────────────┤
│     SQLite (开发)    │    PostgreSQL (生产可选)                    │
└─────────────────────────────────────────────────────────────────────┘
```

### 服务通信方式

| 场景 | 推荐方案 | 说明 |
|------|----------|------|
| Streamlit → 数据库 | 直接访问 | Streamlit 和 Flask 在同一服务器，直接使用 DatabaseManager |
| 外部调用 → 数据 | Flask API | 供其他服务调用 |
| 定时任务 → 数据 | 直接访问 | 调度任务直接使用 DatabaseManager |

---

## 任务清单

### 1. 数据库设计确认

**文档: `docs/database_schema.md`**

确认以下设计决策：

- [ ] **字段类型确认**:
  - `content_type`: String(50) - 足够存储所有类型
  - `sentiment`: String(20) - 存储英文标签
  - `sentiment_label`: Integer - 存储原始标签值
  - `question`, `answer`: Text - 支持长文本
  - `choices`: Text - JSON 格式存储
  - `similarity`: String(20) - 存储相似度状态

- [ ] **索引设计**:
  ```sql
  CREATE INDEX idx_content_type ON articles(content_type);
  CREATE INDEX idx_sentiment ON articles(sentiment);
  CREATE INDEX idx_dataset_source ON articles(dataset_source);
  CREATE INDEX idx_question ON articles(question) WHERE content_type='qa';
  ```

- [ ] **默认值策略**:
  - `content_type`: 默认 "article"
  - `language`: 默认 "zh"
  - 新字段允许 NULL 以兼容旧数据

**输出**: 数据库设计文档 (`docs/database_schema.md`)

---

### 2. 向后兼容性设计

**文档: `docs/migration_strategy.md`**

设计迁移策略：

- [ ] **数据迁移脚本** (`storage/migration_add_huggingface_fields.py`):
  ```python
  def upgrade():
      # 添加新字段
      op.add_column('articles', sa.Column('content_type', ...))
      # ...

  def downgrade():
      # 回滚方案
      op.drop_column('articles', 'content_type')
      # ...
  ```

- [ ] **旧数据处理**:
  - 自动设置 `content_type="article"` 给所有旧数据
  - 根据 `source` 推断类型: weibo→social, toutiao→news

- [ ] **API 兼容性**:
  - 所有现有 API 端点保持不变
  - 新参数为可选，不影响现有调用

- [ ] **回滚机制**:
  - 数据库迁移前自动备份
  - 提供 downgrade 脚本

**输出**: 迁移策略文档 (`docs/migration_strategy.md`)

---

### 3. API 接口设计

**文档: `docs/api_reference.md`**

定义新 API 契约：

- [ ] `/api/articles` - 获取文章列表
  ```
  GET /api/articles?content_type=review&sentiment=positive&page=1&limit=20

  Response:
  {
    "success": true,
    "data": {
      "articles": [...],
      "total": 100,
      "page": 1
    }
  }
  ```

- [ ] `/api/stats/detailed` - 详细统计
  ```
  Response:
  {
    "success": true,
    "data": {
      "by_content_type": {"article": 1000, "review": 500, ...},
      "by_sentiment": {"positive": 300, "negative": 150, ...},
      "by_dataset_source": {"lansinuote/ChnSentiCorp": 800, ...}
    }
  }
  ```

- [ ] `/api/datasets` - 数据集列表
- [ ] `/api/datasets/<name>/sync` - 触发同步

**输出**: API 参考文档 (`docs/api_reference.md`)

---

### 4. 技术决策记录

**文档: `docs/adr.md` (Architecture Decision Records)**

记录以下决策：

| 决策点 | 选择 | 理由 |
|--------|------|------|
| Streamlit 数据访问 | 直接数据库访问 | 同服务器，减少网络开销，简化开发 |
| DatasetMetadata 表 | P3 阶段实现 | 第一阶段核心功能优先，元数据可后续添加 |
| 数据集同步 | 手动触发 + 定时任务 | 灵活控制，避免过度消耗资源 |
| 情感标签存储 | 同时存英文和数字 | 英文可读，数字保留原始值 |
| QA 内容存储 | 分开 question/answer 字段 | 便于查询和展示 |

**输出**: 技术决策文档 (`docs/adr.md`)

---

### 5. 测试策略

**文档: `docs/testing_strategy.md`**

设计测试方案：

- [ ] **单元测试**:
  - 测试 `DatabaseManager` 新增方法
  - 测试爬虫返回数据格式

- [ ] **集成测试**:
  ```python
  # tests/integration/test_huggingface_flow.py
  def test_chnsenticorp_flow():
      # 1. 爬取数据
      jobs.crawl_source("chnsenticorp", max_pages=1)
      # 2. 验证数据库
      articles = db.get_articles(source="chnsenticorp")
      assert articles[0].content_type == "review"
      assert articles[0].sentiment is not None
      # 3. 验证 API
      response = client.get("/api/articles?content_type=review")
      assert response.status_code == 200
  ```

- [ ] **性能测试**:
  - 测试大数据量下的统计查询性能
  - 测试并发爬取的性能

- [ ] **数据一致性验证**:
  ```python
  def test_data_consistency():
      # 验证所有文章都有 content_type
      # 验证 review 类型都有 sentiment
      # 验证 qa 类型都有 question 和 answer
  ```

**输出**: 测试策略文档 (`docs/testing_strategy.md`)

---

### 6. 文档和规范

**输出文档清单**:

- [ ] `docs/database_schema.md` - 数据库设计文档
- [ ] `docs/migration_strategy.md` - 迁移策略文档
- [ ] `docs/api_reference.md` - API 参考文档
- [ ] `docs/adr.md` - 技术决策记录
- [ ] `docs/testing_strategy.md` - 测试策略文档
- [ ] `README.md` - 更新项目说明（包含新功能）

---

## 交付物清单

| 交付物 | 格式 | 优先级 |
|--------|------|--------|
| 数据库设计文档 | Markdown | P0 |
| 迁移策略文档 | Markdown | P0 |
| 迁移脚本 | Python | P0 |
| API 参考文档 | Markdown | P1 |
| 技术决策记录 | Markdown | P1 |
| 测试策略文档 | Markdown | P2 |
| 集成测试代码 | Python | P2 |

---

## 协调要点

### 与后端开发协调

1. 确认数据库字段命名约定
2. 确认 API 响应格式
3. 确认错误处理策略
4. 审核迁移脚本

### 与前端开发协调

1. 确认数据获取方式（直接数据库 vs API）
2. 确认筛选器参数命名
3. 确认图表数据格式
4. 审核前端组件接口

---

## 风险和应对

| 风险 | 影响 | 应对措施 |
|------|------|----------|
| 数据库迁移失败 | 高 | 提前备份，提供回滚脚本 |
| 旧数据兼容性问题 | 中 | 设置合理默认值，提供迁移脚本 |
| API 性能问题 | 中 | 添加数据库索引，考虑分页 |
| 前后端接口不一致 | 中 | 提前定义 API 契约，使用类型提示 |

---

## 决策点确认

在项目开始前，需要确认以下决策：

- [ ] **Streamlit 数据访问方式**: 直接数据库访问 ✅
- [ ] **DatasetMetadata 表**: P3 阶段实现 ✅
- [ ] **数据集同步**: 手动触发 + 定时任务 ✅
- [ ] **数据库**: SQLite (开发), PostgreSQL (生产可选) ✅

---

## 验收标准

- [ ] 所有设计文档完成并经过评审
- [ ] 数据库迁移脚本可安全执行和回滚
- [ ] API 接口文档与实际实现一致
- [ ] 集成测试覆盖主要数据流
- [ ] 旧数据成功迁移且功能正常
- [ ] 新旧功能共存且无冲突
