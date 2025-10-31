from google import genai
from dotenv import load_dotenv
load_dotenv()
import os

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

response = client.models.generate_content(
    model="gemini-2.5-pro", contents="""
    <CONTEXT>
    주소:서울 강남구 언주로 711
    규모: 1000세대
    타입: 84m²
    </CONTEXT>
    <GOAL>
    <CONTEXT>의 주소, 규모, 타입이 유사하고, 최단거리에 있는 매매아파트 3개, 분양아파트트 3개를 찾아서 매매아파트 3개는 각각의 평당매매가격, 분양단지 3개는 각각의 평당분양가격을 출력해 주세요
    </GOAL>
    <RULE>
    <OUTPUT>을 참조해서서 json 형식으로 출력해주세요.
    </RULE>
    <OUTPUT>
{
  "매매아파트": [
    {
      "주소와단지명": "",
      "규모": "",
      "타입": "",
      "평당매매가격": "",
      "거리": "약 0.3km",
      "비고": "대상지와 가장 인접한 대단지 준신축 아파트로 직접적인 시세 비교군입니 다."
    },
  ],
  "분양아파트": [
 
    {
      "주소와단지명": "",
      "규모": "",
      "타입": "",
      "평당매매가격": "",
      "거리": "약 0.3km",
      "비고": "대상지와 가장 인접한 대단지 준신축 아파트로 직접적인 시세 비교군입니 다."
    },
  ],
}
    </OUTPUT>

    """
)
print(response.text)