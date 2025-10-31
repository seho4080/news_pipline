import os 
import shutil
from datetime import datetime

REALTIME_DIR = "/opt/airflow/data/realtime"
ARCHIVE_DIR = "/opt/airflow/data/news_archive"

def move_file(**context):
    """
    realtime 디렉토리의 JSON 파일을 날짜별 archive로 이동
    Airflow context를 받아 실행 날짜 기준으로 처리
    """
    try:
        # Airflow에서 전달되는 실행 날짜 (YYYY-MM-DD)
        execution_date = context.get('ds', datetime.now().strftime('%Y-%m-%d'))
        
        # 디렉토리 존재 확인
        if not os.path.exists(REALTIME_DIR):
            print(f"⚠️ 경고: {REALTIME_DIR} 디렉토리가 없습니다.")
            return 0
        
        # 날짜별 아카이브 디렉토리 생성
        date_archive_dir = os.path.join(ARCHIVE_DIR, execution_date)
        os.makedirs(date_archive_dir, exist_ok=True)
        print(f"📁 아카이브 디렉토리 생성/확인: {date_archive_dir}")
        
        moved_count = 0
        error_count = 0
        
        # 디렉토리 내 모든 파일 가져오기
        files = os.listdir(REALTIME_DIR)
        if not files:
            print("📭 이동할 파일이 없습니다.")
            return 0
        
        for filename in files:
            if not filename.endswith('.json'):
                print(f"⏭️ 건너뜀 (JSON 아님): {filename}")
                continue
                
            src_path = os.path.join(REALTIME_DIR, filename)
            dst_path = os.path.join(date_archive_dir, filename)
            
            try:
                # 파일인지 확인
                if os.path.isfile(src_path):
                    # 대상 파일이 이미 존재하면 타임스탬프 추가
                    if os.path.exists(dst_path):
                        timestamp = datetime.now().strftime('%H%M%S')
                        name, ext = os.path.splitext(filename)
                        dst_path = os.path.join(date_archive_dir, f"{name}_{timestamp}{ext}")
                        print(f"⚠️ 중복 파일: {filename} → {os.path.basename(dst_path)}")
                    
                    shutil.move(src_path, dst_path)
                    moved_count += 1
                    print(f"✅ 이동 완료: {filename}")
            except PermissionError as e:
                print(f"❌ 권한 오류: {filename} - {e}")
                error_count += 1
            except Exception as e:
                print(f"❌ 이동 실패: {filename} - {e}")
                error_count += 1
        
        print(f"📊 이동 완료: {moved_count}개 성공, {error_count}개 실패")
        return moved_count
        
    except Exception as e:
        print(f"❌ 파일 이동 프로세스 실패: {e}")
        import traceback
        traceback.print_exc()
        raise
