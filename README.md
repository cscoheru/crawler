# 知乎/头条/微信公众号内容采集系统

基于 Python 的多平台内容采集系统，支持从知乎、今日头条、微信公众号采集专业领域文章，并进行**三级智能分类**。

## 功能特点

- **多平台采集**: 支持知乎、今日头条、微信公众号
- **三级分类体系**: 支持一级、二级、三级细分分类
- **智能分类**: 基于关键词规则和 AI 模型的混合分类系统
- **数据清洗**: 自动清洗 HTML、去重、质量评分
- **定时任务**: 可配置的定时采集和分类任务
- **多种导出**: 支持 TXT、JSON、CSV 格式导出，可按子类目导出
- **反爬虫策略**: 请求频率控制、User-Agent 轮换、代理 IP 池

## 三级分类体系

系统采用三级分类层次结构，支持精细化的知识组织：

### 一级分类 (3大类)

1. **心理咨询** (psychology)
2. **企业管理** (management)
3. **财务会计税务** (finance)

### 二级分类

#### 心理咨询
- 临床心理
- 咨询技术
- 发展心理
- 婚恋家庭
- 职场心理
- 情绪管理

#### 企业管理
- 战略管理
- 人力资源
- 企业文化
- 运营管理
- 市场营销
- 创新管理
- 领导力发展

#### 财务会计税务
- 财务会计
- 管理会计
- 税务
- 审计
- 财务管理
- 财务报告

### 三级分类 (示例)

#### 人力资源二级下的细分
- 人力资源规划
- 组织架构
- 职位体系
- 薪酬绩效
- 人才管理
- 招聘选拔
- 培训发展
- 员工关系

#### 临床心理二级下的细分
- 抑郁障碍
- 焦虑障碍
- 强迫障碍
- 恐惧症
- 双相障碍
- 睡眠障碍
- 进食障碍
- 创伤应激

#### 税务二级下的细分
- 增值税
- 企业所得税
- 个人所得税
- 税务筹划
- 税务申报
- 其他税种

> 完整的分类体系请查看 `config/category_taxonomy.py`

## 系统架构

```
pyStcratch/
├── config/
│   ├── settings.py              # 配置文件
│   ├── category_taxonomy.py     # 三级分类体系定义 ★新增★
│   └── keywords.py              # 关键词规则
├── crawler/                     # 爬虫模块
│   ├── base.py                  # 爬虫基类
│   ├── zhihu.py                 # 知乎爬虫
│   ├── toutiao.py               # 头条爬虫
│   └── wechat.py                # 微信公众号爬虫
├── classifier/
│   ├── multi_level_classifier.py # 三级分类器 ★新增★
│   ├── rule_based.py            # 规则分类
│   └── ai_classifier.py         # AI分类
├── storage/                     # 数据存储
│   ├── database.py              # 数据库操作
│   └── models.py                # 数据模型 (支持三级分类)
├── utils/                       # 工具函数
├── scheduler/                   # 定时任务
├── scripts/                     # 辅助脚本
│   └── export_by_subcategory.py # 按子类目导出 ★新增★
└── main.py                      # 主入口
```

## 安装步骤

### 1. 环境要求

- Python 3.10+
- PostgreSQL 12+

### 2. 安装依赖

```bash
cd pyStcratch
pip install -r requirements.txt
```

### 3. 安装 Playwright (用于浏览器自动化)

```bash
playwright install chromium
```

### 4. 配置数据库

```bash
# 创建数据库
createdb crawler_db

# 或使用 Docker
docker run -d --name postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=crawler_db \
  -p 5432:5432 postgres:14
```

### 5. 配置环境变量

创建 `.env` 文件:

```bash
# 数据库
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/crawler_db

# AI API (可选，用于高精度分类)
ZHIPUAI_API_KEY=your_zhipuai_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key

# 代理 (可选)
PROXY_ENABLED=False
```

## 使用方法

### 命令行工具

```bash
# 采集知乎文章
python main.py crawl --source zhihu --max-pages 2

# 采集所有平台
python main.py crawl --source all --max-pages 1

# 使用指定关键词采集
python main.py crawl --source zhihu --keywords "心理咨询" "企业管理"

# 分类未分类文章 (使用三级分类器)
python main.py classify

# 导出数据为 TXT (用于 Dify 知识库)
python main.py export --output ./output --format txt

# 查看统计信息
python main.py stats

# 启动定时任务调度器
python main.py scheduler
```

### 按子类目导出

使用辅助脚本按三级分类导出文章，方便创建多个 Dify 知识库：

```bash
# 层级导出 (保留分类目录结构)
python scripts/export_by_subcategory.py \
  --output ./dify_knowledge_base \
  --min-quality 0.6

# 扁平导出 (每个子类目一个目录)
python scripts/export_by_subcategory.py \
  --output ./dify_knowledge_base \
  --flat \
  --min-quality 0.6

# 只导出某个一级分类
python scripts/export_by_subcategory.py \
  --output ./dify_knowledge_base \
  --category management \
  --min-quality 0.6
```

