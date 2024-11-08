# 使用官方 FastAPI 與 Python 3.12 映像作為基礎映像
FROM python:3.12

# 設定工作目錄
WORKDIR /app

# 將當前目錄的內容複製到 Docker 容器的 /app 目錄
COPY . /app

# 安裝依賴包
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 安裝依賴包
RUN apt-get update && apt-get install -y libgl1 nano

# 暴露應用程序的運行端口
EXPOSE 8000

# 啟動 FastAPI 應用程序
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]