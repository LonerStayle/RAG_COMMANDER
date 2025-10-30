from google import genai
from dotenv import load_dotenv
load_dotenv()
import os

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

response = client.models.generate_content(
    model="gemini-2.5-pro", contents="""
    <context>
    주소:송파구 마천동 299-23
    규모: 1000세대
    타입: 84m²
    </context>
    <goal>
    <context>의 주소, 규모, 타입이 유사하고, 최단거리에 있는 매매아파트 3개, 분양 단지 3개를 찾아주세요.
    </goal>
    <rule>
    json 형식으로 출력해주세요.
    </rule>

    """
)
print(response.text)