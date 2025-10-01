from django.urls import path
from . import views
# from .views import article_list

urlpatterns = [
    # 뉴스 리스트
    path('', views.article_list, name='article_list'),  # /api/news/
    # 개별 기사 상세 내용
    path('<int:article_id>/', views.article_detail, name='article_detail'),
    # 개별 기사에 대한 좋아요
    path('<int:article_id>/likes/' ,views.article_like , name = 'article_like'),
    # 비슷한 뉴스 찾아 주기
    path('<int:article_id>/similar/',views.similar_articles, name = "similar_articles"),
    # 뉴스 기사 검색
    path("search/", views.NewsSearchAPIView.as_view(), name="search_articles"),
    # 댓글 읽기 
    path('comment/<int:article_id>/',views.NewsCommentAPIView.as_view(), name= "new_comment"),
    # 개별 기사에 대한 챗봇
    path('<int:article_id>/chat/', views.ChatbotView.as_view(), name = 'chatbot'),
]
