#!/bin/bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "=== Idol News Tracker 起動 ==="

# --- Backend ---
echo ""
echo "[1/3] バックエンド依存インストール中..."
cd "$ROOT/backend"

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install -q -r requirements.txt

if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "  .env ファイルを作成しました。YouTube API キー等を設定してください: backend/.env"
fi

echo "[2/3] バックエンド起動 (port 8000)..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# --- Frontend ---
echo ""
echo "[3/3] フロントエンド依存インストール・起動 (port 3000)..."
cd "$ROOT/frontend"
npm install --silent
npm run dev &
FRONTEND_PID=$!

echo ""
echo "==================================="
echo "起動完了!"
echo "  ダッシュボード: http://localhost:3000"
echo "  API ドキュメント: http://localhost:8000/api/docs"
echo ""
echo "終了するには Ctrl+C を押してください"
echo "==================================="

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
