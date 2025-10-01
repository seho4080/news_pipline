"""
URL configuration for myproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path
from django.http import HttpResponse

# 기본 페이지 뷰 함수
def home(request):
    return HttpResponse("Welcome to the homepage!")


urlpatterns = [
    path('', home),  # 빈 경로에 대한 URL 패턴
    path('api/news/', include('mynews.urls')),         # 뉴스 관련
    path('api/members/', include('members.urls')),   # 회원 관련
    # path('api/auth/', include('authmember.urls')),  # 인증 관련(임시)
    path("admin/", admin.site.urls),
]
