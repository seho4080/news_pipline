from django.urls import path
# from .views import signup_view, my_profile, auth_check, like_list, read_list, user_target_article
from .views import *

# 토큰 
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
# urlpatterns = [
#     # 회원가입
#     path('signup/', signup_view, name='signup'),
#     # 내 정보 조회 
#     path('me/', my_profile, name='my_profile'),
#     # 알아서 서버가 로그인 검증하고 토큰 리턴함
#     path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
#     # 좋아요 기사 목록
#     path('likes/' , like_list , name = 'like_list'),
#     # 읽은 기사 목록 
#     path('reads/' , read_list , name = 'read_list'),
#     # 키워드 기반 기사 목록
#     path('target/', user_target_article, name = 'user_target_article'),

# ]

# 맴버 관리하는 API
urlpatterns = [
    # 회원가입 
    path('signup/', SignupView.as_view()),
    # 내 정보 조회
    path('me/', MyProfileView.as_view()),
    # path('auth-check/', views.AuthCheckView.as_view()),
    # 로그인 검증하고 토큰 리턴함
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    # 좋아요 기사 목록
    path('likes/', LikeListView.as_view()),
    # 읽은 기사 목록
    path('reads/', ReadListView.as_view()),
    # 키워드 기반 기사 목록
    path('recommendations/', UserTargetArticleView.as_view()),
    # 대쉬보드 출력 내용
    path('dashboard/', UserDashboardView.as_view()),
]