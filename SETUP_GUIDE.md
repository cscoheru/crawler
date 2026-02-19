# 多平台内容采集系统 - 完整部署指南

## 系统概述

本系统支持从6个平台自动采集专业内容并同步到Dify知识库：

**文本平台**：知乎、头条、微信公众号
**视频平台**：B站（提取字幕）
**知识平台**：得到、喜马拉雅（提取课程文稿）

## 快速开始

### 1. 安装依赖

```bash
cd /Users/kjonekong/pyStcratch
pip3 install -r requirements.txt
```

### 2. 配置环境变量

编辑 `.env` 文件：

```bash
# 数据库配置（默认使用SQLite）
DATABASE_URL=sqlite:///data/crawler.db

# Dify知识库配置（可选 - 用于自动同步）
DIFY_API_KEY=your_dify_api_key
DIFY_BASE_URL=http://localhost:3001
DIFY_DATASET_ID=your_dataset_id

# AI分类配置（可选 - 用于AI增强分类）
ZHIPUAI_API_KEY=
DEEPSEEK_API_KEY=
```

### 3. 初始化数据库

```bash
python3 main.py stats
```

### 4. 测试系统

```bash
# 运行完整测试
python3 scripts/test_all_crawlers.py

# 测试单个爬虫
python3 main.py crawl --source zhihu --keywords "企业管理" --max-pages 1
```

## 使用说明

### 手动采集

```bash
# 采集单个平台
python3 main.py crawl --source zhihu --max-pages 2

# 采集所有平台
python3 main.py crawl --source all --max-pages 2

# 指定关键词采集
python3 main.py crawl --source wechat --keywords "心理咨询" "企业管理" --max-pages 3
```

### 数据导出

```bash
# 导出到TXT（适用于Dify知识库）
python3 main.py export --output ./output --format txt

# 按分类导出
python3 main.py export --output ./output --format txt --category psychology

# 导出JSON
python3 main.py export --output ./output --format json
```

### 查看统计

```bash
python3 main.py stats
```

## 自动化部署

### 方案1: 使用macOS launchd（推荐）

```bash
# 安装定时任务（每天16:00自动运行）
bash scripts/setup_scheduler.sh

# 查看任务状态
launchctl list | grep claudecrawler

# 停止任务
launchctl stop com.claudecrawler.scheduler

# 卸载任务
launchctl unload ~/Library/LaunchAgents/com.claudecrawler.scheduler.plist
```

### 方案2: 手动运行完整脚本

```bash
# 运行完整采集和同步流程
bash scripts/auto_crawl_and_sync.sh
```

### 方案3: 使用n8n工作流

由于您提到使用n8n，以下是n8n工作流配置建议：

1. **Cron触发器**：每天16:00触发
2. **执行命令**：运行 `bash /Users/kjonekong/pyStcratch/scripts/auto_crawl_and_sync.sh`
3. **等待完成**
4. **HTTP Request**：调用Dify API更新知识库（如需额外配置）

## Dify知识库集成

### 方式1: 自动同步（推荐）

1. 在 `.env` 中配置Dify API密钥
2. 运行采集脚本会自动同步

### 方式2: 手动导出后上传

```bash
# 导出数据
python3 main.py export --output ./dify_kb --format txt

# 在Dify中导入该目录
```

### 方式3: API直接同步

```python
from utils.dify_integration import DifyBatchSyncer
from storage.database import DatabaseManager

db = DatabaseManager()
syncer = DifyBatchSyncer()
syncer.export_and_sync(db, output_dir='./dify_kb', min_quality=0.6)
```

## 定时任务时间表

系统默认配置以下任务（在 `config/settings.py` 中配置）：

| 时间 | 任务 |
|------|------|
| 06:00 | 知乎采集 |
| 08:00 | 头条采集 |
| 10:00 | 微信公众号采集 |
| 12:00 | B站采集（字幕内容） |
| 13:00 | 得到平台采集 |
| 13:30 | 喜马拉雅采集 |
| 14:00 | AI分类处理 |
| 15:00 | Dify知识库同步 |
| 20:00 | 数据质量检查 |

## 数据分类

系统自动将内容分类为三大领域（支持三级细分）：

1. **心理咨询** (psychology)
   - 临床心理学、咨询技术等

2. **企业管理** (management)
   - 人力资源管理、战略管理等

3. **财务会计税务** (finance)
   - 会计核算、税务筹划等

## 文件结构

```
pyStcratch/
├── main.py                  # 主入口
├── .env                     # 配置文件
├── requirements.txt         # 依赖包
├── crawler/                 # 爬虫模块
│   ├── base.py             # 基类
│   ├── zhihu.py            # 知乎
│   ├── toutiao.py          # 头条
│   ├── wechat.py           # 微信
│   ├── bilibili.py         # B站
│   ├── dedao.py            # 得到
│   └── ximalaya.py         # 喜马拉雅
├── classifier/             # 分类器
├── storage/                # 数据存储
├── scheduler/              # 定时任务
├── utils/                  # 工具类
│   └── dify_integration.py # Dify集成
├── scripts/                # 脚本
│   ├── test_all_crawlers.py
│   ├── auto_crawl_and_sync.sh
│   └── setup_scheduler.sh
├── data/                   # 数据目录
├── logs/                   # 日志目录
└── com.claudecrawler.scheduler.plist  # launchd配置
```

## 日志查看

```bash
# 查看最新日志
tail -f logs/crawler.log

# 查看定时任务日志
tail -f logs/scheduler.log

# 查看定时任务错误日志
tail -f logs/scheduler_error.log
```

## 常见问题

### 1. 爬虫被反爬虫拦截

- 这是正常现象，网站会检测频繁访问
- 可以增加请求延迟（修改 `config/settings.py` 中的 `delay_range`）
- 可以配置代理IP（设置 `PROXY_ENABLED=True`）

### 2. Dify同步失败

- 检查 `.env` 中的 `DIFY_API_KEY` 和 `DIFY_BASE_URL`
- 确保Dify服务正在运行
- 检查 `DIFY_DATASET_ID` 是否正确

### 3. 数据库错误

- 默认使用SQLite，无需额外配置
- 如需PostgreSQL，修改 `.env` 中的 `DATABASE_URL`

## 维护建议

1. **定期检查日志**：`tail -f logs/crawler.log`
2. **数据质量检查**：运行 `python3 main.py stats`
3. **导出备份**：定期导出数据作为备份
4. **更新爬虫**：网站结构变化时需更新爬虫逻辑

## 扩展功能

系统支持扩展：

1. **添加新平台**：在 `crawler/` 目录创建新的爬虫类
2. **自定义分类**：修改 `config/category_taxonomy.py`
3. **自定义关键词**：修改 `config/keywords.py`
4. **添加新的导出格式**：在 `storage/database.py` 中添加方法

## 技术支持

- 日志位置：`/Users/kjonekong/pyStcratch/logs/`
- 数据位置：`/Users/kjonekong/pyStcratch/data/`
- 配置文件：`/Users/kjonekong/pyStcratch/.env`

## 测试验证

```bash
# 运行完整测试套件
python3 scripts/test_all_crawlers.py

# 预期输出：
# ✓ PASS: Database
# ✓ PASS: Imports
# ✓ PASS: Initialization
# ✓ PASS: Basic Search
# ✓ PASS: Classifier
# ✓ PASS: Export
# Total: 6/6 tests passed
```
