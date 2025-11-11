# 대한항공 RAG 챗봇 시스템

Databricks Agent Framework 기반의 사내 문서 검색 및 질의응답 시스템

## 🎯 주요 기능

- **실시간 스트리밍 응답**: Server-Sent Events (SSE)를 통한 실시간 응답
- **세션 관리**: 대화 히스토리를 유지하며 맥락 기반 대화
- **파일 업로드**: Unity Catalog Volume에 파일 업로드 및 검색
- **마크다운 렌더링**: 코드 하이라이팅 및 마크다운 포맷팅
- **반응형 UI**: 모바일/태블릿/데스크톱 지원

## 🏗️ 아키텍처

```
User (Browser)
    ↓
Flask Web App (app.py)
    ↓
Databricks Agent (REST API)
    ↓
Vector Search Index
    ↓
Unity Catalog Volume (Documents)
```

## 📦 기술 스택

- **Backend**: Flask 3.0.0
- **Frontend**: Vanilla JavaScript + Marked.js + Highlight.js
- **Deployment**: Databricks Apps
- **Storage**: Unity Catalog Volume
- **AI**: Databricks Agent Framework

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env` 파일을 생성하고 다음 내용을 추가:

```bash
# Agent 설정
AGENT_ENDPOINT_URL=https://your-workspace.cloud.databricks.com/serving-endpoints/your-agent/invocations
DATABRICKS_TOKEN=your_databricks_token

# Unity Catalog 설정
CATALOG_NAME=your_catalog
SCHEMA_NAME=your_schema
VOLUME_NAME=your_volume
VOLUME_BASE_PATH=/Volumes/your_catalog/your_schema/your_volume

# 세션 설정
SESSION_TIMEOUT_MINUTES=60
MAX_HISTORY_TURNS=5

# 파일 업로드 설정
ALLOWED_FILE_TYPES=pdf,docx,pptx,txt,xlsx
MAX_UPLOAD_MB=10
```

### 3. 로컬 실행

```bash
python app.py
```

브라우저에서 `http://localhost:5000` 접속

## 📱 Databricks Apps 배포

### 사전 준비

1. Databricks CLI 설치:
```bash
pip install databricks-cli
```

2. Databricks 인증 설정:
```bash
databricks configure
```

### 배포 방법

#### 방법 1: 배포 스크립트 사용 (권장)

```bash
./deploy.sh
```

대화형 메뉴에서 선택:
- **1번**: 처음 배포 (Workspace 동기화 + 앱 배포)
- **2번**: 업데이트 배포 (기존 앱 업데이트)
- **3번**: Workspace 동기화만 (watch 모드)

#### 방법 2: 수동 배포

```bash
# Workspace에 파일 동기화
databricks sync . /Workspace/Users/your-email@company.com/your-app

# 앱 배포
databricks apps deploy your-app-name --source-code-path /Workspace/Users/your-email@company.com/your-app
```

### app.yaml 설정

배포 전 `app.yaml` 파일을 확인하고 필요한 값을 수정하세요:

```yaml
command:
  - "python"
  - "app.py"

env:
  - name: AGENT_ENDPOINT_URL
    value: "your-agent-endpoint"
  
  - name: DATABRICKS_TOKEN
    value: "YOUR_TOKEN_HERE"  # 실제 토큰으로 변경
  
  - name: CATALOG_NAME
    value: "your_catalog"
  
  # ... 기타 설정
```

**⚠️ 보안 주의사항**: `app.yaml`의 토큰은 배포 전에만 실제 값으로 변경하고, Git에는 절대 커밋하지 마세요!

더 안전한 방법은 Secret Scope를 사용하는 것입니다 (자세한 내용은 `SECURITY.md` 참조).

## 🎨 UI 특징

