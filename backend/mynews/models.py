from django.db import models
from members.models import User
from pgvector.django import VectorField

# 뉴스 기사 테이블
class news_article(models.Model):
    title = models.TextField()
    writer = models.TextField()
    write_date = models.DateTimeField()
    category = models.TextField()
    content = models.TextField()
    url = models.TextField(unique=True)
    keywords = models.TextField(null=True, blank=True)  # 배열로 쓸 거면 JSONField 추천
    # keywords = models.JSONField(null=True, blank=True)
    # embedding = models.JSONField(null=True, blank=True) # vector(임베딩)는 JSONField 사용
    embedding = VectorField(dimensions=1536)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'news_article'  # 원하면 명시적으로 테이블명 지정
        # managed = False

# 좋아요 누른 테이블
class Likes(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    article_id = models.ForeignKey(news_article, to_field='url', db_column='article_id', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'article_id')  # 한 유저가 한 기사에 여러번 like 못 하게
        db_table = 'likes'
        # managed = False
# 읽은 여부를 알게 해주는 테이블 
class Reads(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    article_id = models.ForeignKey(news_article, to_field='url', db_column='article_id', on_delete=models.CASCADE)
    # 같은 유저더라도 읽은 수 만큼 row 생성해야 함
    read_at = models.DateTimeField(auto_now_add=True)  # 읽은 시각 기록
    #이거 하면 중복없이 읽은 사람만 추가 될 듯
    class Meta:
        # unique_together = ('user', 'news_article')
        db_table = 'read'   # <<--- 실제 테이블명과 일치!
        managed = True

# 댓글 테이블

class Comment(models.Model):
    # settings에 이미 설정 해놓음
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # 댓글 단 기사
    article = models.ForeignKey('news_article', on_delete=models.CASCADE, related_name='comments')
    # 댓글 내용
    content = models.TextField()
    # 댓글 쓴 시각
    created_at = models.DateTimeField(auto_now_add=True)
    # 댓글 수정 시각
    updated_at = models.DateTimeField(auto_now=True)
    # 부모 댓글
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')  # 대댓글 지원

    class Meta:
        db_table = 'comments'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} - {self.content[:30]}'