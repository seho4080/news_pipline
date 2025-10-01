from rest_framework.response import Response
from rest_framework import status

class SUCCESS_RESPONSE(Response):
    def __init__(self, message: str, data: dict | None = None):
        if data is None:
            super().__init__({"message": message}, status=status.HTTP_200_OK)
        else:
            super().__init__({"message": message, "data": data}, status=status.HTTP_200_OK)

class UNAUTHORIZED_RESPONSE(Response):
    def __init__(self):
        super().__init__({"message": "로그인이 필요합니다."}, status=status.HTTP_401_UNAUTHORIZED)