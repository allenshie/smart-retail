#!/bin/bash
# 這個腳本用來建構 Docker 映像
IMAGE_NAME="smart-retail-ai-server"

# 獲取腳本文件的完整路徑
script_path=$(realpath "$0")

# 獲取腳本文件所在目錄
script_dir=$(dirname "$script_path")

# 定義項目根目錄 (script_dir 的父目錄)
project_root=$(dirname "$script_dir")

# 切換到項目根目錄
cd "$project_root"

echo "正在建構 Docker 映像: $IMAGE_NAME"
docker build -t $IMAGE_NAME .
echo "Docker 映像建構完成"
