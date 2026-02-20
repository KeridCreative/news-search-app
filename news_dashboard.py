#!/usr/bin/env python3
"""
아이돌 뉴스 대시보드 - 로컬 전용
검색 → 평가 → 선택 → 스크립트 생성 요청까지 원스톱 UI

실행: streamlit run news_dashboard.py
"""

import streamlit as st
import json
import os
import datetime
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(BASE_DIR, 'news_results')
NEWS_DIR = os.path.join(BASE_DIR, 'news')
GUIDE_FILE = os.path.join(NEWS_DIR, '뉴스생성가이드.txt')

st.set_page_config(
    page_title="아이돌 뉴스 대시보드",
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS ──
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    .stApp { font-family: 'Inter', -apple-system, sans-serif; background: #0f172a; color: #e2e8f0; }
    #MainMenu, footer, header { visibility: hidden; }

    .dash-hero {
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        border-radius: 16px; padding: 24px; margin-bottom: 16px;
        color: white; position: relative; overflow: hidden;
    }
    .dash-hero::after {
        content: ''; position: absolute; width: 140px; height: 140px;
        background: rgba(255,255,255,0.06); border-radius: 50%; top: -30px; right: -20px;
    }
    .dash-hero h1 { font-size: 1.4em; font-weight: 800; margin: 0; position: relative; }
    .dash-hero p { font-size: 0.8em; opacity: 0.7; margin: 4px 0 0; position: relative; }

    .stat-row { display: flex; gap: 10px; margin-bottom: 14px; }
    .stat-box {
        flex: 1; background: #1e293b; border: 1px solid #334155;
        border-radius: 12px; padding: 14px; text-align: center;
    }
    .stat-box .num { font-size: 1.8em; font-weight: 800; color: #a78bfa; }
    .stat-box .label { font-size: 0.65em; color: #64748b; text-transform: uppercase; letter-spacing: 1px; margin-top: 2px; }

    .news-card {
        background: #1e293b; border: 1px solid #334155; border-radius: 12px;
        padding: 16px; margin-bottom: 8px; transition: all 0.15s;
        border-left: 4px solid transparent;
    }
    .news-card:hover { border-color: #6366f1; transform: translateX(2px); }
    .news-card.rank-1 { border-left-color: #f59e0b; background: #1e293b; }
    .news-card.rank-2 { border-left-color: #94a3b8; }
    .news-card.rank-3 { border-left-color: #b45309; }
    .news-card .card-top { display: flex; justify-content: space-between; align-items: flex-start; gap: 10px; }
    .news-card .card-title { flex: 1; font-size: 0.9em; font-weight: 600; color: #f1f5f9; line-height: 1.5; }
    .news-card .card-title a { color: inherit; text-decoration: none; }
    .news-card .card-title a:hover { color: #a78bfa; }
    .news-card .card-meta { display: flex; gap: 14px; margin-top: 6px; font-size: 0.72em; color: #64748b; }
    .score-badge {
        padding: 3px 12px; border-radius: 100px; font-size: 0.75em;
        font-weight: 700; white-space: nowrap; flex-shrink: 0;
    }
    .score-high { background: #7c3aed22; color: #a78bfa; border: 1px solid #7c3aed44; }
    .score-mid { background: #0ea5e922; color: #38bdf8; border: 1px solid #0ea5e944; }
    .score-low { background: #64748b22; color: #94a3b8; border: 1px solid #64748b44; }
    .cat-badge {
        padding: 2px 8px; border-radius: 6px; font-size: 0.65em; font-weight: 600;
        background: #334155; color: #94a3b8; white-space: nowrap;
    }
    .src-badge {
        padding: 2px 8px; border-radius: 100px; font-size: 0.6em; font-weight: 700;
    }
    .src-yahoo { background: #dc262622; color: #f87171; border: 1px solid #dc262644; }
    .src-pr { background: #0284c722; color: #38bdf8; border: 1px solid #0284c744; }

    .section-label {
        font-size: 0.75em; font-weight: 700; color: #6366f1;
        text-transform: uppercase; letter-spacing: 1.5px; margin: 18px 0 8px;
    }

    section[data-testid="stSidebar"] { background: #1e293b; }
    section[data-testid="stSidebar"] .stMarkdown { color: #e2e8f0; }

    .script-box {
        background: #0f172a; border: 1px solid #334155; border-radius: 10px;
        padding: 16px; margin: 8px 0; font-family: 'Inter', monospace;
        font-size: 0.85em; line-height: 1.7; color: #cbd5e1; white-space: pre-wrap;
    }
</style>
""", unsafe_allow_html=True)


# ── Helper Functions ──

def get_available_dates():
    """news_results 폴더에서 사용 가능한 날짜 목록"""
    if not os.path.exists(RESULTS_DIR):
        return []
    dates = []
    for f in sorted(os.listdir(RESULTS_DIR), reverse=True):
        if f.endswith('_evaluated.json'):
            dates.append(f.replace('_evaluated.json', ''))
    return dates


def load_evaluated(date_str):
    """평가 결과 로드"""
    path = os.path.join(RESULTS_DIR, f"{date_str}_evaluated.json")
    if not os.path.exists(path):
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_raw(date_str):
    """원본 검색 결과 로드"""
    path = os.path.join(RESULTS_DIR, f"{date_str}.json")
    if not os.path.exists(path):
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def run_scanner():
    """스캐너 + 평가기 실행"""
    scanner = os.path.join(BASE_DIR, 'news_scanner.py')
    evaluator = os.path.join(BASE_DIR, 'news_evaluator.py')
    result1 = subprocess.run([sys.executable, scanner], capture_output=True, text=True, cwd=BASE_DIR)
    result2 = subprocess.run([sys.executable, evaluator], capture_output=True, text=True, cwd=BASE_DIR)
    return result1.stdout + "\n" + result2.stdout, result1.stderr + result2.stderr


def score_class(score):
    if score >= 8: return 'score-high'
    if score >= 6: return 'score-mid'
    return 'score-low'


def rank_class(i):
    if i == 0: return 'rank-1'
    if i == 1: return 'rank-2'
    if i == 2: return 'rank-3'
    return ''


def render_news_card(article, index):
    s = article.get('source', 'Yahoo')
    sc = article.get('score', 5)
    cat = article.get('category', '기타')
    src_cls = 'src-yahoo' if s == 'Yahoo' else 'src-pr'
    rank_emoji = ['🥇','🥈','🥉'][index] if index < 3 else f'{index+1}.'

    st.markdown(f"""<div class="news-card {rank_class(index)}">
        <div class="card-top">
            <div class="card-title">
                {rank_emoji} <a href="{article['link']}" target="_blank">{article['title']}</a>
            </div>
            <span class="score-badge {score_class(sc)}">{sc}점</span>
        </div>
        <div class="card-meta">
            <span class="cat-badge">{cat}</span>
            <span class="src-badge {src_cls}">{s}</span>
            <span>📰 {article.get('media','')}</span>
            <span>🕐 {article.get('publish_time','')}</span>
            <span>🔑 {article.get('keyword','')}</span>
        </div>
    </div>""", unsafe_allow_html=True)


def get_next_news_number():
    """news/ 폴더에서 다음 번호"""
    if not os.path.exists(NEWS_DIR):
        return 1
    nums = []
    for f in os.listdir(NEWS_DIR):
        m = __import__('re').match(r'^(\d+)\.', f)
        if m:
            nums.append(int(m.group(1)))
    return max(nums) + 1 if nums else 1


def generate_script_prompt(article, version='short'):
    """스크립트 생성용 프롬프트 구성"""
    if version == 'short':
        length = "500자"
        structure = """<앵커>
[1-2문장] 뉴스 요지

<리포터>
[핵심 사실 300-350자]

<앵커>
[1문장] 마무리 + "이상, 에이미가 전해드렸습니다."
"""
    else:
        length = "700자"
        structure = """<앵커>
[2문장] 뉴스 요지 + 의미 부여

<리포터>
[핵심 사실 + 배경 500-550자]
- 구체적 수치/기록
- 그룹/멤버 배경 정보
- 인용문 (1-2개)
- 향후 일정/전망

<앵커>
[2문장] 의미 정리 + 기대감 + "이상, 에이미가 전해드렸습니다."
"""
    prompt = f"""아래 기사를 {length} 분량의 아이돌 뉴스 스크립트로 작성해줘.

[기사 정보]
제목: {article['title']}
출처: {article.get('media','')} ({article.get('source','')})
날짜: {article.get('publish_time','')}
링크: {article.get('link','')}
키워드: {article.get('keyword','')}
카테고리: {article.get('category','')}

[스크립트 구조]
{structure}

[규칙]
- 톤: 친근하고 따뜻하게, 존경과 응원
- 금지: 비하, 과장, 추측, 팬커뮤니티 속어
- 필수: 구체적 수치, 날짜, 인용문(가능시)
- 리포터 음성: 35세 일본 남성 아나운서, 뉴스 엔터테인먼트 톤, 110% 속도
"""
    return prompt


# ══════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════
with st.sidebar:
    st.markdown("### ⚙️ 컨트롤")

    # 스캔 실행 버튼
    if st.button("🔄 지금 스캔 실행", use_container_width=True):
        with st.spinner("검색 중... (1~2분 소요)"):
            stdout, stderr = run_scanner()
        st.success("스캔 완료!")
        if stderr:
            with st.expander("에러 로그"):
                st.code(stderr[:2000])
        st.rerun()

    st.markdown("---")

    # 날짜 선택
    dates = get_available_dates()
    if dates:
        selected_date = st.selectbox("📅 날짜 선택", dates, index=0)
    else:
        selected_date = None
        st.warning("스캔 결과가 없습니다. '지금 스캔 실행'을 눌러주세요.")

    st.markdown("---")

    # 필터
    st.markdown("### 🔍 필터")
    min_score = st.slider("최소 점수", 1, 10, 5)
    source_filter = st.radio("소스", ["전체", "Yahoo", "PR Times"])

    st.markdown("---")

    # 선택된 기사 표시
    if 'selected_articles' not in st.session_state:
        st.session_state.selected_articles = []

    sel_count = len(st.session_state.selected_articles)
    st.markdown(f"### 📋 선택된 기사: **{sel_count}**건")
    if sel_count > 0:
        if st.button("🗑️ 선택 초기화", use_container_width=True):
            st.session_state.selected_articles = []
            st.rerun()


# ══════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════

# Hero
st.markdown("""<div class="dash-hero">
    <h1>🎤 아이돌 뉴스 대시보드</h1>
    <p>뉴스 검색 → 가치 평가 → 스크립트 생성 원스톱 시스템</p>
</div>""", unsafe_allow_html=True)

if not selected_date:
    st.info("왼쪽 사이드바에서 '지금 스캔 실행'을 눌러 시작하세요.")
    st.stop()

# 데이터 로드
eval_data = load_evaluated(selected_date)
raw_data = load_raw(selected_date)

if not eval_data:
    st.warning(f"{selected_date}의 평가 결과가 없습니다. 평가기를 실행하세요.")
    st.stop()

articles = eval_data.get('ranked_articles', [])

# 필터 적용
filtered = [a for a in articles if a.get('score', 0) >= min_score]
if source_filter == "Yahoo":
    filtered = [a for a in filtered if a.get('source') == 'Yahoo']
elif source_filter == "PR Times":
    filtered = [a for a in filtered if a.get('source') == 'PR Times']

# 통계
total = len(articles)
yahoo_n = sum(1 for a in articles if a.get('source') == 'Yahoo')
pr_n = sum(1 for a in articles if a.get('source') == 'PR Times')
high_n = sum(1 for a in articles if a.get('score', 0) >= 8)

st.markdown(f"""<div class="stat-row">
    <div class="stat-box"><div class="num">{total}</div><div class="label">전체 기사</div></div>
    <div class="stat-box"><div class="num" style="color:#f87171">{yahoo_n}</div><div class="label">Yahoo</div></div>
    <div class="stat-box"><div class="num" style="color:#38bdf8">{pr_n}</div><div class="label">PR Times</div></div>
    <div class="stat-box"><div class="num" style="color:#f59e0b">{high_n}</div><div class="label">High Value (8+)</div></div>
</div>""", unsafe_allow_html=True)

# ── 탭 ──
tab1, tab2, tab3 = st.tabs(["🏆 뉴스 순위", "📝 스크립트 생성", "📊 키워드별"])

# ── TAB 1: 뉴스 순위 ──
with tab1:
    st.markdown(f'<div class="section-label">검색 결과 ({len(filtered)}건 표시 / 전체 {total}건)</div>', unsafe_allow_html=True)

    for i, article in enumerate(filtered[:50]):
        col1, col2 = st.columns([20, 1])
        with col1:
            render_news_card(article, i)
        with col2:
            article_key = article.get('title', '')[:50]
            is_selected = article_key in [a.get('title', '')[:50] for a in st.session_state.selected_articles]
            btn_label = "✅" if is_selected else "➕"
            if st.button(btn_label, key=f"sel_{i}", help="스크립트 생성 목록에 추가/제거"):
                if is_selected:
                    st.session_state.selected_articles = [
                        a for a in st.session_state.selected_articles
                        if a.get('title', '')[:50] != article_key
                    ]
                else:
                    st.session_state.selected_articles.append(article)
                st.rerun()

# ── TAB 2: 스크립트 생성 ──
with tab2:
    st.markdown('<div class="section-label">스크립트 생성</div>', unsafe_allow_html=True)

    # 자동 선택: 선택된 기사가 없으면 상위 2개
    target_articles = st.session_state.selected_articles if st.session_state.selected_articles else filtered[:2]

    if not target_articles:
        st.info("뉴스 순위 탭에서 기사를 선택하거나, 스캔 결과가 있으면 상위 2개가 자동 선택됩니다.")
        st.stop()

    st.markdown(f"**생성 대상: {len(target_articles)}건** {'(자동 선택: 상위 2개)' if not st.session_state.selected_articles else '(수동 선택)'}")

    for idx, article in enumerate(target_articles):
        with st.expander(f"{'🥇🥈🥉'[idx] if idx < 3 else '📰'} [{article.get('score',5)}점] {article['title'][:50]}...", expanded=(idx < 2)):
            st.markdown(f"**출처:** {article.get('media','')} ({article.get('source','')}) | **키워드:** {article.get('keyword','')}")
            st.markdown(f"**링크:** [{article['title'][:30]}...]({article.get('link','')})")

            st.markdown("---")

            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("**📋 속보 버전 (500자) 프롬프트:**")
                prompt_short = generate_script_prompt(article, 'short')
                st.code(prompt_short, language=None)
                st.button("📎 복사용 팝업", key=f"copy_short_{idx}", help="위 프롬프트를 Claude/ChatGPT에 붙여넣기")

            with col_b:
                st.markdown("**📋 상세 버전 (700자) 프롬프트:**")
                prompt_long = generate_script_prompt(article, 'long')
                st.code(prompt_long, language=None)
                st.button("📎 복사용 팝업", key=f"copy_long_{idx}", help="위 프롬프트를 Claude/ChatGPT에 붙여넣기")

    st.markdown("---")
    st.markdown("""
    💡 **사용법:**
    1. 위 프롬프트를 복사하세요
    2. Claude, ChatGPT 등 AI에 붙여넣기
    3. 생성된 스크립트를 `news/` 폴더에 저장
    4. 또는 Cowork에서 "이 기사로 뉴스 만들어줘"라고 요청
    """)


# ── TAB 3: 키워드별 ──
with tab3:
    st.markdown('<div class="section-label">키워드별 기사 분포</div>', unsafe_allow_html=True)

    # 키워드별 집계
    kw_stats = {}
    for a in articles:
        kw = a.get('keyword', '기타')
        if kw not in kw_stats:
            kw_stats[kw] = {'count': 0, 'max_score': 0, 'articles': []}
        kw_stats[kw]['count'] += 1
        kw_stats[kw]['max_score'] = max(kw_stats[kw]['max_score'], a.get('score', 0))
        kw_stats[kw]['articles'].append(a)

    # 최고 점수 순 정렬
    sorted_kws = sorted(kw_stats.items(), key=lambda x: x[1]['max_score'], reverse=True)

    for kw, stats in sorted_kws:
        with st.expander(f"**{kw}** — {stats['count']}건 (최고 {stats['max_score']}점)"):
            for a in sorted(stats['articles'], key=lambda x: x.get('score', 0), reverse=True)[:10]:
                sc = a.get('score', 5)
                s = a.get('source', '')
                st.markdown(f"- **[{sc}점]** [{s}] {a['title'][:60]}... _{a.get('media','')}_")