### 모던한 디자인
- 대한항공 브랜드 컬러 (#0047BB) 적용
- 부드러운 애니메이션과 트랜지션
- 직관적인 사용자 인터페이스

### 실시간 스트리밍
- 질문 즉시 상태 메시지 표시 ("문서를 검색하고 있습니다...")
- 응답을 실시간으로 받아서 표시
- 마크다운 포맷팅 및 코드 하이라이팅

### 스마트 스크롤
- 사용자가 스크롤 위치를 조정하면 자동 스크롤 중지
- 새 메시지 버튼으로 빠르게 최신 메시지로 이동
- 맨 아래에 있을 때만 자동 스크롤

## 📂 프로젝트 구조

```
대한항공_RAG/
├── app.py                 # Flask 애플리케이션 (메인)
├── config.py             # 설정 파일
├── requirements.txt      # Python 패키지
├── app.yaml             # Databricks Apps 설정
├── deploy.sh            # 배포 스크립트
├── .databricksignore    # 배포 제외 파일
├── templates/
│   └── index.html       # 메인 UI
├── static/
│   └── css/
│       └── style.css    # 스타일시트
└── local_volumes/       # 로컬 개발용 (Git 제외)
    └── uploads/
```

## 🔧 주요 구성 요소

### 1. Flask 애플리케이션 (app.py)

**SessionManager**: 세션 및 채팅 히스토리 관리
- `get_or_create_session()`: 세션 생성/조회
- `add_to_history()`: 대화 히스토리 추가
- `clear_old_sessions()`: 만료된 세션 정리

**DatabricksAgentClient**: Agent API 통신
- `query()`: 일반 질의 (비스트리밍)
- `query_stream()`: 스트리밍 질의 (SSE)

**VolumeUploader**: 파일 업로드 관리
- Unity Catalog Volume에 파일 저장
- 파일 타입 및 크기 검증
- 안전한 파일명 처리

### 2. API 엔드포인트

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/` | GET | 메인 페이지 |
| `/api/chat` | POST | 채팅 (비스트리밍) |
| `/api/chat/stream` | POST | 채팅 (스트리밍) |
| `/api/upload` | POST | 파일 업로드 |
| `/api/session/new` | POST | 새 세션 생성 |
| `/api/session/<id>/history` | GET | 세션 히스토리 조회 |
| `/health` | GET | 헬스체크 |

### 3. 프론트엔드

**주요 함수**:
- `sendMessage()`: 메시지 전송 및 스트리밍 처리
- `scrollToBottom()`: 스마트 스크롤 관리
- `createNewSession()`: 새 세션 시작
- `handleFileSelect()`: 파일 업로드 처리

**상태 관리**:
- `sessionId`: 현재 세션 ID
- `messageCount`: 대화 수
- `isUserScrolling`: 사용자 스크롤 여부
- `isSending`: 메시지 전송 중 여부

## 🔐 보안

### 토큰 관리

**개발 환경**: `.env` 파일 사용
```bash
DATABRICKS_TOKEN=your_token_here
```

**배포 환경**: Secret Scope 사용 (권장)
```yaml
resources:
  - name: databricks-token
    secret:
      scope: your-scope
      key: databricks-token
      permission: READ

env:
  - name: DATABRICKS_TOKEN
    valueFrom: "{{resources.databricks-token}}"
```

자세한 내용은 `SECURITY.md`를 참조하세요.

## 🐛 트러블슈팅

### 401 Unauthorized 오류
- `DATABRICKS_TOKEN` 환경 변수가 올바르게 설정되었는지 확인
- 토큰이 만료되지 않았는지 확인
- Service Principal 권한 확인

### 파일 업로드 실패
- Unity Catalog Volume 경로가 올바른지 확인
- Service Principal에 Volume 쓰기 권한이 있는지 확인
- 파일 크기가 제한 내인지 확인 (기본 10MB)

### 스트리밍 응답이 표시되지 않음
- 브라우저 콘솔에서 에러 메시지 확인
- Agent 엔드포인트가 정상 작동하는지 확인
- 네트워크 탭에서 SSE 연결 상태 확인

## 📊 성능 최적화

- **GPU 가속**: CSS transform 및 opacity 속성 사용
- **디바운싱**: 스크롤 이벤트 최적화
- **청크 단위 렌더링**: 대용량 응답 처리
- **코드 스플리팅**: 필요한 라이브러리만 로드

## 🔄 업데이트 내역

### 최신 버전 (2025-11-11)
- ✅ 타이핑 커서 효과 제거 (사용자 피드백 반영)
- ✅ 명확한 상태 메시지 추가
- ✅ CSS 스타일 시스템 전면 개선
- ✅ 스마트 스크롤 관리 시스템
- ✅ 보안 강화 (토큰 플레이스홀더)

## 📝 라이선스

Internal Use Only - 대한항공

## 🤝 기여

프로젝트 개선을 위한 제안이나 버그 리포트는 이슈를 생성해주세요.

## 📧 문의

기술 지원이 필요하신 경우 IT 헬프데스크로 연락주세요.