导出目录结构示例：

```
dify_knowledge_base/
├── psychology_心理咨询/
│   ├── clinical_临床心理/
│   │   ├── depression_抑郁障碍/
│   │   ├── anxiety_焦虑障碍/
│   │   └── ...
│   ├── therapy_咨询技术/
│   └── ...
├── management_企业管理/
│   ├── hr_人力资源/
│   │   ├── compensation_benefits_薪酬绩效/
│   │   ├── talent_management_人才管理/
│   │   └── ...
│   ├── strategy_战略管理/
│   └── ...
└── finance_财务会计税务/
    ├── tax_税务/
    │   ├── vat_增值税/
    │   ├── corporate_tax_企业所得税/
    │   └── ...
    └── ...
```

### Python API

```python
from main import run_crawler, export_data
from classifier.multi_level_classifier import MultiLevelClassifier

# 采集数据
result = run_crawler(source="zhihu", max_pages=2)

# 使用三级分类器分类
classifier = MultiLevelClassifier()
result = classifier.classify("文章标题", "文章内容...")
print(result)
# {
#     "category": "psychology",
#     "subcategory": "clinical",
#     "sub_subcategory": "depression",
#     "category_path": ["心理咨询", "临床心理", "抑郁障碍"],
#     "overall_confidence": 0.85
# }

# 导出为 TXT (用于 Dify)
export_data(
    output_dir="./dify_knowledge_base",
    format="txt",
    category="psychology"
)
```

## 导出格式用于 Dify

系统支持将采集的文章导出为 TXT 格式，**包含三级分类信息**：

```
标题: [文章标题]
来源: zhihu
作者: [作者名]
发布时间: [时间]
URL: [文章链接]
一级分类: 心理咨询
二级分类: 临床心理
三级分类: 抑郁障碍
分类路径: 心理咨询 > 临床心理 > 抑郁障碍
质量评分: 0.85
分类置信度: 0.92

================================================================================

[文章正文内容...]

================================================================================
```

### 推荐 Dify 知识库架构

#### 方案1: 按一级分类创建知识库

- 心理咨询知识库 (导入所有 psychology 分类文章)
- 企业管理知识库 (导入所有 management 分类文章)
- 财务会计知识库 (导入所有 finance 分类文章)

#### 方案2: 按二级分类创建知识库

例如企业管理下：
- 人力资源知识库
- 战略管理知识库
- 市场营销知识库
- 运营管理知识库
- ...

#### 方案3: 按三级分类创建知识库 (最精细)

例如人力资源下：
- 薪酬绩效知识库
- 人才管理知识库
- 组织架构知识库
- ...

### Dify 配置建议

- **数据源**: 文件上传
- **文件格式**: TXT
- **分块方式**: 自动分块
- **分块大小**: 800 tokens
- **重叠大小**: 50 tokens
- **索引方式**: 高质量 (适合专业内容)

## 定时任务配置

默认定时任务 (可在 `config/settings.py` 中修改):

- 06:00 - 知乎采集
- 08:00 - 头条采集
- 10:00 - 微信公众号采集
- 14:00 - AI 分类批量处理
- 20:00 - 数据质量检查和报告

启动调度器:

```bash
python main.py scheduler
```

## 反爬虫策略

- 请求间隔: 3-10 秒随机延迟
- User-Agent 轮换: 模拟真实浏览器
- 代理 IP 池: 支持付费/免费代理
- 请求频率限制: 按域名控制并发

## 数据质量

- **最小长度**: 200 字符
- **最大长度**: 50,000 字符
- **质量评分**: 基于长度、结构、内容丰富度
- **垃圾过滤**: 自动过滤广告、垃圾内容

## 注意事项

1. **法律合规**: 仅采集公开内容，遵守网站服务条款
2. **频率控制**: 初始每天少量采集，逐步增加
3. **数据验证**: 采集内容建议人工抽检
4. **API 限制**: AI 分类 API 可能有调用限制

## 自定义分类体系

如需修改分类体系，编辑 `config/category_taxonomy.py`:

```python
CATEGORY_TAXONOMY = {
    "your_category": {
        "name": "您的分类名称",
        "subcategories": {
            "sub_key": {
                "name": "二级分类名",
                "sub_subcategories": {
                    "leaf_key": {
                        "name": "三级分类名",
                        "keywords": ["关键词1", "关键词2", ...]
                    }
                }
            }
        }
    }
}
```

## 后续扩展

- [ ] 添加更多数据源 (小红书、B站等)
- [ ] 内容去重和相似度分析
- [ ] 构建知识图谱
- [ ] 数据可视化面板
- [ ] 分布式采集

## 许可证

MIT License
