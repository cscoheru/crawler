# Railway云端部署指南

## 快速开始

### 方式一：自动化部署脚本（推荐）

```bash
cd /Users/kjonekong/pyStcratch
bash scripts/deploy_to_railway.sh
```

脚本会自动完成：
1. ✅ 安装Railway CLI
2. ✅ 登录Railway
3. ✅ 初始化项目
4. ✅ 配置环境变量
5. ✅ 添加数据卷
6. ✅ 部署应用

### 方式二：手动部署

```bash
# 1. 安装Railway CLI
npm install -g @railway/cli

# 2. 登录
railway login

# 3. 初始化项目
cd /Users/kjonekong/pyStcratch
railway init

# 4. 设置环境变量
railway variables set DATABASE_URL="sqlite:///data/crawler.db"
railway variables set LOG_LEVEL="INFO"

# 5. 添加数据卷
railway volume add data

# 6. 部署
railway up

# 7. 获取项目域名
railway domain
```

## 部署后配置

### 1. 配置定时任务（Cron Job）

在Railway Dashboard中配置：

1. 打开你的项目
2. 进入 "Cron Jobs" 标签
3. 点击 "New Cron Job"
4. 配置如下：
   - **Name**: `daily-crawl`
   - **Command**: `curl -X POST http://localhost:8000/api/run-full-sync`
   - **Schedule**: `0 8 * * *` (UTC时间8:00 = 北京时间16:00)

### 2. 验证部署

```bash
# 获取项目域名
railway domain

# 假设域名是: https://your-project.railway.app

# 测试健康检查
curl https://your-project.railway.app/health

# 查看统计信息
curl https://your-project.railway.app/api/stats

# 手动触发完整同步
curl -X POST https://your-project.railway.app/api/run-full-sync
```

### 3. 查看日志

```bash
# 实时日志
railway logs

# 查看最近100行
railway logs -n 100

# 持续监控
railway logs --follow
```

## API端点

部署后的Web服务提供以下API：

### 健康检查
```
GET /health
```

### 获取统计信息
```
GET /api/stats
```

### 手动触发爬虫
```
POST /api/crawl
Content-Type: application/json

{
  "source": "zhihu",
  "max_pages": 1
}
```

### 导出数据
```
POST /api/export
Content-Type: application/json

{
  "format": "txt",
  "category": "psychology",
  "min_quality": 0.6
}
```

### 同步到Dify
```
POST /api/sync-dify
Content-Type: application/json

{
  "hours": 24,
  "min_quality": 0.6
}
```

### 完整同步流程
```
POST /api/run-full-sync
```

执行完整流程：爬取 → 分类 → 导出 → Dify同步

## 数据持久化

Railway Volume配置：
- **挂载路径**: `/app/data`
- **本地路径**: `data/`
- **用途**: 存储SQLite数据库和导出文件

数据库位置：`/app/data/crawler.db`

导出文件位置：`/app/data/exports/`

## 环境变量

必需的环境变量：

```bash
DATABASE_URL=sqlite:///data/crawler.db
LOG_LEVEL=INFO
```

可选的环境变量：

```bash
# Dify集成
DIFY_API_KEY=your_key
DIFY_BASE_URL=http://your-dify-instance
DIFY_DATASET_ID=your_dataset_id

# AI分类
ZHIPUAI_API_KEY=your_key
DEEPSEEK_API_KEY=your_key
```

## 监控和维护

### 查看执行状态
```bash
# 查看项目状态
railway status

# 查看所有环境变量
railway variables

# 查看数据卷
railway volume
```

### 重新部署
```bash
# 代码更新后重新部署
railway up

# 强制重新构建
railway up --force
```

### 回滚部署
```bash
# 查看部署历史
railway logs

# 回滚到上一个版本
railway rollback
```

## 故障排查

### 1. 部署失败
```bash
# 查看构建日志
railway logs --build

# 常见问题：
# - Python版本不兼容 → 检查Dockerfile中的Python版本
# - 依赖安装失败 → 检查requirements.txt
# - 端口冲突 → 确保使用8000端口
```

### 2. 定时任务不执行
- 检查Cron表达式是否正确
- 检查时区设置（Railway使用UTC时间）
- 查看Cron Job日志

### 3. 数据丢失
- 确认Volume已正确挂载
- 检查DATABASE_URL路径是否正确
- Railway免费额度重启会丢失未持久化的数据

## 成本估算

Railway定价：
- **免费额度**: $5/月
  - 512MB RAM
  - 1GB Volume
  - 无限请求
- **付费计划**: $20/月起
  - 更多资源
  - 更长执行时间

对于爬虫系统（每天运行1次，每次约10-15分钟），免费额度足够。

## 从本地迁移到Railway

### 1. 备份本地数据
```bash
# 备份数据库
cp data/crawler.db data/crawler.db.backup

# 导出数据
python3 main.py export --output ./backup --format txt
```

### 2. 部署到Railway
```bash
bash scripts/deploy_to_railway.sh
```

### 3. 初始数据导入（可选）
如果需要将本地数据导入Railway：

```bash
# 通过Railway CLI上传文件
railway upload data/crawler.db.backup

# 在Railway容器中恢复
railway shell
# 然后在容器中执行:
cp /tmp/crawler.db.backup /app/data/crawler.db
```

### 4. 禁用本地调度器
```bash
# 停止本地launchd任务
launchctl stop com.claudecrawler.scheduler
launchctl unload ~/Library/LaunchAgents/com.claudecrawler.scheduler.plist
```

## 对比：本地 vs Railway

| 特性 | 本地launchd | Railway云端 |
|------|------------|------------|
| 运行位置 | 本地Mac | 云端容器 |
| 依赖本地机器 | ✅ 是 | ❌ 否 |
| 可访问性 | 仅局域网 | 公网访问 |
| 成本 | 免费 | $5/月免费额度 |
| 维护 | 需要维护 | 自动维护 |
| 数据持久化 | 本地磁盘 | Railway Volume |
| 定时任务 | macOS launchd | Railway Cron |
| 监控 | 本地日志 | Railway Dashboard |

## 升级和维护

### 更新代码
```bash
# 1. 修改代码
# 2. 测试本地
python3 scripts/test_all_crawlers.py

# 3. 推送到GitHub（如果链接了）
git push origin main

# 4. 或手动重新部署
railway up
```

### 扩展资源
如果免费额度不够：
1. 进入Railway Dashboard
2. 选择项目
3. 点击 "Settings"
4. 选择付费计划

## 安全建议

1. **环境变量**: 始终通过Railway环境变量管理敏感信息
2. **API密钥**: 不要在代码中硬编码密钥
3. **访问控制**: Railway项目默认是私有的
4. **定期备份**: 定期导出重要数据

## 常见问题

### Q: 如何修改定时任务时间？
A: 在Railway Dashboard > Cron Jobs中编辑Cron表达式

### Q: 数据会在重启后丢失吗？
A: 使用Railway Volume的数据不会丢失，但内存中的临时数据会丢失

### Q: 如何查看爬虫执行历史？
A: 通过`railway logs`查看日志，或调用`/api/stats`获取统计信息

### Q: 可以同时运行多个爬虫吗？
A: 可以，调用`/api/run-full-sync`会依次运行各平台爬虫

### Q: 如何测试API？
A: 使用curl或Postman测试API端点

## 下一步

1. **部署到Railway**: 执行部署脚本
2. **配置定时任务**: 在Dashboard中设置Cron
3. **验证功能**: 测试各个API端点
4. **监控运行**: 观察日志确保正常运行
5. **配置Dify**（可选）: 添加Dify API密钥实现自动同步
