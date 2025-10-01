from rest_framework import serializers
# from django.contrib.auth.models import User
from .models import User
from mynews.models import news_article
import json
from mynews.models import Likes, Reads

# 유저 시리얼 라이저
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)
    
# 뉴스 기사 시리얼 라이저
class ArticleSerializer(serializers.ModelSerializer):
    total_like = serializers.SerializerMethodField()
    total_read = serializers.SerializerMethodField()
    is_like = serializers.SerializerMethodField()
    article_id = serializers.IntegerField(source='id')
    class Meta:
        model = news_article
        fields = ['article_id', 'title', 'writer', 'write_date', 'url', 'category','content','keywords',            'total_like', 
            'total_read','is_like','total_like']

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        # keywords가 문자열이라면 → 리스트로 파싱
        keywords_raw = rep.get('keywords')
        if isinstance(keywords_raw, str):
            try:
                rep['keywords'] = json.loads(keywords_raw)
            except json.JSONDecodeError:
                rep['keywords'] = []
        return rep
    
    def get_total_like(self, obj):
        return Likes.objects.filter(article_id=obj).count()

    def get_total_read(self, obj):
        return Reads.objects.filter(article_id=obj).count()

    def get_is_like(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return Likes.objects.filter(article_id=obj, user=user).exists()
        return False

# 대시보드 줄 내용 시리얼 라이저
class DashboardArticleSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = news_article
        fields = ['id', 'title', 'writer', 'write_date']
