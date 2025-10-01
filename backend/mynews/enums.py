from django.db import models


class ArticleCategory(models.TextChoices):
    전체 = "전체", "전체"
    IT_과학 = "IT_과학", "IT/과학"
    건강 = "건강", "건강"
    경제 = "경제", "경제"
    교육 = "교육", "교육"
    국제 = "국제", "국제"
    라이프스타일 = "라이프스타일", "라이프스타일"
    문화 = "문화", "문화"
    사건사고 = "사건사고", "사건사고"
    사회일반 = "사회일반", "사회일반"
    산업 = "산업", "산업"
    스포츠 = "스포츠", "스포츠"
    여성복지 = "여성복지", "여성복지"
    여행레저 = "여행레저", "여행레저"
    연예 = "연예", "연예"
    정치 = "정치", "정치"
    지역 = "지역", "지역"
    취미 = "취미", "취미"


class ArticleInteractionType(models.TextChoices):
    LIKE = "like", "Like"
    READ = "read", "Read"
