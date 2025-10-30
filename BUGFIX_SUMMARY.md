# 버그 수정 및 디버깅 개선

## 배포 정보
- **배포 시각**: 2025-10-28 14:06 KST
- **배포 ID**: 01f0b4073e8f1e0e9f36e9ae1a2c0bed
- **상태**: ✅ SUCCEEDED

## 수정 사항

### 1. 한글 입력 시 중복 전송 문제 수정 ⭐

#### 문제
- 한글 입력 후 Enter 키를 누르면 질문이 2번 전송됨
- 예: "대한항공 합병 결정 시기" 입력 시 → "대한항공 합병 결정 시기"와 "기" 2개 전송

#### 원인
- IME(Input Method Editor) composition 이벤트와 keydown 이벤트가 충돌
- 한글 입력 완료(`compositionend`)와 Enter 키(`keydown`)가 거의 동시에 발생
- 중복 호출 방지 로직 부재

#### 해결 방법 (templates/index.html)

```javascript
// 상태 플래그 추가
let isComposing = false; // 한글 입력 중 여부
let isSending = false;   // 메시지 전송 중 여부

// composition 이벤트 리스너 추가
questionInput.addEventListener('compositionstart', () => {
    isComposing = true;
});

questionInput.addEventListener('compositionend', () => {
    isComposing = false;
});

// Enter 키 처리 수정 (한글 입력 중이 아닐 때만)
questionInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey && !isComposing) {
        e.preventDefault();
        sendMessage();
    }
});

// sendMessage 함수에 중복 호출 방지 추가
async function sendMessage() {
    const question = questionInput.value.trim();
    if (!question) return;
    
    // 중복 전송 방지
    if (isSending) {
        console.log('이미 전송 중입니다');
        return;
    }
    
    isSending = true;
    sendBtn.disabled = true;
    
    try {
        // ... 메시지 전송 로직 ...
    } finally {
        isSending = false;
        sendBtn.disabled = false;
    }
}
```

#### 효과
- ✅ 한글 입력 후 Enter 시 1번만 전송
- ✅ 영문 입력도 정상 작동
- ✅ 전송 중 중복 클릭 방지

---

### 2. Citations 디버깅 로그 추가 🔍

#### 추가된 백엔드 로그 (app.py)

```python
# Agent API 전체 응답 구조 로깅
logger.info(f"Agent 응답 구조 (키): {list(result.keys())}")
logger.info(f"전체 Agent 응답:\n{json.dumps(result, indent=2, ensure_ascii=False)}")

# Citations 추출 과정 상세 로깅
logger.info("=== Citations 추출 시작 ===")
logger.info(f"응답 최상위 키: {list(result.keys())}")

# 각 형식별 로깅
if 'citations' in result:
    logger.info("형식 1: 'citations' 필드 발견")
    logger.info(f"citations 타입: {type(raw_citations)}, 길이: {len(raw_citations)}")
    
if 'output' in result:
    logger.info("형식 2: 'output' 필드 확인")
    logger.info(f"output 배열 길이: {len(output)}")
    for idx, item in enumerate(output):
        logger.info(f"output[{idx}] type: {item_type}, keys: {list(item.keys())}")

# ... (trace, data 필드도 동일하게 상세 로깅)

logger.info(f"=== Citations 추출 완료: {len(citations)}개 ===")
```

#### 추가된 프론트엔드 로그 (templates/index.html)

```javascript
// API 응답 디버깅
console.log('=== Citations 디버그 ===');
console.log('전체 응답 데이터:', data);
console.log('citations 존재 여부:', 'citations' in data);
console.log('citations 값:', data.citations);
console.log('citations 타입:', typeof data.citations);
console.log('citations 길이:', data.citations ? data.citations.length : 'N/A');

// Citations 함수 호출 추적
console.log('addCitationsToMessage 호출됨');
console.log('messageDiv:', messageDiv);
console.log('citations:', citations);
console.log('정렬된 citations:', sortedCitations);

// HTML 추가 확인
console.log('message-content 찾음:', messageContent);
console.log('Citations HTML 추가 완료');
```

#### 효과
- ✅ Databricks Agent API 실제 응답 형식 확인 가능
- ✅ Citations가 어느 필드에 있는지 파악 가능
- ✅ 정규화 과정 추적 가능
- ✅ 프론트엔드까지 데이터 전달 여부 확인 가능

---

## 디버깅 방법

### 1. 백엔드 로그 확인
```bash
# Databricks Apps 로그 조회
databricks workspace export /Users/jaewoo.park@databricks.com/jw-rag-chat/.databricks/apps/logs/app.log

# 또는 UI에서
# Databricks Apps > jw-rag-chat > Logs 탭
```

### 2. 프론트엔드 로그 확인
```
1. 브라우저에서 앱 접속
2. F12 또는 Cmd+Option+I로 개발자 도구 열기
3. Console 탭에서 로그 확인
```

### 3. Citations 문제 진단 순서

**Step 1: Agent API 응답 확인**
```
로그에서 "전체 Agent 응답:" 검색
→ citations, sources, output, trace, data 중 어떤 필드에 문서 정보가 있는지 확인
```

**Step 2: Citations 추출 확인**
```
로그에서 "=== Citations 추출 시작 ===" 검색
→ 어떤 형식에서 추출을 시도했는지 확인
→ "정규화된 citations 수" 확인
```

**Step 3: 프론트엔드 전달 확인**
```
브라우저 Console에서 "=== Citations 디버그 ===" 검색
→ citations 데이터가 전달되었는지 확인
→ addCitationsToMessage가 호출되었는지 확인
```

**Step 4: API 응답 형식에 맞게 추출 로직 수정**
```python
# app.py의 _extract_citations 함수에 새 형식 추가
if 'your_custom_field' in result:
    logger.info("새 형식 발견!")
    citations = _normalize_citations(result['your_custom_field'])
```

---

## 테스트 체크리스트

### 한글 입력 테스트
- [ ] "대한항공" 입력 후 Enter → 1번만 전송되는지 확인
- [ ] "복리후생 제도" 입력 후 Enter → 1번만 전송되는지 확인
- [ ] 전송 중 Enter 연타 → 무시되는지 확인
- [ ] 전송 버튼 클릭 연타 → 무시되는지 확인

### Citations 디버깅 테스트
- [ ] 질문 입력 후 F12 Console 확인
- [ ] "=== Citations 디버그 ===" 로그 확인
- [ ] citations 데이터 구조 확인
- [ ] 백엔드 로그에서 Agent 응답 구조 확인

### 기능 테스트
- [ ] 영문 입력도 정상 작동하는지 확인
- [ ] Shift+Enter로 줄바꿈 가능한지 확인
- [ ] 예시 질문 클릭 시 정상 작동하는지 확인

---

## 다음 단계

1. **실제 Agent API 응답 확인**
   - 로그를 확인하여 실제 응답 형식 파악
   - 필요 시 `_extract_citations` 함수에 해당 형식 추가

2. **Citations UI 확인**
   - 실제로 Citations가 표시되는지 테스트
   - 스타일이 제대로 적용되는지 확인

3. **디버깅 로그 정리**
   - 문제 해결 후 상세 로그 레벨 조정 (INFO → DEBUG)
   - 프로덕션 환경에서는 console.log 제거 고려

---

## 관련 파일
- `templates/index.html`: 한글 입력 수정, 프론트엔드 디버깅 로그
- `app.py`: 백엔드 디버깅 로그, Citations 추출 로직

