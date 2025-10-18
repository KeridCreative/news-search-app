# 📰 뉴스 검색기

Yahoo News Japan과 PR Times에서 아이돌 뉴스를 검색하는 웹 애플리케이션입니다.

## 🌟 기능

- **Yahoo News 검색**: 일본 야후 뉴스에서 최신 뉴스 검색
- **PR Times 검색**: 프레스 릴리즈 사이트에서 공식 뉴스 검색
- **동시/선택 검색**: 두 사이트를 동시에 또는 선택적으로 검색
- **날짜 필터**: 오늘, 어제, 2-3일 전, 전체(7일) 단위로 필터링
- **배치 검색**: 29개의 등록된 키워드를 한 번에 검색

## 🚀 온라인 사용

[Streamlit Cloud에서 바로 사용하기](https://news-search-app-keridcreative.streamlit.app)

## 💻 로컬 실행

### 요구사항
- Python 3.8+
- pip

### 설치 및 실행

```bash
# 저장소 클론
git clone https://github.com/KeridCreative/news-search-app.git
cd news-search-app

# 필요한 패키지 설치
pip install -r requirements.txt

# Streamlit 앱 실행
streamlit run streamlit_app.py
```

## 📋 키워드

기본 등록 키워드:
- 乃木坂 (노기자카)
- 櫻坂 (사쿠라자카)
- 日向坂 (히나타자카)
- AKB48
- HKT48
- STU48
- NMB48
- SKE48
- NGT48
- 그 외 26개

`keywords.json` 파일을 수정하여 키워드를 추가/변경할 수 있습니다.

## 🔧 기술 스택

- **Frontend**: Streamlit
- **Backend**: Python
- **Web Scraping**: BeautifulSoup4, Requests
- **Deployment**: Streamlit Cloud

## 📝 라이선스

MIT License

## 👤 작성자

KeridCreative
