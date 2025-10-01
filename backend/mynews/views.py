
import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from mynews.models import news_article, Likes, Reads
from members.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from .serializers import ArticleDetailSerializer, ArticleListSerializer, CommentSerializer
from pgvector.django import CosineDistance
from elasticsearch import Elasticsearch
from django.db import connection
from urllib.parse import quote
from .models import Comment,news_article

# 뉴스데이터 10개만 보냄 ㅋㅋ.. 일단
# @api_view(['GET'])
# def article_list(request):
#     # 유저가 있으면 유저가 좋아요한 기사 내보내게 ㅎㅎ;
#     user = request.user if request.user.is_authenticated else None

#     # 원하는 기사만, 예시: 전체 10개 (order 등 추가 가능)
#     articles = news_article.objects.all()[:10]

#     data = []
#     for article in articles:
#         # category가 string 필드면 바로, 아니면 category name만 뽑기
#         category_data = [{"name": article.category}] if isinstance(article.category, str) else [{"name": c.name} for c in article.category.all()]
#         is_like = 0
#         total_like = 0
#         total_read = 0
#         keywords = ["a", "b", "c", "d", "e"]

#         if isinstance(article.category, str):
#             category_value = article.category
#         else:
#             # ManyToMany 등인 경우
#             category_qs = article.category.all()
#             category_value = category_qs[0].name if category_qs else ''

#         data.append({
#             "article_id": article.id,
#             "title": article.title,
#             "writer": article.writer,
#             "write_date": article.write_date.isoformat(),
#             "category": category_value,
#             # "keywords": [kw.strip() for kw in (article.keywords or "").split(",") if kw.strip()],
#             "keywords": keywords,
#             "content": article.content,
#             "url": article.url,
#             "is_like": is_like,
#             "total_like": total_like,
#             "total_read": total_read,
#         })

#     return Response({"article_list": data})

# 기사 리스트 serialize 했을 경우 사용하는 함수
# /api/news/latest/

@api_view(['GET'])
def article_list(request):
    # 로그인 안되어 있을 때, 
    articles = news_article.objects.all()[:10]
    # serializer = ArticleListSerializer(articles, many=True, context={'user': request.user})
    serializer = ArticleListSerializer(articles, many=True, context={'request': request})  # ✅ 수정됨

    raw_data = serializer.data
    response_data = {
        "연예": [],
        "경제": [],
        "교육": [],
        "국제": [],
        "산업": [],
        "정치": [],
        "지역": [],
        "건강": [],
        "문화": [],
        "취미": [],
        "스포츠": [],
        "사건사고": [],
        "사회일반": [],
        "IT_과학": [],
        "여성복지": [],
        "여행레저": [],
        "라이프스타일": []
    }

    for data in raw_data:
        response_data[data["category"]].append(data)

    return Response(response_data)
    # 로그인 되어 있을 때, -> 사용자 좋아요 기반의 뉴스 큐레이팅 

# /api/news/recommendation/

# /api/news/views/




# 뉴스 디테일 보낼거 
# @api_view(['GET'])
# @permission_classes([AllowAny])
# def article_detail(request, article_id):
#     try:
#         article = news_article.objects.get(id=article_id)
#     except news_article.DoesNotExist:
#         return Response({'error': 'Article not found'}, status=status.HTTP_404_NOT_FOUND)

#     # 좋아요, 읽음 집계
#     total_like = Likes.objects.filter(article_id=article_id, is_liked=True).count()
#     total_read = Reads.objects.filter(article_id=article_id).count()  # 읽은 기록의 개수

#     # (로그인한 유저가 있을 경우) 해당 유저의 좋아요 여부
#     is_like = 0
#     if request.user.is_authenticated:
#         is_like = 1 if Likes.objects.filter(article_id=article_id, user_id=request.user.id, is_liked=True).exists() else 0

#     if request.user.is_authenticated:
#         Reads.objects.get_or_create(user=request.user, article_id=article)    

#     # 원하는 형태의 딕셔너리 생성
#     data = {
#         "article_id": article.id,
#         "title": article.title,
#         "writer": article.writer,
#         "write_date": article.write_date.strftime("%Y-%m-%d %H:%M:%S"),
#         "category": article.category,
#         "keywords": [kw.strip() for kw in (article.keywords or "").split(",") if kw.strip()],
#         "content": article.content,
#         "url": article.url,
#         "is_like": is_like,
#         "total_like": total_like,
#         "total_read": total_read,
#     }
#     return Response(data)

