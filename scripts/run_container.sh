#!/bin/bash
# 這個腳本用來啟動 Docker 容器

CONTAINER_NAME="smart-retail-ai-server-container"
IMAGE_NAME="smart-retail-ai-server"
PORT=65333
HOST_CONFIG_PATH="$(dirname "$0")/../src/config"  # 指定宿主機上的 config 目錄
HOST_PATH="$(dirname "$0")/../src"  # 指定宿主機上的 config 目錄

echo "正在啟動 Docker 容器: $CONTAINER_NAME"
docker run --name $CONTAINER_NAME --gpus all -p $PORT:8000 -v "$HOST_PATH":/app/src $IMAGE_NAME 
echo "Docker 容器 $CONTAINER_NAME 正在運行於端口 $PORT"
