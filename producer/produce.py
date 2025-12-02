
import os
import json
import time
import logging
import csv
import feedparser
import urllib.request
import ssl
import requests
from bs4 import BeautifulSoup
import re
import signal
import sys
from kafka import KafkaProducer
from dotenv import load_dotenv
from datetime import datetime
from urllib.parse import quote

# 환경 변수 로드
load_dotenv()

# 통계 변수 (전역)
stats = {
    'total_sent': 0,
    'total_failed': 0,
    'start_time': None,
    'by_category': {}
}

# 로그 디렉토리 및 파일 경로
# Docker 환경에서는 /app/logs, 로컬에서는 ../logs 사용
LOG_DIR = os.getenv('LOG_DIR', '/app/logs')
LOG_FILE = os.path.join(LOG_DIR, 'producer_stats.csv')

# 로그 디렉토리 생성
try:
    os.makedirs(LOG_DIR, exist_ok=True)
except Exception as e:
    print(f"로그 디렉토리 생성 실패: {e}")

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('producer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

context = ssl._create_unverified_context()

# 환경 변수에서 설정 로드 (예외처리 포함)
try:
    KAFKA_BROKER = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "news-raw")
    RSS_FETCH_INTERVAL = int(os.getenv("RSS_FETCH_INTERVAL", "300"))  # 5분
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
except ValueError as e:
    logger.error(f"환경 변수 파싱 오류: {e}. 기본값 사용")
    KAFKA_BROKER = "localhost:9092"
    KAFKA_TOPIC = "news-raw"
    RSS_FETCH_INTERVAL = 300
    MAX_RETRIES = 3
    REQUEST_TIMEOUT = 30

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


# RSS 피드 가져오기 (재시도 로직 포함)
def fetch_rss(rss_url, retries=MAX_RETRIES):
    """RSS 피드를 가져오는 함수 (재시도 로직 포함)"""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                rss_url,
                headers={'User-Agent': 'Mozilla/5.0 (compatible; NewsBot/1.0)'}
            )
            with urllib.request.urlopen(req, context=context, timeout=REQUEST_TIMEOUT) as response:
                data = response.read()
            
            feed = feedparser.parse(data)
            if feed.bozo:
                logger.warning(f"RSS 파싱 경고: {rss_url} - {feed.bozo_exception}")
            
            logger.info(f"RSS 피드 성공적으로 가져옴: {rss_url} ({len(feed.entries)}개 기사)")
            return feed
            
        except Exception as e:
            logger.error(f"RSS 피드 가져오기 실패 (시도 {attempt + 1}/{retries}): {rss_url} - {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # 지수 백오프
            else:
                logger.error(f"RSS 피드 최종 실패: {rss_url}")
                return None



# 기사 본문 크롤링 (재시도 로직 포함)
def crawl_article(url, retries=MAX_RETRIES):
    """기사 본문을 크롤링하는 함수 (재시도 로직 포함)"""
    for attempt in range(retries):
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (compatible; NewsBot/1.0)'}
            response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            origin = soup.select_one('.story-news')
            
            if not origin:
                logger.warning(f"기사 본문 요소를 찾을 수 없음: {url}")
                return "본문 없음"

            content = ""
            # 부제목 추출
            sub_titles = origin.find_all('h2')
            for tag in sub_titles:
                content += tag.get_text(strip=True) + " "
            
            # 본문 단락 추출
            paragraphs = origin.find_all('p')
            for tag in paragraphs:
                if not tag.attrs:  # 속성이 없는 순수 p 태그만
                    text = tag.get_text(strip=True)
                    if text and len(text) > 10:  # 의미있는 텍스트만
                        content += text + " "

            # 정제된 내용 반환
            cleaned_content = re.sub(r'\s+', ' ', content).strip()
            return cleaned_content if len(cleaned_content) > 50 else "본문 없음"
            
        except requests.RequestException as e:
            logger.error(f"기사 크롤링 실패 (시도 {attempt + 1}/{retries}): {url} - {e}")
            if attempt < retries - 1:
                time.sleep(1 * (attempt + 1))  # 점진적 백오프
            else:
                logger.error(f"기사 크롤링 최종 실패: {url}")
                return "본문 없음"
        except Exception as e:
            logger.error(f"기사 크롤링 예상치 못한 오류: {url} - {e}")
            return "본문 없음"


# 기사 데이터 구조화
def enrich_article(entry, category="일반"):
    """RSS entry를 풍부한 기사 데이터로 변환"""
    try:
        content = crawl_article(entry.link)
        
        # 날짜 정규화
        published_date = entry.published if hasattr(entry, 'published') else datetime.now().isoformat()
        
        # 데이터 구조화
        article_data = {
            'title': entry.title.strip() if hasattr(entry, 'title') else "제목 없음",
            'write_date': published_date,
            'content': content,
            'url': entry.link,
            'category': category,
            'summary': entry.summary if hasattr(entry, 'summary') else "",
            'author': entry.author if hasattr(entry, 'author') else "연합뉴스",
            'collected_at': datetime.now().isoformat(),
            'source': "연합뉴스"
        }
        
        logger.debug(f"기사 데이터 구조화 완료: {article_data['title'][:50]}...")
        return article_data
        
    except Exception as e:
        logger.error(f"기사 데이터 구조화 실패: {entry.link if hasattr(entry, 'link') else 'unknown'} - {e}")
        return None


# Kafka Producer 설정 및 초기화
def create_kafka_producer():
    """Kafka Producer를 생성하고 연결을 확인"""
    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BROKER,
            value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            acks='all',  # 모든 replica에서 확인
            retries=3,
            retry_backoff_ms=1000,
            request_timeout_ms=30000,
            max_in_flight_requests_per_connection=1,  # 순서 보장
            compression_type='gzip'  # 압축
        )
        
        # 연결 테스트
        metadata = producer.bootstrap_connected()
        logger.info(f"Kafka Producer 초기화 성공: {KAFKA_BROKER}")
        return producer
        
    except Exception as e:
        logger.error(f"Kafka Producer 초기화 실패: {e}")
        raise


