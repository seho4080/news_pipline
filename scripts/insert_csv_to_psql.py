# 이건 csv파일 psql에 넣는 파일임

import pandas as pd
import json
import psycopg2
from datetime import datetime


def parse_keywords(raw):
    if isinstance(raw, str):
        raw = raw.strip('"')
        return [kw.strip() for kw in raw.split(",") if kw.strip()]
    return []
# CSV 읽기
df = pd.read_csv("news_article.csv")


df["embedding"] = df["embedding"].apply(json.loads)
df["keywords"] = df["keywords"].apply(parse_keywords)
df["write_date"] = pd.to_datetime(df["write_date"])

# PostgreSQL 연결
conn = psycopg2.connect(
    host="localhost",
    dbname="news",
    user="ssafyuser",
    password="ssafy"
)
cur = conn.cursor()

# 테이블에 삽입
for _, row in df.iterrows():
    cur.execute("""
        INSERT INTO news_article (id, title, writer, write_date, category, content, url, keywords, embedding, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (url) DO NOTHING;
    """, (
        int(row["id"]),
        row["title"],
        row["writer"],
        row["write_date"],
        row["category"],
        row["content"],
        row["url"],
        ",".join(row["keywords"]) if isinstance(row["keywords"], list) else str(row["keywords"]),
        json.dumps(row["embedding"]),
        # row["embedding"]
        datetime.now()   # ← updated_at
    ))


conn.commit()
cur.close()
conn.close()