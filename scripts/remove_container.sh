#!/bin/bash
# 這個腳本用來刪除 Docker 容器

CONTAINER_NAME="smart-retail-ai-server-container"

echo "正在刪除 Docker 容器: $CONTAINER_NAME"
docker rm $CONTAINER_NAME
echo "Docker 容器 $CONTAINER_NAME 已刪除"
