# 使用官方 Python 运行时作为父镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 将依赖文件复制到工作目录
COPY requirements.txt .

# 安装所需的包
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# 将项目源代码复制到工作目录
COPY src/ /app/src

# 设置 PYTHONPATH 以便解析模块
ENV PYTHONPATH /app/src

# 暴露应用程序运行的端口（如果需要）
# EXPOSE 8000

# 运行应用的命令
CMD ["python", "-m", "searcrawl.main"]
