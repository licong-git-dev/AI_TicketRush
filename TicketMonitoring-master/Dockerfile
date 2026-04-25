FROM python:3.11-slim

WORKDIR /app

# 系统时区设为上海，避免日志时间错位
RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata curl \
    && rm -rf /var/lib/apt/lists/*
ENV TZ=Asia/Shanghai

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 无网调试时跑自检会失败，docker exec 进容器手动跑即可
HEALTHCHECK --interval=5m --timeout=10s --start-period=30s --retries=3 \
    CMD pgrep -f "python.*start.py" > /dev/null || exit 1

CMD ["python", "-u", "start.py"]
