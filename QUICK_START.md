# 快速参考 - 爬虫系统命令

## 基础命令

```bash
# 进入项目目录
cd /Users/kjonekong/pyStcratch

# 测试系统
python3 scripts/test_all_crawlers.py

# 查看数据库统计
python3 main.py stats

# 手动采集所有平台（1页测试）
python3 main.py crawl --source all --max-pages 1

# 导出数据到TXT
python3 main.py export --output ./output --format txt
```

## 自动化设置

```bash
# 安装自动定时任务（每天16:00运行）
bash scripts/setup_scheduler.sh

# 手动运行完整流程（采集+分类+导出+Dify同步）
bash scripts/auto_crawl_and_sync.sh
```

## 配置文件

- `.env` - 环境配置（数据库、API密钥等）
- `config/settings.py` - 爬虫配置、定时任务时间表

## 日志位置

- `logs/crawler.log` - 主日志
- `logs/scheduler.log` - 定时任务日志
- `logs/auto_crawl.log` - 自动运行日志

## 数据位置

- `data/crawler.db` - SQLite数据库
- `data/dify_export/` - Dify导出目录
- `data/processed/` - 处理后数据

## 支持的平台

| 平台 | 命令参数 |
|------|---------|
| 知乎 | `--source zhihu` |
| 头条 | `--source toutiao` |
| 微信 | `--source wechat` |
| B站 | `--source bilibili` |
| 得到 | `--source dedao` |
| 喜马拉雅 | `--source ximalaya` |
| 全部 | `--source all` |

## 定时任务管理

```bash
# 查看状态
launchctl list | grep claudecrawler

# 停止任务
launchctl stop com.claudecrawler.scheduler

# 启动任务
launchctl start com.claudecrawler.scheduler

# 卸载任务
launchctl unload ~/Library/LaunchAgents/com.claudecrawler.scheduler.plist
```

## 故障排除

**爬虫被拦截**：增加请求延迟（settings.py中的delay_range）
**Dify同步失败**：检查.env中的API配置
**数据库错误**：检查DATABASE_URL是否正确
