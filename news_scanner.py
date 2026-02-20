#!/usr/bin/env python3
"""
아이돌 뉴스 스캐너 - 야후뉴스 + PR Times 자동 검색
Streamlit 의존성 없이 독립 실행 가능
사용법: python3 news_scanner.py
"""

import requests
from bs4 import BeautifulSoup
import datetime
import re
import json
import os
import urllib.parse
import sys
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KEYWORDS_FILE = os.path.join(BASE_DIR, 'keywords.json')
RESULTS_DIR = os.path.join(BASE_DIR, 'news_results')

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
}


def load_keywords():
    try:
        with open(KEYWORDS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f).get("search_keyword", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def fmt_jp(d):
    return f"{d.month}/{d.day}"


def scrape_yahoo(kw, dates):
    url = f"https://news.yahoo.co.jp/search?p={urllib.parse.quote(kw)}&rkf=2&ei=UTF-8"
    arts = []
    dstrs = [fmt_jp(d) for d in dates]
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        for li in soup.find_all('li', class_='sc-1u4589e-0'):
            t = li.find('time')
            if not t:
                continue
            dtxt = t.text
            m = re.search(r'(\d{1,2}/\d{1,2})', dtxt)
            if m and m.group(1) in dstrs:
                title_el = li.find('div', class_='sc-3ls169-0')
                link_el = li.find('a')
                media_el = li.find('span')
                if title_el and link_el:
                    arts.append({
                        'title': title_el.text.strip(),
                        'link': link_el.get('href', '#'),
                        'media': media_el.text.strip() if media_el else 'N/A',
                        'publish_time': dtxt.strip(),
                        'source': 'Yahoo',
                        'keyword': kw
                    })
    except Exception as e:
        print(f"  [Yahoo 오류] {kw}: {e}", file=sys.stderr)
    arts.sort(key=lambda x: x['publish_time'], reverse=True)
    return arts


def scrape_prtimes(kw, dates):
    url = f"https://prtimes.jp/main/action.php?run=html&page=searchkey&search_word={urllib.parse.quote(kw)}"
    arts = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        sc = soup.find('script', id='__NEXT_DATA__')
        if not sc:
            return arts
        data = json.loads(sc.string)
        releases = []
        for q in data.get('props', {}).get('pageProps', {}).get('dehydratedState', {}).get('queries', []):
            for pg in q.get('state', {}).get('data', {}).get('pages', []):
                releases.extend(pg.get('releaseList', []))
        today = datetime.date.today()
        for rel in releases:
            ra = rel.get('releasedAt', '')
            ok = False
            if any(p in ra for p in ['分前', '時間前', '秒前']):
                ok = today in dates
            if '昨日' in ra:
                ok = ok or (today - datetime.timedelta(days=1)) in dates
            am = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', ra)
            if am:
                try:
                    ad = datetime.date(int(am.group(1)), int(am.group(2)), int(am.group(3)))
                    ok = ok or ad in dates
                except:
                    pass
            dm = re.search(r'(\d+)日前', ra)
            if dm:
                ok = ok or (today - datetime.timedelta(days=int(dm.group(1)))) in dates
            if ok:
                ru = rel.get('releaseUrl', '')
                arts.append({
                    'title': rel.get('title', ''),
                    'link': f"https://prtimes.jp{ru}" if ru.startswith('/') else ru,
                    'media': rel.get('companyName', 'N/A'),
                    'publish_time': ra,
                    'source': 'PR Times',
                    'keyword': kw
                })
    except Exception as e:
        print(f"  [PR Times 오류] {kw}: {e}", file=sys.stderr)
    return arts


def search_all(kw, dates):
    """야후뉴스 + PR Times 동시 검색"""
    arts = []
    arts.extend(scrape_yahoo(kw, dates))
    arts.extend(scrape_prtimes(kw, dates))
    return arts


def deduplicate(articles):
    """제목 기반 중복 제거 (앞에 나온 것 우선)"""
    seen = set()
    unique = []
    for a in articles:
        title_key = re.sub(r'\s+', '', a['title'])[:50]
        if title_key not in seen:
            seen.add(title_key)
            unique.append(a)
    return unique


def run_scan():
    """메인 스캔 실행"""
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    dates = [today, yesterday]

    keywords = load_keywords()
    if not keywords:
        print("키워드가 없습니다. keywords.json을 확인하세요.")
        return None

    print(f"=== 아이돌 뉴스 스캔 시작 ===")
    print(f"검색 날짜: {today.isoformat()} ~ {yesterday.isoformat()}")
    print(f"키워드 수: {len(keywords)}개")
    print(f"{'='*40}")

    all_articles = []
    results_by_keyword = {}

    for i, kw in enumerate(keywords):
        print(f"[{i+1}/{len(keywords)}] '{kw}' 검색 중...")
        arts = search_all(kw, dates)
        if arts:
            results_by_keyword[kw] = arts
            all_articles.extend(arts)
            print(f"  → {len(arts)}건 발견")
        else:
            print(f"  → 결과 없음")
        time.sleep(0.5)  # 서버 부하 방지

    # 중복 제거
    unique_articles = deduplicate(all_articles)

    print(f"{'='*40}")
    print(f"총 {len(all_articles)}건 → 중복 제거 후 {len(unique_articles)}건")

    # 결과 저장
    os.makedirs(RESULTS_DIR, exist_ok=True)
    output = {
        "search_date": today.isoformat(),
        "date_range": [today.isoformat(), yesterday.isoformat()],
        "total_articles": len(unique_articles),
        "total_before_dedup": len(all_articles),
        "keywords_with_results": list(results_by_keyword.keys()),
        "results": unique_articles,
        "results_by_keyword": {kw: arts for kw, arts in results_by_keyword.items()}
    }

    output_file = os.path.join(RESULTS_DIR, f"{today.isoformat()}.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"결과 저장: {output_file}")
    return output_file


if __name__ == '__main__':
    result_path = run_scan()
    if result_path:
        print(f"\n완료! 결과: {result_path}")
