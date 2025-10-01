from rest_framework import generics, permissions, status
from .serializers import UserSerializer, ArticleSerializer, DashboardArticleSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from mynews.models import news_article, Likes, Reads
from .models import User
from rest_framework.generics import CreateAPIView
from django.db.models import Max, Avg
from pgvector.django import CosineDistance
from collections import defaultdict
import json

# 내 정보 조회
# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def my_profile(request):
#     serializer = UserSerializer(request.user)
#     return Response(serializer.data)

# 내 정보 보기
class MyProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)



# # 인증 확인용
# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def auth_check(request):
#     return Response({"message": "인증 성공!", "user": request.user.id})




# 유저 로그인 테스트 
# @api_view(['POST'])
# @permission_classes([AllowAny])
# def signup_view(request):
#     serializer = UserSerializer(data=request.data)
#     if serializer.is_valid():
#         serializer.save()
#         return Response(serializer.data, status=status.HTTP_201_CREATED)
#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# 회원가입
class SignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# # 좋아요한 기사 목록 
# @api_view(['GET'])
# # 유저 토큰 인증
# @permission_classes([IsAuthenticated])
# def like_list(request):

#     user = request.user
#     liked_articles = news_article.objects.filter(
#         likes__user=user,
#     ).distinct().order_by('-likes__id')[:10]
#     # liked_articles = news_article.objects.filter(
#     #     likes__user=user,
#     # ).order_by('-likes__id').distinct()[:10]

#     serializer = ArticleSerializer(liked_articles, many=True, context={"request": request})
#     return Response(serializer.data)

# 좋아요 누른 기사들 보내주기 10개 
class LikeListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        liked_articles = news_article.objects.filter(
            likes__user=user,
        ).distinct().order_by('-likes__id')[:10]

        serializer = ArticleSerializer(liked_articles, many=True, context={"request": request})
        return Response(serializer.data)

# # 읽은 기사 목록 
# @api_view(['GET'])
# # 유저 토큰 인증
# @permission_classes([IsAuthenticated])
# def read_list(request):
#     user = request.user 
#     read_articles = news_article.objects.filter(
#         reads__user = user,
#     ).annotate(
#     last_read_id=Max('reads__id')
#     ).order_by('-last_read_id')[:10]
#     # .distinct().order_by('-reads__id')[:10]
#     serializer = ArticleSerializer(read_articles, many=True, context={"request": request})
#     return Response(serializer.data)

# 읽은 뉴스 보내주기 10개
class ReadListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        read_articles = news_article.objects.filter(
            reads__user=user,
        ).annotate(
            last_read_id=Max('reads__id')
        ).order_by('-last_read_id')[:10]

        serializer = ArticleSerializer(read_articles, many=True, context={"request": request})
        # return Response(serializer.data)
        return Response({
            "article_list" : serializer.data
        })

# 유저한테 좋아요 기반 유사도 측정된 기사 보여주기 
# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def user_target_article(request):
#     user = request.user
#     # 유저가 좋아요한 기사 목록
#     liked_articles = news_article.objects.filter(likes__user=user).exclude(embedding=None)

#     # # 평균 벡터 구하기
#     # if liked_articles.exists():
#     #     # embedding 평균 (벡터 평균)
#     user_vector = liked_articles.aggregate(avg_embedding=Avg("embedding"))["avg_embedding"]
#     # else:
#     #     user_vector = None  # 혹은 기본 추천 로직으로 대체

#     # if user_vector:
#     similar_articles = (
#         news_article.objects
#         .exclude(likes__user=user)  # 이미 좋아요 누른 건 제외
#         .exclude(embedding=None)    # 임베딩 없는 거 제외
#         .annotate(similarity=CosineDistance("embedding", user_vector))
#         .order_by("similarity")[:5]  # 유사도 낮을수록 가까움
#     )
#     # else:
#         # similar_articles = news_article.objects.none()
#     results = []
#     for article in similar_articles:
#         results.append({
#             "id": article.id,
#             "title": article.title,
#             "similarity": round(article.similarity, 4),  # 소수점 4자리로 보기 좋게
#         })
#     for result in results:
#         print(result)
#     serializer = ArticleSerializer(similar_articles, many=True, context={"request": request})
#     return Response(serializer.data)


# 유사도 기반 기사 추천 
class UserTargetArticleView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        liked_articles = news_article.objects.filter(likes__user=user).exclude(embedding=None)
        user_vector = liked_articles.aggregate(avg_embedding=Avg("embedding"))["avg_embedding"]

        similar_articles = (
            news_article.objects
            .exclude(likes__user=user)
            .exclude(embedding=None)
            .annotate(similarity=CosineDistance("embedding", user_vector))
            .order_by("similarity")[:5]
        )

        serializer = ArticleSerializer(similar_articles, many=True, context={"request": request})
        return Response(serializer.data)
    

# 대시보드 내용 보내줌
class UserDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Likes 테이블 가져와야 함 user == user 
        # user로 필터링하고 
        # 기사 자료 전부 다 가져와야함 
        # 그래서 카테고리 별로 다 합계해서 딕셔너리 만들고 
        # 키워드 별로 합계해서 딕셔너리 만들고 
        # 아티클 작성 날짜기준으로  합계하고
        # 좋아하는 기사 리스트로 article으로 리스트 만들고
        # {
        #     "id": 5,
        #     "title": "지속 가능한 에너지와 환경 보호",
        #     "author": "환경일보",
        #     "write_date": "2024-09-12",
        # }, 이거 시리얼 라이저로 하나 새로 만들고
        # ----------------------------------------------------------------------
        
        user = request.user
        # 1. 좋아요한 Likes row 불러오기
        liked_articles = Likes.objects.filter(user=user).select_related('article_id')

        # 2. 관련 뉴스 기사 추출
        articles = [like.article_id for like in liked_articles]

        # 3. 카테고리별 개수
        category_count = defaultdict(int)
        for article in articles:
            category_count[article.category] += 1

        # 4. 키워드별 개수
        keyword_count = defaultdict(int)
        for article in articles:
            # 이 코드는 문자 하나 하나 검색하는거임
            # if article.keywords:
            #     for keyword in article.keywords:  # keywords는 리스트라고 가정
            #         keyword_count[keyword] += 1
            if article.keywords:
                try:
            # 문자열일 경우 JSON 파싱
                    keywords = json.loads(article.keywords) if isinstance(article.keywords, str) else article.keywords
                    for keyword in keywords:
                        keyword_count[keyword] += 1
                except json.JSONDecodeError:
                    continue  # 혹시 파싱 안 되는 잘못된 데이터가 있으면 무시

        # 5. 날짜별 읽은 기사 수
        date_count = defaultdict(int)
        reads = Reads.objects.filter(user=request.user)

        for read in reads:
            date = read.read_at.strftime('%Y-%m-%d')
            date_count[date] += 1
        # 6. 기사 요약 리스트
        article_list = DashboardArticleSerializer(articles, many=True).data

        return Response({
            "message" : f"{user}의 대시보드입니다",
            "category_count": category_count,
            "keyword_count": keyword_count,
            "number_of_written_articles": date_count,
            "favorite_articles": article_list
        })