# 뉴스 디테일 시리얼라이즈 버전
@api_view(['GET'])
@permission_classes([AllowAny])
def article_detail(request, article_id):
    try:
        article = news_article.objects.get(id=article_id)
    except news_article.DoesNotExist:
        return Response({'error': 'Article not found'}, status=status.HTTP_404_NOT_FOUND)
    # print("USER:", request.user)
    # print("IS AUTH:", request.user.is_authenticated)
    # 읽음 기록 저장
    if request.user.is_authenticated:
        # Reads.objects.get_or_create(user=request.user, article_id=article)
        Reads.objects.create(user=request.user, article_id=article)
        # print("e들어오긴함")

    # 시리얼라이저로 응답 생성
    serializer = ArticleDetailSerializer(article, context={'request': request})
    return Response(serializer.data)



# 좋아요 + 좋아요 취소 
@api_view(['PUT','DELETE'])
# 유저 토큰 인증
@permission_classes([IsAuthenticated])
def article_like(request, article_id):
    user = request.user
    try:
        article = news_article.objects.get(id=article_id)
        # article_id 랑 

    except news_article.DoesNotExist:
        return Response({"error": "해당 기사가 없습니다."}, status=404)
    
    
    # ✅ 좋아요가 이미 존재하면 → 삭제 (취소)
    # ❌ 좋아요가 없으면 → 생성 (등록)
    # db에 데이터 생성하고, created(boolean)
    like_obj, created = Likes.objects.get_or_create(user=user, article_id=article)

    if created:
        return Response({"message": "좋아요 등록", "is_liked": True})
    else:
        like_obj.delete()
        return Response({"message": "좋아요 취소", "is_liked": False})


# 좋아요 기반 추천
# 관련 뉴스 유사도 5개까지 나오게 하는 함수 
@api_view(['GET'])
def similar_articles(request, article_id):
    try:
        target = news_article.objects.get(id=article_id)
    except news_article.DoesNotExist:
        return Response({"error": "Article not found"}, status=400)

    similar_qs = (
        news_article.objects
        .exclude(id=article_id)
        .annotate(similarity=CosineDistance('embedding', target.embedding))
        .order_by('similarity')[:10]
    )

    # data = [
    #     {
    #         "id": article.id,
    #         "title": article.title,
    #         "similarity": round(article.similarity, 4)
    #     }
    #     for article in similar_qs
    # ]

    # return Response({"target": target.title, "similar_articles": data})
    serializer = ArticleDetailSerializer(similar_qs, many=True, context={"request": request})
    result = serializer.data

    # similarity 값은 annotate 필드이므로 따로 추가
    # for obj, article in zip(result, similar_qs):
    #     obj["similarity"] = round(article.similarity, 4)

    return Response({
        # "target": target.title,
        "article_list": result
    })


# /api/news/search/
# 키워드 검색 기반
class NewsSearchAPIView(APIView):
    def get(self, request):
        query = request.query_params.get("q")  # ← GET 파라미터 읽기

        if not query:
            return Response({"error": "검색어를 입력해주세요"}, status=status.HTTP_400_BAD_REQUEST)

        # 1. ES 검색
        es = Elasticsearch("http://localhost:9200")
        es_result = es.search(
            # 인덱스 이름
            index="news",
            # 몇개 뱉어낼건지
            size=10,
            query={
                # 일단 멀티 매치로 ㄱㄱ
                "multi_match": {
                    "query": query,
                    "fields": ["title", "content", "keywords"]
                }
            }
        )
        # unique한 url을 검색 용도로 씀
        urls = [hit["_source"]["url"] for hit in es_result["hits"]["hits"]]

        # 2. PostgreSQL 조회

        # 없으면.. 없을리는 없음
        if not urls:
            return Response({"results": []})

        placeholder = ','.join(['%s'] * len(urls))
        # 색인 방식으로 한다 Index Scan
        # url은 unique 속성을 가지고 있기 때문에 index가 자동 생성
        query_sql = f"""
            SELECT title, writer, write_date, category, url
            FROM news_article
            WHERE url IN ({placeholder})
        """

        with connection.cursor() as cursor:
            cursor.execute(query_sql, urls)
            rows = cursor.fetchall()

        # 3. 응답 정리
        results = [
            {
                "title": row[0],
                "writer": row[1],
                "write_date": row[2],
                "category": row[3],
                "url": row[4],
            }
            for row in rows
        ]
        return Response({"results": results})
    

