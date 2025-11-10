# Railway 배포 가이드

## 사전 준비

### 1. GitHub 저장소 준비
코드를 GitHub에 업로드해야 합니다.

1. GitHub에서 새 저장소 생성
2. 로컬에서 코드 푸시:
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/사용자명/저장소명.git
git push -u origin main
```

### 2. Railway 계정 생성
1. https://railway.app 접속
2. "Start a New Project" 클릭
3. GitHub로 로그인

## 배포 단계

### 1. 새 프로젝트 생성
1. Railway 대시보드에서 "New Project" 클릭
2. "Deploy from GitHub repo" 선택
3. GitHub 저장소 선택

### 2. 서비스 설정

#### FastAPI 서버 배포
1. "New Service" → "GitHub Repo" 선택
2. 저장소 선택
3. 설정:
   - **Root Directory**: (비워두기)
   - **Build Command**: (자동 감지)
   - **Start Command**: `uvicorn src.fastapi.main_api:app --host 0.0.0.0 --port $PORT`
   - **Port**: Railway가 자동으로 설정

#### Streamlit 앱 배포 (별도 서비스)
1. "New Service" → "GitHub Repo" 선택
2. 같은 저장소 선택
3. 설정:
   - **Root Directory**: (비워두기)
   - **Build Command**: (자동 감지)
   - **Start Command**: `streamlit run src/streamlit/web.py --server.address 0.0.0.0 --server.port $PORT`
   - **Port**: Railway가 자동으로 설정

### 3. 환경 변수 설정
Railway 대시보드에서 "Variables" 탭에서 다음 환경 변수 추가:

**필수:**
```
LANGSMITH_API_KEY=...
LANGSMITH_TRACING=false
TAVILY_API_KEY=...
OPENAI_API_KEY=...
R_ONE_API_KEY=...
POSTGRES_URL=...
MCP_KEY=...
PERPLEXITY_API_KEY=...
ANTHROPIC_API_KEY=...
```

**옵션:**
```
MATHPIX_API_KEY=...
MATHPIX_API_ID=...
```

### 4. PostgreSQL 데이터베이스 추가
1. "New Service" → "Database" → "Add PostgreSQL" 선택
2. 자동으로 생성됨
3. 생성된 데이터베이스의 "Variables" 탭에서 `POSTGRES_URL` 확인
4. 이 URL을 FastAPI 서비스의 환경 변수에 추가

### 5. 도메인 설정 (선택사항)
1. 서비스 선택 → "Settings" → "Generate Domain" 클릭
2. 자동으로 도메인 생성됨 (예: `your-app.up.railway.app`)
3. 커스텀 도메인도 연결 가능

## 배포 확인

### 1. 빌드 로그 확인
Railway 대시보드에서 "Deployments" 탭에서 빌드 진행 상황 확인

### 2. 로그 확인
"Logs" 탭에서 실시간 로그 확인

### 3. 접속 테스트
생성된 도메인으로 접속:
- FastAPI: `https://your-app.up.railway.app`
- Streamlit: `https://your-streamlit.up.railway.app`

## 문제 해결

### 빌드 실패 시
1. 로그 확인: "Deployments" → 실패한 배포 클릭 → 로그 확인
2. 의존성 문제: `pyproject.toml` 확인
3. Python 버전: Railway는 자동으로 감지하지만, 필요시 `runtime.txt` 파일 생성:
   ```
   python-3.12.11
   ```

### 환경 변수 오류
1. 모든 필수 환경 변수가 설정되었는지 확인
2. 서비스별로 환경 변수 설정 필요 (FastAPI와 Streamlit 각각)

### 포트 오류
- Railway는 `$PORT` 환경 변수를 자동으로 제공
- 코드에서 `$PORT` 사용 필수

## 비용

### 무료 플랜
- 월 $5 크레딧 제공
- 소규모 프로젝트에 충분
- 사용한 만큼만 과금

### 유료 플랜
- 월 $20부터
- 더 많은 리소스 제공
- 프로덕션 환경에 적합

## 주의사항

1. **환경 변수 보안**: 민감한 정보는 Railway의 환경 변수로만 관리
2. **데이터베이스 백업**: Railway PostgreSQL은 자동 백업 제공
3. **리소스 제한**: 무료 플랜은 제한적이므로 모니터링 필요
4. **Streamlit URL 수정**: 배포 후 Streamlit 앱의 FastAPI URL을 Railway 도메인으로 변경 필요

## Streamlit URL 수정

배포 후 `src/streamlit/web.py` 파일의 44번 줄을 수정:

```python
response = requests.post(
    "https://your-fastapi-app.up.railway.app/invoke",  # Railway 도메인으로 변경
    json=payload            
)
```

또는 환경 변수로 관리:
```python
import os
FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8080")

response = requests.post(
    f"{FASTAPI_URL}/invoke",
    json=payload            
)
```

환경 변수에 `FASTAPI_URL=https://your-fastapi-app.up.railway.app` 추가

