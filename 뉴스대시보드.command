#!/bin/bash

# 아이돌 뉴스 대시보드 실행기
# 더블클릭하면 브라우저까지 자동으로 열립니다

cd "$(dirname "$0")"

PORT=8502

echo "========================================"
echo "  🎤 아이돌 뉴스 대시보드 시작"
echo "========================================"

# 이미 실행 중이면 종료하고 재시작
EXISTING=$(lsof -ti tcp:$PORT 2>/dev/null)
if [ -n "$EXISTING" ]; then
    echo "⚠️  포트 $PORT 이미 사용 중 → 기존 프로세스 종료 후 재시작합니다..."
    kill $EXISTING 2>/dev/null
    sleep 1
fi

# 가상환경 활성화
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "✓ 가상환경 활성화"
else
    echo "❌ venv 폴더를 찾을 수 없습니다."
    echo "   run_scraper.command를 먼저 실행해서 가상환경을 만들어주세요."
    read -p "엔터를 눌러 종료..."
    exit 1
fi

# streamlit 설치 확인
if ! command -v streamlit &> /dev/null; then
    echo "📦 streamlit 설치 중..."
    pip install -q streamlit
fi

echo ""
echo "🚀 대시보드 서버 시작 중..."
echo "🌐 브라우저가 자동으로 열립니다: http://localhost:$PORT"
echo ""
echo "  종료하려면 이 창을 닫거나 Ctrl+C 를 누르세요."
echo "========================================"

# Streamlit 백그라운드로 실행
streamlit run news_dashboard.py \
    --server.port $PORT \
    --server.headless true \
    --browser.gatherUsageStats false &

STREAMLIT_PID=$!

# 서버 뜰 때까지 대기 (최대 10초)
echo ""
echo "⏳ 서버 준비 중..."
for i in {1..10}; do
    sleep 1
    if curl -s http://localhost:$PORT > /dev/null 2>&1; then
        echo "✅ 서버 준비 완료!"
        break
    fi
    echo "   ... ($i/10)"
done

# 브라우저 오픈
open "http://localhost:$PORT"

echo ""
echo "✅ 브라우저가 열렸습니다: http://localhost:$PORT"
echo ""
echo "  이 터미널 창을 열어두는 동안 대시보드가 유지됩니다."
echo "  창을 닫으면 서버도 종료됩니다."
echo "========================================"

# Streamlit 프로세스가 살아있는 동안 대기
wait $STREAMLIT_PID
