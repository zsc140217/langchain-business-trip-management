#!/bin/bash
# API 启动脚本 - 自动设置 Python 路径

export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
cd src/api
uvicorn main:app --reload --host 0.0.0.0 --port 8000
