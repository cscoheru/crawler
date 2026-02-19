FROM python:3.14-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 创建数据目录
RUN mkdir -p data logs data/exports

# 暴露端口
EXPOSE 8000

# 默认命令 - 启动Flask服务
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--timeout", "600", "web_server:app"]
