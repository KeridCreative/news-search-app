#!/bin/bash

# 스크립트가 있는 디렉토리로 이동
cd "$(dirname "$0")"

echo "현재 위치: $(pwd)"

# Python3 경로 찾기
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ Python이 설치되어 있지 않습니다!"
    echo "Python을 설치해주세요: https://www.python.org/downloads/"
    read -p "엔터를 눌러 종료..."
    exit 1
fi

echo "✓ Python 찾음: $PYTHON_CMD"

# 가상환경이 없으면 생성
if [ ! -d "venv" ]; then
    echo "📦 가상환경을 생성합니다..."
    $PYTHON_CMD -m venv venv
    
    if [ $? -ne 0 ]; then
        echo "❌ 가상환경 생성 실패!"
        read -p "엔터를 눌러 종료..."
        exit 1
    fi
fi

# 가상환경 활성화
echo "🔧 가상환경을 활성화합니다..."
source venv/bin/activate

# requirements.txt가 있으면 패키지 설치
if [ -f "requirements.txt" ]; then
    echo "📥 필요한 패키지를 확인합니다..."
    pip install -q -r requirements.txt
else
    echo "📥 기본 패키지를 설치합니다..."
    pip install -q requests flask beautifulsoup4
    pip freeze > requirements.txt
fi

# Flask 앱 실행
echo ""
echo "🚀 Flask 웹 서버를 시작합니다..."
echo "🌐 브라우저에서 자동으로 열립니다"
echo ""
python app.py

# 종료 대기
read -p "엔터를 눌러 종료..."
