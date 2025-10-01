# 이것마저 테스트 파일임

import feedparser
import urllib.request
import ssl
import requests
from bs4 import BeautifulSoup
from load_pgvector import save_to_db, save_to_json
import re


context = ssl._create_unverified_context()

CATEGORY_RSS = {
    "최신": "https://www.yna.co.kr/rss/news.xml",
    "정치": "https://www.yna.co.kr/rss/politics.xml",
    "북한": "https://www.yna.co.kr/rss/northkorea.xml",
    "경제": "https://www.yna.co.kr/rss/economy.xml",
    "마켓+": "https://www.yna.co.kr/rss/market.xml",
    "산업": "https://www.yna.co.kr/rss/industry.xml",
    "사회": "https://www.yna.co.kr/rss/society.xml",
    "전국": "https://www.yna.co.kr/rss/local.xml",
    "세계": "https://www.yna.co.kr/rss/international.xml",
    "문화": "https://www.yna.co.kr/rss/culture.xml",
    "건강": "https://www.yna.co.kr/rss/health.xml",
    "연예": "https://www.yna.co.kr/rss/entertainment.xml",
    "스포츠": "https://www.yna.co.kr/rss/sports.xml",
    "오피니언": "https://www.yna.co.kr/rss/opinion.xml",
    "사람들": "https://www.yna.co.kr/rss/people.xml"
}


# rss
def fetch_rss(rss_url):
    req = urllib.request.Request(
        rss_url,
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    with urllib.request.urlopen(req, context=context) as response:
        data = response.read()
    return feedparser.parse(data)


# 파싱
def crawl_article(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    origin = soup.select_one('.story-news')

    content = ""
    sub_title = origin.find_all('h2')
    lines = origin.find_all('p')
    for tag in sub_title:
        content += tag.get_text(strip=True) + " "
    
    for tag in lines:
        if not tag.attrs:
            content += tag.get_text(strip=True) + " "

    return content if len(content) > 0 else "본문 없음"


# 기자 이름 빼낼 정규식
def extract_writer(content):
    match = re.search(r'([가-힣]{2,4})\s?기자', content)
    return match.group(1) if match else "연합뉴스"


def enrich_article(entry, category="일반"):
    content = crawl_article(entry.link)
    result = {
        'title': entry.title,
        'write_date': entry.published,
        'content': content,
        'url': entry.link   # 'url' 필드로 맞춤
    }

    return result


def main():
    news_data = []

    for category, url in CATEGORY_RSS.items():
        print(f"[{category}] 뉴스 수집 중...")

        feed = fetch_rss(url)
        for entry in feed.entries:

            article = enrich_article(entry, category)  # 안전한 구조 사용
            news_data.append(article)
        break

    # save_to_db(news_data)
    # save_to_json(news_data)

if __name__ == "__main__":
    main()