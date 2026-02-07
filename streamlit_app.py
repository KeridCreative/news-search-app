import streamlit as st
import requests
from bs4 import BeautifulSoup
import datetime
import re
import json
import os
import urllib.parse

# --- Page Config ---
st.set_page_config(
    page_title="아이돌 뉴스 검색기",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Custom CSS (Clean Light Theme) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* === Reset & Global === */
    .stApp {
        font-family: 'Inter', -apple-system, sans-serif;
        background: #f5f6fa;
    }
    #MainMenu, footer, header { visibility: hidden; }

    /* === Hero === */
    .hero {
        background: linear-gradient(135deg, #6366f1, #8b5cf6, #a78bfa);
        border-radius: 20px;
        padding: 36px 32px 28px;
        margin-bottom: 24px;
        color: white;
        position: relative;
        overflow: hidden;
    }
    .hero::after {
        content: '';
        position: absolute;
        width: 200px; height: 200px;
        background: rgba(255,255,255,0.08);
        border-radius: 50%;
        top: -60px; right: -40px;
    }
    .hero h1 { font-size: 1.6em; font-weight: 800; margin: 0; position: relative; }
    .hero p { font-size: 0.9em; opacity: 0.8; margin: 6px 0 0; position: relative; }

    /* === Control Bar (source + date) === */
    .ctrl-bar {
        background: white;
        border: 1px solid #e8eaf0;
        border-radius: 16px;
        padding: 20px 24px;
        margin-bottom: 20px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.03);
    }
    .ctrl-row {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        align-items: center;
    }
    .ctrl-label {
        font-size: 0.75em;
        font-weight: 700;
        color: #6366f1;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 8px;
    }
    .pill-group { display: flex; gap: 6px; flex-wrap: wrap; }
    .pill {
        display: inline-flex;
        align-items: center;
        padding: 6px 16px;
        border-radius: 100px;
        font-size: 0.82em;
        font-weight: 600;
        cursor: pointer;
        border: 2px solid #e8eaf0;
        background: white;
        color: #64748b;
        transition: all 0.15s;
        white-space: nowrap;
    }
    .pill.active {
        background: #6366f1;
        color: white;
        border-color: #6366f1;
    }
    .pill:hover:not(.active) {
        border-color: #a5b4fc;
        background: #f5f3ff;
        color: #6366f1;
    }

    /* === Search Box === */
    .search-box {
        background: white;
        border: 1px solid #e8eaf0;
        border-radius: 16px;
        padding: 20px 24px;
        margin-bottom: 24px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.03);
    }

    /* === Stats === */
    .stats-row {
        display: flex;
        gap: 12px;
        margin-bottom: 20px;
    }
    .stat-pill {
        flex: 1;
        background: white;
        border: 1px solid #e8eaf0;
        border-radius: 14px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 1px 4px rgba(0,0,0,0.03);
    }
    .stat-pill .sp-num {
        font-size: 1.8em;
        font-weight: 800;
        line-height: 1;
        color: #1e293b;
    }
    .stat-pill .sp-num.c-yahoo { color: #ef4444; }
    .stat-pill .sp-num.c-pr { color: #0ea5e9; }
    .stat-pill .sp-label {
        font-size: 0.7em;
        font-weight: 600;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 4px;
    }

    /* === Source Filter Tabs === */
    .source-tabs {
        display: flex;
        gap: 0;
        margin-bottom: 16px;
        background: #f1f5f9;
        border-radius: 12px;
        padding: 4px;
    }
    .src-tab {
        flex: 1;
        text-align: center;
        padding: 10px 16px;
        font-size: 0.85em;
        font-weight: 600;
        color: #64748b;
        border-radius: 10px;
        cursor: pointer;
        transition: all 0.15s;
    }
    .src-tab.active {
        background: white;
        color: #1e293b;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }
    .src-tab .tab-count {
        font-size: 0.8em;
        font-weight: 700;
        margin-left: 4px;
        opacity: 0.6;
    }

    /* === Keyword Toggle Chips === */
    .kw-chips {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        margin-bottom: 20px;
    }
    .kw-chip {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 14px;
        border-radius: 100px;
        font-size: 0.8em;
        font-weight: 600;
        border: 2px solid #e2e8f0;
        background: white;
        color: #475569;
        cursor: pointer;
        transition: all 0.15s;
    }
    .kw-chip.on {
        background: #6366f1;
        color: white;
        border-color: #6366f1;
    }
    .kw-chip .chip-count {
        background: rgba(0,0,0,0.1);
        padding: 1px 7px;
        border-radius: 100px;
        font-size: 0.85em;
    }
    .kw-chip.on .chip-count {
        background: rgba(255,255,255,0.25);
    }

    /* === Article Card === */
    .a-card {
        background: white;
        border: 1px solid #e8eaf0;
        border-radius: 14px;
        padding: 18px 22px;
        margin-bottom: 10px;
        transition: all 0.15s;
        border-left: 4px solid transparent;
    }
    .a-card:hover {
        box-shadow: 0 4px 16px rgba(0,0,0,0.05);
        transform: translateY(-1px);
    }
    .a-card.src-yahoo { border-left-color: #ef4444; }
    .a-card.src-pr { border-left-color: #0ea5e9; }
    .a-card .a-top {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 12px;
    }
    .a-card .a-title {
        flex: 1;
        font-size: 0.92em;
        font-weight: 600;
        line-height: 1.55;
        color: #1e293b;
    }
    .a-card .a-title a {
        color: inherit;
        text-decoration: none;
    }
    .a-card .a-title a:hover { color: #6366f1; }
    .a-card .a-meta {
        display: flex;
        gap: 14px;
        margin-top: 8px;
        font-size: 0.78em;
        color: #94a3b8;
    }
    .a-card .a-meta span {
        display: flex;
        align-items: center;
        gap: 4px;
    }
    .badge-s {
        padding: 2px 10px;
        border-radius: 100px;
        font-size: 0.68em;
        font-weight: 700;
        white-space: nowrap;
        flex-shrink: 0;
    }
    .badge-s.b-yahoo { background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }
    .badge-s.b-pr { background: #f0f9ff; color: #0284c7; border: 1px solid #bae6fd; }

    /* === Keyword Section === */
    .kw-sec {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 18px;
        background: #f8fafc;
        border-radius: 12px;
        margin: 20px 0 10px;
        border: 1px solid #e8eaf0;
    }
    .kw-sec .kw-n { font-weight: 700; color: #1e293b; font-size: 1em; }
    .kw-sec .kw-c {
        background: #6366f1;
        color: white;
        padding: 3px 12px;
        border-radius: 100px;
        font-size: 0.78em;
        font-weight: 700;
    }

    /* === Empty === */
    .empty { text-align: center; padding: 48px 20px; color: #94a3b8; }
    .empty .e-icon { font-size: 2.5em; margin-bottom: 10px; }

    /* === Streamlit Overrides === */
    .stButton > button {
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 10px 24px;
        font-weight: 600;
        font-size: 0.88em;
        box-shadow: 0 2px 8px rgba(99,102,241,0.25);
        transition: all 0.15s;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 14px rgba(99,102,241,0.35);
    }
    .stTextInput > div > div > input {
        border-radius: 12px;
        border: 2px solid #e2e8f0;
        padding: 10px 14px;
        font-size: 0.9em;
    }
    .stTextInput > div > div > input:focus {
        border-color: #6366f1;
        box-shadow: 0 0 0 3px rgba(99,102,241,0.1);
    }
    .stSelectbox > div > div { border-radius: 12px; }

    /* Sidebar light override */
    section[data-testid="stSidebar"] { background: #f8fafc; }

    /* Responsive */
    @media (max-width: 768px) {
        .hero { padding: 24px 20px 20px; }
        .hero h1 { font-size: 1.3em; }
        .stats-row { flex-direction: column; }
        .ctrl-row { flex-direction: column; align-items: stretch; }
    }
</style>
""", unsafe_allow_html=True)

# --- File Path ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KEYWORDS_FILE = os.path.join(BASE_DIR, 'keywords.json')

def load_keywords():
    try:
        with open(KEYWORDS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f).get("search_keyword", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []

# --- Date ---
def get_date_range(mode, value):
    today = datetime.date.today()
    if mode == 'cumulative':
        return [today - datetime.timedelta(days=i) for i in range(value + 1)]
    return [today - datetime.timedelta(days=value)]

def fmt_jp(d):
    return f"{d.month}/{d.day}"

# --- Scraping ---
def scrape_yahoo(kw, dates):
    url = f"https://news.yahoo.co.jp/search?p={urllib.parse.quote(kw)}&rkf=2&ei=UTF-8"
    hdrs = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"}
    arts = []
    dstrs = [fmt_jp(d) for d in dates]
    try:
        r = requests.get(url, headers=hdrs, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        for li in soup.find_all('li', class_='sc-1u4589e-0'):
            t = li.find('time')
            if not t: continue
            dtxt = t.text
            m = re.search(r'(\d{1,2}/\d{1,2})', dtxt)
            if m and m.group(1) in dstrs:
                title_el = li.find('div', class_='sc-3ls169-0')
                link_el = li.find('a')
                media_el = li.find('span')
                if title_el and link_el:
                    arts.append({'title': title_el.text.strip(), 'link': link_el.get('href','#'),
                                 'media': media_el.text.strip() if media_el else 'N/A',
                                 'publish_time': dtxt.strip(), 'source': 'Yahoo'})
    except: pass
    arts.sort(key=lambda x: x['publish_time'], reverse=True)
    return arts

def scrape_prtimes(kw, dates):
    url = f"https://prtimes.jp/main/action.php?run=html&page=searchkey&search_word={urllib.parse.quote(kw)}"
    hdrs = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"}
    arts = []
    try:
        r = requests.get(url, headers=hdrs, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        sc = soup.find('script', id='__NEXT_DATA__')
        if not sc: return arts
        data = json.loads(sc.string)
        releases = []
        for q in data.get('props',{}).get('pageProps',{}).get('dehydratedState',{}).get('queries',[]):
            for pg in q.get('state',{}).get('data',{}).get('pages',[]):
                releases.extend(pg.get('releaseList',[]))
        today = datetime.date.today()
        for rel in releases:
            ra = rel.get('releasedAt','')
            ok = False
            if any(p in ra for p in ['分前','時間前','秒前']):
                ok = today in dates
            if '昨日' in ra:
                ok = ok or (today - datetime.timedelta(days=1)) in dates
            am = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', ra)
            if am:
                try:
                    ad = datetime.date(int(am.group(1)),int(am.group(2)),int(am.group(3)))
                    ok = ok or ad in dates
                except: pass
            dm = re.search(r'(\d+)日前', ra)
            if dm:
                ok = ok or (today - datetime.timedelta(days=int(dm.group(1)))) in dates
            if ok:
                ru = rel.get('releaseUrl','')
                arts.append({'title': rel.get('title',''),
                             'link': f"https://prtimes.jp{ru}" if ru.startswith('/') else ru,
                             'media': rel.get('companyName','N/A'),
                             'publish_time': ra, 'source': 'PR Times'})
    except: pass
    return arts

def search_all(kw, dates, src):
    a = []
    if src in ['Yahoo News','둘 다']: a.extend(scrape_yahoo(kw, dates))
    if src in ['PR Times','둘 다']: a.extend(scrape_prtimes(kw, dates))
    return a

# --- Render ---
def render_card(a):
    s = a.get('source','Yahoo')
    cc = 'src-yahoo' if s=='Yahoo' else 'src-pr'
    bc = 'b-yahoo' if s=='Yahoo' else 'b-pr'
    si = '📺' if s=='Yahoo' else '📢'
    st.markdown(f"""<div class="a-card {cc}">
        <div class="a-top">
            <div class="a-title"><a href="{a['link']}" target="_blank">{a['title']}</a></div>
            <span class="badge-s {bc}">{s}</span>
        </div>
        <div class="a-meta"><span>{si} {a['media']}</span><span>🕐 {a['publish_time']}</span></div>
    </div>""", unsafe_allow_html=True)

# ============================================================
keywords = load_keywords()

# === HERO ===
st.markdown("""<div class="hero">
    <h1>📰 아이돌 뉴스 검색기</h1>
    <p>Yahoo News Japan & PR Times에서 실시간 아이돌 뉴스를 한눈에</p>
</div>""", unsafe_allow_html=True)

# === CONTROLS: Source + Date in one bar ===
c1, c2 = st.columns([1, 1])
with c1:
    src = st.radio("🌐 검색 소스", ["Yahoo News", "PR Times", "둘 다"], horizontal=True, key="src_r")
with c2:
    dm = st.radio("📅 기간 모드", ["누적 기간", "특정 날짜"], horizontal=True, key="dm_r")

# Date options
if dm == "누적 기간":
    opts = {"오늘":0, "~어제":1, "~3일":3, "~5일":5, "~7일":7}
    sel = st.select_slider("기간", list(opts.keys()), value="~7일", key="cum_sl")
    dv = opts[sel]
    dmk = 'cumulative'
    today = datetime.date.today()
    ed = today - datetime.timedelta(days=dv)
    info = f"{today.strftime('%m/%d')}" if dv==0 else f"{ed.strftime('%m/%d')} ~ {today.strftime('%m/%d')}"
    st.caption(f"📌 검색 범위: **{info}**")
else:
    opts = {"오늘":0,"어제":1,"2일전":2,"3일전":3,"4일전":4,"5일전":5,"6일전":6,"7일전":7}
    sel = st.select_slider("날짜", list(opts.keys()), value="오늘", key="sin_sl")
    dv = opts[sel]
    dmk = 'single'
    td = datetime.date.today() - datetime.timedelta(days=dv)
    st.caption(f"📌 검색 날짜: **{td.strftime('%Y/%m/%d')}**")

dates = get_date_range(dmk, dv)

st.markdown("---")

# === SEARCH: Unified ===
search_type = st.radio("검색 방법", ["🔍 키워드 선택", "✏️ 직접 입력", "📋 전체 검색"], horizontal=True, label_visibility="collapsed", key="st_r")

do_search = False
do_all = False
kw_to_search = None

if search_type == "🔍 키워드 선택":
    c_s, c_b = st.columns([5, 1])
    with c_s:
        kw_to_search = st.selectbox("키워드", ["-- 선택 --"] + keywords, label_visibility="collapsed", key="kw_s")
        if kw_to_search == "-- 선택 --": kw_to_search = None
    with c_b:
        st.markdown("<div style='height:2px'></div>", unsafe_allow_html=True)
        do_search = st.button("검색", key="b1", use_container_width=True)
elif search_type == "✏️ 직접 입력":
    c_i, c_b = st.columns([5, 1])
    with c_i:
        inp = st.text_input("키워드", placeholder="예: AKB48, 乃木坂, TWICE...", label_visibility="collapsed", key="kw_i")
        kw_to_search = inp.strip() if inp else None
    with c_b:
        st.markdown("<div style='height:2px'></div>", unsafe_allow_html=True)
        do_search = st.button("검색", key="b2", use_container_width=True)
else:  # 전체 검색
    st.info(f"등록된 **{len(keywords)}개** 키워드를 한 번에 검색합니다.")
    do_all = st.button("🔍 전체 검색 시작", key="b3", use_container_width=True)

# === RESULTS ===

def show_results(articles, is_multi=False, all_results=None):
    """Display results with source tabs and keyword toggles"""
    if not articles:
        st.markdown('<div class="empty"><div class="e-icon">🔍</div><p>검색된 기사가 없습니다</p></div>', unsafe_allow_html=True)
        return

    yahoo_n = sum(1 for a in articles if a['source'] == 'Yahoo')
    pr_n = sum(1 for a in articles if a['source'] == 'PR Times')

    # Stats
    st.markdown(f"""<div class="stats-row">
        <div class="stat-pill"><div class="sp-num">{len(articles)}</div><div class="sp-label">Total</div></div>
        <div class="stat-pill"><div class="sp-num c-yahoo">{yahoo_n}</div><div class="sp-label">Yahoo News</div></div>
        <div class="stat-pill"><div class="sp-num c-pr">{pr_n}</div><div class="sp-label">PR Times</div></div>
    </div>""", unsafe_allow_html=True)

    # Source filter tabs
    src_filter = st.radio("소스 필터", ["전체", f"Yahoo ({yahoo_n})", f"PR Times ({pr_n})"],
                          horizontal=True, label_visibility="collapsed", key="src_filter")

    # Filter by source
    if "Yahoo" in src_filter:
        filtered = [a for a in articles if a['source'] == 'Yahoo']
    elif "PR Times" in src_filter:
        filtered = [a for a in articles if a['source'] == 'PR Times']
    else:
        filtered = articles

    # Keyword toggles (for multi-keyword results)
    if is_multi and all_results:
        st.markdown("##### 키워드 필터")
        # Create columns for keyword toggle buttons
        kw_list = list(all_results.keys())

        # Use multiselect as toggle
        active_kws = st.multiselect(
            "표시할 키워드",
            options=kw_list,
            default=kw_list,
            format_func=lambda x: f"{x} ({len(all_results[x])})",
            label_visibility="collapsed",
            key="kw_toggle"
        )

        # Filter by active keywords
        filtered = [a for a in filtered if any(
            a in all_results.get(kw, []) for kw in active_kws
        )]

        # Show keyword section headers
        for kw in active_kws:
            kw_arts = [a for a in all_results[kw] if a in filtered]
            if kw_arts:
                st.markdown(f"""<div class="kw-sec">
                    <span class="kw-n">{kw}</span>
                    <span class="kw-c">{len(kw_arts)}건</span>
                </div>""", unsafe_allow_html=True)
                for a in kw_arts:
                    render_card(a)
    else:
        for a in filtered:
            render_card(a)

# --- Execute Search ---
if do_search and kw_to_search:
    with st.spinner(f"'{kw_to_search}' 검색 중..."):
        results = search_all(kw_to_search, dates, src)
    show_results(results)

if do_all:
    all_results = {}
    total_arts = []
    prog = st.progress(0)
    stat = st.empty()

    for i, kw in enumerate(keywords):
        stat.markdown(f"**`{kw}`** 검색 중... ({i+1}/{len(keywords)})")
        arts = search_all(kw, dates, src)
        if arts:
            all_results[kw] = arts
            total_arts.extend(arts)
        prog.progress((i+1)/len(keywords))

    stat.empty()
    prog.empty()

    show_results(total_arts, is_multi=True, all_results=all_results)
