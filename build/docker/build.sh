#!/bin/bash

# 設定Image的名稱
PY2_IMAGE_NAME="dictrack_py2"
PY3_IMAGE_NAME="dictrack_py3"

# 設定Python基底映像
PY2_IMAGE_BASE="python:2.7-slim"
PY3_IMAGE_BASE="python:3.11-slim"

# 設定Python套件版本描述檔案
PY2_PIP_FILE="requirements_py2"
PY3_PIP_FILE="requirements_py3"

# 建立Docker Image的函數
build_image() {
    local python_base_image=$1
    local image_name=$2
    local pip_file=$3

    echo "開始建置Docker Image: $image_name 使用基底映像: $python_base_image 搭配套件描述檔案: $pip_file"
    docker build --build-arg PYTHON_BASE_IMAGE=$python_base_image --build-arg PIP_FILE=$pip_file -t $image_name .
    if [ $? -eq 0 ]; then
        echo "Docker Image $image_name 建置成功"
    else
        echo "Docker Image $image_name 建置失敗"
    fi
}

# 主選單
echo "請選擇要建置的Docker Image:"
echo "1) Python 2"
echo "2) Python 3"
echo "3) 兩者都建置"
echo "4) Docker Compose"

read -p "輸入選項 (1/2/3/4): " choice

# 複製主專案
mkdir -p ./tmp
cp -r ../../app/ ./tmp/app/

case $choice in
    1)
        build_image $PY2_IMAGE_BASE $PY2_IMAGE_NAME $PY2_PIP_FILE
        ;;
    2)
        build_image $PY3_IMAGE_BASE $PY3_IMAGE_NAME $PY3_PIP_FILE
        ;;
    3)
        build_image $PY2_IMAGE_BASE $PY2_IMAGE_NAME $PY2_PIP_FILE &
        build_image $PY3_IMAGE_BASE $PY3_IMAGE_NAME $PY3_PIP_FILE &
        wait
        ;;
    4)  
        build_image $PY2_IMAGE_BASE $PY2_IMAGE_NAME $PY2_PIP_FILE &
        build_image $PY3_IMAGE_BASE $PY3_IMAGE_NAME $PY3_PIP_FILE &
        wait
        docker compose -p dictrack up -d --scale locust-worker=4 --scale locust-worker-2=4
        ;;
    *)
        echo "無效的選項"
        exit 1
        ;;
esac

# 清除暫存
rm -r ./tmp/