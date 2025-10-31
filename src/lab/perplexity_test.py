import os
from perplexity import Perplexity
from dotenv import load_dotenv

load_dotenv()

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
client = Perplexity(api_key=PERPLEXITY_API_KEY) # Automatically uses PERPLEXITY_API_KEY

response = client.chat.completions.create(
    model="sonar-deep-research",
    messages=[
        {"role": "user", "content": 
        """
    <CONTEXT>
    주소:송파구 마천동 299-23
    규모: 1000세대
    타입: 84m²
    </CONTEXT>
    <GOAL>
    <CONTEXT>의 주소, 규모, 타입이 유사하고, 최단거리에 있는 매매아파트 3개, 분양단지 3개를 찾아서 매매아파트 3개는 각각의 평당매매가격, 분양단지 3개는 각각의 평당분양가격을 출력해 주세요
    </GOAL>
    <RULE>
    json 형식으로 출력해주세요.
    </RULE>
    <OUTPUT>
    단지명:
    주소:
    규모:
    타입:
    평당매매가격 OR 평당분양가격:
    거리:
    비고:
    </OUTPUT>

    """}
    ]
)

print(response.choices[0].message.content)