# 使用官方 Python 运行时作为父镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 将依赖文件复制到工作目录
COPY requirements.txt .

# 安装 playwright 依赖
RUN sed -i s@/deb.debian.org/@/mirrors.aliyun.com/@g /etc/apt/sources.list.d/debian.sources && \
    apt-get update && apt-get install -y --no-install-recommends libnss3 libnspr4 libdbus-1-3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libatspi2.0-0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libxkbcommon0 libpango-1.0-0 libcairo2 libasound2 && rm -rf /var/lib/apt/lists/*

# 安装所需的包
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt && \
    playwright install chromium

# 将项目源代码复制到工作目录
COPY src/ /app/src

# 设置 PYTHONPATH 以便解析模块
ENV PYTHONPATH /app/src

# 暴露应用程序运行的端口（如果需要）
# EXPOSE 8000

# 运行应用的命令
CMD ["python", "-m", "searcrawl.main"]
