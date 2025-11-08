
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
    try:
        # 페이지네이션 파라미터
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 1000))  # 기본값 1000으로 증가
        category = request.query_params.get('category', None)
        
        # 페이지 시작/끝 계산
        start = (page - 1) * page_size
        end = start + page_size
        
        # 기본 쿼리 (최신순 정렬)
        queryset = news_article.objects.all().order_by('-write_date')
        
        # 카테고리 필터링 (선택적)
        if category and category != 'all':
            queryset = queryset.filter(category=category)
        
        # 전체 개수
        total_count = queryset.count()
        
        # 페이지네이션 적용
        articles = queryset[start:end]
        serializer = ArticleListSerializer(articles, many=True, context={'request': request})

        raw_data = serializer.data
        
        # 프론트엔드 tabs 순서와 일치하도록 OrderedDict 사용
        from collections import OrderedDict
        response_data = OrderedDict([
            ("연예", []),
            ("경제", []),
            ("교육", []),
            ("국제", []),
            ("산업", []),
            ("정치", []),
            ("지역", []),
            ("건강", []),
            ("문화", []),
            ("취미", []),
            ("스포츠", []),
            ("사건사고", []),
            ("사회일반", []),
            ("IT_과학", []),
            ("여성복지", []),
            ("여행레저", []),
            ("라이프스타일", [])
        ])

        for data in raw_data:
            cat = data.get("category")
            if cat and cat in response_data:
                response_data[cat].append(data)
            else:
                # 카테고리가 없거나 알 수 없는 경우 처리
                if "기타" not in response_data:
                    response_data["기타"] = []
                response_data["기타"].append(data)

        # 페이지네이션 메타데이터는 헤더로 전송
        total_pages = (total_count + page_size - 1) // page_size
        
        # 응답 데이터에 총 개수 추가
        response_data["total_count"] = total_count
        
        response = Response(response_data)
        response['X-Total-Count'] = str(total_count)
        response['X-Total-Pages'] = str(total_pages)
        response['X-Current-Page'] = str(page)
        response['X-Page-Size'] = str(page_size)
        response['X-Has-Next'] = 'true' if page < total_pages else 'false'
        response['X-Has-Prev'] = 'true' if page > 1 else 'false'
        
        return response
    except Exception as e:
        return Response(
            {"error": f"기사 목록 조회 실패: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
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
    except ValueError:
        return Response({'error': 'Invalid article ID'}, status=status.HTTP_400_BAD_REQUEST)
    
    # 읽음 기록 저장 (트랜잭션 독립적으로 처리)
    if request.user.is_authenticated:
        try:
            from django.db import transaction
            # 읽음 기록은 실패해도 조회는 계속되어야 하므로 독립 트랜잭션
            with transaction.atomic():
                Reads.objects.create(user=request.user, article_id=article)
        except Exception as e:
            # 읽음 기록 저장 실패는 치명적이지 않으므로 로깅만
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"읽음 기록 저장 실패 (user={request.user.id}, article={article_id}): {e}")

    try:
        # 시리얼라이저로 응답 생성
        serializer = ArticleDetailSerializer(article, context={'request': request})
        return Response(serializer.data)
    except Exception as e:
        return Response(
            {'error': f'Serialization failed: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )



# 좋아요 + 좋아요 취소 
@api_view(['PUT','DELETE'])
@permission_classes([IsAuthenticated])
def article_like(request, article_id):
    from django.db import transaction
    
    user = request.user
    try:
        article = news_article.objects.get(id=article_id)
    except news_article.DoesNotExist:
        return Response({"error": "해당 기사가 없습니다."}, status=status.HTTP_404_NOT_FOUND)
    except ValueError:
        return Response({"error": "잘못된 기사 ID입니다."}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # 트랜잭션으로 묶어서 원자성 보장
        with transaction.atomic():
            # ✅ 좋아요가 이미 존재하면 → 삭제 (취소)
            # ❌ 좋아요가 없으면 → 생성 (등록)
            like_obj, created = Likes.objects.get_or_create(user=user, article_id=article)

            if created:
                return Response({"message": "좋아요 등록", "is_liked": True})
            else:
                like_obj.delete()
                return Response({"message": "좋아요 취소", "is_liked": False})
    except Exception as e:
        return Response(
            {"error": f"좋아요 처리 실패: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# 좋아요 기반 추천
# 관련 뉴스 유사도 5개까지 나오게 하는 함수 
@api_view(['GET'])
def similar_articles(request, article_id):
    try:
        target = news_article.objects.get(id=article_id)
    except news_article.DoesNotExist:
        return Response({"error": "Article not found"}, status=status.HTTP_404_NOT_FOUND)
    except ValueError:
        return Response({"error": "Invalid article ID"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # embedding이 None인 경우 체크
        if target.embedding is None:
            return Response(
                {"error": "해당 기사의 임베딩이 없어 유사 기사를 찾을 수 없습니다."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        similar_qs = (
            news_article.objects
            .exclude(id=article_id)
            .annotate(similarity=CosineDistance('embedding', target.embedding))
            .order_by('similarity')[:10]
        )

        serializer = ArticleDetailSerializer(similar_qs, many=True, context={"request": request})
        result = serializer.data

        return Response({
            "article_list": result
        })
    except Exception as e:
        return Response(
            {"error": f"유사 기사 조회 실패: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# /api/news/search/
# 키워드 검색 기반
class NewsSearchAPIView(APIView):
    def get(self, request):
        query = request.query_params.get("q")

        if not query or not query.strip():
            return Response({"error": "검색어를 입력해주세요"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 1. ES 검색
            es = Elasticsearch("http://localhost:9200")
            
            # Elasticsearch 연결 확인
            if not es.ping():
                return Response(
                    {"error": "검색 서비스에 연결할 수 없습니다."}, 
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            es_result = es.search(
                index="news",
                size=10,
                query={
                    "multi_match": {
                        "query": query,
                        "fields": ["title", "content", "keywords"]
                    }
                }
            )
            
            # unique한 url을 검색 용도로 씀
            urls = [hit["_source"]["url"] for hit in es_result["hits"]["hits"]]

            # 2. PostgreSQL 조회
            if not urls:
                return Response({"results": []})

            placeholder = ','.join(['%s'] * len(urls))
            query_sql = f"""
                SELECT title, writer, write_date, category, url
                FROM news_article
                WHERE url IN ({placeholder})
            """

            with connection.cursor() as cursor:
                cursor.execute(query_sql, urls)
                rows = cursor.fetchall()

            # 3. ES 순서 유지하며 응답 정리
            url_to_row = {row[4]: row for row in rows}
            results = []
            for url in urls:
                if url in url_to_row:
                    row = url_to_row[url]
                    results.append({
                        "title": row[0],
                        "writer": row[1],
                        "write_date": row[2],
                        "category": row[3],
                        "url": row[4],
                    })
            
            return Response({"results": results})
            
        except Exception as e:
            return Response(
                {"error": f"검색 실패: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    

# 댓글 생성, 삭제, 요청

class NewsCommentAPIView(APIView):
    def get(self, request, article_id):
        self.permission_classes = [AllowAny]
        self.check_permissions(request)

        try:
            comments = Comment.objects.filter(article_id=article_id, parent__isnull=True).order_by("-created_at")
            serializer = CommentSerializer(comments, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"error": f"댓글 조회 실패: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request, article_id):
        from django.db import transaction
        
        self.permission_classes = [IsAuthenticated]
        self.check_permissions(request)
        
        try:
            # 트랜잭션으로 묶어서 댓글 생성의 원자성 보장
            with transaction.atomic():
                # 기사 존재 여부 확인
                if not news_article.objects.filter(id=article_id).exists():
                    return Response(
                        {"error": "존재하지 않는 기사입니다."}, 
                        status=status.HTTP_404_NOT_FOUND
                    )
                
                serializer = CommentSerializer(data=request.data)
                if serializer.is_valid():
                    comment = serializer.save(user=request.user, article_id=article_id)
                    out_serializer = CommentSerializer(comment)
                    return Response(out_serializer.data, status=status.HTTP_201_CREATED)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": f"댓글 작성 실패: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def delete(self, request, article_id):
        from django.db import transaction
        
        self.permission_classes = [IsAuthenticated]
        self.check_permissions(request)

        comment_id = request.data.get("id")
        if not comment_id:
            return Response({"error": "댓글 ID가 필요합니다."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 트랜잭션으로 묶어서 삭제의 원자성 보장 (대댓글도 함께 삭제될 수 있음)
            with transaction.atomic():
                comment = Comment.objects.select_for_update().get(id=comment_id, article_id=article_id)
                if comment.user != request.user:
                    return Response({"error": "본인 댓글만 삭제할 수 있습니다."}, status=status.HTTP_403_FORBIDDEN)
                comment.delete()
                return Response({"message": "삭제되었습니다."}, status=status.HTTP_204_NO_CONTENT)
        except Comment.DoesNotExist:
            return Response({"error": "존재하지 않는 댓글입니다."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response(
                {"error": f"댓글 삭제 실패: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        



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
    
    def post(self, request, article_id):
        if not request.user.is_authenticated:
            return Response({"message": "인증이 필요합니다."}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            article = news_article.objects.get(id=article_id)
        except news_article.DoesNotExist:
            return Response({"message": "해당 뉴스 기사를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response({"message": "잘못된 기사 ID입니다."}, status=status.HTTP_400_BAD_REQUEST)
        
        question = request.data.get("message")

        if not question or not question.strip():
            return Response({"message": "질문을 입력해주세요."}, status=status.HTTP_400_BAD_REQUEST)

        if not all([article.title, article.content]):
            return Response({"message": "기사 정보가 불완전합니다."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            session_key = f"chat_history_{request.user.id}_{article_id}"
            
            # 세션 초기화 (dict 형태로 저장)
            if session_key not in request.session:
                prompt = f"""너는 친절한 뉴스 비서 <소봇>이야.
                    - 뉴스 기사 내용을 바탕으로 사용자의 질문에 쉽고 친절하게 대답해줘.
                    - 기사의 내용에 없는 정보는 "죄송해요, 여기 보고계신 기사에서는 찾을 수 없네요."라고 말해줘. 
                    기사 제목: {article.title}, 작성일: {article.write_date}, 내용: {article.content}"""
                request.session[session_key] = [{"role": "system", "content": prompt}]

            # 세션에서 메시지 히스토리 가져오기
            messages_dict = request.session.get(session_key, [])
            messages = [dict_to_message(d) for d in messages_dict]
            messages.append(HumanMessage(content=question))
            
            # LLM 호출
            llm = ChatOpenAI(model="gpt-4o", api_key=os.getenv("OPENAI_API_KEY"), timeout=30.0)
            answer = llm.invoke(messages[-20:])

            # 응답 메시지 추가
            messages.append(AIMessage(content=answer.content))

            # 세션에 dict 형태로 저장
            request.session[session_key] = [message_to_dict(m) for m in messages]

            return Response({"message": answer.content})
            
        except TimeoutError:
            return Response(
                {"message": "응답 시간이 초과되었습니다. 다시 시도해주세요."}, 
                status=status.HTTP_504_GATEWAY_TIMEOUT
            )
        except Exception as e:
            return Response(
                {"message": f"챗봇 응답 생성 실패: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )