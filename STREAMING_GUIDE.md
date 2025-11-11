---
description: 스트리밍 챗 구현 상세 가이드
---

# 스트리밍 챗 구현 가이드

## 개요

이 문서는 대한항공 RAG 웹앱의 스트리밍 기능 구현에 대해 설명합니다.

## 변경 사항 요약

### 백엔드 (Flask/Python)

#### 1. `DatabricksAgentClient` 클래스
- **`_build_headers()` 메서드 업데이트**: `streaming` 파라미터 추가
  - `streaming=True`일 때 `Accept: text/event-stream` 헤더 추가
  
- **`query_stream()` 메서드 추가**: 스트리밍 질의 처리
  - Databricks Agent API에 `stream=True` 파라미터 전송
  - SSE(Server-Sent Events) 형식으로 응답 수신
  - Python 제너레이터로 이벤트 스트림 반환

#### 2. 새로운 엔드포인트: `/api/chat/stream`
- SSE 스트리밍으로 실시간 응답 전송
- 이벤트 타입:
  - `session`: 세션 ID 전송
  - `delta`: 텍스트 청크 (실시간 누적)
  - `done`: 완료 신호 (전체 텍스트 포함)
  - `error`: 오류 발생
  - `[DONE]`: 스트림 종료 신호

#### 3. 기존 엔드포인트 유지
- `/api/chat`: 기존 방식 유지 (하위 호환성)

### 프론트엔드 (JavaScript)

#### 1. `sendMessage()` 함수 완전 재작성
- **이전**: 일반 fetch + 가상 타이핑 효과
- **현재**: fetch + ReadableStream으로 실시간 SSE 수신

#### 2. 실시간 렌더링
- 스트림 청크를 받을 때마다 마크다운 렌더링
- 자동 스크롤
- 코드 블록 하이라이팅

## 아키텍처

```
클라이언트 (브라우저)
    ↓ [fetch + ReadableStream]
Flask 백엔드 (/api/chat/stream)
    ↓ [SSE Generator]
Databricks Agent API (stream=true)
    ↓ [SSE]
Vector Search + LLM
```

## Databricks 스트리밍 API 형식

### 요청
```json
{
  "input": [
    {"role": "user", "content": "질문 내용"}
  ],
  "stream": true
}
```

### 응답 (SSE)
```
data: {"delta": {"text": "안"}, "event_type": "delta"}

data: {"delta": {"text": "녕"}, "event_type": "delta"}

data: {"delta": {"text": "하세요"}, "event_type": "delta"}

data: {"event_type": "response.completed"}

data: [DONE]
```

## 주요 구현 세부사항

### 백엔드

```python
def query_stream(self, question, history=None, uploaded_files=None):
    """에이전트에 스트리밍 질의"""
    payload = {
        'input': messages,
        'stream': True  # 핵심 파라미터
    }
    
    response = requests.post(
        self.endpoint_url,
        json=payload,
        headers=self._build_headers(streaming=True),
        stream=True  # requests 스트리밍 모드
    )
    
    # SSE 파싱
    for line in response.iter_lines():
        if line.startswith(b'data: '):
            data_str = line[6:].decode('utf-8')
            event_data = json.loads(data_str)
            yield event_data
```

### 프론트엔드

```javascript
// SSE 수신
const reader = response.body.getReader();
const decoder = new TextDecoder();
let buffer = '';
let accumulatedText = '';

while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    
    buffer += decoder.decode(value, { stream: true });
    
    // "data: {...}\n\n" 형식 파싱
    const lines = buffer.split('\n\n');
    buffer = lines.pop();
    
    for (const line of lines) {
        if (line.startsWith('data: ')) {
            const event = JSON.parse(line.substring(6));
            
            if (event.type === 'delta') {
                accumulatedText += event.text;
                textDiv.innerHTML = marked.parse(accumulatedText);
            }
        }
    }
}
```

## 운영 고려사항

### 1. 타임아웃 설정
- 백엔드: `timeout=120` (2분)
- 프론트엔드: 브라우저 기본 타임아웃 사용

### 2. 프록시 설정 (Nginx/ALB)
응답 버퍼링을 비활성화해야 스트리밍이 제대로 작동합니다:

```nginx
location /api/chat/stream {
    proxy_pass http://backend;
    proxy_buffering off;
    proxy_cache off;
    proxy_set_header Connection '';
    proxy_http_version 1.1;
    chunked_transfer_encoding off;
}
```

Flask 응답에 이미 `X-Accel-Buffering: no` 헤더가 포함되어 있습니다.

### 3. 오류 처리
- 네트워크 오류: 자동으로 catch되어 오류 메시지 표시
- 파싱 오류: 콘솔에 로그 출력, 계속 진행
- 서버 오류: SSE로 `error` 이벤트 전송

### 4. 성능
- 마크다운 렌더링은 매 청크마다 수행되지만, 브라우저가 효율적으로 처리
- 긴 응답의 경우 렌더링 주기를 조절할 수 있음 (현재는 모든 청크마다)

## 테스트

### 로컬 테스트
```bash
# 1. 가상환경 활성화
source venv/bin/activate

# 2. Flask 실행
python app.py

# 3. 브라우저에서 http://localhost:5000 접속
```

### 스트리밍 동작 확인
1. 질문 입력
2. 개발자 도구 → 네트워크 탭
3. `/api/chat/stream` 요청 확인
4. 응답 타입이 `text/event-stream`인지 확인
5. 텍스트가 실시간으로 나타나는지 확인

### Databricks 서빙 엔드포인트 설정
환경 변수에 다음을 설정:
```bash
AGENT_ENDPOINT_URL=https://<workspace>.azuredatabricks.net/serving-endpoints/<endpoint>/invocations
DATABRICKS_TOKEN=<your-token>
```

## 폴백 메커니즘

스트리밍이 지원되지 않는 경우를 대비해 기존 `/api/chat` 엔드포인트도 유지됩니다.

프론트엔드에서 필요시 다음과 같이 전환할 수 있습니다:

```javascript
// 스트리밍 시도
try {
    await streamingRequest();
} catch (error) {
    // 폴백: 일반 요청
    await normalRequest();
}
```

## 향후 개선 사항

1. **툴 호출 표시**: RAG 검색, 함수 호출 등의 중간 단계를 UI에 표시
2. **재시도 로직**: 네트워크 오류 시 자동 재시도
3. **부분 렌더링 최적화**: 긴 응답의 경우 렌더링 주기 조절
4. **피드백 수집**: 각 응답에 대한 사용자 피드백 (Trace ID 활용)

## 참고 자료

- [Databricks Foundation Model API - Streaming](https://docs.databricks.com/en/machine-learning/foundation-models/api-reference.html)
- [Databricks Agent Framework - Responses](https://docs.databricks.com/en/generative-ai/agent-framework/create-agent.html)
- [MDN - Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- [Flask - Streaming](https://flask.palletsprojects.com/en/3.0.x/patterns/streaming/)

## 변경 이력

- **2025-11-11**: 스트리밍 기능 추가
  - 백엔드: `/api/chat/stream` 엔드포인트 추가
  - 프론트엔드: ReadableStream 기반 실시간 렌더링
  - 기존 코드: ZIP으로 백업 (`대한항공_RAG_backup_*.zip`)


