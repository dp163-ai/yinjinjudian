#!/usr/bin/env bash
# 《引金据典》一键演示：灌数据 -> 跑测试 -> 启动后端
set -e
cd "$(dirname "$0")/.."

echo "==> 1/3 灌入演示数据"
python scripts/seed.py

echo "==> 2/3 运行测试"
cd backend
python -m pytest -q

echo "==> 3/3 启动后端 (http://127.0.0.1:8000)"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
