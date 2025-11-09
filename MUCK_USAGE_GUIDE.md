# Muck 더미 데이터 활용 가이드

## 목차
- [개요](#개요)
- [왜 Muck을 사용하나요?](#왜-muck을-사용하나요)
- [main_agent vs main_agent_copy](#main_agent-vs-main_agent_copy)
- [Muck 데이터 저장 방법](#muck-데이터-저장-방법)
- [특정 에이전트만 업데이트하기](#특정-에이전트만-업데이트하기)
- [실전 사용 예시](#실전-사용-예시)

---

## 개요

**Muck**은 7개 분석 에이전트의 실행 결과를 미리 저장해둔 더미 데이터입니다.

### 위치
```
src/utils/muck.py
```

### 구조
```python
muck_main_state = {
    'messages': [],
    'start_input': {...},           # 사업 입력 정보
    'analysis_outputs': {           # 7개 에이전트 결과
        'location_insight': {...},   # 입지 분석
        'policy_output': {...},      # 정책 분석
        'housing_faq': {...},        # 청약 FAQ
        'nearby_market': {...},      # 주변 시세
        'population_insight': {...}, # 인구 분석
        'supply_demand': {...},      # 공급/수요
        'unsold_insight': {...},     # 미분양
    },
    'final_report': '...',           # 최종 보고서
    'source': '...',                 # 출처 페이지
}
```

---

## 왜 Muck을 사용하나요?

### 문제: 전체 실행은 시간이 오래 걸림

```
main_agent 실행 시간
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. 입지 분석        (~5분)
2. 정책 분석        (~7분)
3. 청약 FAQ        (~3분)
4. 주변 시세        (~4분)
5. 인구 분석        (~3분)
6. 공급/수요        (~5분)
7. 미분양          (~2분)
8. jung_min_jae    (~5분)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
총 소요 시간: 약 30~40분
```

### 해결책: Muck으로 빠른 테스트

```
main_agent_copy 실행 시간
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Muck 데이터 로드  (~1초)
2. jung_min_jae만   (~5분)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
총 소요 시간: 약 5분
```

**사용 시나리오:**
- jung_min_jae 프롬프트만 수정했을 때
- 특정 에이전트 결과만 업데이트하고 테스트할 때
- 빠른 보고서 생성 테스트

---

## main_agent vs main_agent_copy

### main_agent (전체 실행)

**파일:** `src/agents/main/main_agent.ipynb`

**실행 순서:**
1. 7개 분석 에이전트 모두 실행
2. jung_min_jae 에이전트로 최종 보고서 생성
3. 이메일 발송

**사용 시기:**
- 처음 분석을 시작할 때
- 모든 데이터를 최신으로 갱신해야 할 때
- Muck 데이터를 만들 때

---

### main_agent_copy (빠른 테스트)

**파일:** `src/agents/main/main_agent_copy_run.ipynb`

**실행 순서:**
1. Muck 데이터 로드 (7개 에이전트 결과)
2. jung_min_jae 에이전트만 실행
3. 이메일 발송

**사용 시기:**
- jung_min_jae 프롬프트를 수정한 후 테스트
- 특정 에이전트만 업데이트한 후 최종 보고서 확인
- 빠르게 결과를 확인하고 싶을 때

---

## Muck 데이터 저장 방법

### 방법 1: 자동 저장 (추천)

#### 1단계: main_agent 실행

`src/agents/main/main_agent.ipynb`를 실행하여 `result` 변수에 전체 결과 저장

```python
result = await graph.ainvoke({
    "start_input": {
        "policy_period": "최근 1년",
        "policy_count": 2,
        "policy_list": "[2025.10.15, 2025.6.27]",
        "target_area": "서울시 송파구 신천동",
        "total_units": "2275세대",
        "main_type": "84",
        ...
    }
})
```

#### 2단계: Muck 저장 함수 실행

노트북에 다음 셀 추가:

```python
import pprint
from pathlib import Path

def save_to_muck(result_data):
    """result 데이터를 muck.py에 저장"""
    muck_path = Path("c:/RAG_COMMANDER/src/utils/muck.py")

    # result를 Python 코드 형식으로 변환
    result_str = pprint.pformat(result_data, width=120, compact=False)

    # muck.py 파일 작성
    with open(muck_path, 'w', encoding='utf-8') as f:
        f.write("from langchain_core.messages import HumanMessage\n")
        f.write(f"muck_main_state = {result_str}\n")

    print(f"✅ muck.py 업데이트 완료: {muck_path}")

# 실행
save_to_muck(result)
```

---

### 방법 2: 수동 복사-붙여넣기

#### 1단계: result 출력

```python
import pprint
pprint.pprint(result)
```

#### 2단계: 출력된 내용 복사

터미널 출력 내용 전체를 복사

#### 3단계: muck.py에 붙여넣기

`src/utils/muck.py` 파일을 열고:

```python
from langchain_core.messages import HumanMessage

# 이 부분을 복사한 데이터로 교체
muck_main_state = {
    # 여기에 복사한 데이터 붙여넣기
}
```

---

## 특정 에이전트만 업데이트하기

### 예시: policy_agent만 다시 실행하고 업데이트

#### 1단계: 특정 에이전트만 실행

```python
from agents.analysis.policy_agent import policy_graph
from utils.muck import muck_main_state  # 기존 Muck 데이터 로드

# policy_agent만 실행
new_policy_result = policy_graph.invoke({
    "start_input": {
        "policy_period": "최근 1년",
        "policy_count": 2,
        "policy_list": "[2025.10.15, 2025.6.27]",
        "target_area": "서울시 송파구 신천동",
    }
})

# 결과 확인
print(new_policy_result['policy_output']['result'])
```

#### 2단계: Muck 데이터 부분 업데이트

```python
# 기존 Muck 데이터에서 policy 부분만 업데이트
muck_main_state['analysis_outputs']['policy_output'] = new_policy_result['policy_output']

# 저장 (방법 1의 save_to_muck 함수 사용)
save_to_muck(muck_main_state)
```

#### 3단계: main_agent_copy로 테스트

`src/agents/main/main_agent_copy_run.ipynb` 실행

```python
from agents.main.main_agent_copy import graph_builder
from utils.muck import muck_main_state

graph = graph_builder.compile()
result = await graph.ainvoke(muck_main_state)
```

---

## 실전 사용 예시

### 시나리오 1: jung_min_jae 프롬프트 수정 후 테스트

**상황:** SEGMENT_02 프롬프트를 수정하고 결과를 확인하고 싶음

**절차:**

1. **프롬프트 수정**
   ```yaml
   # src/prompts/jung_min_jae.yaml
   JUNG_MIN_JAE_SEGMENT_02:
     prompt: |
       (수정된 프롬프트)
   ```

2. **main_agent_copy로 빠른 테스트**
   ```python
   # src/agents/main/main_agent_copy_run.ipynb
   from agents.main.main_agent_copy import graph_builder
   from utils.muck import muck_main_state

   graph = graph_builder.compile()
   result = await graph.ainvoke(muck_main_state)
   ```

3. **결과 확인**
   - 약 5분 후 최종 보고서 확인
   - 이메일 수신

---

### 시나리오 2: 정책 데이터만 최신으로 업데이트

**상황:** 새로운 정책이 발표되어 policy_agent 결과만 업데이트하고 싶음

**절차:**

1. **policy_agent만 실행**
   ```python
   from agents.analysis.policy_agent import policy_graph
   from utils.muck import muck_main_state

   new_policy = policy_graph.invoke({
       "start_input": muck_main_state['start_input']
   })
   ```

2. **Muck 업데이트**
   ```python
   muck_main_state['analysis_outputs']['policy_output'] = new_policy['policy_output']
   save_to_muck(muck_main_state)
   ```

3. **최종 보고서 생성**
   ```python
   # main_agent_copy_run.ipynb
   result = await graph.ainvoke(muck_main_state)
   ```

---

### 시나리오 3: 처음부터 전체 실행 후 Muck 생성

**상황:** 새로운 사업지 분석을 시작

**절차:**

1. **main_agent 실행**
   ```python
   # src/agents/main/main_agent.ipynb
   result = await graph.ainvoke({
       "start_input": {
           "target_area": "부산 해운대구 우동",
           "total_units": "1500세대",
           "main_type": "84",
           ...
       }
   })
   ```

2. **Muck 저장**
   ```python
   save_to_muck(result)
   ```

3. **이후 빠른 테스트**
   - main_agent_copy 사용

---

## 주의사항

### 1. Muck 데이터 최신성 확인
- Muck 데이터는 한 번 저장하면 계속 사용됩니다
- 오래된 데이터일 수 있으므로 주기적으로 main_agent를 실행하여 갱신

### 2. start_input 일치 확인
- main_agent_copy는 Muck의 `start_input`을 사용합니다
- 다른 사업지를 분석하려면 새로 main_agent를 실행하거나 Muck의 start_input을 수정

### 3. 파일 크기 주의
- muck.py 파일은 매우 큽니다 (수만 줄)
- Git에 커밋할 때는 `.gitignore`에 추가 권장

---

## 빠른 참조

| 작업 | 사용 파일 | 소요 시간 |
|------|----------|----------|
| 전체 분석 실행 | `main_agent.ipynb` | ~30분 |
| Muck 데이터 저장 | `save_to_muck(result)` | ~1초 |
| jung_min_jae만 테스트 | `main_agent_copy_run.ipynb` | ~5분 |
| 특정 에이전트 업데이트 | 해당 agent 실행 + `save_to_muck` | ~10분 |

---

## 관련 파일

- **Muck 데이터:** `src/utils/muck.py`
- **전체 실행:** `src/agents/main/main_agent.ipynb`
- **빠른 테스트:** `src/agents/main/main_agent_copy_run.ipynb`
- **에이전트 구현:** `src/agents/main/main_agent_copy.py`
- **jung_min_jae 에이전트:** `src/agents/jung_min_jae/jung_min_jae_agent.py`

---

## 문제 해결

### Q: main_agent_copy 실행 시 에러 발생
**A:** Muck 데이터가 없거나 구조가 맞지 않음
- main_agent를 먼저 실행하여 Muck 생성
- muck.py 파일 구조 확인

### Q: 특정 에이전트 업데이트 후 반영 안됨
**A:** save_to_muck을 실행했는지 확인
```python
save_to_muck(muck_main_state)
```

### Q: 파일이 너무 커서 저장이 안됨
**A:** Python의 pprint 대신 pickle 사용 고려
```python
import pickle
with open('muck.pkl', 'wb') as f:
    pickle.dump(result, f)
```

---

**작성일:** 2025-11-09
**버전:** 1.0
