# API 接口设计文档

## 1. 概述

本文档定义爬虫数据管理与内容创作系统的 RESTful API 接口规范。

---

## 2. 基础规范

### 2.1 协议与格式

| 属性 | 值 |
|------|-----|
| 协议 | HTTP/1.1, HTTPS |
| 数据格式 | JSON |
| 字符编码 | UTF-8 |
| 版本控制 | URL 版本 (/api/v1/...) |

### 2.2 统一响应格式

**成功响应**:
```json
{
    "success": true,
    "data": {},
    "meta": {
        "page": 1,
        "page_size": 20,
        "total": 100,
        "has_more": true
    }
}
```

**错误响应**:
```json
{
    "success": false,
    "error": {
        "code": "ERROR_CODE",
        "message": "错误描述",
        "details": {}
    }
}
```

### 2.3 错误码规范

| 代码 | 常量 | 描述 |
|------|------|------|
| 1000 | INTERNAL_ERROR | 内部错误 |
| 1001 | INVALID_REQUEST | 无效请求 |
| 1002 | UNAUTHORIZED | 未授权 |
| 1003 | FORBIDDEN | 禁止访问 |
| 1004 | NOT_FOUND | 资源未找到 |
| 1005 | RATE_LIMIT_EXCEEDED | 超出速率限制 |
| 2000 | DATABASE_ERROR | 数据库错误 |
| 2001 | DUPLICATE_ENTRY | 重复条目 |
| 2002 | INVALID_FILTER | 无效过滤条件 |
| 3000 | CRAWLER_ERROR | 爬虫错误 |
| 3001 | CRAWLER_SOURCE_NOT_SUPPORTED | 不支持的数据源 |
| 3002 | CRAWLER_TIMEOUT | 爬虫超时 |
| 4000 | CLASSIFIER_ERROR | 分类器错误 |
| 4001 | LOW_CONFIDENCE | 置信度过低 |
| 5000 | CREATION_ERROR | 创作错误 |
| 5001 | AI_SERVICE_UNAVAILABLE | AI 服务不可用 |
| 5002 | INSUFFICIENT_REFERENCES | 参考文章不足 |

### 2.4 分页规范

```json
{
    "page": 1,           // 页码，从 1 开始
    "page_size": 20,     // 每页数量，默认 20，最大 100
    "sort_by": "created_at",     // 排序字段
    "sort_order": "desc"          // asc 或 desc
}
```

---

## 3. 文章管理 API

### 3.1 获取文章列表

**端点**: `GET /api/v1/articles`

**请求参数**:
```json
{
    "page": 1,
    "page_size": 20,
    "source": "zhihu",           // 可选: zhihu/toutiao/wechat/bilibili/dedao/ximalaya
    "category": "psychology",     // 可选
    "subcategory": "clinical",    // 可选
    "min_quality": 0.6,          // 可选
    "search": "搜索关键词",       // 可选 (全文搜索)
    "sort_by": "created_at",     // 可选: created_at/publish_time/quality_score
    "sort_order": "desc"          // 可选: asc/desc
}
```

**响应**:
```json
{
    "success": true,
    "data": {
        "articles": [
            {
                "id": 1,
                "source": "zhihu",
                "article_id": "12345678",
                "title": "文章标题",
                "content": "文章内容...",
                "author": "作者名",
                "publish_time": "2024-01-15T10:00:00Z",
                "url": "https://...",
                "category": "psychology",
                "subcategory": "clinical",
                "sub_subcategory": "depression",
                "category_path": ["心理咨询", "临床心理", "抑郁障碍"],
                "confidence": 0.85,
                "quality_score": 0.75,
                "is_valid": true,
                "is_spam": false,
                "created_at": "2024-01-15T10:00:00Z",
                "updated_at": "2024-01-15T10:00:00Z"
            }
        ],
        "total": 100,
        "page": 1,
        "page_size": 20,
        "has_more": true
    }
}
```

### 3.2 获取文章详情

**端点**: `GET /api/v1/articles/:id`

