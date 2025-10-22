import streamlit as st
import requests
from bs4 import BeautifulSoup
import datetime
import re
import json


# ページ設定
st.set_page_config(
    page_title="📰 ニュース検索",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main { max-width: 1200px; }
    </style>
""", unsafe_allow_html=True)


# パスワード認証機能
def check_password():
    """パスワード入力確認"""
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    
    if st.session_state.password_correct:
        return True
    
    # パスワード入力ページ
    st.title("🔐 アクセス権限")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("パスワードを入力してください")
        password = st.text_input(
            "パスワード",
            type="password",
            placeholder="数字で入力してください"
        )
        
        if st.button("入力", use_container_width=True):
            if password == "0708":
                st.session_state.password_correct = True
                st.success("✅ アクセスが承認されました！")
                st.rerun()
            else:
                st.error("❌ パスワードが間違っています。")
    
    st.stop()


# パスワード確認
check_password()


def load_keywords():
    """キーワードファイルから検索語を読み込みます。"""
    try:
        with open('keywords.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("search_keyword", [])
    except:
        return ['乃木坂', '櫻坂', '日向坂', 'AKB', 'HKT']

def format_date_japanese(date):
    """日付をM/D形式に変換します。"""
    return f"{date.month}/{date.day}"

def get_date_range(days_ago):
    """指定された日付範囲を返します。"""
    if days_ago == 'all':
        return [datetime.date.today() - datetime.timedelta(days=i) for i in range(7)]
    else:
        return [datetime.date.today() - datetime.timedelta(days=int(days_ago))]

def scrape_yahoo_news(keyword, days_ago='0'):
    """Yahooニュースジャパンでキーワードを検索します。"""
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
        st.error(f"Yahooニュース検索エラー: {e}")
    
    found_articles.sort(key=lambda x: x['publish_time'], reverse=True)
    return found_articles

def scrape_prtimes(keyword, days_ago='0'):
    """PR Timesでキーワードを検索します。"""
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
        st.error(f"PR Times検索エラー: {e}")
    
    found_articles.sort(key=lambda x: x['publish_time'], reverse=True)
    return found_articles

def display_articles(articles):
    """記事リストを表示します。"""
    if not articles:
        st.info("検索された記事はありません。")
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


# メインアプリ
st.title("📰 ニュース検索")
st.markdown("Yahooニュース & PR Timesでニュースを検索")

# サイドバー設定
with st.sidebar:
    st.header("⚙️ 検索設定")
    
    date_options = [
        ("今日", "0"),
        ("昨日", "1"),
        ("2日前", "2"),
        ("3日前", "3"),
        ("全て (7日間)", "all")
    ]
    date_selected = st.selectbox(
        "📅 検索期間",
        range(len(date_options)),
        format_func=lambda i: date_options[i][0]
    )
    days_ago = date_options[date_selected][1]
    
    source_options = [
        ("🔀 両方", "both"),
        ("🔔 Yahooニュースのみ", "yahoo"),
        ("📢 PR Timesのみ", "prtimes")
    ]
    source_selected = st.selectbox(
        "📡 検索ソース",
        range(len(source_options)),
        format_func=lambda i: source_options[i][0]
    )
    source = source_options[source_selected][1]

# メインコンテンツ
tab1, tab2, tab3 = st.tabs(["🔍 キーワード検索", "📝 新しいキーワード", "🌐 全体検索"])

with tab1:
    st.subheader("登録済みキーワードで検索")
    keywords = load_keywords()
    
    selected_keyword = st.selectbox("キーワード選択", keywords, key="keyword_select")
    
    if st.button("🔍 検索", key="search_btn1"):
        with st.spinner("検索中..."):
            yahoo_results = [] if source == 'prtimes' else scrape_yahoo_news(selected_keyword, days_ago)
            prtimes_results = [] if source == 'yahoo' else scrape_prtimes(selected_keyword, days_ago)
            all_results = yahoo_results + prtimes_results
        
        st.success(f"'{selected_keyword}' 検索完了！")
        st.metric("合計記事数", len(all_results), f"Yahoo: {len(yahoo_results)} | PR Times: {len(prtimes_results)}")
        
        if source == 'both' and (yahoo_results or prtimes_results):
            result_tab1, result_tab2, result_tab3 = st.tabs(["📄 全て", "🔔 Yahoo", "📢 PR Times"])
            with result_tab1:
                display_articles(all_results)
            with result_tab2:
                display_articles(yahoo_results)
            with result_tab3:
                display_articles(prtimes_results)
        else:
            display_articles(all_results)

with tab2:
    st.subheader("新しいキーワードで検索")
    new_keyword = st.text_input("キーワード入力", placeholder="例: AKB48, 乃木坂...")
    
    if st.button("🔍 検索", key="search_btn2"):
        if new_keyword:
            with st.spinner("検索中..."):
                yahoo_results = [] if source == 'prtimes' else scrape_yahoo_news(new_keyword, days_ago)
                prtimes_results = [] if source == 'yahoo' else scrape_prtimes(new_keyword, days_ago)
                all_results = yahoo_results + prtimes_results
            
            st.success(f"'{new_keyword}' 検索完了！")
            st.metric("合計記事数", len(all_results), f"Yahoo: {len(yahoo_results)} | PR Times: {len(prtimes_results)}")
            
            if source == 'both' and (yahoo_results or prtimes_results):
                result_tab1, result_tab2, result_tab3 = st.tabs(["📄 全て", "🔔 Yahoo", "📢 PR Times"])
                with result_tab1:
                    display_articles(all_results)
                with result_tab2:
                    display_articles(yahoo_results)
                with result_tab3:
                    display_articles(prtimes_results)
            else:
                display_articles(all_results)
        else:
            st.warning("キーワードを入力してください。")

with tab3:
    st.subheader("全てのキーワードを検索")
    keywords = load_keywords()
    
    if st.button(f"🔍 {len(keywords)}個のキーワードを全て検索", key="search_btn3"):
        with st.spinner("全体検索中..."):
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
        
        st.success(f"全体検索完了！")
        st.metric("合計記事数", total_count)
        
        for keyword in keywords:
            if keyword in all_keywords_results:
                with st.expander(f"**{keyword}** ({len(all_keywords_results[keyword])}個)", expanded=True):
                    display_articles(all_keywords_results[keyword])
