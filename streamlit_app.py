import streamlit as st
import requests
from bs4 import BeautifulSoup
import datetime
import re
import json
import os

# --- Page Config ---
st.set_page_config(
    page_title="아이돌 뉴스 검색기",
    page_icon="📰",
    layout="wide"
)

# --- Custom CSS ---
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 40px 30px;
        text-align: center;
        border-radius: 15px;
        margin-bottom: 30px;
    }
    .main-header h1 { font-size: 2.5em; margin-bottom: 10px; }
    .main-header p { font-size: 1.1em; opacity: 0.9; }
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white; padding: 20px; border-radius: 15px; text-align: center;
    }
    .stat-number { font-size: 2.5em; font-weight: 700; }
    .stat-label { opacity: 0.9; font-size: 0.9em; }
    .article-card {
        background: white; border: 2px solid #e9ecef;
        border-left: 5px solid #667eea; border-radius: 12px;
        padding: 20px; margin-bottom: 15px;
    }
    .article-card:hover { border-color: #667eea; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
    .article-card.prtimes { border-left-color: #00a4de; }
    .article-title a { color: #333; text-decoration: none; font-size: 1.1em; font-weight: 600; }
    .article-title a:hover { color: #667eea; }
    .article-meta { color: #6c757d; font-size: 0.9em; margin-top: 10px; }
    .source-badge {
        display: inline-block; padding: 2px 8px; border-radius: 10px;
        font-size: 0.75em; font-weight: 600; margin-left: 8px;
    }
    .source-badge.yahoo { background: #ff0033; color: white; }
    .source-badge.prtimes { background: #00a4de; color: white; }
    .keyword-header {
        background: #f8f9fa; padding: 15px 20px; border-radius: 10px;
        border-left: 5px solid #667eea; margin-top: 30px; margin-bottom: 15px;
        display: flex; justify-content: space-between; align-items: center;
    }
    .no-results { text-align: center; padding: 40px; color: #6c757d; }
</style>
""", unsafe_allow_html=True)

# --- File Path ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KEYWORDS_FILE = os.path.join(BASE_DIR, 'keywords.json')

# --- Keyword Loading ---
def load_keywords():
    try:
        with open(KEYWORDS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("search_keyword", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []

# --- Date Calculation ---
def get_date_range(days_ago):
    if days_ago == 'all':
        return [datetime.date.today() - datetime.timedelta(days=i) for i in range(7)]
    else:
        return [datetime.date.today() - datetime.timedelta(days=int(days_ago))]

def format_date_japanese(date):
    return f"{date.month}/{date.day}"

# --- Yahoo News Scraping ---
def scrape_yahoo_news(keyword, days_ago='0'):
    url = f"https://news.yahoo.co.jp/search?p={keyword}&rkf=2&ei=UTF-8"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    found_articles = []
    target_dates = get_date_range(days_ago)
    target_date_strs = [format_date_japanese(d) for d in target_dates]

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = soup.find_all('li', class_='sc-1u4589e-0')

        for article in articles:
            date_element = article.find('time')
            if not date_element:
                continue
            date_text = date_element.text
            match = re.search(r'(\d{1,2}/\d{1,2})', date_text)
            if match and match.group(1) in target_date_strs:
                title_element = article.find('div', class_='sc-3ls169-0')
                link_element = article.find('a')
                media_element = article.find('span')
                if title_element and link_element:
                    found_articles.append({
                        'title': title_element.text.strip(),
                        'link': link_element.get('href', '#'),
                        'media': media_element.text.strip() if media_element else 'N/A',
                        'publish_time': date_text.strip(),
                        'source': 'Yahoo'
                    })
    except requests.exceptions.RequestException as e:
        st.error(f"[Yahoo] '{keyword}' 검색 중 네트워크 오류: {e}")
    except Exception as e:
        st.error(f"[Yahoo] '{keyword}' 검색 중 오류: {e}")

    found_articles.sort(key=lambda x: x['publish_time'], reverse=True)
    return found_articles

# --- PR Times Scraping ---
def scrape_prtimes(keyword, days_ago='0'):
    url = f"https://prtimes.jp/main/action.php?run=html&page=searchkey&search_word={keyword}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    found_articles = []
    target_dates = get_date_range(days_ago)

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract from __NEXT_DATA__ JSON (most reliable)
        script = soup.find('script', id='__NEXT_DATA__')
        if not script:
            return found_articles

        data = json.loads(script.string)
        try:
            queries = data['props']['pageProps']['dehydratedState']['queries']
            releases = []
            for q in queries:
                state_data = q.get('state', {}).get('data', {})
                pages = state_data.get('pages', [])
                for page in pages:
                    release_list = page.get('releaseList', [])
                    if release_list:
                        releases.extend(release_list)
        except (KeyError, IndexError, TypeError):
            return found_articles

        for release in releases:
            title = release.get('title', '')
            release_url = release.get('releaseUrl', '')
            company_name = release.get('companyName', 'N/A')
            released_at = release.get('releasedAt', '')

            # Date filtering for PR Times
            # releasedAt can be relative ("2時間前") or absolute ("2026年2月6日 12時00分")
            is_match = False

            # Check relative time (today's articles)
            relative_patterns = ['分前', '時間前', '秒前']
            if any(p in released_at for p in relative_patterns):
                # These are from today
                if datetime.date.today() in target_dates:
                    is_match = True

            # Check "昨日" (yesterday)
            if '昨日' in released_at:
                yesterday = datetime.date.today() - datetime.timedelta(days=1)
                if yesterday in target_dates:
                    is_match = True

            # Check absolute date format: "2026年2月6日..."
            abs_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', released_at)
            if abs_match:
                try:
                    article_date = datetime.date(
                        int(abs_match.group(1)),
                        int(abs_match.group(2)),
                        int(abs_match.group(3))
                    )
                    if article_date in target_dates:
                        is_match = True
                except ValueError:
                    pass

            # Check "日前" pattern (X days ago)
            days_match = re.search(r'(\d+)日前', released_at)
            if days_match:
                days_offset = int(days_match.group(1))
                article_date = datetime.date.today() - datetime.timedelta(days=days_offset)
                if article_date in target_dates:
                    is_match = True

            if is_match:
                full_url = f"https://prtimes.jp{release_url}" if release_url.startswith('/') else release_url
                found_articles.append({
                    'title': title,
                    'link': full_url,
                    'media': company_name,
                    'publish_time': released_at,
                    'source': 'PR Times'
                })

    except requests.exceptions.RequestException as e:
        st.error(f"[PR Times] '{keyword}' 검색 중 네트워크 오류: {e}")
    except Exception as e:
        st.error(f"[PR Times] '{keyword}' 검색 중 오류: {e}")

    return found_articles

# --- Combined Search ---
def search_articles(keyword, days_ago, source):
    articles = []
    if source in ['Yahoo News', '둘 다']:
        articles.extend(scrape_yahoo_news(keyword, days_ago))
    if source in ['PR Times', '둘 다']:
        articles.extend(scrape_prtimes(keyword, days_ago))
    return articles

# --- Render article card ---
def render_article(article):
    source = article.get('source', 'Yahoo')
    card_class = 'article-card prtimes' if source == 'PR Times' else 'article-card'
    badge_class = 'source-badge prtimes' if source == 'PR Times' else 'source-badge yahoo'
    source_icon = '📢' if source == 'PR Times' else '📺'
    st.markdown(f"""
    <div class="{card_class}">
        <div class="article-title">
            <a href="{article['link']}" target="_blank">{article['title']}</a>
            <span class="{badge_class}">{source}</span>
        </div>
        <div class="article-meta">
            {source_icon} {article['media']} &nbsp;&nbsp; 🕐 {article['publish_time']}
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- Render stats ---
def render_stats(articles, keyword=None, label_left="검색된 기사", label_right="검색 키워드"):
    col1, col2 = st.columns(2)
    with col1:
        yahoo_count = sum(1 for a in articles if a.get('source') == 'Yahoo')
        prtimes_count = sum(1 for a in articles if a.get('source') == 'PR Times')
        count_detail = f"{len(articles)}"
        if yahoo_count > 0 and prtimes_count > 0:
            count_detail = f"{len(articles)}<br><span style='font-size:0.4em'>Yahoo {yahoo_count} / PR Times {prtimes_count}</span>"
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{count_detail}</div>
            <div class="stat-label">{label_left}</div>
        </div>
        """, unsafe_allow_html=True)
    if keyword:
        with col2:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{keyword}</div>
                <div class="stat-label">{label_right}</div>
            </div>
            """, unsafe_allow_html=True)

# --- Render no results ---
def render_no_results():
    st.markdown("""
    <div class="no-results">
        <h2>📭</h2>
        <p>검색된 기사가 없습니다.</p>
    </div>
    """, unsafe_allow_html=True)

# ===== MAIN UI =====

# --- Header ---
st.markdown("""
<div class="main-header">
    <h1>📰 아이돌 뉴스 검색기</h1>
    <p>Yahoo News Japan & PR Times에서 아이돌 뉴스를 검색하세요</p>
</div>
""", unsafe_allow_html=True)

# --- Load keywords ---
keywords = load_keywords()

# --- Source & Date Filter ---
col_source, col_date = st.columns([1, 2])

with col_source:
    st.markdown("### 🌐 검색 소스")
    source_option = st.radio(
        "소스 선택",
        options=["Yahoo News", "PR Times", "둘 다"],
        horizontal=True,
        label_visibility="collapsed"
    )

with col_date:
    st.markdown("### 📅 검색 기간 선택")
    date_options = {
        "오늘": "0",
        "어제": "1",
        "2일 전": "2",
        "3일 전": "3",
        "전체 (7일)": "all"
    }
    selected_date_label = st.radio(
        "기간 선택",
        options=list(date_options.keys()),
        horizontal=True,
        label_visibility="collapsed"
    )
    days_ago = date_options[selected_date_label]

st.markdown("---")

# --- Search Tabs ---
tab1, tab2, tab3 = st.tabs(["🔍 등록된 키워드로 검색", "✏️ 새로운 키워드로 검색", "📋 전체 키워드 검색"])

with tab1:
    selected_keyword = st.selectbox(
        "키워드 선택",
        options=["-- 키워드를 선택하세요 --"] + keywords,
        key="keyword_select"
    )
    if st.button("🔍 검색하기", key="btn_select"):
        if selected_keyword == "-- 키워드를 선택하세요 --":
            st.warning("키워드를 선택해주세요.")
        else:
            with st.spinner(f"'{selected_keyword}' 검색 중... ({source_option})"):
                articles = search_articles(selected_keyword, days_ago, source_option)
            render_stats(articles, selected_keyword)
            st.markdown("")
            if articles:
                for article in articles:
                    render_article(article)
            else:
                render_no_results()

with tab2:
    new_keyword = st.text_input(
        "키워드 입력",
        placeholder="예: 乃木坂, AKB48...",
        key="keyword_new"
    )
    if st.button("🔍 검색하기", key="btn_new"):
        if not new_keyword:
            st.warning("키워드를 입력해주세요.")
        else:
            with st.spinner(f"'{new_keyword}' 검색 중... ({source_option})"):
                articles = search_articles(new_keyword, days_ago, source_option)
            render_stats(articles, new_keyword)
            st.markdown("")
            if articles:
                for article in articles:
                    render_article(article)
            else:
                render_no_results()

with tab3:
    st.markdown(f"등록된 모든 키워드(**{len(keywords)}개**)를 한 번에 검색합니다.")
    if st.button("🔍 전체 검색하기", key="btn_all"):
        all_results = {}
        total_count = 0
        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, keyword in enumerate(keywords):
            status_text.text(f"'{keyword}' 검색 중... ({i+1}/{len(keywords)}) [{source_option}]")
            articles = search_articles(keyword, days_ago, source_option)
            if articles:
                all_results[keyword] = articles
                total_count += len(articles)
            progress_bar.progress((i + 1) / len(keywords))

        status_text.empty()
        progress_bar.empty()

        # Stats
        all_articles_flat = [a for arts in all_results.values() for a in arts]
        col1, col2 = st.columns(2)
        with col1:
            yahoo_total = sum(1 for a in all_articles_flat if a.get('source') == 'Yahoo')
            prtimes_total = sum(1 for a in all_articles_flat if a.get('source') == 'PR Times')
            count_detail = f"{total_count}"
            if yahoo_total > 0 and prtimes_total > 0:
                count_detail = f"{total_count}<br><span style='font-size:0.4em'>Yahoo {yahoo_total} / PR Times {prtimes_total}</span>"
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{count_detail}</div>
                <div class="stat-label">총 기사 수</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{len(all_results)}</div>
                <div class="stat-label">결과가 있는 키워드</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("")
        if all_results:
            for keyword, articles in all_results.items():
                st.markdown(f"""
                <div class="keyword-header">
                    <span style="font-size:1.3em; font-weight:700; color:#333;">{keyword}</span>
                    <span style="background:#667eea; color:white; padding:5px 12px; border-radius:15px; font-weight:600;">{len(articles)}개</span>
                </div>
                """, unsafe_allow_html=True)
                for article in articles:
                    render_article(article)
        else:
            render_no_results()