**响应**:
```json
{
    "success": true,
    "data": {
        "article": { /* 完整文章对象 */ }
    }
}
```

### 3.3 创建文章

**端点**: `POST /api/v1/articles`

**请求**:
```json
{
    "source": "manual",
    "title": "文章标题",
    "content": "文章内容",
    "author": "作者",
    "category": "psychology",
    "url": "https://..."
}
```

**响应**:
```json
{
    "success": true,
    "data": {
        "article": { /* 创建的文章对象 */ }
    }
}
```

### 3.4 更新文章

**端点**: `PATCH /api/v1/articles/:id`

**请求** (仅包含要更新的字段):
```json
{
    "category": "management",
    "quality_score": 0.8,
    "is_valid": true
}
```

### 3.5 删除文章

**端点**: `DELETE /api/v1/articles/:id`

**响应**:
```json
{
    "success": true,
    "data": {
        "deleted_id": 123
    }
}
```

### 3.6 批量删除

**端点**: `DELETE /api/v1/articles/batch`

**请求**:
```json
{
    "ids": [1, 2, 3, 4, 5]
}
```

**响应**:
```json
{
    "success": true,
    "data": {
        "deleted_count": 5,
        "failed_ids": []
    }
}
```

### 3.7 清洗文章

**端点**: `POST /api/v1/articles/:id/clean`

**请求**:
```json
{
    "remove_duplicates": true,
    "remove_html": true,
    "normalize_whitespace": true
}
```

**响应**:
```json
{
    "success": true,
    "data": {
        "article": { /* 更新后的文章 */ },
        "changes": {
            "content_before": "...",
            "content_after": "...",
            "chars_removed": 150
        }
    }
}
```

### 3.8 查找相似文章

**端点**: `GET /api/v1/articles/similar`

**请求参数**:
```json
{
    "topic": "抑郁症的治疗方法",
    "limit": 10,
    "category": "psychology",
    "min_quality": 0.6
}
```

**响应**:
```json
{
    "success": true,
    "data": {
        "articles": [
            {
                "id": 1,
                "title": "文章标题",
                "similarity": 0.85,
                "category": "psychology",
                "quality_score": 0.75
            }
        ]
    }
}
```

---

## 4. 统计 API

### 4.1 获取统计数据

**端点**: `GET /api/v1/statistics`

**响应**:
```json
{
    "success": true,
    "data": {
        "overview": {
            "total_articles": 5000,
            "valid_articles": 4800,
            "average_quality_score": 0.72,
            "today_new_articles": 50
        },
        "by_source": {
            "zhihu": 2000,
            "toutiao": 1500,
            "wechat": 1000,
            "bilibili": 300,
            "dedao": 150,
            "ximalaya": 50
        },
        "by_category": {
            "psychology": 2000,
            "management": 1800,
            "finance": 1000,
            "other": 200
        },
        "recent_trend": [
            {"date": "2024-01-01", "count": 45},
            {"date": "2024-01-02", "count": 52},
            {"date": "2024-01-03", "count": 48}
        ],
        "quality_distribution": {
            "high": 3000,
            "medium": 1500,
            "low": 500
        }
    }
}
```

---

## 5. 创作 API

### 5.1 创建文章任务

**端点**: `POST /api/v1/create-article`

**请求**:
```json
{
    "topic": "如何缓解职场压力",
    "reference_ids": [1, 2, 3],      // 可选: 指定参考文章
    "style": "professional",          // 可选: professional/casual/humorous
    "length": "medium",               // 可选: short/medium/long
    "title_type": "catchy",           // 可选: catchy/descriptive/question
    "target_audience": "职场人士",
    "tips": ["要实用", "给出具体方法"]
}
```

**响应**:
```json
{
    "success": true,
    "data": {
        "task_id": "uuid-string",
        "status": "processing",
        "estimated_time": 60
    }
}
```

### 5.2 查询任务状态

**端点**: `GET /api/v1/create-article/:task_id`