# 메인 뉴스 수집 및 전송 함수
def collect_and_send_news():
    """뉴스를 수집하고 Kafka로 전송"""
    producer = create_kafka_producer()
    
    try:
        for category, url in CATEGORY_RSS.items():
            logger.info(f"📰 [{category}] 카테고리 뉴스 수집 시작...")
            
            # 카테고리별 통계 초기화
            if category not in stats['by_category']:
                stats['by_category'][category] = {'sent': 0, 'failed': 0}
            
            # RSS 피드 가져오기
            feed = fetch_rss(url)
            if not feed or not feed.entries:
                logger.warning(f"RSS 피드가 비어있음: {category}")
                continue
            
            category_sent = 0
            category_failed = 0
            
            for entry in feed.entries:
                try:
                    # 기사 데이터 구조화
                    article = enrich_article(entry, category)
                    if not article:
                        category_failed += 1
                        continue
                    
                    # 필수 필드 검증
                    if not article.get('url') or not article.get('title'):
                        logger.warning(f"필수 필드 누락: {article}")
                        category_failed += 1
                        continue
                    
                    # Kafka로 전송
                    try:
                        key = article['url']  # URL을 키로 사용 (중복 방지)
                        future = producer.send(KAFKA_TOPIC, key=key, value=article)
                        
                        # 전송 결과 확인 (비동기)
                        record_metadata = future.get(timeout=10)
                        logger.info(f"✅ 전송 성공: {article['title'][:50]}... "
                                  f"(토픽: {record_metadata.topic}, 파티션: {record_metadata.partition})")
                        
                        category_sent += 1
                        stats['total_sent'] += 1
                    except TimeoutError:
                        logger.error(f"❌ Kafka 전송 타임아웃: {article['title'][:50]}...")
                        category_failed += 1
                        stats['total_failed'] += 1
                    
                except AttributeError as e:
                    logger.error(f"❌ entry 속성 오류: {e}")
                    category_failed += 1
                    stats['total_failed'] += 1
                except Exception as e:
                    logger.error(f"❌ 기사 전송 실패: {entry.title if hasattr(entry, 'title') else 'unknown'} - {e}")
                    category_failed += 1
                    stats['total_failed'] += 1
            
            # 카테고리별 통계 업데이트
            stats['by_category'][category]['sent'] += category_sent
            stats['by_category'][category]['failed'] += category_failed
            
            logger.info(f"📊 [{category}] 완료 - 성공: {category_sent}, 실패: {category_failed}")
            
            # 각 카테고리 수집 후 바로 저장
            save_statistics_to_csv()
            
            time.sleep(1)  # 카테고리 간 간격
        
        # 전체 결과 로깅
        logger.info(f"🎯 뉴스 수집 완료 - 총 성공: {stats['total_sent']}, 총 실패: {stats['total_failed']}")
        
    finally:
        # Producer 종료
        producer.flush()
        producer.close()
        logger.info("Kafka Producer 종료됨")


