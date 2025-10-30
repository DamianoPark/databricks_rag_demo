# 대한항공 RAG 웹앱 - 아키텍처 및 권한 관리

## 목차
1. [개요](#개요)
2. [시스템 아키텍처](#시스템-아키텍처)
3. [권한 요구사항](#권한-요구사항)
4. [설정 가이드](#설정-가이드)
5. [보안 고려사항](#보안-고려사항)
6. [트러블슈팅](#트러블슈팅)

---

## 개요

### 앱 정보
- **앱 이름**: jw-rag-chat (대한항공 RAG 채팅 웹앱)
- **목적**: Databricks Agent 기반 RAG 질의응답 시스템
- **배포 환경**: Databricks Apps
- **프레임워크**: Flask (Python)

### 주요 기능
1. ✅ RAG 기반 질의응답
2. ✅ 세션 및 대화 히스토리 관리
3. ✅ 파일 업로드 (Unity Catalog Volume)
4. ✅ 한글 파일명 지원
5. ✅ 디버그 엔드포인트

---

## 시스템 아키텍처

### 전체 구조도

```
┌─────────────────────────────────────────────────────────────┐
│                        사용자 브라우저                         │
│                    (웹 인터페이스)                            │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            │ HTTPS
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  Databricks Apps (Flask)                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Service Principal                                   │   │
│  │  - 앱 대신 리소스 접근                               │   │
│  │  - DATABRICKS_TOKEN으로 인증                        │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────┐  ┌──────────────────────────────┐   │
│  │  Session Manager │  │  VolumeUploader              │   │
│  │  - 세션 관리     │  │  - Files API 사용            │   │
│  │  - 히스토리 저장 │  │  - 한글 파일명 지원          │   │
│  └──────────────────┘  └──────────────────────────────┘   │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  DatabricksAgentClient                               │   │
│  │  - Agent API 호출                                    │   │
│  │  - 히스토리 전달                                     │   │
│  └─────────────────────────────────────────────────────┘   │
└───────────────┬──────────────────────┬──────────────────────┘
                │                      │
                │ API Call             │ Files API
                ↓                      ↓
┌──────────────────────────┐  ┌──────────────────────────────┐
│  Databricks Agent         │  │  Unity Catalog Volume        │
│  (Serving Endpoint)       │  │  /Volumes/catalog/schema/vol │
│                           │  │                              │
│  - Vector Search          │  │  - 파일 저장                 │
│  - LLM 추론               │  │  - 읽기/쓰기 권한 필요       │
│  - RAG 처리               │  │                              │
└──────────────────────────┘  └──────────────────────────────┘
```

### 컴포넌트 설명

#### 1. Flask 웹 애플리케이션
- **역할**: 사용자 인터페이스 제공, API 라우팅
- **주요 엔드포인트**:
  - `/` - 메인 페이지
  - `/api/chat` - 채팅 API
  - `/api/upload` - 파일 업로드
  - `/api/session/new` - 새 세션 생성
  - `/health` - 헬스체크
  - `/debug/auth` - 인증 디버그
  - `/debug/volume` - Volume 디버그

#### 2. SessionManager
- **역할**: 세션 및 대화 히스토리 관리
- **기능**:
  - 세션 생성 및 조회
  - 대화 히스토리 저장
  - 만료된 세션 자동 정리
  - 최대 턴 수 제한

#### 3. DatabricksAgentClient
- **역할**: Databricks Agent API 연동
- **기능**:
  - Agent 엔드포인트 호출
  - 히스토리 포함 질의
  - 인증 토큰 관리
  - 에러 처리

#### 4. VolumeUploader
- **역할**: Unity Catalog Volume 파일 업로드
- **기능**:
  - 로컬 임시 저장 (`/tmp/uploads`)
  - Files API를 통한 Volume 업로드
  - 한글 파일명 보존
  - 환경 자동 감지 (Databricks/로컬)

---

## 권한 요구사항

### 1. 인증 방식

#### ⚠️ 현재 상태 (개인 토큰 사용)

**현재 설정**: 개인 사용자 토큰을 사용하여 인증
```yaml
# app.yaml (현재)
- name: DATABRICKS_TOKEN
  value: "dapi*********************"  # 개인 토큰 (보안을 위해 마스킹)
```

**보안 위험**:
- ⚠️ 개인 토큰이 코드/설정에 노출됨
- ⚠️ 토큰 소유자의 모든 권한이 앱에 부여됨
- ⚠️ 토큰 소유자가 퇴사/이동 시 앱 작동 중단
- ⚠️ 감사 추적이 개인 계정으로 기록됨

#### ✅ 권장 방식 (Service Principal 사용)

Databricks Apps는 **Service Principal**을 사용하여 리소스에 접근하는 것이 권장됩니다.

**Service Principal 생성:**
```bash
# Databricks CLI 사용
databricks service-principals create \
  --display-name "jw-rag-chat-sp"
```

**토큰 생성:**
```bash
# Service Principal에 대한 토큰 생성
databricks tokens create \
  --service-principal-id <SP_ID> \
  --comment "RAG Chat App Token"
```

**장점**:
- ✅ 앱 전용 ID로 명확한 권한 분리
- ✅ Secrets를 통한 안전한 토큰 관리
- ✅ 개인 계정과 독립적인 운영
- ✅ 명확한 감사 추적

### 2. 필수 권한

#### A. Serving Endpoint 권한

**리소스**: `agents_jaewoo_catalog-mlfow_eval-rag_agent_v1`

- **권한 레벨**: 쿼리 가능 (Can Query)
- **목적**: Agent API 호출
- **설정 위치**: Databricks Apps 설정 → 앱 리소스

```yaml
# app.yaml에서 참조되는 엔드포인트
AGENT_ENDPOINT_URL: "https://e2-demo-field-eng.cloud.databricks.com/serving-endpoints/agents_jaewoo_catalog-mlfow_eval-rag_agent_v1/invocations"
```

#### B. Unity Catalog Volume 권한

**리소스**: `/Volumes/jaewoo_catalog/mlfow_eval/volume01`

- **권한 레벨**: 읽기 및 쓰기 가능 (Read & Write)
- **목적**: 파일 업로드 및 저장
- **설정 위치**: Databricks Apps 설정 → 앱 리소스

```yaml
# app.yaml에서 설정
VOLUME_BASE_PATH: "/Volumes/jaewoo_catalog/mlfow_eval/volume01"
```

### 3. 권한 매트릭스

| 리소스 타입 | 리소스 경로 | 필요 권한 | 사용 용도 |
|------------|-----------|---------|----------|
| Serving Endpoint | `agents_jaewoo_catalog-mlfow_eval-rag_agent_v1` | Can Query | Agent API 호출 |
| UC Volume | `/Volumes/jaewoo_catalog/mlfow_eval/volume01` | Read & Write | 파일 업로드/저장 |
| Catalog | `jaewoo_catalog` | USE | Volume 접근 |
| Schema | `jaewoo_catalog.mlfow_eval` | USE | Volume 접근 |

### 4. Databricks Apps 리소스 키

```yaml
앱 리소스 설정:
  - 리소스 타입: serving-endpoint
    리소스 이름: agents_jaewoo_catalog-mlfow_eval-rag_agent_v1
    권한: 쿼리 가능
    리소스 키: serving-endpoint

  - 리소스 타입: volume
    리소스 경로: /Volumes/jaewoo_catalog/mlfow_eval/volume01
    권한: 읽기 및 쓰기 가능
    리소스 키: volume
```

---

## 설정 가이드

### 1. 환경 변수 설정 (app.yaml)

```yaml
command:
  - "python"
  - "app.py"

env:
  # === Agent 설정 ===
  - name: AGENT_ENDPOINT_URL
    value: "https://<workspace>/serving-endpoints/<endpoint>/invocations"
  
  # === 인증 설정 ===
  - name: DATABRICKS_TOKEN
    value: "dapi..."  # Service Principal 토큰
  
  # === Unity Catalog 설정 ===
  - name: CATALOG_NAME
    value: "jaewoo_catalog"
  
  - name: SCHEMA_NAME
    value: "mlfow_eval"
  
  - name: VOLUME_NAME
    value: "volume01"
  
  - name: VOLUME_BASE_PATH
    value: "/Volumes/jaewoo_catalog/mlfow_eval/volume01"
  
  # === Vector Search (선택사항) ===
  - name: VECTOR_SEARCH_INDEX
    value: "jaewoo_catalog.mlfow_eval.index_oai"
  
  # === 앱 설정 ===
  - name: SESSION_TIMEOUT_MINUTES
    value: "60"
  
  - name: MAX_HISTORY_TURNS
    value: "5"
  
  - name: ALLOWED_FILE_TYPES
    value: "pdf,docx,pptx,txt,xlsx"
  
  - name: MAX_UPLOAD_MB
    value: "10"
  
  - name: LOG_LEVEL
    value: "INFO"
  
  - name: PORT
    value: "8000"
```

### 2. Service Principal 권한 설정

#### 단계 1: Apps 설정 페이지 접근
```
Databricks Workspace → Apps → jw-rag-chat → 설정
```

#### 단계 2: 앱 리소스 추가

**Serving Endpoint 추가:**
```
1. "앱 리소스" 섹션 → "리소스 추가"
2. 리소스 타입: serving-endpoint
3. 엔드포인트 선택: agents_jaewoo_catalog-mlfow_eval-rag_agent_v1
4. 권한: 쿼리 가능
5. 저장
```

**UC Volume 추가:**
```
1. "앱 리소스" 섹션 → "리소스 추가"
2. 리소스 타입: volume
3. 경로 입력: /Volumes/jaewoo_catalog/mlfow_eval/volume01
4. 권한: 읽기 및 쓰기 가능
5. 저장
```

#### 단계 3: 배포
```bash
databricks apps deploy jw-rag-chat
```

### 3. 권한 확인

#### A. 디버그 엔드포인트로 확인

**인증 확인:**
```bash
curl https://<workspace>/apps/jw-rag-chat/debug/auth
```

예상 응답:
```json
{
  "agent_endpoint_url": "https://...",
  "token_present": true,
  "token_sources": {
    "config": false,
    "env_DATABRICKS_TOKEN": true,
    "env_DATABRICKS_APP_TOKEN": false
  },
  "token_preview": "dapi***abc123"
}
```

**Volume 확인:**
```bash
curl https://<workspace>/apps/jw-rag-chat/debug/volume
```

예상 응답:
```json
{
  "configured_path": "/Volumes/jaewoo_catalog/mlfow_eval/volume01",
  "use_files_api": true,
  "is_databricks": true,
  "files_api_status": "enabled",
  "checks": {
    "local_temp_exists": true,
    "local_temp_writable": true,
    "can_write_local": true
  }
}
```

#### B. 로그 확인

```bash
# 앱 로그 조회
databricks apps logs jw-rag-chat

# 주요 확인 사항
# - "VolumeUploader 초기화 완료: use_files_api=True"
# - "Agent 호출 성공"
# - "Files API 업로드 완료"
```

---

## 보안 고려사항

### 1. 토큰 관리

#### 🔴 현재 상태 (개선 필요)
```yaml
# 현재 app.yaml
- name: DATABRICKS_TOKEN
  value: "dapi*********************"  # ❌ 하드코딩됨! (보안을 위해 마스킹)
```

**문제점**:
- 개인 토큰이 설정 파일에 노출
- Git에 커밋되면 보안 위험
- 토큰 갱신 시 앱 재배포 필요

#### ✅ 권장 방법 (Databricks Secrets 사용)

**1단계: Secret Scope 생성**
```bash
databricks secrets create-scope rag-app
```

**2단계: Service Principal 토큰을 Secret으로 저장**
```bash
# Service Principal 토큰 생성 후
databricks secrets put \
  --scope rag-app \
  --key databricks-token \
  --string-value "dapi..."
```

**3단계: app.yaml에서 Secret 참조**
```yaml
# 개선된 app.yaml
- name: DATABRICKS_TOKEN
  value: "{{secrets/rag-app/databricks-token}}"  # ✅ Secret 참조
```

**장점**:
- ✅ 토큰이 코드에 노출되지 않음
- ✅ 중앙 집중식 토큰 관리
- ✅ 토큰 교체 시 앱 재배포 불필요
- ✅ 접근 권한 제어 가능

### 2. 최소 권한 원칙

Service Principal에는 **필요한 최소한의 권한**만 부여합니다.

```
✅ 필요한 권한:
  - Serving Endpoint: Can Query
  - UC Volume: Read & Write
  - Catalog/Schema: USE

❌ 불필요한 권한:
  - Workspace Admin
  - Can Manage (Endpoint)
  - ALL PRIVILEGES (Volume)
```

### 3. 네트워크 보안

```yaml
# 필요 시 앱 접근 제한
access_control:
  # 특정 그룹만 접근 허용
  - group: "data-science-team"
    permission: "CAN_USE"
```

### 4. 파일 업로드 보안

```python
# config.py에서 설정된 제한
ALLOWED_FILE_TYPES = {'pdf', 'docx', 'pptx', 'txt', 'xlsx'}
MAX_UPLOAD_MB = 10

# 파일명 보안
# - 경로 구분자 제거 (/, \, :)
# - 특수문자 필터링 (*, ?, ", <, >, |)
# - 제어 문자 제거
```

### 5. 세션 관리

```python
# 세션 타임아웃 설정
SESSION_TIMEOUT_MINUTES = 60

# 히스토리 제한
MAX_HISTORY_TURNS = 5

# 만료된 세션 자동 정리
SessionManager.clear_old_sessions()  # /health 호출 시
```

---

## 트러블슈팅

### 1. 권한 오류

#### 문제: "Permission denied: /Volumes"
```json
{
  "error": "[Errno 13] Permission denied: '/Volumes'"
}
```

**원인**: Volume에 대한 읽기/쓰기 권한 없음

**해결**:
1. Databricks Apps 설정에서 Volume 리소스 추가
2. 권한을 "읽기 및 쓰기 가능"으로 설정
3. 앱 재배포

#### 문제: "401 Unauthorized"
```json
{
  "error": "Agent API error: 401 Unauthorized"
}
```

**원인**: DATABRICKS_TOKEN 미설정 또는 잘못됨

**해결**:
1. `app.yaml`에서 DATABRICKS_TOKEN 확인
2. Service Principal 토큰이 유효한지 확인
3. `/debug/auth` 엔드포인트로 토큰 상태 확인

#### 문제: "404 Not Found (Agent)"
```json
{
  "error": "Agent endpoint not found"
}
```

**원인**: Agent 엔드포인트 URL 오류 또는 권한 없음

**해결**:
1. AGENT_ENDPOINT_URL 확인
2. Serving Endpoint 리소스 추가 확인
3. "쿼리 가능" 권한 확인

### 2. 파일 업로드 오류

#### 문제: "Files API 업로드 실패"
```json
{
  "error": "Files API upload failed: 403 Forbidden"
}
```

**원인**: Volume 쓰기 권한 없음

**해결**:
1. Volume 리소스 권한을 "읽기 및 쓰기 가능"으로 변경
2. 앱 재배포
3. `/debug/volume` 엔드포인트로 상태 확인

#### 문제: "한글 파일명 깨짐"
```
업로드된 파일명: "_____.pdf" (원본: "문서.pdf")
```

**원인**: 이전 `secure_filename` 사용

**해결**:
현재 버전에서는 `safe_filename` 메서드가 한글을 지원합니다.
최신 코드로 업데이트하세요.

### 3. 성능 문제

#### 문제: "응답 시간이 너무 길다"

**확인 사항**:
1. Agent 응답 시간 확인 (로그)
2. Vector Search 인덱스 상태
3. 히스토리 턴 수 (MAX_HISTORY_TURNS)

**최적화**:
```yaml
# 히스토리 제한
MAX_HISTORY_TURNS: "3"  # 5에서 3으로 감소

# 타임아웃 조정
timeout: 120  # Agent 호출 타임아웃
```

### 4. 디버깅 도구

#### 로그 레벨 조정
```yaml
# 상세 로그
LOG_LEVEL: "DEBUG"
```

#### 헬스체크
```bash
curl https://<workspace>/apps/jw-rag-chat/health
```

예상 응답:
```json
{
  "status": "healthy",
  "active_sessions": 3
}
```

#### 세션 히스토리 조회
```bash
curl https://<workspace>/apps/jw-rag-chat/api/session/<session-id>/history
```

---

## 배포 체크리스트

### 배포 전

#### 현재 설정 (개인 토큰 사용 시)
- [x] 개인 Databricks 토큰 발급 완료
- [x] `app.yaml`에 토큰 직접 입력
- [ ] ⚠️ **보안 개선 필요**: Secret으로 전환 권장
- [x] Agent 엔드포인트 URL 확인
- [x] Volume 경로 확인
- [x] 앱 리소스 권한 설정 완료

#### 권장 설정 (Service Principal 사용 시)
- [ ] Service Principal 생성 완료
- [ ] Service Principal 토큰 생성 완료
- [ ] Secret Scope 생성 및 토큰 저장
- [ ] `app.yaml`에서 Secret 참조로 변경
- [ ] Agent 엔드포인트 URL 확인
- [ ] Volume 경로 확인
- [ ] 앱 리소스 권한 설정 완료

### 배포 중
```bash
# 배포 명령
databricks apps deploy jw-rag-chat

# 배포 상태 확인
databricks apps list
databricks apps get jw-rag-chat
```

### 배포 후
- [ ] `/health` 엔드포인트 확인
- [ ] `/debug/auth` 엔드포인트 확인
- [ ] `/debug/volume` 엔드포인트 확인
- [ ] 채팅 기능 테스트
- [ ] 파일 업로드 테스트
- [ ] 한글 파일명 테스트
- [ ] 세션 관리 테스트
- [ ] 로그 확인

---

## 참고 자료

### Databricks 문서
- [Databricks Apps](https://docs.databricks.com/en/dev-tools/databricks-apps/index.html)
- [Service Principals](https://docs.databricks.com/en/administration-guide/users-groups/service-principals.html)
- [Unity Catalog Volumes](https://docs.databricks.com/en/connect/unity-catalog/volumes.html)
- [Files API](https://docs.databricks.com/api/workspace/files/upload)
- [Agent Framework](https://docs.databricks.com/en/generative-ai/agent-framework/index.html)

### 프로젝트 문서
- `README.md` - 프로젝트 개요
- `QUICKSTART.md` - 빠른 시작 가이드
- `DEPLOYMENT.md` - 배포 가이드
- `DEPLOYMENT_HISTORY.md` - 배포 이력

---

---

## 보안 개선 로드맵

### 우선순위 1: 토큰 관리 개선 (즉시)

**현재 상태**:
```yaml
DATABRICKS_TOKEN: "dapi*********************"  # 개인 토큰 하드코딩 (보안을 위해 마스킹)
```

**개선 단계**:

1. **Secret으로 전환** (단기)
   ```bash
   # Secret 생성
   databricks secrets create-scope rag-app
   databricks secrets put --scope rag-app --key databricks-token
   
   # app.yaml 수정
   DATABRICKS_TOKEN: "{{secrets/rag-app/databricks-token}}"
   ```

2. **Service Principal 전환** (중기)
   ```bash
   # SP 생성 및 권한 부여
   databricks service-principals create --display-name "jw-rag-chat-sp"
   # SP 토큰을 Secret에 저장
   ```

### 우선순위 2: 권한 최소화

**현재**: 개인 계정의 모든 권한 사용  
**목표**: 앱에 필요한 최소 권한만 부여

```
필요 권한:
- Serving Endpoint: Can Query (agents_jaewoo_catalog-mlfow_eval-rag_agent_v1)
- UC Volume: Read & Write (/Volumes/jaewoo_catalog/mlfow_eval/volume01)

불필요 권한 제거:
- Workspace 전체 접근
- 다른 Catalog/Schema 접근
- 클러스터 관리 등
```

### 우선순위 3: 감사 및 모니터링

- [ ] 앱 접근 로그 설정
- [ ] 토큰 사용 모니터링
- [ ] 비정상 활동 알림 설정

---

## 연락처

기술 지원 또는 문의사항은 개발팀에 연락주세요.

**현재 상태**: 개인 토큰 사용 (보안 개선 권장)  
**버전**: 1.0  
**최종 업데이트**: 2025-10-28

