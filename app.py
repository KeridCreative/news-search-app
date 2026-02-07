import requests
from bs4 import BeautifulSoup
import datetime
import re
import socket
import webbrowser
import threading
import json
import os
from flask import Flask, render_template, request, redirect, url_for


app = Flask(__name__)

# --- File Path --- (to make it runnable from anywhere)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KEYWORDS_FILE = os.path.join(BASE_DIR, 'keywords.json')

# --- Keyword Loading ---
def load_keywords():
    """Loads search keywords from the JSON file."""
    try:
        with open(KEYWORDS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("search_keyword", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []

# --- Date Calculation ---
def get_date_range(days_ago):
    """Returns a list of date strings for filtering."""
    if days_ago == 'all':
        # Return dates for the last 7 days
        return [datetime.date.today() - datetime.timedelta(days=i) for i in range(7)]
    else:
        # Return specific date
        return [datetime.date.today() - datetime.timedelta(days=int(days_ago))]

def format_date_japanese(date):
    """Formats date as M/D for Japanese format."""
    return f"{date.month}/{date.day}"

# --- Web Scraping Logic ---
def scrape_yahoo_news(keyword, days_ago='0'):
    """
    Scrapes Yahoo News Japan for a given keyword and returns a list of articles.
    days_ago: '0' (today), '1' (yesterday), '2' (2 days ago), '3' (3 days ago), or 'all'
    """
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
                        'date_match': match.group(1)
                    })

    except requests.exceptions.RequestException as e:
        print(f"Error fetching web page for keyword '{keyword}': {e}")
    except Exception as e:
        print(f"An unknown error occurred for keyword '{keyword}': {e}")
    
    # Sort by date (most recent first)
    found_articles.sort(key=lambda x: x['publish_time'], reverse=True)
    return found_articles

# --- Flask Routes ---

@app.route('/')
def index():
    keywords = load_keywords()
    return render_template('index.html', keywords=keywords)

@app.route('/search', methods=['POST'])
def search():
    search_type = request.form.get('search_type')
    days_ago = request.form.get('days_ago', '0')
    
    if search_type == 'select':
        keyword = request.form.get('keyword_select')
        articles = scrape_yahoo_news(keyword, days_ago)
        return render_template('results.html', 
                             keyword=keyword, 
                             articles=articles, 
                             days_ago=days_ago,
                             search_type='single')
    
    elif search_type == 'new':
        keyword = request.form.get('keyword_new')
        if not keyword:
            keywords = load_keywords()
            return render_template('index.html', keywords=keywords, error="키워드를 입력해주세요.")
        articles = scrape_yahoo_news(keyword, days_ago)
        return render_template('results.html', 
                             keyword=keyword, 
                             articles=articles, 
                             days_ago=days_ago,
                             search_type='single')

    elif search_type == 'all':
        keywords = load_keywords()
        all_results = {}
        total_count = 0
        for keyword in keywords:
            articles = scrape_yahoo_news(keyword, days_ago)
            if articles:  # Only include keywords with results
                all_results[keyword] = articles
                total_count += len(articles)
        return render_template('results.html', 
                             all_results=all_results, 
                             days_ago=days_ago,
                             search_type='all',
                             total_count=total_count)
    
    # Fallback
    return redirect(url_for('index'))

# --- Server and Port Logic ---

def find_free_port():
    """Finds a free port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]

def open_browser(port):
    """Opens the web browser to the given URL."""
    webbrowser.open(f'http://127.0.0.1:{port}')

if __name__ == '__main__':
    port = find_free_port()
    print(f" * 서버가 http://127.0.0.1:{port} 에서 실행됩니다.")
    print(f" * 브라우저를 자동으로 엽니다...")
    threading.Timer(1, lambda: open_browser(port)).start()
    app.run(host='127.0.0.1', port=port, debug=False)