**响应 - 处理中**:
```json
{
    "success": true,
    "data": {
        "task_id": "uuid-string",
        "status": "processing",
        "progress": 50,
        "current_step": "正在生成内容..."
    }
}
```

**响应 - 完成**:
```json
{
    "success": true,
    "data": {
        "task_id": "uuid-string",
        "status": "completed",
        "article": {
            "id": 123,
            "title": "生成的文章标题",
            "content": "生成的文章内容...",
            "word_count": 2500,
            "reference_articles": [1, 2, 3],
            "created_at": "2024-01-15T10:00:00Z"
        }
    }
}
```

### 5.3 获取创作列表

**端点**: `GET /api/v1/created-articles`

**请求参数**:
```json
{
    "page": 1,
    "page_size": 20,
    "status": "draft",    // draft/published
    "topic": "职场"        // 可选搜索
}
```

### 5.4 导出文章

**端点**: `POST /api/v1/created-articles/:id/export`

**请求**:
```json
{
    "format": "markdown"   // markdown/html/word/plain
}
```

**响应**:
```json
{
    "success": true,
    "data": {
        "download_url": "https://...",
        "expires_at": "2024-01-15T12:00:00Z"
    }
}
```

---

## 6. 爬虫 API

### 6.1 触发爬虫

**端点**: `POST /api/v1/crawl`

**请求**:
```json
{
    "source": "zhihu",           // all/zhihu/toutiao/wechat/bilibili/dedao/ximalaya
    "max_pages": 2,
    "keywords": ["心理咨询", "焦虑症"]  // 可选
}
```

**响应**:
```json
{
    "success": true,
    "data": {
        "job_id": "uuid-string",
        "source": "zhihu",
        "status": "started"
    }
}
```

### 6.2 查询爬虫状态

**端点**: `GET /api/v1/crawl/status/:job_id`

**响应**:
```json
{
    "success": true,
    "data": {
        "job_id": "uuid-string",
        "status": "running",
        "progress": {
            "total": 100,
            "completed": 50
        },
        "result": {
            "success": 45,
            "failed": 5,
            "duplicate": 10
        }
    }
}
```

---

## 7. 系统 API

### 7.1 健康检查

**端点**: `GET /api/v1/health`

**响应**:
```json
{
    "success": true,
    "data": {
        "status": "healthy",
        "timestamp": "2024-01-15T10:00:00Z",
        "services": {
            "database": "healthy",
            "dify": "healthy",
            "ai_service": "healthy"
        },
        "version": "1.0.0"
    }
}
```

---

## 8. 限流策略

### 8.1 速率限制

| 类型 | 限制 |
|------|------|
| 默认 | 60 请求/分钟, 1000 请求/小时 |
| API 密钥用户 | 120 请求/分钟, 5000 请求/小时 |
| 爬虫触发 | 10 请求/小时 |
| 创作任务 | 20 请求/小时 |

### 8.2 限流响应头

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1642262400
```

---

## 9. 认证方式 (可选实现)

### 9.1 API 密钥认证

**请求头**:
```
X-API-Key: your-api-key
```

### 9.2 请求签名 (可选)

**请求头**:
```
X-API-Key: your-api-key
X-Timestamp: 1642262400
X-Signature: calculated-signature
```

**签名计算**:
```python
import hmac
import hashlib

message = f"{api_key}{timestamp}{payload}"
signature = hmac.new(
    secret.encode(),
    message.encode(),
    hashlib.sha256
).hexdigest()
```

---

## 10. API 版本策略

### 10.1 版本控制

- URL 版本控制: `/api/v1/`, `/api/v2/`
- 向后兼容原则: 新版本不破坏旧版本
- 废弃通知: 在响应头中添加 `X-API-Deprecation`

### 10.2 版本生命周期

| 状态 | 描述 |
|------|------|
| Alpha | 内部测试 |
| Beta | 公开测试 |
| Stable | 稳定版本 |
| Deprecated | 已废弃，仍可用 |
| Retired | 已停用 |

---

**文档版本**: v1.0
**最后更新**: 2024-02-26
