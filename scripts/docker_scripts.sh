#!/bin/bash
# 主腳本，整合多個 Docker 操作腳本

case $1 in
  build)
    ./scripts/build_image.sh
    ;;
  run)
    ./scripts/run_container.sh
    ;;
  stop)
    ./scripts/stop_container.sh
    ;;
  remove)
    ./scripts/remove_container.sh
    ;;
  *)
    echo "使用方法: ./scripts/docker_scripts.sh {build|run|stop|remove}"
    exit 1
    ;;
esac
