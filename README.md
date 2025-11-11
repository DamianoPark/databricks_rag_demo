# 대한항공 RAG 시스템 ✈️

Databricks Agent Framework 기반의 문서 검색 및 질의응답 시스템입니다.  
**Streamlit**을 활용한 모던하고 직관적인 UI를 제공합니다.

> 💡 **이전 Flask 버전**은 `flask_version_backup_YYYYMMDD_HHMMSS.zip` 파일에 백업되어 있습니다.

## 🎯 주요 기능

### ✨ 사용자 경험
- **모던한 UI**: 그라디언트 배경과 카드 기반 레이아웃
- **실시간 스트리밍**: AI 응답이 생성되는 과정을 실시간으로 확인
- **직관적인 인터페이스**: Python 코드만으로 구현된 반응형 UI
- **Markdown 지원**: 코드 블록, 표, 리스트 등 풍부한 포맷팅

### 🚀 핵심 기능
1. **자연어 질의응답**: Databricks Agent를 통한 사내 문서 기반 RAG 응답
2. **세션 관리**: 대화 히스토리 자동 유지 및 세션 초기화
3. **파일 업로드**: Unity Catalog Volume에 문서 업로드 (드래그 앤 드롭 지원)
4. **문서 검색**: Vector Search 기반 관련 문서 자동 검색
5. **툴 사용 표시**: 문서 검색 중 상태를 실시간으로 표시

## 🛠️ 기술 스택

- **Framework**: Streamlit (Python)
- **Infrastructure**: Databricks Apps, Unity Catalog
- **AI**: Databricks Mosaic AI Agent, Vector Search
- **스타일링**: Custom CSS with Streamlit

## 📦 설치 및 설정

### 1. 프로젝트 클론 및 의존성 설치

```bash
cd /Users/jaewoo.park/Documents/work/대한항공_RAG

# 가상환경 생성 (선택사항)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`env.template` 파일을 복사하여 `.env` 파일을 생성하고 설정값을 입력합니다:

```bash
cp env.template .env
```

`.env` 파일 주요 설정:

```bash
# Databricks Agent 설정
AGENT_ENDPOINT_URL=https://your-workspace.azuredatabricks.net/serving-endpoints/your-agent/invocations
DATABRICKS_TOKEN=dapi...your-token...

# Unity Catalog 설정
CATALOG_NAME=koreanair_corp
SCHEMA_NAME=hr_docs
VOLUME_NAME=uploads

# Volume 경로 (로컬 테스트 시)
VOLUME_BASE_PATH=./local_volumes

# 세션 설정
SESSION_TIMEOUT_MINUTES=60
MAX_HISTORY_TURNS=5

# 파일 업로드 설정
ALLOWED_FILE_TYPES=pdf,docx,pptx,txt,xlsx
MAX_UPLOAD_MB=10

# 로깅
LOG_LEVEL=INFO
```

### 3. 필수 설정값 확인

#### Databricks Token 발급

1. Databricks 워크스페이스에 로그인
2. **User Settings** → **Developer** → **Access Tokens**
3. **Generate New Token** 클릭
4. Token을 복사하여 `.env` 파일의 `DATABRICKS_TOKEN`에 입력

#### Agent Endpoint URL 확인

1. Databricks 워크스페이스에서 **Serving** 메뉴로 이동
2. 사용할 Agent의 **Serving Endpoint** 확인
3. Endpoint URL을 복사하여 `.env` 파일에 입력

## 🚀 실행 방법

### macOS / Linux

```bash
# 실행 권한 부여 (최초 1회)
chmod +x run_streamlit.sh

# 앱 실행
./run_streamlit.sh
```

### Windows

```bash
run_streamlit.bat
```

### 수동 실행

```bash
# 가상환경 활성화 (옵션)
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate.bat  # Windows

