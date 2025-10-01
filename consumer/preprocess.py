import os
from openai import OpenAI
from dotenv import load_dotenv
import tiktoken
load_dotenv()


class Preprocess:
    def __init__(self):
        os.environ.pop("HTTP_PROXY", None)
        os.environ.pop("HTTPS_PROXY", None)
        api_key = os.getenv("OPENAI_API_KEY")
        # print("OPENAI KEY:", os.getenv("OPENAI_API_KEY"))
        # print("HTTP_PROXY:", os.getenv("HTTP_PROXY"))
        # print("HTTPS_PROXY:", os.getenv("HTTPS_PROXY"))
        self.client = OpenAI(api_key=api_key)
        self.categories = [
                "IT_과학", "건강", "경제", "교육", "국제", "라이프스타일", "문화", "사건사고", "사회일반",
                "산업", "스포츠", "여성복지", "여행레저", "연예", "정치", "지역", "취미"
            ]

    # 기사 내용이 너무 길면 자르는 함수
    def preprocess_content(self, content):
        """
        데이터 전처리 - 텍스트 길이 제한  (5000 토큰)
        토큰 수를 제한하여 처리 효율성 확보
        """

        if not content:
            return ""
            
        encoding = tiktoken.get_encoding("cl100k_base")
        tokens = encoding.encode(content) # token은 텍스트를 임베딩한 결과가 담김
        
        # token 개수가 너무 크지 않도록 파싱 <- 토큰 수 측정해서 5000 이상이면 5000개만 return
        if len(tokens) > 5000:
            truncated_tokens = tokens[:5000]
            return encoding.decode(truncated_tokens)
        
        # 토큰 수가 5000을 넘지 않으면 원래 데이터 return
        return content

    # 기사 내용에서 키워드 추출
    def transform_extract_keywords(self, text):
        """
        텍스트 데이터 변환 - 키워드 5개 추출  
        입력 텍스트에서 핵심 키워드를 추출하는 변환 로직
        """
        text = self.preprocess_content(text)

        context = "입력으로 뉴스 기사가 주어지면, 기사의 핵심 키워드를 5개로 요약해줘. 만약 핵심적인 키워드가 5개가 되지 않을 경우엔, 그보다 더 적게 요약해줘도 돼." \
                "키워드를 요약할 땐, 동사 말고 명사로 요약해줘. 각 키워드는 \',\'로만 구분해줘. 아래 예시를 참고해서 답변 작성해줘."

        # client = OpenAI()
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": context}, # 해당 위치에서 키워드 5개를 추출할 수 있도록 프롬프트 작성
                {
                    "role": "user",
                    "content": "올해 물가가 상승하면서 임금 또한 상승했다."
                },
                {
                    "role": "assistant",
                    "content": "물가 상승,임금 상승"
                },
                {"role": "user", "content": text},
            ],
            max_tokens=100
        )
        keywords = response.choices[0].message.content.strip()
        # keyword_list = [kw.strip() for kw in keywords.split(",")]
        return keywords

    # 텍스트 데이터를 임베딩으로 변환
    def transform_to_embedding(self, text: str) -> list[float]:
        """
        텍스트 데이터 변환 - 벡터 임베딩  
        텍스트를 수치형 벡터로 변환하는 변환 로직
        """
        text = self.preprocess_content(text)

        # client = OpenAI()
        response = self.client.embeddings.create(input=text, model="text-embedding-3-small")
        return response.data[0].embedding

    # 카테고리 추출
    def transform_classify_category(self, content):
        """
        TODO: 해당 로직을 위의 코드와 아래의 category를 참고하여 openai 기반의 카테고리 분류가 가능한 형태로 구현하세요.

        텍스트 데이터 변환 - 카테고리 분류  
        뉴스 내용을 기반으로 적절한 카테고리로 분류하는 변환 로직
        """
        
        context = f"기사 내용이 주어지면, {self.categories} 안에 있는 카테고리 중, 가장 유사한 하나를 선택해서 출력해줘." \
                "만약 카테고리 안에 기사 내용과 유사한 내용이 없다고 판단되면 \"없음\"을 출력해줘."

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": context}, # 해당 위치에서 키워드 5개를 추출할 수 있도록 프롬프트 작성
                {
                    "role": "user",
                    "content": "올해 물가가 상승하면서 임금 또한 상승했다."
                },
                {
                    "role": "assistant",
                    "content": "경제"
                },
                {
                    "role": "user",
                    "content": "이상한 내용"
                },
                {
                    "role": "assistant",
                    "content": "없음"
                },
                {"role": "user", "content": content},
            ],
            max_tokens=100
        )
        model_output = response.choices[0].message.content.strip()

        if model_output not in self.categories:
            model_output = "미분류"

        return model_output
