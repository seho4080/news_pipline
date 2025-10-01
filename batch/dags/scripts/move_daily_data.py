import os 
import shutil

REALTIME_DIR = "/opt/airflow/data/realtime"
ARCHIVE_DIR = "/opt/airflow/data/news_archive"
def move_file():
    # 디렉토리 내 모든 파일 가져오기
    for filename in os.listdir(REALTIME_DIR):
        src_path = os.path.join(REALTIME_DIR, filename)
        dst_path = os.path.join(ARCHIVE_DIR, filename)
    # realtime에서 archive로 이동
        if os.path.isfile(src_path):
            shutil.move(src_path, dst_path)
            print(f"Moved: {filename}")