# Streamlit 앱 실행
streamlit run streamlit_app.py
```

앱이 실행되면 브라우저에서 자동으로 http://localhost:8501 이 열립니다.

## 📁 프로젝트 구조

```
대한항공_RAG/
├── streamlit_app.py          # Streamlit 메인 앱
├── config.py                  # 설정 관리
├── requirements.txt           # Python 의존성
├── .env                       # 환경 변수 (수동 생성 필요)
├── env.template               # 환경 변수 템플릿
├── .streamlit/
│   └── config.toml           # Streamlit 설정 (테마, 서버)
├── run_streamlit.sh          # 실행 스크립트 (macOS/Linux)
├── run_streamlit.bat         # 실행 스크립트 (Windows)
├── local_volumes/            # 로컬 개발용 파일 저장소
├── README.md                 # 이 문서
└── flask_version_backup_*.zip # 이전 Flask 버전 백업
```

## 🎨 UI 기능

### 헤더
- 그라디언트 배경의 멋진 헤더
- 앱 제목과 설명 표시

### 사이드바
- **세션 정보**: 대화 수, 업로드 파일 수를 카드 형태로 표시
- **새 세션 시작**: 버튼 클릭으로 대화 초기화
- **파일 업로드**: 드래그 앤 드롭 또는 클릭으로 파일 선택
- **업로드된 파일 목록**: 파일명과 크기 표시
- **예시 질문**: 클릭 한 번으로 질문 입력

### 채팅 영역
- **사용자 메시지**: 👤 아이콘과 함께 표시
- **AI 응답**: ✈️ 아이콘과 함께 실시간 스트리밍
- **툴 사용 표시**: 문서 검색 중 상태 배지 표시
- **Markdown 렌더링**: 코드, 표, 리스트 등 자동 포맷팅

## 🔧 설정 커스터마이징

### 테마 변경

`.streamlit/config.toml` 파일에서 색상과 폰트를 변경할 수 있습니다:

```toml
[theme]
primaryColor = "#667eea"        # 주요 색상
backgroundColor = "#f5f7fa"     # 배경 색상
secondaryBackgroundColor = "#ffffff"  # 보조 배경
textColor = "#262730"           # 텍스트 색상
font = "sans serif"             # 폰트
```

### 서버 설정

```toml
[server]
port = 8501                     # 포트 번호
maxUploadSize = 10              # 최대 업로드 크기 (MB)
```

## 📊 Streamlit의 장점

### Flask 버전과의 비교

| 항목 | Flask | Streamlit |
|------|-------|-----------|
| 코드 라인 수 | ~900줄 | ~600줄 |
| UI 구현 | HTML/CSS/JS 수동 작성 | Python만으로 구현 |
| 상태 관리 | 수동 세션 관리 | `st.session_state` 자동 관리 |
| 스트리밍 | SSE 구현 필요 | 내장 지원 |
| 파일 업로드 | FormData 처리 필요 | `st.file_uploader()` |
| 반응성 | 수동 이벤트 처리 | 자동 재렌더링 |
| 개발 속도 | 느림 | 매우 빠름 |
| 유지보수 | 복잡 | 간단 |

### 주요 개선사항

1. **코드 간결성**: 33% 코드 감소 (900줄 → 600줄)
2. **개발 효율성**: HTML/CSS/JS 작성 불필요
3. **상태 관리**: Streamlit의 자동 세션 관리 활용
4. **반응성**: 사용자 입력에 대한 자동 재렌더링
5. **UI/UX**: 더 모던하고 직관적인 인터페이스

## 🐛 트러블슈팅

### 1. Streamlit이 설치되지 않음

```bash
pip install streamlit==1.31.0
```

### 2. 포트 8501이 이미 사용 중

```bash
# 다른 포트로 실행
streamlit run streamlit_app.py --server.port 8502
```

### 3. Agent 호출 실패 (401 Unauthorized)

- `DATABRICKS_TOKEN`이 유효한지 확인
- Agent 엔드포인트 URL이 올바른지 확인
- Service Principal 권한 확인

### 4. 파일 업로드 실패

- `.env` 파일에서 `DATABRICKS_TOKEN`이 올바르게 설정되었는지 확인
- Unity Catalog Volume 경로가 올바른지 확인
- 로컬 개발 모드에서는 `./local_volumes/uploads` 디렉토리가 자동 생성됨

### 5. 세션 초기화 문제

- 브라우저를 새로고침하면 세션이 초기화됩니다 (Streamlit 특성)
- 장기 세션이 필요한 경우 외부 저장소 사용 고려

## 🔐 권한 설정

### 필수 권한

#### 1. Unity Catalog 권한

앱이 실행되는 서비스 주체(Service Principal) 또는 사용자에게 다음 권한이 필요합니다:

```sql
-- Catalog 권한
GRANT USE CATALOG ON CATALOG koreanair_corp TO `service-principal-name`;