def save_statistics_to_csv():
    """통계를 CSV 파일에 저장"""
    try:
        logger.info(f"📝 CSV 저장 시도: {LOG_FILE}")
        logger.info(f"📂 LOG_DIR exists: {os.path.exists(LOG_DIR)}")
        
        # 파일이 없으면 헤더 작성
        write_header = not os.path.exists(LOG_FILE)
        logger.info(f"✍️ Write header: {write_header}")
        
        with open(LOG_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            if write_header:
                writer.writerow([
                    '종료시각', '실행시간(초)', '총_전송_성공', '총_전송_실패', 
                    '성공률(%)', '카테고리별_상세'
                ])
            
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            runtime = int(time.time() - stats['start_time']) if stats['start_time'] else 0
            success_rate = 0
            if stats['total_sent'] + stats['total_failed'] > 0:
                success_rate = (stats['total_sent'] / (stats['total_sent'] + stats['total_failed'])) * 100
            
            # 카테고리별 상세 정보를 JSON 형태로
            category_details = json.dumps(stats['by_category'], ensure_ascii=False)
            
            writer.writerow([
                timestamp,
                runtime,
                stats['total_sent'],
                stats['total_failed'],
                f"{success_rate:.2f}",
                category_details
            ])
        
        logger.info(f"✅ 통계가 파일에 저장됨: {LOG_FILE}")
    except Exception as e:
        logger.error(f"❌ CSV 파일 저장 실패: {e}", exc_info=True)

def print_final_statistics():
    """종료 시 최종 통계 출력"""
    logger.info("\n" + "="*70)
    logger.info("📊 뉴스 Producer 최종 통계")
    logger.info("="*70)
    
    if stats['start_time']:
        runtime = time.time() - stats['start_time']
        hours, remainder = divmod(int(runtime), 3600)
        minutes, seconds = divmod(remainder, 60)
        logger.info(f"⏱️  총 실행 시간: {hours}시간 {minutes}분 {seconds}초")
    
    logger.info(f"✅ 총 전송 성공: {stats['total_sent']}개")
    logger.info(f"❌ 총 전송 실패: {stats['total_failed']}개")
    
    if stats['total_sent'] + stats['total_failed'] > 0:
        success_rate = (stats['total_sent'] / (stats['total_sent'] + stats['total_failed'])) * 100
        logger.info(f"📈 성공률: {success_rate:.2f}%")
    
    if stats['by_category']:
        logger.info("\n📂 카테고리별 통계:")
        logger.info("-" * 70)
        for category, data in stats['by_category'].items():
            total = data['sent'] + data['failed']
            if total > 0:
                rate = (data['sent'] / total) * 100
                logger.info(f"  {category:12s} | 성공: {data['sent']:4d} | 실패: {data['failed']:4d} | 성공률: {rate:5.1f}%")
    
    logger.info("="*70)
    logger.info("👋 Producer 종료")
    logger.info("="*70 + "\n")


def signal_handler(signum, frame):
    """시그널 핸들러 (Ctrl+C 처리)"""
    logger.info("\n⚠️  종료 신호 감지됨 (Ctrl+C)")
    save_statistics_to_csv()
    print_final_statistics()
    sys.exit(0)


def main():
    """메인 실행 함수"""
    # 시그널 핸들러 등록
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    stats['start_time'] = time.time()
    
    logger.info("🚀 뉴스 Producer 시작")
    logger.info(f"설정: Kafka={KAFKA_BROKER}, Topic={KAFKA_TOPIC}, Interval={RSS_FETCH_INTERVAL}s")
    
    # 프로그램 시작 시 초기 CSV 파일 생성 (헤더만)
    save_statistics_to_csv()
    
    while True:
        try:
            start_time = time.time()
            collect_and_send_news()
            elapsed_time = time.time() - start_time
            
            # 매 수집 후 통계를 CSV에 저장
            save_statistics_to_csv()
            
            logger.info(f"⏱️ 수집 완료 (소요시간: {elapsed_time:.2f}초)")
            logger.info(f"😴 다음 수집까지 {RSS_FETCH_INTERVAL}초 대기...")
            
            time.sleep(RSS_FETCH_INTERVAL)
            
        except KeyboardInterrupt:
            logger.info("\n⚠️  사용자에 의해 중단됨")
            save_statistics_to_csv()
            print_final_statistics()
            break
        except Exception as e:
            logger.error(f"예상치 못한 오류: {e}")
            logger.info(f"60초 후 재시도...")
            time.sleep(60)

if __name__ == "__main__":
    main()
