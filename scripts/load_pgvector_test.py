# 이것도 테스트 파일임

import psycopg2
import os
from dotenv import load_dotenv
import json
import re


load_dotenv()


def save_to_db(news_data):
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USERNAME"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port='5432'
    )
    
    cur = conn.cursor()

    for article in news_data:
        try:
            cur.execute("""
                INSERT INTO news_article
                (title, writer, write_date, category, content, url, keywords, embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (url) DO NOTHING
            """, (
                article['title'],
                article['writer'],
                article['write_date'],
                # article['category'],
                article['content'],
                article['url'],  
                # json.dumps(article['keywords']),
                # article['embedding']
            ))
        except Exception as e:
            print(f"디비 삽입 에러: {e}")

    conn.commit()
    cur.close()
    conn.close()

def save_to_json(news_data):
    for article in news_data:
        title = re.sub(r'[\\/*?:"<>|]', '', article['title'])
        output_file_path = f"./data/{title}_{article['writer']}_article.json"

        with open(output_file_path, 'w', encoding="utf-8") as f:
            json.dump(article, f, indent='\t', ensure_ascii=False)