-- Schema 권한
GRANT USE SCHEMA ON SCHEMA koreanair_corp.hr_docs TO `service-principal-name`;

-- Volume 권한 (읽기/쓰기)
GRANT READ VOLUME, WRITE VOLUME ON VOLUME koreanair_corp.hr_docs.uploads TO `service-principal-name`;
```

#### 2. Vector Search Index 권한

```sql
-- Vector Search Index 읽기 권한
GRANT SELECT ON TABLE koreanair_docs_index TO `service-principal-name`;
```

#### 3. Serving Endpoint 권한

1. Databricks 워크스페이스에서 **Serving** → **Endpoints** 이동
2. Agent Endpoint 선택
3. **Permissions** 탭에서 서비스 주체에게 **Can Query** 권한 부여

## 📈 성능 최적화

1. **스트리밍 응답**: 답변을 실시간으로 표시하여 체감 속도 향상
2. **세션 상태 캐싱**: Streamlit의 세션 상태로 불필요한 API 호출 방지
3. **파일 업로드 최적화**: 로컬 캐싱 후 Volume 업로드

## 🎯 향후 개선 계획

- [ ] Databricks Apps 배포 가이드 추가
- [ ] 대화 내역 내보내기 (JSON, TXT)
- [ ] 다중 파일 업로드 지원
- [ ] 응답 평가 기능 (👍/👎)
- [ ] 문서 출처 표시 (Citations)
- [ ] 다크 모드 지원
- [ ] 사용자 피드백 수집

## 📝 환경변수 참조

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `AGENT_ENDPOINT_URL` | Databricks Agent REST API 엔드포인트 | 필수 |
| `DATABRICKS_TOKEN` | Databricks 인증 토큰 | 필수 |
| `VECTOR_SEARCH_INDEX` | Vector Search 인덱스 이름 | `koreanair_docs_index` |
| `CATALOG_NAME` | Unity Catalog 카탈로그 이름 | `koreanair_corp` |
| `SCHEMA_NAME` | Unity Catalog 스키마 이름 | `hr_docs` |
| `VOLUME_NAME` | Unity Catalog 볼륨 이름 | `uploads` |
| `VOLUME_BASE_PATH` | 볼륨 베이스 경로 | `./local_volumes` (로컬) |
| `SESSION_TIMEOUT_MINUTES` | 세션 타임아웃 (분) | `60` |
| `MAX_HISTORY_TURNS` | 최대 히스토리 턴 수 | `5` |
| `ALLOWED_FILE_TYPES` | 허용 파일 형식 (콤마 구분) | `pdf,docx,pptx,txt,xlsx` |
| `MAX_UPLOAD_MB` | 최대 업로드 파일 크기 (MB) | `10` |
| `LOG_LEVEL` | 로그 레벨 | `INFO` |

## 🤝 기여

이 프로젝트는 대한항공 사내 시스템입니다. 개선 사항이나 버그는 사내 이슈 트래커에 등록해주세요.

## 📄 라이선스

대한항공 내부 사용 전용

---

## 📞 문의

기술 지원이 필요한 경우 IT 지원팀으로 문의해주세요.

**Made with ❤️ using Streamlit and Databricks**
