import sys
import argparse
import os
import shutil
from datetime import datetime, timedelta

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, explode, count, from_json, to_timestamp, to_date, split, hour, regexp_replace
from pyspark.sql.types import ArrayType, StringType
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages
import seaborn as sns


def main(report_date_str):
    print(f"시작 날짜: {report_date_str}")
    
    # 폰트 설정 (기본 폰트)
    FONT_PATH = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
    INPUT_PATH = "/opt/airflow/data/realtime/*.json"
    # temp_input_path = "../../data/realtime/*.json"
    REALTIME_DIR = "/opt/airflow/data/realtime"
    ARCHIVE_DIR = "/opt/airflow/data/news_archive"
    REPORT_DIR = "/opt/airflow/data/daily_report"
    font_prop = fm.FontProperties(fname=FONT_PATH, size=12)
    plt.rcParams['font.family'] = 'NanumGothic'

    spark = SparkSession.builder \
            .appName("DailyNewsReport") \
            .getOrCreate()
    # spark로 json 데이터 읽기
    df = spark.read.json(INPUT_PATH)
    # 데이터 잘 들어왔나 체크
    # df.show(5, truncate=False)

    # 날짜 컬럼 정제
    df = df.withColumn("date", to_date("write_date"))
    df_keywords = df.withColumn("clean_keywords", regexp_replace(col("keywords"), '^"|"$', ''))
    df_keywords = df_keywords.withColumn("keyword", explode(split("clean_keywords", ",")))
    # -------------------------
    # (1) 시간대별 기사 수
    # 시간 추출
    df_hours = df.withColumn("hour", hour("write_date"))

    # 집계
    hours_counts = df_hours.groupBy("hour").agg(count("*").alias("article_count_by_hour")).orderBy("hour")

    # (2) 카테고리별 기사 수
    category_counts = df.groupBy("category").agg(count("*").alias("each_category_article_count")).orderBy("each_category_article_count", ascending=False)

    # (3) 키워드별 기사 수
    # df_keywords = df.withColumn("keyword", explode(split("keywords", ",")))  # 키워드를 explode
    keyword_counts = df_keywords.groupBy("keyword").agg(count("*").alias("article_count")).orderBy("article_count", ascending=False)


    # (4) 제일 많이 나온 키워드
    Trend_keyword_counts = df_keywords.groupBy("keyword").agg(count("*").alias("keyword_count")).orderBy("keyword_count",ascending=False)

    # 결과 잘 나왔나 출력 한 번 해보시고
    hours_counts.show()
    category_counts.show()
    df_keywords.show()
    keyword_counts.show()
    Trend_keyword_counts.show()
    
    # Spark DataFrame ->Pandas로 변환

    hours_counts_pd = hours_counts.toPandas()
    category_counts_pd = category_counts.toPandas()
    keyword_counts_pd = keyword_counts.toPandas()
    Trend_keyword_counts_pd = Trend_keyword_counts.toPandas()
    # combo_pd = combo.toPandas().pivot(index="keyword", columns="category", values="count").fillna(0)
    top_keyword_counts = keyword_counts_pd.iloc[:20]
    top_Trend_keywords_pd = Trend_keyword_counts_pd.iloc[:20]

    # (5) 카테고리 + 키워드 조합 (히트맵 or stacked bar)
        # 1. 키워드 등장 빈도 집계
    top_keywords = keyword_counts_pd.sort_values("article_count", ascending=False).head(20)["keyword"].tolist()

        # 2. 원본 Spark DataFrame에서 상위 키워드만 필터링
    df_top_keywords = df_keywords.filter(col("keyword").isin(top_keywords))

        # 3. 카테고리-키워드 조합 카운트
    combo_top = df_top_keywords.groupBy("category", "keyword").agg(count("*").alias("count"))

        # 4. Pandas 피벗으로 변환
    combo_top_pd = combo_top.toPandas().pivot(index="keyword", columns="category", values="count").fillna(0)

    
    # PDF 만들기
    # with PdfPages(f'/home/ssafy/data-pjt-seho-jungrae/batch/data/daily_report/{report_date_str}_news_analysis_report.pdf') as pdf:
    with PdfPages(f'{REPORT_DIR}/{report_date_str}_news_analysis_report.pdf') as pdf:
        #전체 개요 
        # plt.figure(figsize=(8, 2))
        plt.subplots_adjust(bottom=0.25)
        plt.axis('off')
        plt.title(f"{report_date_str} 뉴스 요약", fontsize=14)
        data = [
            ["총 기사 수", len(df_keywords.select("id").distinct().collect())],
            ["카테고리 수", category_counts_pd.shape[0]],
            ["고유 키워드 수", keyword_counts_pd.shape[0]]
        ]
        table = plt.table(cellText=data, colLabels=["항목", "값"], loc='center')
        table.scale(1, 1.5)
        pdf.savefig()
        plt.close()

        # 1번 그래프
        plt.figure(figsize=(10, 4))
        plt.subplots_adjust(bottom=0.25)
        plt.bar(hours_counts_pd["hour"], hours_counts_pd["article_count_by_hour"])
        plt.xlabel("시간대 (시)")
        plt.ylabel("기사 수")
        plt.title("시간대별 기사 발생량")
        plt.xticks(range(0, 24))
        plt.tight_layout()
        pdf.savefig()
        plt.close()
        
        # 2번 그래프
        plt.figure(figsize=(10, 5))
        plt.subplots_adjust(bottom=0.25)
        plt.plot(category_counts_pd["category"], category_counts_pd["each_category_article_count"], marker='o')
        plt.title("카테고리별 뉴스 기사 수")
        plt.xlabel("카테고리")
        plt.ylabel("기사 수")
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()
        pdf.savefig()  # 현재 figure를 PDF에 저장
        plt.close()

        # 3번 그래프
        plt.figure(figsize=(10, 5))
        plt.subplots_adjust(bottom=0.25)
        plt.bar(top_keyword_counts["keyword"], top_keyword_counts["article_count"])
        plt.title("상위 키워드별 기사 수")
        plt.xlabel("키워드")
        plt.ylabel("기사 수")
        plt.xticks(rotation=45)
        plt.tight_layout()
        pdf.savefig()
        plt.close()

        # 4번 그래프
        plt.figure(figsize=(10, 5))
        plt.subplots_adjust(bottom=0.25)
        plt.bar(top_Trend_keywords_pd["keyword"], top_Trend_keywords_pd["keyword_count"])
        plt.title("키워드별 빈도 수")
        plt.xlabel("키워드")
        plt.ylabel("빈도 수")
        plt.xticks(rotation=45)
        plt.tight_layout()
        pdf.savefig()
        plt.close()


        # 5번 그래프 
        plt.figure(figsize=(8, 6))
        plt.subplots_adjust(bottom=0.25)
        sns.heatmap(combo_top_pd, annot=True, cmap="YlGnBu")
        plt.title("카테고리-키워드 조합 히트맵")
        plt.tight_layout()
        pdf.savefig()
        plt.close()
        



    # TODO: 데이터 처리, 리포트 저장, realtime 파일 -> news_archive로 이동 등
    
    # realtime에 있는 json파일을 news_archive로 이동 


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Spark를 이용한 일일 뉴스 리포트 생성")
    parser.add_argument("--date", required=True, help="보고서 기준 날짜 (YYYY-MM-DD)")
    args = parser.parse_args()

    main(args.date)


'''
airflow/
├── dags/
│   └── scripts/
│       └── spark_daily_report.py     ← 이 파일 위치
├── data/                            ← PDF 리포트 저장
│   ├── realtime/                     ← JSON 원본 데이터
│   └── news_archive/                ← 처리 완료된 파일 이동                       
│   └── daily_report/               ← 이거 추가해서 PDF 저장

mkdir -p dags/scripts         # Spark 스크립트
mkdir -p data/realtime        # JSON 수신
mkdir -p data/news_archive    # 이동 대상
mkdir -p data              # PDF 출력

'''
