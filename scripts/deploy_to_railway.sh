#!/bin/bash
# Railway部署脚本 - 自动化部署爬虫系统到Railway平台

set -e  # 遇到错误立即退出

PROJECT_DIR="/Users/kjonekong/pyStcratch"
cd "$PROJECT_DIR" || exit 1

# 添加npm全局bin路径到PATH
NPM_BIN_PREFIX="$(npm config get prefix)/bin"
export PATH="$NPM_BIN_PREFIX:$PATH"

echo "========================================"
echo "  爬虫系统 Railway 部署工具"
echo "========================================"
echo ""

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. 检查Node.js
echo -e "${YELLOW}[1/8]${NC} 检查Node.js环境..."
if ! command -v node &> /dev/null; then
    echo -e "${RED}✗ Node.js未安装${NC}"
    echo "请先安装Node.js: https://nodejs.org/"
    exit 1
fi
NODE_VERSION=$(node --version)
echo -e "${GREEN}✓${NC} Node.js已安装: $NODE_VERSION"

# 2. 检查Railway CLI
echo ""
echo -e "${YELLOW}[2/8]${NC} 检查Railway CLI..."
if ! command -v railway &> /dev/null; then
    echo "Railway CLI未安装，正在安装..."
    npm install -g @railway/cli
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} Railway CLI安装成功"
    else
        echo -e "${RED}✗${NC} Railway CLI安装失败"
        exit 1
    fi
else
    echo -e "${GREEN}✓${NC} Railway CLI已安装"
fi

# 3. 登录Railway
echo ""
echo -e "${YELLOW}[3/8]${NC} 登录Railway..."
railway login
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Railway登录成功"
else
    echo -e "${RED}✗${NC} Railway登录失败"
    exit 1
fi

# 4. 初始化Railway项目
echo ""
echo -e "${YELLOW}[4/8]${NC} 初始化Railway项目..."
if [ ! -f ".railway/project.json" ]; then
    echo "创建新的Railway项目..."
    railway init
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} Railway项目初始化成功"
    else
        echo -e "${RED}✗${NC} Railway项目初始化失败"
        exit 1
    fi
else
    echo -e "${GREEN}✓${NC} Railway项目已存在"
fi

# 5. 链接GitHub仓库（可选）
echo ""
echo -e "${YELLOW}[5/8]${NC} 链接GitHub仓库..."
read -p "是否链接到GitHub仓库？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    railway link
    echo -e "${GREEN}✓${NC} 已链接到GitHub"
else
    echo "跳过GitHub链接，将直接从当前目录部署"
fi

# 6. 配置环境变量
echo ""
echo -e "${YELLOW}[6/8]${NC} 配置环境变量..."
echo "设置环境变量:"

# 数据库URL
echo "  - DATABASE_URL"
railway variables set DATABASE_URL="sqlite:///data/crawler.db"

# 日志级别
echo "  - LOG_LEVEL"
railway variables set LOG_LEVEL="INFO"

# 可选：Dify配置
echo ""
read -p "是否配置Dify知识库集成？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "DIFY_API_KEY: " DIFY_KEY
    read -p "DIFY_BASE_URL (默认: http://localhost:3001): " DIFY_URL
    DIFY_URL=${DIFY_URL:-http://localhost:3001}
    read -p "DIFY_DATASET_ID: " DIFY_DATASET

    railway variables set DIFY_API_KEY="$DIFY_KEY"
    railway variables set DIFY_BASE_URL="$DIFY_URL"
    railway variables set DIFY_DATASET_ID="$DIFY_DATASET"
    echo -e "${GREEN}✓${NC} Dify配置已添加"
else
    echo "跳过Dify配置"
fi

echo -e "${GREEN}✓${NC} 环境变量配置完成"

# 7. 添加持久化卷
echo ""
echo -e "${YELLOW}[7/8]${NC} 配置数据持久化..."
echo "添加Volume用于存储SQLite数据库和导出文件..."
railway volume add data
echo -e "${GREEN}✓${NC} Volume配置完成 (挂载路径: /app/data)"

# 8. 部署到Railway
echo ""
echo -e "${YELLOW}[8/8]${NC} 部署到Railway..."
echo "开始部署，这可能需要几分钟..."
railway up

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================"
    echo -e "${GREEN}✓ 部署成功！${NC}"
    echo "========================================"
    echo ""
    echo "后续步骤："
    echo ""
    echo "1. 查看项目信息："
    echo "   railway domain"
    echo ""
    echo "2. 查看实时日志："
    echo "   railway logs"
    echo ""
    echo "3. 配置定时任务（Cron Job）："
    echo "   访问 Railway Dashboard > 你的项目 > Cron Jobs"
    echo "   添加以下Cron表达式："
    echo "   0 8 * * * python /app/scripts/auto_crawl_and_sync.sh"
    echo "   (UTC时间 8:00 = 北京时间 16:00)"
    echo ""
    echo "4. 测试Web服务："
    echo "   curl https://your-project.railway.app/health"
    echo "   curl https://your-project.railway.app/api/stats"
    echo ""
    echo "5. 手动触发完整同步："
    echo "   curl -X POST https://your-project.railway.app/api/run-full-sync"
    echo ""
else
    echo ""
    echo -e "${RED}✗ 部署失败${NC}"
    echo "请检查日志: railway logs"
    exit 1
fi
