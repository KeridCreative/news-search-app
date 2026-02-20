#!/usr/bin/env python3
"""
아이돌 뉴스 가치 평가기 - 검색 결과를 분석하여 뉴스 가치 순위를 매기고 요약 생성
사용법: python3 news_evaluator.py [날짜(YYYY-MM-DD)]
날짜 생략 시 오늘 날짜 사용
"""

import json
import os
import sys
import datetime
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(BASE_DIR, 'news_results')

# === 뉴스 가치 판단 키워드 (뉴스생성가이드.txt 기반) ===

# 최우선 (9-10점) 키워드
TOP_KEYWORDS = [
    '1位', '首位', 'オリコン', '初登場', '新記録', '最高記録', '歴代',
    '国立競技場', '東京ドーム', 'ワールドツアー', '初の', '史上初',
    'デビュー', 'ソロデビュー', 'センター', '卒業', '脱退', '加入',
    '写真集', 'ビルボード', 'Billboard', 'iTunes', 'TikTok',
    '1億', '億再生', '100万', 'ミリオン', '金メダル', '受賞',
    '結婚', '解散', '復帰', '活動再開', '活動休止',
    'ドーム', 'アリーナツアー', '全国ツアー', '追加公演',
    'MV', 'ミュージックビデオ', '公開', '解禁',
]

# 높은 우선순위 (7-8점) 키워드
HIGH_KEYWORDS = [
    'コラボ', 'タイアップ', '新曲', 'ニューシングル', 'アルバム',
    '表紙', 'カバー', 'モデル', '出演', 'ドラマ', '映画', '舞台',
    'ラジオ', '冠番組', 'MC', '司会', '初主演',
    'ツアー', 'コンサート', 'ライブ', 'フェス',
    '紅白', 'レコード大賞', 'FNS', 'Mステ',
]

# 일반 (5-6점) 키워드
NORMAL_KEYWORDS = [
    'ランキング', 'TOP', '順位', '投票', '総選挙',
    'バラエティ', '番組', 'テレビ', 'ラジオ',
    'ファンミーティング', 'イベント', 'トークショー',
    'グラビア', '撮影', 'オフショット',
]

# 제외 (뉴스가치 낮음)
EXCLUDE_KEYWORDS = [
    '広告', 'PR', 'スポンサー', 'タレント名鑑',
    'まとめ', 'ネタバレ', '予想', '噂', 'スキャンダル',
]


def score_article(article):
    """기사의 뉴스 가치를 점수로 평가 (1-10)"""
    title = article.get('title', '')
    score = 5  # 기본 점수

    # 최우선 키워드 체크
    for kw in TOP_KEYWORDS:
        if kw in title:
            score = max(score, 9)
            break

    # 높은 우선순위 키워드 체크
    for kw in HIGH_KEYWORDS:
        if kw in title:
            score = max(score, 7)
            break

    # 일반 키워드 체크
    for kw in NORMAL_KEYWORDS:
        if kw in title:
            score = max(score, 6)
            break

    # 제외 키워드 감점
    for kw in EXCLUDE_KEYWORDS:
        if kw in title:
            score = min(score, 3)
            break

    # 보너스: 숫자가 포함되면 구체적 뉴스일 확률 높음
    if re.search(r'\d+万|1位|初|最', title):
        score = min(score + 1, 10)

    # 보너스: Yahoo 뉴스가 PR Times보다 가치 높음 (일반적으로)
    if article.get('source') == 'Yahoo':
        score = min(score + 0.5, 10)

    return round(score, 1)


def categorize_article(article):
    """기사 유형 분류"""
    title = article.get('title', '')

    if any(kw in title for kw in ['1位', '首位', 'オリコン', '初登場', '売上']):
        return '싱글/앨범 1위'
    if any(kw in title for kw in ['卒業', '脱退', '復帰', '結婚', '解散', '加入']):
        return '멤버 변화'
    if any(kw in title for kw in ['国立', 'ドーム', 'アリーナ', 'ツアー', 'コンサート', 'ライブ']):
        return '콘서트/투어'
    if any(kw in title for kw in ['デビュー', 'ソロ', '初の', '史上初', '新記録']):
        return '역사적 이정표'
    if any(kw in title for kw in ['写真集', '表紙', 'モデル', 'グラビア']):
        return '개인 성취'
    if any(kw in title for kw in ['MV', '新曲', 'シングル', 'アルバム']):
        return '신곡/앨범'
    if any(kw in title for kw in ['ランキング', 'TOP', '順位']):
        return '순위'
    if any(kw in title for kw in ['TikTok', 'SNS', '話題', 'バズ', '億']):
        return 'SNS 화제'
    if any(kw in title for kw in ['ドラマ', '映画', '舞台', '出演']):
        return 'TV/영화'
    return '기타'


def evaluate(date_str=None):
    """검색 결과를 평가하고 순위를 매김"""
    if date_str is None:
        date_str = datetime.date.today().isoformat()

    result_file = os.path.join(RESULTS_DIR, f"{date_str}.json")
    if not os.path.exists(result_file):
        print(f"검색 결과 파일이 없습니다: {result_file}")
        print("먼저 news_scanner.py를 실행하세요.")
        return None

    with open(result_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    articles = data.get('results', [])
    if not articles:
        print("검색된 기사가 없습니다.")
        return None

    # 점수 매기기
    scored = []
    for a in articles:
        a['score'] = score_article(a)
        a['category'] = categorize_article(a)
        scored.append(a)

    # 점수 순 정렬
    scored.sort(key=lambda x: x['score'], reverse=True)

    # 평가 결과 저장
    eval_output = {
        "eval_date": date_str,
        "total_articles": len(scored),
        "ranked_articles": scored,
        "top_10": scored[:10],
    }

    eval_file = os.path.join(RESULTS_DIR, f"{date_str}_evaluated.json")
    with open(eval_file, 'w', encoding='utf-8') as f:
        json.dump(eval_output, f, ensure_ascii=False, indent=2)

    # 콘솔 출력 (사용자용)
    print(f"\n{'='*60}")
    print(f"  아이돌 뉴스 가치 평가 결과 ({date_str})")
    print(f"  총 {len(scored)}건 분석 완료")
    print(f"{'='*60}\n")

    print("🏆 뉴스 가치 TOP 10:")
    print(f"{'-'*60}")
    for i, a in enumerate(scored[:10]):
        emoji = ['🥇','🥈','🥉','4️⃣','5️⃣','6️⃣','7️⃣','8️⃣','9️⃣','🔟'][i]
        print(f"{emoji} [{a['score']}점] [{a['category']}] [{a['keyword']}]")
        print(f"   {a['title'][:70]}")
        print(f"   📰 {a['media']} | 🕐 {a['publish_time']} | 🔗 {a['source']}")
        print()

    print(f"{'='*60}")
    print(f"📁 상세 결과: {eval_file}")
    return eval_output


if __name__ == '__main__':
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    evaluate(date_arg)