# 댓글 생성, 삭제, 요청

class NewsCommentAPIView(APIView):
    def get(self, request, article_id):
        self.permission_classes = [AllowAny]  # 인증 없이 조회 가능
        self.check_permissions(request)

        comments = Comment.objects.filter(article_id=article_id, parent__isnull=True).order_by("-created_at")
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)

    def post(self, request, article_id):
        self.permission_classes = [IsAuthenticated]
        self.check_permissions(request)
        
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            comment = serializer.save(user=request.user, article_id=article_id)
            out_serializer = CommentSerializer(comment)

            return Response(out_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, article_id):
        self.permission_classes = [IsAuthenticated]
        self.check_permissions(request)

        comment_id = request.data.get("id")  # 댓글 ID는 여전히 body에서 받는 걸로
        if not comment_id:
            return Response({"error": "댓글 ID가 필요합니다."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            comment = Comment.objects.get(id=comment_id, article_id=article_id)
            if comment.user != request.user:
                return Response({"error": "본인 댓글만 삭제할 수 있습니다."}, status=status.HTTP_403_FORBIDDEN)
            comment.delete()
            return Response({"message": "삭제되었습니다."}, status=status.HTTP_204_NO_CONTENT)
        except Comment.DoesNotExist:
            return Response({"error": "존재하지 않는 댓글입니다."}, status=status.HTTP_404_NOT_FOUND)
        



def message_to_dict(msg):
    if isinstance(msg, SystemMessage):
        return {"role": "system", "content": msg.content}
    elif isinstance(msg, HumanMessage):
        return {"role": "user", "content": msg.content}
    elif isinstance(msg, AIMessage):
        return {"role": "assistant", "content": msg.content}
    raise TypeError("Unsupported message type")

def dict_to_message(d):
    role = d.get("role")
    content = d.get("content", "")
    if role == "system":
        return SystemMessage(content=content)
    elif role == "user":
        return HumanMessage(content=content)
    elif role == "assistant":
        return AIMessage(content=content)
    raise ValueError("Unknown role")


class ChatbotView(APIView):
    load_dotenv()
    openai_api_key = os.getenv("OPENAI_API_KEY")
    permission_classes = [IsAuthenticated]
    def post(self, request,article_id):
        # return Response({"message": "백엔드 통신 잘됨"}, status=status.HTTP_200_OK)
        if not request.user.is_authenticated:
            return Response({"message": "인증이 필요합니다."}, status=401)

        # article_id = request.data.get("article_id")
        try:
            article = news_article.objects.get(id=article_id)
        except news_article.DoesNotExist:
            return Response({"message": "해당 뉴스 기사를 찾을 수 없습니다."}, status=400)
        question = request.data.get("message")

        if not all([article.title, article.write_date, article.content, question]):
            print("hello")
            return Response({"message": "입력값이 부족합니다."}, status=400)

        session_key = f"chat_history_{request.user.id}_{article_id}"
        if session_key not in request.session:
            prompt = f"""너는 친절한 뉴스 비서 <소봇>이야.
                - 뉴스 기사 내용을 바탕으로 사용자의 질문에 쉽고 친절하게 대답해줘.
                - 기사의 내용에 없는 정보는 "죄송해요, 여기 보고계신 기사에서는 찾을 수 없네요."라고 말해줘. 
                기사 제목: {article.title}, 작성일: {article.write_date}, 내용: {article.content}"""
            request.session[session_key] = [SystemMessage(content=prompt)]


        messages = request.session.get(session_key, [])
        messages.append(HumanMessage(content=question))
        llm = ChatOpenAI(model="gpt-4o", api_key=os.getenv("OPENAI_API_KEY"))
        answer = llm.invoke(messages[-20:])  # 최근 20개만 사용

        # ✅ 응답 메시지 추가
        messages.append(AIMessage(content=answer.content))

        # ✅ 세션에 dict 형태로 저장 (LangChain 객체 직접 저장 ❌)
        request.session[session_key] = [message_to_dict(m) for m in messages]

        return Response({"message": answer.content})