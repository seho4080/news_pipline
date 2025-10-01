import sys
import subprocess
import shlex
import argparse
import os
from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, explode, count, to_date, split, hour, regexp_replace
)
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.backends.backend_pdf import PdfPages
import seaborn as sns


# ------------------------------
# 상수 정의 (HDFS 경로)
# ------------------------------
HDFS_BASE = "hdfs://host.docker.internal:9000/news"           # 네임노드 URI + 루트 디렉터리
INPUT_PATH = f"{HDFS_BASE}/realtime/*.json"        # 실시간 JSON 위치
ARCHIVE_BASE = f"{HDFS_BASE}/archive"              # 아카이브 디렉터리 루트
REPORT_BASE = f"{HDFS_BASE}/report"                # PDF 리포트 저장 루트 (선택)
FONT_PATH = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"

# 로컬 임시 PDF 저장 위치 (컨테이너 내부)
LOCAL_TMP_DIR = "/tmp/news_reports"
os.makedirs(LOCAL_TMP_DIR, exist_ok=True)


# ------------------------------
# 유틸 함수: HDFS CLI 래퍼
# ------------------------------
def hdfs_mkdir(path: str):
    subprocess.run(["hdfs", "dfs", "-mkdir", "-p", path], check=True)


def hdfs_mv(src: str, dst: str):
    subprocess.run(["hdfs", "dfs", "-mv", src, dst], check=True)


def hdfs_put(local_path: str, hdfs_path: str):
    subprocess.run(["hdfs", "dfs", "-put", "-f", local_path, hdfs_path], check=True)


# ------------------------------
# 메인 로직
# ------------------------------

def main(report_date_str: str):
    print(f"[INFO] 리포트 날짜: {report_date_str}")

    # Spark 세션
    spark = SparkSession.builder.appName("DailyNewsReport").getOrCreate()

    # ------------------ 데이터 로드 ------------------
    df = spark.read.json(INPUT_PATH)
    if df.rdd.isEmpty():
        print("[WARN] 입력 데이터가 없습니다. 작업을 종료합니다.")
        return

    # 날짜 파싱 및 키워드 explode
    df = df.withColumn("date", to_date("write_date"))
    df_keywords = (
        df.withColumn("clean_keywords", regexp_replace(col("keywords"), '^"|"$', ""))
          .withColumn("keyword", explode(split("clean_keywords", ",")))
    )

    # ------------------ 집계 ------------------
    df_hours = df.withColumn("hour", hour("write_date"))
    hours_counts = df_hours.groupBy("hour").agg(count("*").alias("article_count_by_hour")).orderBy("hour")
    category_counts = df.groupBy("category").agg(count("*").alias("each_category_article_count")).orderBy("each_category_article_count", ascending=False)
    keyword_counts = df_keywords.groupBy("keyword").agg(count("*").alias("article_count")).orderBy("article_count", ascending=False)
    trend_keyword_counts = df_keywords.groupBy("keyword").agg(count("*").alias("keyword_count")).orderBy("keyword_count", ascending=False)

    # ------------------ 시각화 ------------------
    font_prop = fm.FontProperties(fname=FONT_PATH, size=12)
    plt.rcParams["font.family"] = "NanumGothic"

    pdf_local_path = os.path.join(LOCAL_TMP_DIR, f"{report_date_str}_news_analysis_report.pdf")
    with PdfPages(pdf_local_path) as pdf:
        # 표 개요
        plt.figure(figsize=(8, 2))
        plt.axis("off")
        plt.title(f"{report_date_str} 뉴스 요약", fontsize=14)
        data = [
            ["총 기사 수", df_keywords.select("url").distinct().count()],
            ["카테고리 수", category_counts.count()],
            ["고유 키워드 수", keyword_counts.count()],
        ]
        table = plt.table(cellText=data, colLabels=["항목", "값"], loc="center")
        table.scale(1, 1.5)
        pdf.savefig(); plt.close()

        # 시간대별 기사 수
        hours_pd = hours_counts.toPandas()
        plt.figure(figsize=(10, 4)); plt.bar(hours_pd["hour"], hours_pd["article_count_by_hour"])
        plt.xlabel("시간대"); plt.ylabel("기사 수"); plt.title("시간대별 기사 발생량"); plt.xticks(range(0, 24))
        pdf.savefig(); plt.close()

        # 카테고리별 기사 수
        cat_pd = category_counts.toPandas()
        plt.figure(figsize=(10, 4)); plt.plot(cat_pd["category"], cat_pd["each_category_article_count"], marker="o")
        plt.xticks(rotation=45); plt.title("카테고리별 기사 수"); plt.tight_layout()
        pdf.savefig(); plt.close()

        # 상위 키워드 빈도
        top_kw_pd = keyword_counts.toPandas().head(20)
        plt.figure(figsize=(10, 4)); plt.bar(top_kw_pd["keyword"], top_kw_pd["article_count"])
        plt.xticks(rotation=45); plt.title("상위 키워드별 기사 수"); plt.tight_layout()
        pdf.savefig(); plt.close()

        # 트렌드 키워드
        trend_pd = trend_keyword_counts.toPandas().head(20)
        plt.figure(figsize=(10, 4)); plt.bar(trend_pd["keyword"], trend_pd["keyword_count"])
        plt.xticks(rotation=45); plt.title("키워드별 빈도 수"); plt.tight_layout()
        pdf.savefig(); plt.close()

        # 카테고리-키워드 히트맵
        top_keywords = top_kw_pd["keyword"].tolist()
        combo = (df_keywords.filter(col("keyword").isin(top_keywords))
                             .groupBy("category", "keyword")
                             .agg(count("*").alias("cnt")))
        combo_pd = combo.toPandas().pivot(index="keyword", columns="category", values="cnt").fillna(0)
        plt.figure(figsize=(8, 6)); sns.heatmap(combo_pd, annot=True, cmap="YlGnBu"); plt.title("카테고리-키워드 히트맵")
        pdf.savefig(); plt.close()

    print(f"[INFO] PDF 저장 완료: {pdf_local_path}")

    # ------------------ HDFS 결과 업로드 / 파일 이동 ------------------
    report_hdfs_dir = f"{REPORT_BASE}/{report_date_str}"
    hdfs_mkdir(report_hdfs_dir)
    hdfs_put(pdf_local_path, report_hdfs_dir)

    # realtime → archive/yyyy-mm-dd 이동
    archive_dir = f"{ARCHIVE_BASE}/{report_date_str}"
    hdfs_mkdir(archive_dir)
    hdfs_mv(f"{HDFS_BASE}/realtime", archive_dir)
    print("[INFO] realtime JSON → archive 이동 완료")

    spark.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Spark를 이용한 일일 뉴스 리포트 (HDFS 버전)")
    parser.add_argument("--date", required=True, help="보고서 기준 날짜 YYYY-MM-DD")
    args = parser.parse_args()

    # 디렉터리 존재 미리 확보 (첫 실행 대비)
    for p in [f"{HDFS_BASE}/realtime", ARCHIVE_BASE, REPORT_BASE]:
        try:
            hdfs_mkdir(p)
        except Exception:
            pass

    main(args.date)
