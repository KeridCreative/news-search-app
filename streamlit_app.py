import streamlit as st
import requests
from bs4 import BeautifulSoup
import datetime
import re
import json


# 페이지 설정
st.set_page_config(
    page_title="📰 뉴스 검색기",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main { max-width: 1200px; }
    </style>
""", unsafe_allow_html=True)


# 암호 인증 기능
def check_password():
    """암호 입력 확인"""
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    
    if st.session_state.password_correct:
        return True
    
    # 암호 입력 페이지
    st.title("🔐 접근 권한")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("암호를 입력하세요")
        password = st.text_input(
            "암호",
            type="password",
            placeholder="숫자로 입력하세요"
        )
        
        if st.button("입력", use_container_width=True):
            if password == "0708":
                st.session_state.password_correct = True
                st.success("✅ 접근 승인되었습니다!")
                st.rerun()
            else:
                st.error("❌ 암호가 잘못되었습니다.")
    
    st.stop()


# 암호 확인
check_password()


def load_keywords():
    """키워드 파일에서 검색어를 불러옵니다."""
    try:
        with open('keywords.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("search_keyword", [])
    except:
        return ['乃木坂', '櫻坂', '日向坂', 'AKB', 'HKT']


def format_date_japanese(date):
    """날짜를 M/D 형식으로 변환합니다."""
    return f"{date.month}/{date.day}"


def get_date_range(days_ago):
    """지정된 날짜 범위를 반환합니다."""
    if days_ago == 'all':
        return [datetime.date.today() - datetime.timedelta(days=i) for i in range(7)]
    else:
        return [datetime.date.today() - datetime.timedelta(days=int(days_ago))]


def scrape_yahoo_news(keyword, days_ago='0'):
    """Yahoo News Japan에서 키워드를 검색합니다."""
    url = f"https://news.yahoo.co.jp/search?p={keyword}&rkf=2&ei=UTF-8"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }
    
    found_articles = []
    target_dates = get_date_range(days_ago)
    target_date_strs = [format_date_japanese(d) for d in target_dates]
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = soup.find_all('li', class_='sc-1u4589e-0')
        
        for article in articles:
            date_element = article.find('time')
            if not date_element:
                continue

            date_text = date_element.text
            match = re.search(r'(\d{1,2}/\d{1,2})', date_text)

            if match:
                if days_ago == '0':
                    if match.group(1) not in target_date_strs:
                        continue
                
                title_element = article.find('div', class_='sc-3ls169-0')
                link_element = article.find('a')
                media_element = article.find('span')

                if title_element and link_element:
                    found_articles.append({
                        'title': title_element.text.strip(),
                        'link': link_element.get('href', '#'),
                        'media': media_element.text.strip() if media_element else 'N/A',
                        'publish_time': date_text.strip(),
                        'source': 'Yahoo News'
                    })

    except Exception as e:
        st.error(f"Yahoo News 검색 오류: {e}")
    
    found_articles.sort(key=lambda x: x['publish_time'], reverse=True)
    return found_articles


def scrape_prtimes(keyword, days_ago='0'):
    """PR Times에서 키워드를 검색합니다."""
    search_keyword = keyword.replace(' ', '+')
    url = f"https://prtimes.jp/main/action.php?run=html&page=searchkey&search_word={search_keyword}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }
    
    found_articles = []
    target_dates = get_date_range(days_ago)
    target_date_strs = [format_date_japanese(d) for d in target_dates]
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        article_links = soup.find_all('a', class_='release-card_link__ssvnv')
        
        for link_elem in article_links:
            try:
                title_elem = link_elem.find('h3', class_='release-card_title__WLzWi')
                title = title_elem.text.strip() if title_elem else ""
                link = link_elem.get('href', '#')
                
                time_elem = link_elem.find('time')
                time_text = time_elem.text.strip() if time_elem else ""
                
                date_text = ""
                
                if '年' in time_text:
                    match = re.search(r'(\d+)年(\d+)月(\d+)日', time_text)
                    if match:
                        year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
                        try:
                            date_obj = datetime.date(year, month, day)
                            date_text = format_date_japanese(date_obj)
                        except:
                            pass
                elif '時間前' in time_text:
                    date_text = format_date_japanese(datetime.date.today())
                elif '日前' in time_text:
                    match = re.search(r'(\d+)日前', time_text)
                    if match:
                        days_before = int(match.group(1))
                        date_text = format_date_japanese(datetime.date.today() - datetime.timedelta(days=days_before))
                else:
                    date_text = format_date_japanese(datetime.date.today())
                
                if not date_text or date_text not in target_date_strs:
                    continue
                
                article = link_elem.parent
                while article and article.name != 'article':
                    article = article.parent
                
                company_link = article.find('a', class_='release-card_companyLink__jRgSJ') if article else None
                company = company_link.text.strip() if company_link else 'PR Times'
                
                found_articles.append({
                    'title': title,
                    'link': link if link.startswith('http') else f"https://prtimes.jp{link}",
                    'media': company,
                    'publish_time': time_text,
                    'source': 'PR Times'
                })
            except:
                continue
    
    except Exception as e:
        st.error(f"PR Times 검색 오류: {e}")
    
    found_articles.sort(key=lambda x: x['publish_time'], reverse=True)
    return found_articles


def display_articles(articles):
    """기사 목록을 표시합니다."""
    if not articles:
        st.info("검색된 기사가 없습니다.")
        return
    
    for article in articles:
        with st.container():
            col1, col2 = st.columns([4, 1])
            
            with col1:
                st.markdown(f"[**{article['title']}**]({article['link']})")
                col_a, col_b = st.columns(2)
                with col_a:
                    st.caption(f"📺 {article['media']}")
                with col_b:
                    st.caption(f"🕐 {article['publish_time']}")
            
            with col2:
                badge_color = "#FF6B6B" if article['source'] == "Yahoo News" else "#4ECDC4"
                st.markdown(f"<span style='background-color:{badge_color}; color:white; padding:5px 10px; border-radius:5px; font-size:0.8em;'>{article['source']}</span>", unsafe_allow_html=True)
            
            st.divider()


# 메인 앱
st.title("📰 뉴스 검색기")
st.markdown("Yahoo News & PR Times에서 뉴스를 검색하세요")

# 사이드바 설정
with st.sidebar:
    st.header("⚙️ 검색 설정")
    
    date_options = [
        ("오늘", "0"),
        ("어제", "1"),
        ("2일 전", "2"),
        ("3일 전", "3"),
        ("전체 (7일)", "all")
    ]
    date_selected = st.selectbox(
        "📅 검색 기간",
        range(len(date_options)),
        format_func=lambda i: date_options[i][0]
    )
    days_ago = date_options[date_selected][1]
    
    source_options = [
        ("🔀 둘 다", "both"),
        ("🔔 Yahoo News만", "yahoo"),
        ("📢 PR Times만", "prtimes")
    ]
    source_selected = st.selectbox(
        "📡 검색 소스",
        range(len(source_options)),
        format_func=lambda i: source_options[i][0]
    )
    source = source_options[source_selected][1]

# 메인 콘텐츠
tab1, tab2, tab3 = st.tabs(["🔍 키워드 검색", "📝 새 키워드", "🌐 전체 검색"])

with tab1:
    st.subheader("등록된 키워드로 검색")
    keywords = load_keywords()
    
    selected_keyword = st.selectbox("키워드 선택", keywords, key="keyword_select")
    
    if st.button("🔍 검색", key="search_btn1"):
        with st.spinner("검색 중..."):
            yahoo_results = [] if source == 'prtimes' else scrape_yahoo_news(selected_keyword, days_ago)
            prtimes_results = [] if source == 'yahoo' else scrape_prtimes(selected_keyword, days_ago)
            all_results = yahoo_results + prtimes_results
        
        st.success(f"'{selected_keyword}' 검색 완료!")
        st.metric("총 기사 수", len(all_results), f"Yahoo: {len(yahoo_results)} | PR Times: {len(prtimes_results)}")
        
        if source == 'both' and (yahoo_results or prtimes_results):
            result_tab1, result_tab2, result_tab3 = st.tabs(["📄 전체", "🔔 Yahoo", "📢 PR Times"])
            with result_tab1:
                display_articles(all_results)
            with result_tab2:
                display_articles(yahoo_results)
            with result_tab3:
                display_articles(prtimes_results)
        else:
            display_articles(all_results)

with tab2:
    st.subheader("새로운 키워드로 검색")
    new_keyword = st.text_input("키워드 입력", placeholder="예: AKB48, 乃木坂...")
    
    if st.button("🔍 검색", key="search_btn2"):
        if new_keyword:
            with st.spinner("검색 중..."):
                yahoo_results = [] if source == 'prtimes' else scrape_yahoo_news(new_keyword, days_ago)
                prtimes_results = [] if source == 'yahoo' else scrape_prtimes(new_keyword, days_ago)
                all_results = yahoo_results + prtimes_results
            
            st.success(f"'{new_keyword}' 검색 완료!")
            st.metric("총 기사 수", len(all_results), f"Yahoo: {len(yahoo_results)} | PR Times: {len(prtimes_results)}")
            
            if source == 'both' and (yahoo_results or prtimes_results):
                result_tab1, result_tab2, result_tab3 = st.tabs(["📄 전체", "🔔 Yahoo", "📢 PR Times"])
                with result_tab1:
                    display_articles(all_results)
                with result_tab2:
                    display_articles(yahoo_results)
                with result_tab3:
                    display_articles(prtimes_results)
            else:
                display_articles(all_results)
        else:
            st.warning("키워드를 입력해주세요.")

with tab3:
    st.subheader("모든 키워드 검색")
    keywords = load_keywords()
    
    if st.button(f"🔍 {len(keywords)}개 키워드 모두 검색", key="search_btn3"):
        with st.spinner("전체 검색 중..."):
            all_keywords_results = {}
            total_count = 0
            
            progress_bar = st.progress(0)
            for idx, keyword in enumerate(keywords):
                yahoo_results = [] if source == 'prtimes' else scrape_yahoo_news(keyword, days_ago)
                prtimes_results = [] if source == 'yahoo' else scrape_prtimes(keyword, days_ago)
                results = yahoo_results + prtimes_results
                
                if results:
                    all_keywords_results[keyword] = results
                    total_count += len(results)
                
                progress_bar.progress((idx + 1) / len(keywords))
        
        st.success(f"전체 검색 완료!")
        st.metric("총 기사 수", total_count)
        
        for keyword in keywords:
            if keyword in all_keywords_results:
                with st.expander(f"**{keyword}** ({len(all_keywords_results[keyword])}개)"):
                    display_articles(all_keywords_results[keyword])
