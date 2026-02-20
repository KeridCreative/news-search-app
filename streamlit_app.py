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

# --- Custom CSS ---
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
        padding: 28px 24px 22px;
        margin-bottom: 18px;
        color: white;
        position: relative;
        overflow: hidden;
    }
    .hero::after {
        content: '';
        position: absolute;
        width: 160px; height: 160px;
        background: rgba(255,255,255,0.08);
        border-radius: 50%;
        top: -40px; right: -20px;
    }
    .hero h1 { font-size: 1.4em; font-weight: 800; margin: 0; position: relative; }
    .hero p { font-size: 0.82em; opacity: 0.8; margin: 3px 0 0; position: relative; }

    /* Stats */
    .stats-row { display: flex; gap: 10px; margin-bottom: 14px; }
    .stat-pill {
        flex: 1; background: white; border: 1px solid #e8eaf0;
        border-radius: 14px; padding: 12px; text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }
    .stat-pill .sp-num { font-size: 1.6em; font-weight: 800; line-height: 1; color: #1e293b; }
    .stat-pill .sp-num.c-yahoo { color: #ef4444; }
    .stat-pill .sp-num.c-pr { color: #0ea5e9; }
    .stat-pill .sp-label {
        font-size: 0.65em; font-weight: 600; color: #94a3b8;
        text-transform: uppercase; letter-spacing: 0.5px; margin-top: 2px;
    }

    /* Article Card */
    .a-card {
        background: white; border: 1px solid #e8eaf0; border-radius: 14px;
        padding: 14px 18px; margin-bottom: 7px; transition: all 0.15s;
        border-left: 4px solid transparent;
    }
    .a-card:hover { box-shadow: 0 4px 14px rgba(0,0,0,0.05); transform: translateY(-1px); }
    .a-card.src-yahoo { border-left-color: #ef4444; }
    .a-card.src-pr { border-left-color: #0ea5e9; }
    .a-card .a-top { display: flex; justify-content: space-between; align-items: flex-start; gap: 10px; }
    .a-card .a-title { flex: 1; font-size: 0.88em; font-weight: 600; line-height: 1.5; color: #1e293b; }
    .a-card .a-title a { color: inherit; text-decoration: none; }
    .a-card .a-title a:hover { color: #6366f1; }
    .a-card .a-meta { display: flex; gap: 12px; margin-top: 5px; font-size: 0.73em; color: #94a3b8; }
    .a-card .a-meta span { display: flex; align-items: center; gap: 4px; }
    .badge-s {
        padding: 2px 10px; border-radius: 100px; font-size: 0.65em;
        font-weight: 700; white-space: nowrap; flex-shrink: 0;
    }
    .badge-s.b-yahoo { background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }
    .badge-s.b-pr { background: #f0f9ff; color: #0284c7; border: 1px solid #bae6fd; }

    /* Keyword Section Header */
    .kw-sec {
        display: flex; justify-content: space-between; align-items: center;
        padding: 10px 16px; background: #f8fafc; border-radius: 10px;
        margin: 14px 0 6px; border: 1px solid #e8eaf0;
    }
    .kw-sec .kw-n { font-weight: 700; color: #1e293b; font-size: 0.92em; }
    .kw-sec .kw-c {
        background: #6366f1; color: white; padding: 2px 10px;
        border-radius: 100px; font-size: 0.72em; font-weight: 700;
    }

    /* Empty */
    .empty { text-align: center; padding: 36px 20px; color: #94a3b8; }
    .empty .e-icon { font-size: 2.5em; margin-bottom: 8px; }

    /* Section label */
    .sec-label {
        font-size: 0.78em; font-weight: 700; color: #6366f1;
        text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px;
    }

    /* Date step indicators */
    .date-steps {
        display: flex; justify-content: space-between; padding: 0 4px;
        margin-top: -4px; margin-bottom: 8px;
    }
    .date-step {
        display: flex; flex-direction: column; align-items: center; gap: 2px;
    }
    .date-dot {
        width: 10px; height: 10px; border-radius: 50%;
        background: #cbd5e1; border: 2px solid #e2e8f0;
    }
    .date-dot.active { background: #6366f1; border-color: #6366f1; }
    .date-step-label { font-size: 0.6em; color: #94a3b8; font-weight: 600; }
    .date-step-label.active { color: #6366f1; font-weight: 700; }

    /* Streamlit Overrides */
    .stTextInput > div > div > input {
        border-radius: 10px; border: 2px solid #e2e8f0;
        padding: 8px 12px; font-size: 0.88em;
    }
    .stTextInput > div > div > input:focus {
        border-color: #6366f1; box-shadow: 0 0 0 3px rgba(99,102,241,0.1);
    }
    section[data-testid="stSidebar"] { background: #f8fafc; }

    @media (max-width: 768px) {
        .hero { padding: 18px 14px 14px; }
        .hero h1 { font-size: 1.15em; }
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

# --- Session State ---
if 'search_results' not in st.session_state:
    st.session_state.search_results = {}
if 'search_done' not in st.session_state:
    st.session_state.search_done = False
# Toggle states for keyword selection (search screen)
for kw in keywords:
    if f"sel_{kw}" not in st.session_state:
        st.session_state[f"sel_{kw}"] = False
# Toggle states for result visibility
if 'result_vis' not in st.session_state:
    st.session_state.result_vis = {}

# === HERO ===
st.markdown("""<div class="hero">
    <h1>📰 아이돌 뉴스 검색기</h1>
    <p>Yahoo News Japan & PR Times에서 실시간 아이돌 뉴스를 한눈에</p>
</div>""", unsafe_allow_html=True)

# ============================================================
# RESULT SCREEN (if search done)
# ============================================================
if st.session_state.search_done:
    results = st.session_state.search_results

    # Reset button
    if st.button("🔄 새로운 검색", key="reset_btn", use_container_width=True):
        st.session_state.search_done = False
        st.session_state.search_results = {}
        st.session_state.result_vis = {}
        st.rerun()

    if not results:
        st.markdown('<div class="empty"><div class="e-icon">🔍</div><p>검색된 기사가 없습니다</p></div>', unsafe_allow_html=True)
    else:
        all_articles = []
        for arts in results.values():
            all_articles.extend(arts)

        # Stats
        yahoo_n = sum(1 for a in all_articles if a['source'] == 'Yahoo')
        pr_n = sum(1 for a in all_articles if a['source'] == 'PR Times')
        st.markdown(f"""<div class="stats-row">
            <div class="stat-pill"><div class="sp-num">{len(all_articles)}</div><div class="sp-label">Total</div></div>
            <div class="stat-pill"><div class="sp-num c-yahoo">{yahoo_n}</div><div class="sp-label">Yahoo News</div></div>
            <div class="stat-pill"><div class="sp-num c-pr">{pr_n}</div><div class="sp-label">PR Times</div></div>
        </div>""", unsafe_allow_html=True)

        # Source filter
        src_filter = st.radio("소스 필터", ["전체", f"Yahoo ({yahoo_n})", f"PR Times ({pr_n})"],
                              horizontal=True, label_visibility="collapsed", key="src_filter")

        # --- Keyword Result Toggle Buttons ---
        if len(results) > 1:
            st.markdown('<div class="sec-label">키워드별 결과 필터</div>', unsafe_allow_html=True)

            # Init visibility for new results
            for kw in results:
                if kw not in st.session_state.result_vis:
                    st.session_state.result_vis[kw] = True

            # All ON / All OFF
            ctl1, ctl2, _ = st.columns([1, 1, 4])
            with ctl1:
                if st.button("전체 ON", key="r_all_on", use_container_width=True):
                    for kw in results:
                        st.session_state.result_vis[kw] = True
                    st.rerun()
            with ctl2:
                if st.button("전체 OFF", key="r_all_off", use_container_width=True):
                    for kw in results:
                        st.session_state.result_vis[kw] = False
                    st.rerun()

            # Toggle buttons grid
            kw_list = list(results.keys())
            cols_per_row = 5
            for row_start in range(0, len(kw_list), cols_per_row):
                row_kws = kw_list[row_start:row_start + cols_per_row]
                cols = st.columns(max(cols_per_row, len(row_kws)))
                for i, kw in enumerate(row_kws):
                    cnt = len(results[kw])
                    is_on = st.session_state.result_vis.get(kw, True)
                    label = f"{'🟢' if is_on else '⚫'} {kw} ({cnt})"
                    with cols[i]:
                        if st.button(label, key=f"rv_{kw}", use_container_width=True):
                            st.session_state.result_vis[kw] = not is_on
                            st.rerun()

        # --- Display Articles ---
        visible_kws = set()
        if len(results) > 1:
            for kw in results:
                if st.session_state.result_vis.get(kw, True):
                    visible_kws.add(kw)
        else:
            visible_kws = set(results.keys())

        if not visible_kws:
            st.markdown('<div class="empty"><div class="e-icon">👆</div><p>표시할 키워드를 선택하세요</p></div>', unsafe_allow_html=True)
        else:
            for kw in results:
                if kw not in visible_kws:
                    continue
                kw_articles = results[kw]

                # Source filter
                if "Yahoo" in src_filter:
                    kw_articles = [a for a in kw_articles if a['source'] == 'Yahoo']
                elif "PR Times" in src_filter:
                    kw_articles = [a for a in kw_articles if a['source'] == 'PR Times']

                if not kw_articles:
                    continue

                st.markdown(f"""<div class="kw-sec">
                    <span class="kw-n">{kw}</span>
                    <span class="kw-c">{len(kw_articles)}건</span>
                </div>""", unsafe_allow_html=True)

                for a in kw_articles:
                    render_card(a)

# ============================================================
# SEARCH SCREEN (initial)
# ============================================================
else:
    # === Controls: Source + Date ===
    c1, c2 = st.columns([1, 1])
    with c1:
        src = st.radio("🌐 검색 소스", ["Yahoo News", "PR Times", "둘 다"], horizontal=True, key="src_r")
    with c2:
        dm = st.radio("📅 기간 모드", ["누적 기간", "특정 날짜"], horizontal=True, key="dm_r")

    # Date selection with clear steps
    if dm == "누적 기간":
        cum_opts = ["오늘", "~1일", "~2일", "~3일", "~4일", "~5일", "~6일", "~7일"]
        cum_vals = [0, 1, 2, 3, 4, 5, 6, 7]
        sel = st.select_slider("기간 선택", options=cum_opts, value="~7일", key="cum_sl")
        dv = cum_vals[cum_opts.index(sel)]
        dmk = 'cumulative'
        today = datetime.date.today()
        ed = today - datetime.timedelta(days=dv)
        # Render date step dots
        dots_html = '<div class="date-steps">'
        for j, opt in enumerate(cum_opts):
            active = cum_opts.index(sel) >= j
            ac = ' active' if active else ''
            dots_html += f'<div class="date-step"><div class="date-dot{ac}"></div><div class="date-step-label{ac}">{opt}</div></div>'
        dots_html += '</div>'
        st.markdown(dots_html, unsafe_allow_html=True)
        info = f"{today.strftime('%m/%d')}" if dv == 0 else f"{ed.strftime('%m/%d')} ~ {today.strftime('%m/%d')}"
        st.caption(f"📌 검색 범위: **{info}**")
    else:
        sin_opts = ["오늘", "어제", "2일전", "3일전", "4일전", "5일전", "6일전", "7일전"]
        sin_vals = [0, 1, 2, 3, 4, 5, 6, 7]
        sel = st.select_slider("날짜 선택", options=sin_opts, value="오늘", key="sin_sl")
        dv = sin_vals[sin_opts.index(sel)]
        dmk = 'single'
        td = datetime.date.today() - datetime.timedelta(days=dv)
        # Render date step dots
        dots_html = '<div class="date-steps">'
        for j, opt in enumerate(sin_opts):
            active = sin_opts.index(sel) == j
            ac = ' active' if active else ''
            dots_html += f'<div class="date-step"><div class="date-dot{ac}"></div><div class="date-step-label{ac}">{opt}</div></div>'
        dots_html += '</div>'
        st.markdown(dots_html, unsafe_allow_html=True)
        st.caption(f"📌 검색 날짜: **{td.strftime('%Y/%m/%d')}**")

    dates = get_date_range(dmk, dv)

    st.markdown("---")

    # === Search Mode ===
    search_mode = st.radio("검색 방법", ["📋 전체 검색", "🔍 개별 선택", "✏️ 직접 입력"],
                           horizontal=True, label_visibility="collapsed", key="sm_r")

    # ---- 전체 검색 ----
    if search_mode == "📋 전체 검색":
        st.info(f"등록된 **{len(keywords)}개** 키워드를 한 번에 검색합니다.")
        if st.button("🔍 전체 검색 시작", key="search_all_btn", use_container_width=True):
            all_results = {}
            prog = st.progress(0)
            stat = st.empty()
            for i, kw in enumerate(keywords):
                stat.markdown(f"**`{kw}`** 검색 중... ({i+1}/{len(keywords)})")
                arts = search_all(kw, dates, src)
                if arts:
                    all_results[kw] = arts
                prog.progress((i + 1) / len(keywords))
            stat.empty()
            prog.empty()
            st.session_state.search_results = all_results
            st.session_state.result_vis = {kw: True for kw in all_results}
            st.session_state.search_done = True
            st.rerun()

    # ---- 개별 선택 ----
    elif search_mode == "🔍 개별 선택":
        st.markdown('<div class="sec-label">키워드를 클릭하여 선택/해제</div>', unsafe_allow_html=True)

        # All ON / All OFF
        ctl1, ctl2, ctl3 = st.columns([1, 1, 4])
        with ctl1:
            if st.button("전체 선택", key="s_all_on", use_container_width=True):
                for kw in keywords:
                    st.session_state[f"sel_{kw}"] = True
                st.rerun()
        with ctl2:
            if st.button("전체 해제", key="s_all_off", use_container_width=True):
                for kw in keywords:
                    st.session_state[f"sel_{kw}"] = False
                st.rerun()
        with ctl3:
            sel_cnt = sum(1 for kw in keywords if st.session_state.get(f"sel_{kw}", False))
            st.caption(f"선택: **{sel_cnt}** / {len(keywords)}")

        # Keyword toggle button grid
        cols_per_row = 5
        for row_start in range(0, len(keywords), cols_per_row):
            row_kws = keywords[row_start:row_start + cols_per_row]
            cols = st.columns(cols_per_row)
            for i, kw in enumerate(row_kws):
                is_on = st.session_state.get(f"sel_{kw}", False)
                label = f"{'🟢' if is_on else '⚫'} {kw}"
                with cols[i]:
                    if st.button(label, key=f"sel_btn_{kw}", use_container_width=True):
                        st.session_state[f"sel_{kw}"] = not is_on
                        st.rerun()

        # Search button
        selected = [kw for kw in keywords if st.session_state.get(f"sel_{kw}", False)]
        if selected:
            if st.button(f"🔍 선택한 {len(selected)}개 키워드 검색", key="search_sel_btn", use_container_width=True):
                all_results = {}
                prog = st.progress(0)
                stat = st.empty()
                for i, kw in enumerate(selected):
                    stat.markdown(f"**`{kw}`** 검색 중... ({i+1}/{len(selected)})")
                    arts = search_all(kw, dates, src)
                    if arts:
                        all_results[kw] = arts
                    prog.progress((i + 1) / len(selected))
                stat.empty()
                prog.empty()
                st.session_state.search_results = all_results
                st.session_state.result_vis = {kw: True for kw in all_results}
                st.session_state.search_done = True
                st.rerun()
        else:
            st.caption("👆 검색할 키워드를 선택하세요")

    # ---- 직접 입력 ----
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
            st.session_state.result_vis = {kw: True} if arts else {}
            st.session_state.search_done = True
            st.rerun()
