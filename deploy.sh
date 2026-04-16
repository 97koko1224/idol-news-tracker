#!/bin/bash
# フロントエンドを本番デプロイして固定URLに向ける

set -e
FIXED_URL="kawaii-lab-news.vercel.app"

cd "$(dirname "$0")/frontend"

echo "=== Vercel デプロイ中... ==="
DEPLOY_URL=$(vercel --prod --yes 2>&1 | grep "Production:" | tail -1 | awk '{print $2}')

echo "=== 固定URLに割り当て中: https://$FIXED_URL ==="
vercel alias set "$DEPLOY_URL" "$FIXED_URL"

echo ""
echo "デプロイ完了: https://$FIXED_URL"
