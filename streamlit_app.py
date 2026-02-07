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
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS (Modern Dark Theme) ---
st.markdown("""
<style>
    /* === Global === */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* === Sidebar === */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0f1a 0%, #1a1a2e 100%);
    }
    section[data-testid="stSidebar"] * {
        color: #e0e0e0 !important;
    }
    section[data-testid="stSidebar"] .stRadio label,
    section[data-testid="stSidebar"] .stSelectbox label {
        color: #a0a0b8 !important;
        font-size: 0.85em;
    }
    section[data-testid="stSidebar"] hr {
        border-color: rgba(255,255,255,0.08);
    }

    .sidebar-title {
        font-size: 0.7em;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 2px;
        color: #7c7cff !important;
        margin-bottom: 8px;
        padding-bottom: 4px;
    }
    .sidebar-section {
        background: rgba(255,255,255,0.03);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 16px;
        border: 1px solid rgba(255,255,255,0.06);
    }

    /* === Header === */
    .hero-header {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #a855f7 100%);
        color: white;
        padding: 32px 40px;
        border-radius: 16px;
        margin-bottom: 28px;
        position: relative;
        overflow: hidden;
    }
    .hero-header::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -20%;
        width: 300px;
        height: 300px;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
        border-radius: 50%;
    }
    .hero-header h1 {
        font-size: 1.8em;
        font-weight: 800;
        margin: 0 0 4px 0;
        position: relative;
    }
    .hero-header p {
        font-size: 0.95em;
        opacity: 0.85;
        margin: 0;
        position: relative;
    }

    /* === Search Bar === */
    .search-container {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }

    /* === Stat Cards === */
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 16px;
        margin-bottom: 28px;
    }
    .stat-card-new {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 20px;
        text-align: center;
        transition: all 0.2s ease;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .stat-card-new:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    .stat-icon { font-size: 1.6em; margin-bottom: 6px; }
    .stat-value {
        font-size: 2em;
        font-weight: 800;
        color: #1a1a2e;
        line-height: 1.1;
    }
    .stat-value.yahoo-color { color: #ef4444; }
    .stat-value.prtimes-color { color: #0ea5e9; }
    .stat-desc {
        font-size: 0.8em;
        color: #94a3b8;
        font-weight: 500;
        margin-top: 4px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* === Article Cards === */
    .article-card-new {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 12px;
        transition: all 0.2s ease;
        position: relative;
        border-left: 4px solid #e2e8f0;
    }
    .article-card-new:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 16px rgba(0,0,0,0.06);
        border-color: #c7d2fe;
    }
    .article-card-new.yahoo-card { border-left-color: #ef4444; }
    .article-card-new.prtimes-card { border-left-color: #0ea5e9; }
    .article-card-new .card-top {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 12px;
    }
    .article-card-new .card-title {
        flex: 1;
        font-size: 0.95em;
        font-weight: 600;
        line-height: 1.5;
        color: #1e293b;
    }
    .article-card-new .card-title a {
        color: #1e293b;
        text-decoration: none;
    }
    .article-card-new .card-title a:hover {
        color: #4f46e5;
    }
    .article-card-new .card-bottom {
        display: flex;
        align-items: center;
        gap: 16px;
        margin-top: 10px;
        font-size: 0.8em;
        color: #94a3b8;
    }
    .article-card-new .card-bottom span {
        display: flex;
        align-items: center;
        gap: 4px;
    }

    /* Source Badges */
    .badge {
        display: inline-flex;
        align-items: center;
        padding: 3px 10px;
        border-radius: 100px;
        font-size: 0.7em;
        font-weight: 700;
        letter-spacing: 0.3px;
        white-space: nowrap;
        flex-shrink: 0;
    }
    .badge-yahoo {
        background: #fef2f2;
        color: #dc2626;
        border: 1px solid #fecaca;
    }
    .badge-prtimes {
        background: #f0f9ff;
        color: #0284c7;
        border: 1px solid #bae6fd;
    }

    /* === Keyword Section Header === */
    .kw-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 14px 20px;
        background: #f8fafc;
        border-radius: 12px;
        margin: 28px 0 14px 0;
        border: 1px solid #e2e8f0;
    }
    .kw-header .kw-name {
        font-size: 1.1em;
        font-weight: 700;
        color: #1e293b;
    }
    .kw-header .kw-count {
        background: #4f46e5;
        color: white;
        padding: 4px 14px;
        border-radius: 100px;
        font-size: 0.8em;
        font-weight: 700;
    }

    /* === No Results === */
    .empty-state {
        text-align: center;
        padding: 60px 20px;
        color: #94a3b8;
    }
    .empty-state .empty-icon { font-size: 3em; margin-bottom: 12px; }
    .empty-state p { font-size: 1em; }

    /* === Hide Streamlit branding === */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* === Streamlit widget overrides === */
    .stButton > button {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 10px 28px;
        font-weight: 600;
        font-size: 0.9em;
        transition: all 0.2s;
        box-shadow: 0 2px 8px rgba(79,70,229,0.3);
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 16px rgba(79,70,229,0.4);
    }
    .stButton > button:active {
        transform: translateY(0);
    }
    .stTextInput > div > div > input {
        border-radius: 10px;
        border: 2px solid #e2e8f0;
        padding: 10px 14px;
    }
    .stTextInput > div > div > input:focus {
        border-color: #4f46e5;
        box-shadow: 0 0 0 3px rgba(79,70,229,0.1);
    }
    .stSelectbox > div > div {
        border-radius: 10px;
    }
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

# --- Date Calculation (Refactored) ---
def get_date_range(date_mode, date_value):
    """
    date_mode: 'cumulative' or 'single'
    date_value: int (number of days)
    """
    today = datetime.date.today()
    if date_mode == 'cumulative':
        return [today - datetime.timedelta(days=i) for i in range(date_value + 1)]
    else:  # single
        return [today - datetime.timedelta(days=date_value)]

def format_date_japanese(date):
    return f"{date.month}/{date.day}"

# --- Yahoo News Scraping ---
def scrape_yahoo_news(keyword, target_dates):
    url = f"https://news.yahoo.co.jp/search?p={keyword}&rkf=2&ei=UTF-8"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    found_articles = []
    target_date_strs = [format_date_japanese(d) for d in target_dates]

    try:
        response = requests.get(url, headers=headers, timeout=15)
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
    except Exception as e:
        st.toast(f"⚠️ Yahoo: {keyword} - {e}", icon="⚠️")

    found_articles.sort(key=lambda x: x['publish_time'], reverse=True)
    return found_articles

# --- PR Times Scraping ---
def scrape_prtimes(keyword, target_dates):
    url = f"https://prtimes.jp/main/action.php?run=html&page=searchkey&search_word={keyword}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    found_articles = []

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

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

            is_match = False
            today = datetime.date.today()

            relative_patterns = ['分前', '時間前', '秒前']
            if any(p in released_at for p in relative_patterns):
                if today in target_dates:
                    is_match = True
            if '昨日' in released_at:
                if (today - datetime.timedelta(days=1)) in target_dates:
                    is_match = True

            abs_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', released_at)
            if abs_match:
                try:
                    article_date = datetime.date(int(abs_match.group(1)), int(abs_match.group(2)), int(abs_match.group(3)))
                    if article_date in target_dates:
                        is_match = True
                except ValueError:
                    pass

            days_match = re.search(r'(\d+)日前', released_at)
            if days_match:
                article_date = today - datetime.timedelta(days=int(days_match.group(1)))
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

    except Exception as e:
        st.toast(f"⚠️ PR Times: {keyword} - {e}", icon="⚠️")

    return found_articles

# --- Combined Search ---
def search_articles(keyword, target_dates, source):
    articles = []
    if source in ['Yahoo News', '둘 다']:
        articles.extend(scrape_yahoo_news(keyword, target_dates))
    if source in ['PR Times', '둘 다']:
        articles.extend(scrape_prtimes(keyword, target_dates))
    return articles

# --- Render Functions ---
def render_article(article):
    source = article.get('source', 'Yahoo')
    card_cls = 'yahoo-card' if source == 'Yahoo' else 'prtimes-card'
    badge_cls = 'badge-yahoo' if source == 'Yahoo' else 'badge-prtimes'
    source_icon = '📺' if source == 'Yahoo' else '📢'
    st.markdown(f"""
    <div class="article-card-new {card_cls}">
        <div class="card-top">
            <div class="card-title"><a href="{article['link']}" target="_blank">{article['title']}</a></div>
            <span class="badge {badge_cls}">{source}</span>
        </div>
        <div class="card-bottom">
            <span>{source_icon} {article['media']}</span>
            <span>🕐 {article['publish_time']}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_stats(articles):
    total = len(articles)
    yahoo_n = sum(1 for a in articles if a.get('source') == 'Yahoo')
    prtimes_n = sum(1 for a in articles if a.get('source') == 'PR Times')
    st.markdown(f"""
    <div class="stats-grid">
        <div class="stat-card-new">
            <div class="stat-icon">📊</div>
            <div class="stat-value">{total}</div>
            <div class="stat-desc">Total</div>
        </div>
        <div class="stat-card-new">
            <div class="stat-icon">📰</div>
            <div class="stat-value yahoo-color">{yahoo_n}</div>
            <div class="stat-desc">Yahoo News</div>
        </div>
        <div class="stat-card-new">
            <div class="stat-icon">📢</div>
            <div class="stat-value prtimes-color">{prtimes_n}</div>
            <div class="stat-desc">PR Times</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_no_results():
    st.markdown("""
    <div class="empty-state">
        <div class="empty-icon">🔍</div>
        <p>검색된 기사가 없습니다</p>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
#  SIDEBAR
# ============================================================
keywords = load_keywords()

with st.sidebar:
    st.markdown("## 📰 뉴스 검색기")
    st.markdown("---")

    # --- Source ---
    st.markdown('<div class="sidebar-title">🌐 검색 소스</div>', unsafe_allow_html=True)
    source_option = st.radio("소스", ["Yahoo News", "PR Times", "둘 다"], label_visibility="collapsed", key="src")

    st.markdown("---")

    # --- Date Mode ---
    st.markdown('<div class="sidebar-title">📅 검색 기간</div>', unsafe_allow_html=True)
    date_mode = st.radio("기간 모드", ["누적 기간", "특정 날짜"], horizontal=True, label_visibility="collapsed", key="dmode")

    if date_mode == "누적 기간":
        cumulative_options = {
            "오늘": 0,
            "~어제": 1,
            "~3일 전": 3,
            "~5일 전": 5,
            "~7일 전": 7,
        }
        selected_period = st.radio("기간 선택", list(cumulative_options.keys()), label_visibility="collapsed", key="cum")
        date_value = cumulative_options[selected_period]
        date_mode_key = 'cumulative'
        # Show date range info
        today = datetime.date.today()
        end_date = today - datetime.timedelta(days=date_value)
        if date_value == 0:
            st.caption(f"📌 {today.strftime('%m/%d')} (오늘만)")
        else:
            st.caption(f"📌 {end_date.strftime('%m/%d')} ~ {today.strftime('%m/%d')}")
    else:
        single_options = {
            "오늘": 0,
            "어제": 1,
            "2일 전": 2,
            "3일 전": 3,
            "4일 전": 4,
            "5일 전": 5,
            "6일 전": 6,
            "7일 전": 7,
        }
        selected_day = st.radio("날짜 선택", list(single_options.keys()), label_visibility="collapsed", key="single")
        date_value = single_options[selected_day]
        date_mode_key = 'single'
        target_date = datetime.date.today() - datetime.timedelta(days=date_value)
        st.caption(f"📌 {target_date.strftime('%m/%d')} ({selected_day})")

    st.markdown("---")

    # --- Registered Keywords (collapsible) ---
    with st.expander(f"📋 등록 키워드 ({len(keywords)}개)", expanded=False):
        for kw in keywords:
            st.markdown(f"- {kw}")

    st.markdown("---")

    # --- All Keywords Search ---
    st.markdown('<div class="sidebar-title">⚡ 전체 검색</div>', unsafe_allow_html=True)
    btn_all = st.button("🔍 등록 키워드 전체 검색", key="btn_all_sidebar", use_container_width=True)

# Compute target dates
target_dates = get_date_range(date_mode_key, date_value)

# ============================================================
#  MAIN AREA
# ============================================================

# --- Header ---
st.markdown("""
<div class="hero-header">
    <h1>📰 아이돌 뉴스 검색기</h1>
    <p>Yahoo News Japan & PR Times — 실시간 아이돌 뉴스를 한눈에</p>
</div>
""", unsafe_allow_html=True)

# --- Search Bar ---
search_mode = st.radio("검색 방법", ["등록 키워드", "직접 입력"], horizontal=True, label_visibility="collapsed", key="search_mode")

if search_mode == "등록 키워드":
    col_sel, col_btn = st.columns([4, 1])
    with col_sel:
        selected_keyword = st.selectbox("키워드", ["-- 선택 --"] + keywords, label_visibility="collapsed", key="kw_sel")
    with col_btn:
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        btn_search = st.button("검색", key="btn_search_sel", use_container_width=True)
    search_keyword = selected_keyword if selected_keyword != "-- 선택 --" else None
    do_search = btn_search and search_keyword
else:
    col_inp, col_btn = st.columns([4, 1])
    with col_inp:
        new_keyword = st.text_input("키워드", placeholder="예: 乃木坂, AKB48, TWICE...", label_visibility="collapsed", key="kw_inp")
    with col_btn:
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        btn_search = st.button("검색", key="btn_search_inp", use_container_width=True)
    search_keyword = new_keyword.strip() if new_keyword else None
    do_search = btn_search and search_keyword

st.markdown("---")

# --- Single Keyword Search ---
if do_search:
    with st.spinner(f"'{search_keyword}' 검색 중..."):
        articles = search_articles(search_keyword, target_dates, source_option)
    render_stats(articles)
    if articles:
        for article in articles:
            render_article(article)
    else:
        render_no_results()

# --- All Keywords Search ---
if btn_all:
    all_results = {}
    total_count = 0
    progress = st.progress(0)
    status = st.empty()

    for i, kw in enumerate(keywords):
        status.markdown(f"**검색 중:** `{kw}` ({i+1}/{len(keywords)})")
        arts = search_articles(kw, target_dates, source_option)
        if arts:
            all_results[kw] = arts
            total_count += len(arts)
        progress.progress((i + 1) / len(keywords))

    status.empty()
    progress.empty()

    # Stats
    all_flat = [a for arts in all_results.values() for a in arts]
    render_stats(all_flat)

    if all_results:
        for kw, arts in all_results.items():
            st.markdown(f"""
            <div class="kw-header">
                <span class="kw-name">{kw}</span>
                <span class="kw-count">{len(arts)}건</span>
            </div>
            """, unsafe_allow_html=True)
            for article in arts:
                render_article(article)
    else:
        render_no_results()
