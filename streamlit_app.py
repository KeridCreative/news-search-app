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

    .stApp {
        font-family: 'Inter', -apple-system, sans-serif;
        background: #f5f6fa;
    }
    #MainMenu, footer, header { visibility: hidden; }

    /* Hero */
    .hero {
        background: linear-gradient(135deg, #6366f1, #8b5cf6, #a78bfa);
        border-radius: 20px;
        padding: 32px 28px 24px;
        margin-bottom: 20px;
        color: white;
        position: relative;
        overflow: hidden;
    }
    .hero::after {
        content: '';
        position: absolute;
        width: 180px; height: 180px;
        background: rgba(255,255,255,0.08);
        border-radius: 50%;
        top: -50px; right: -30px;
    }
    .hero h1 { font-size: 1.5em; font-weight: 800; margin: 0; position: relative; }
    .hero p { font-size: 0.85em; opacity: 0.8; margin: 4px 0 0; position: relative; }

    /* Stats */
    .stats-row {
        display: flex;
        gap: 10px;
        margin-bottom: 16px;
    }
    .stat-pill {
        flex: 1;
        background: white;
        border: 1px solid #e8eaf0;
        border-radius: 14px;
        padding: 14px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }
    .stat-pill .sp-num {
        font-size: 1.7em;
        font-weight: 800;
        line-height: 1;
        color: #1e293b;
    }
    .stat-pill .sp-num.c-yahoo { color: #ef4444; }
    .stat-pill .sp-num.c-pr { color: #0ea5e9; }
    .stat-pill .sp-label {
        font-size: 0.68em;
        font-weight: 600;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 3px;
    }

    /* Article Card */
    .a-card {
        background: white;
        border: 1px solid #e8eaf0;
        border-radius: 14px;
        padding: 16px 20px;
        margin-bottom: 8px;
        transition: all 0.15s;
        border-left: 4px solid transparent;
    }
    .a-card:hover {
        box-shadow: 0 4px 14px rgba(0,0,0,0.05);
        transform: translateY(-1px);
    }
    .a-card.src-yahoo { border-left-color: #ef4444; }
    .a-card.src-pr { border-left-color: #0ea5e9; }
    .a-card .a-top {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 10px;
    }
    .a-card .a-title {
        flex: 1;
        font-size: 0.9em;
        font-weight: 600;
        line-height: 1.5;
        color: #1e293b;
    }
    .a-card .a-title a { color: inherit; text-decoration: none; }
    .a-card .a-title a:hover { color: #6366f1; }
    .a-card .a-meta {
        display: flex;
        gap: 12px;
        margin-top: 6px;
        font-size: 0.75em;
        color: #94a3b8;
    }
    .a-card .a-meta span { display: flex; align-items: center; gap: 4px; }
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

    /* Keyword Section Header */
    .kw-sec {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 16px;
        background: #f8fafc;
        border-radius: 10px;
        margin: 16px 0 8px;
        border: 1px solid #e8eaf0;
    }
    .kw-sec .kw-n { font-weight: 700; color: #1e293b; font-size: 0.95em; }
    .kw-sec .kw-c {
        background: #6366f1;
        color: white;
        padding: 2px 10px;
        border-radius: 100px;
        font-size: 0.75em;
        font-weight: 700;
    }

    /* Empty */
    .empty { text-align: center; padding: 40px 20px; color: #94a3b8; }
    .empty .e-icon { font-size: 2.5em; margin-bottom: 8px; }

    /* Streamlit Overrides */
    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
        font-size: 0.85em;
        transition: all 0.15s;
    }
    .stTextInput > div > div > input {
        border-radius: 10px;
        border: 2px solid #e2e8f0;
        padding: 8px 12px;
        font-size: 0.88em;
    }
    .stTextInput > div > div > input:focus {
        border-color: #6366f1;
        box-shadow: 0 0 0 3px rgba(99,102,241,0.1);
    }

    section[data-testid="stSidebar"] { background: #f8fafc; }

    @media (max-width: 768px) {
        .hero { padding: 20px 16px 16px; }
        .hero h1 { font-size: 1.2em; }
        .stats-row { flex-direction: column; }
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
                                 'publish_time': dtxt.strip(), 'source': 'Yahoo', 'keyword': kw})
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
                             'publish_time': ra, 'source': 'PR Times', 'keyword': kw})
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
# MAIN APP
# ============================================================
keywords = load_keywords()

# --- Session State Init ---
if 'kw_multi' not in st.session_state:
    st.session_state.kw_multi = []
if 'search_results' not in st.session_state:
    st.session_state.search_results = {}
if 'vis_kw_multi' not in st.session_state:
    st.session_state.vis_kw_multi = []
if 'search_done' not in st.session_state:
    st.session_state.search_done = False

# === HERO ===
st.markdown("""<div class="hero">
    <h1>📰 아이돌 뉴스 검색기</h1>
    <p>Yahoo News Japan & PR Times에서 실시간 아이돌 뉴스를 한눈에</p>
</div>""", unsafe_allow_html=True)

# === CONTROLS: Source + Date ===
c1, c2 = st.columns([1, 1])
with c1:
    src = st.radio("🌐 검색 소스", ["Yahoo News", "PR Times", "둘 다"], horizontal=True, key="src_r")
with c2:
    dm = st.radio("📅 기간 모드", ["누적 기간", "특정 날짜"], horizontal=True, key="dm_r")

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

# === SEARCH MODE ===
search_mode = st.radio("검색 방법", ["🔍 키워드 선택", "✏️ 직접 입력"], horizontal=True, label_visibility="collapsed", key="sm_r")

if search_mode == "🔍 키워드 선택":
    # --- Keyword Toggle Buttons ---
    st.markdown("##### 검색할 키워드 선택")

    # Select All / Deselect All buttons
    ctrl_cols = st.columns([1, 1, 4])
    with ctrl_cols[0]:
        if st.button("✅ 전체 선택", key="sel_all", use_container_width=True):
            st.session_state.kw_multi = list(keywords)
            st.rerun()
    with ctrl_cols[1]:
        if st.button("⬜ 전체 해제", key="desel_all", use_container_width=True):
            st.session_state.kw_multi = []
            st.rerun()
    with ctrl_cols[2]:
        cnt = len(st.session_state.kw_multi)
        st.caption(f"선택됨: **{cnt}** / {len(keywords)}")

    # Keyword toggle grid - multiselect (state managed via key='kw_multi')
    st.multiselect(
        "키워드",
        options=keywords,
        label_visibility="collapsed",
        key="kw_multi"
    )

    selected_kws = st.session_state.kw_multi

    # Search button
    if selected_kws:
        do_search = st.button(
            f"🔍 선택한 {len(selected_kws)}개 키워드 검색",
            key="search_btn",
            use_container_width=True
        )
    else:
        st.info("검색할 키워드를 선택하세요.")
        do_search = False

    # Execute search
    if do_search and selected_kws:
        all_results = {}
        prog = st.progress(0)
        stat = st.empty()

        for i, kw in enumerate(selected_kws):
            stat.markdown(f"**`{kw}`** 검색 중... ({i+1}/{len(selected_kws)})")
            arts = search_all(kw, dates, src)
            if arts:
                all_results[kw] = arts
            prog.progress((i+1)/len(selected_kws))

        stat.empty()
        prog.empty()

        st.session_state.search_results = all_results
        st.session_state.vis_kw_multi = list(all_results.keys())
        st.session_state.search_done = True
        st.rerun()

elif search_mode == "✏️ 직접 입력":
    c_i, c_b = st.columns([5, 1])
    with c_i:
        inp = st.text_input("키워드", placeholder="예: AKB48, 乃木坂, TWICE...", label_visibility="collapsed", key="kw_i")
    with c_b:
        st.markdown("<div style='height:2px'></div>", unsafe_allow_html=True)
        do_direct = st.button("검색", key="b_direct", use_container_width=True)

    if do_direct and inp and inp.strip():
        kw = inp.strip()
        with st.spinner(f"'{kw}' 검색 중..."):
            arts = search_all(kw, dates, src)
        st.session_state.search_results = {kw: arts} if arts else {}
        st.session_state.vis_kw_multi = [kw] if arts else []
        st.session_state.search_done = True
        st.rerun()

# ============================================================
# RESULTS DISPLAY
# ============================================================
if st.session_state.search_done and st.session_state.search_results:
    results = st.session_state.search_results
    all_articles = []
    for arts in results.values():
        all_articles.extend(arts)

    if not all_articles:
        st.markdown('<div class="empty"><div class="e-icon">🔍</div><p>검색된 기사가 없습니다</p></div>', unsafe_allow_html=True)
    else:
        st.markdown("---")

        # --- Stats ---
        yahoo_n = sum(1 for a in all_articles if a['source'] == 'Yahoo')
        pr_n = sum(1 for a in all_articles if a['source'] == 'PR Times')
        st.markdown(f"""<div class="stats-row">
            <div class="stat-pill"><div class="sp-num">{len(all_articles)}</div><div class="sp-label">Total</div></div>
            <div class="stat-pill"><div class="sp-num c-yahoo">{yahoo_n}</div><div class="sp-label">Yahoo News</div></div>
            <div class="stat-pill"><div class="sp-num c-pr">{pr_n}</div><div class="sp-label">PR Times</div></div>
        </div>""", unsafe_allow_html=True)

        # --- Source Filter ---
        src_filter = st.radio("소스 필터", ["전체", f"Yahoo ({yahoo_n})", f"PR Times ({pr_n})"],
                              horizontal=True, label_visibility="collapsed", key="src_filter")

        # --- Keyword Result Toggle Buttons ---
        if len(results) > 1:
            st.markdown("##### 키워드별 결과 필터")

            # Toggle All / None for results
            r_ctrl = st.columns([1, 1, 4])
            with r_ctrl[0]:
                if st.button("✅ 모두 표시", key="show_all_r", use_container_width=True):
                    st.session_state.vis_kw_multi = list(results.keys())
                    st.rerun()
            with r_ctrl[1]:
                if st.button("⬜ 모두 숨기기", key="hide_all_r", use_container_width=True):
                    st.session_state.vis_kw_multi = []
                    st.rerun()

            # Keyword toggle via multiselect (state managed via key='vis_kw_multi')
            kw_opts = list(results.keys())
            st.multiselect(
                "표시할 키워드",
                options=kw_opts,
                format_func=lambda x: f"{x} ({len(results[x])}건)",
                label_visibility="collapsed",
                key="vis_kw_multi"
            )
            visible_kws = set(st.session_state.vis_kw_multi)
        else:
            visible_kws = set(results.keys())

        # --- Display Articles ---
        if not visible_kws:
            st.markdown('<div class="empty"><div class="e-icon">👆</div><p>표시할 키워드를 선택하세요</p></div>', unsafe_allow_html=True)
        else:
            for kw in results:
                if kw not in visible_kws:
                    continue
                kw_articles = results[kw]

                # Apply source filter
                if "Yahoo" in src_filter:
                    kw_articles = [a for a in kw_articles if a['source'] == 'Yahoo']
                elif "PR Times" in src_filter:
                    kw_articles = [a for a in kw_articles if a['source'] == 'PR Times']

                if not kw_articles:
                    continue

                # Keyword section header
                st.markdown(f"""<div class="kw-sec">
                    <span class="kw-n">{kw}</span>
                    <span class="kw-c">{len(kw_articles)}건</span>
                </div>""", unsafe_allow_html=True)

                for a in kw_articles:
                    render_card(a)

elif st.session_state.search_done and not st.session_state.search_results:
    st.markdown('<div class="empty"><div class="e-icon">🔍</div><p>검색된 기사가 없습니다</p></div>', unsafe_allow_html=True)
