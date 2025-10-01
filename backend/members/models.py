from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    pass  # 나중에 nickname 같은 필드 추가 가능