#!/bin/bash
# 아이돌 뉴스 일일 자동 스캔 + 평가
# LaunchAgent에서 매일 15:00에 실행

SCRIPT_DIR="/Users/user0708/Library/CloudStorage/OneDrive-uos.ac.kr/desktopCli/yahoo_search"
LOG_FILE="$SCRIPT_DIR/news_results/scan.log"

echo "=== $(date '+%Y-%m-%d %H:%M:%S') 스캔 시작 ===" >> "$LOG_FILE"

cd "$SCRIPT_DIR"
/usr/bin/python3 news_scanner.py >> "$LOG_FILE" 2>&1
/usr/bin/python3 news_evaluator.py >> "$LOG_FILE" 2>&1

echo "=== $(date '+%Y-%m-%d %H:%M:%S') 스캔 완료 ===" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# macOS 알림 (선택)
osascript -e 'display notification "뉴스 스캔 완료! Cowork에서 확인하세요." with title "아이돌 뉴스"' 2>/dev/null
