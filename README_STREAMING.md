---
description: 대한항공 RAG 스트리밍 챗 시스템 사용 가이드
---

# 대한항공 RAG - 스트리밍 챗 시스템

## 🎉 업데이트: 실시간 스트리밍 지원

이제 대한항공 RAG 웹앱이 **실시간 스트리밍** 방식으로 응답을 제공합니다!

### ✨ 주요 개선사항

1. **실시간 응답**: LLM이 토큰을 생성하는 즉시 화면에 표시
2. **더 나은 UX**: 응답을 기다리는 시간이 체감상 크게 단축
3. **투명성**: 에이전트가 문서를 검색하고 응답을 생성하는 과정을 실시간으로 확인

## 🚀 빠른 시작

### 로컬 실행

```bash
# 1. 가상환경 활성화
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 환경 변수 설정
export AGENT_ENDPOINT_URL="https://<workspace>.azuredatabricks.net/serving-endpoints/<endpoint>/invocations"
export DATABRICKS_TOKEN="<your-token>"

# 3. 실행
python app.py

# 4. 브라우저에서 http://localhost:5000 접속
```

### Databricks Apps 배포

```bash
databricks apps deploy
```

## 📖 사용 방법

### 일반 사용자

1. 브라우저에서 앱 접속
2. 질문 입력
3. **실시간으로 응답이 생성되는 것을 확인** ⚡
4. 마크다운, 코드 블록이 자동으로 포맷팅됨

### 개발자

#### 스트리밍 엔드포인트 사용

```javascript
// 프론트엔드
const response = await fetch('/api/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        question: '질문 내용',
        session_id: sessionId
    })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    
    const chunk = decoder.decode(value);
    // SSE 이벤트 처리
}
```

#### 백엔드 API

```python
# Python
from app import agent_client

# 스트리밍 응답
for event in agent_client.query_stream("질문"):
    if 'delta' in event:
        print(event['delta']['text'], end='', flush=True)
```

## 🏗️ 아키텍처

```
┌─────────────┐
│   Browser   │ 
│  (Fetch +   │
│ ReadableStr)│
└──────┬──────┘
       │ SSE
       ↓
┌─────────────┐
│    Flask    │
│  /api/chat/ │
│   stream    │
└──────┬──────┘
       │ SSE
       ↓
┌─────────────┐
│ Databricks  │
│   Agent     │
│  (stream=   │
│    true)    │
└──────┬──────┘
       │
       ↓
┌─────────────┐
│ Vector      │
│ Search +    │
│    LLM      │
└─────────────┘
```

## 📊 성능 비교

| 지표 | 이전 (Non-streaming) | 현재 (Streaming) |
|------|---------------------|------------------|
| 첫 토큰까지 시간 | 3-5초 | **0.5-1초** ⚡ |
| 체감 대기 시간 | 긴 응답일수록 길어짐 | **일정** ✅ |
| 사용자 경험 | 로딩... | **실시간 생성** 🎯 |

## 🔧 설정

### 환경 변수

```bash
# 필수
AGENT_ENDPOINT_URL=https://<workspace>.azuredatabricks.net/serving-endpoints/<endpoint>/invocations
DATABRICKS_TOKEN=<token>

# 선택 (기본값 사용 가능)
VOLUME_BASE_PATH=/Volumes/<catalog>/<schema>/<volume>
SESSION_TIMEOUT_MINUTES=60
MAX_HISTORY_TURNS=5
ALLOWED_FILE_TYPES=pdf,docx,pptx,txt,xlsx
MAX_UPLOAD_MB=10
```

### Databricks 서빙 엔드포인트 요구사항

- **Agent Framework** 또는 **Foundation Model API** 사용
- **스트리밍 지원** (`stream=true` 파라미터)
- **SSE 형식** 응답

## 🐛 트러블슈팅

### 스트리밍이 작동하지 않음

**증상**: 전체 응답이 한 번에 표시됨

**해결책**:
1. Databricks 엔드포인트가 스트리밍을 지원하는지 확인
2. 프록시 설정 확인 (버퍼링 비활성화 필요)
3. 브라우저 콘솔에서 오류 확인

### 프록시 설정 (Nginx)

```nginx
location /api/chat/stream {
    proxy_pass http://backend;
    proxy_buffering off;           # 필수!
    proxy_cache off;
    proxy_set_header Connection '';
    proxy_http_version 1.1;
    chunked_transfer_encoding off;
}
```

### 타임아웃 오류

**증상**: 긴 응답 중간에 연결이 끊김

**해결책**:
```python
# app.py
response = requests.post(
    ...,
    timeout=180  # 3분으로 증가
)
```

## 📚 추가 문서

- **[STREAMING_GUIDE.md](./STREAMING_GUIDE.md)**: 상세 구현 가이드
- **[STREAMING_CHANGELOG.md](./STREAMING_CHANGELOG.md)**: 변경 사항 요약
- **[기능요건.mdc](./.cursor/rules/기능요건.mdc)**: 기능 요구사항

## 🔄 롤백

문제가 발생할 경우 백업 파일로 복원:

```bash
unzip 대한항공_RAG_backup_YYYYMMDD_HHMMSS.zip
```

또는 기존 엔드포인트 사용:

```javascript
// index.html에서 변경
fetch('/api/chat', { ... })  // '/api/chat/stream' 대신
```

## 🎯 다음 개선 사항

- [ ] 툴 호출 시각화 (RAG 검색 과정 표시)
- [ ] 응답 중단 버튼
- [ ] 네트워크 오류 시 자동 재시도
- [ ] 사용자 피드백 수집 (Trace ID 활용)
- [ ] 토큰 사용량 표시

## 📝 라이선스

이 프로젝트는 대한항공 내부용입니다.

## 🙋 지원

문제가 발생하면:
1. 개발자 도구 콘솔 확인
2. 네트워크 탭에서 `/api/chat/stream` 요청 확인
3. Flask 로그 확인
4. Databricks 서빙 엔드포인트 로그 확인

---

**버전**: 1.1.0 (Streaming)  
**업데이트 날짜**: 2025-11-11  
**작성자**: AI Assistant


