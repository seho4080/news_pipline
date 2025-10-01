# db_test.py
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")  # myproject는 본인 프로젝트 폴더명
import django
django.setup() #setting 쵝화
from django.db import connection

# 연결 확인하는  

# try:
#     with connection.cursor() as cursor:
#         cursor.execute("SELECT 1;")
#         result = cursor.fetchone()
#         print("DB 연결 성공!", result)
# except Exception as e:
#     print("DB 연결 실패:", e)

# 연결된 데이터가 잘나오는지 확인 

# from mynews.models import news_article  # 앱명, 모델명 맞게!

# # 1. 전체 데이터 5개만 조회
# for article in news_article.objects.all()[:5]:
#     print(f"{article.id}: {article.title} ({article.write_date})")

# # 2. 조건 검색 예시 (카테고리가 경제인 기사만)
# for article in news_article.objects.filter(category='경제')[:5]:
#     print(article.title, article.writer)