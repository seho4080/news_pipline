from rest_framework import serializers
from .models import news_article, Likes, Reads, Comment
import json

# 개별 기사 serialize
class ArticleDetailSerializer(serializers.ModelSerializer):
    total_like = serializers.SerializerMethodField()
    total_read = serializers.SerializerMethodField()
    is_like = serializers.SerializerMethodField()
    article_id = serializers.IntegerField(source='id')
    write_date = serializers.DateTimeField()

    class Meta:
        model = news_article
        fields = [
            'article_id', 
            'title', 
            'writer', 
            'write_date', 
            'category',
            'keywords', 
            'content', 
            'url',
            'total_like', 
            'total_read', 
            'is_like'
        ]
        # extra_kwargs = {
        #     'write_date': {'format': '%Y-%m-%d %H:%M:%S'}
        # }
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

    
# 뉴스 기사 리스트 
class ArticleListSerializer(serializers.ModelSerializer):
    total_like = serializers.SerializerMethodField()
    total_read = serializers.SerializerMethodField()
    is_like = serializers.SerializerMethodField()
    article_id = serializers.IntegerField(source='id')
    write_date = serializers.DateTimeField()
    class Meta:
        model = news_article
        fields = [
            'article_id', 
            'title', 
            'writer', 
            'write_date', 
            'category',
            'keywords', 
            'content', 
            'url',
            'total_like', 
            'total_read', 
            'is_like'
        ]
        # extra_kwargs = {
            # 'write_date': {'format': '%Y-%m-%d %H:%M:%S'}
        # }
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
    
# 댓글 시리얼라이저
class CommentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    article_url = serializers.CharField(source='article.url', read_only=True)

    class Meta:
        model = Comment
        fields = [
            'id',
            'user',         # 사용자 ID
            'username',     # 사람이 읽기 좋은 값 (읽기용)
            'article',      # 기사 ID
            'content',
            'created_at',
            'updated_at',
            'parent',       # 대댓글이면 부모 댓글 ID
            'article_url',
        ]
        read_only_fields = ['user', 'article']  # ✅ 여기 중요