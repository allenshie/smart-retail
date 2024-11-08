#!/bin/bash
# 這個腳本用來停止 Docker 容器

CONTAINER_NAME="smart-retail-ai-server-container"

echo "正在停止 Docker 容器: $CONTAINER_NAME"
docker stop $CONTAINER_NAME
echo "Docker 容器 $CONTAINER_NAME 已停止"
