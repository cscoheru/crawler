#!/bin/bash
set -e

echo "🚀 Starting crawler web service..."

# 创建必要的目录
mkdir -p /app/data
mkdir -p /app/data/exports
mkdir -p /app/logs

# 初始化数据库
echo "📊 Initializing database..."
python3 -c "
import sys
import os
sys.path.insert(0, '/app')

# 设置环境变量
os.environ['DATA_DIR'] = '/app/data'

from storage.database import DatabaseManager
db = DatabaseManager()
print('✅ Database initialized successfully')
print(f'📁 Database URL: {db.database_url}')
"

# 启动应用
echo "🌐 Starting Flask application..."
exec gunicorn --bind 0.0.0.0:8000 --workers 1 --timeout 600 --access-logfile - --error-logfile - --log-level info --capture-output web_server:app
