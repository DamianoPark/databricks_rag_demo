# 대한항공 RAG 웹앱

Flask 기반 RAG(Retrieval-Augmented Generation) 질의응답 시스템으로, Databricks Apps에 배포하여 사용합니다.

## 📋 주요 기능

- **자연어 질의응답**: Databricks Agent를 통한 사내 문서 기반 RAG 응답
- **세션 관리**: 대화 히스토리를 유지하여 맥락 있는 대화 지원
- **파일 업로드**: Unity Catalog Volume에 문서 업로드 및 검색
- **근거 문서 표시**: 응답에 사용된 문서 출처 제공
- **모던 UI**: 직관적이고 사용하기 쉬운 채팅 인터페이스

## 🛠️ 기술 스택

- **Backend**: Flask (Python)
- **Frontend**: Vanilla JavaScript + CSS
- **Infrastructure**: Databricks Apps, Unity Catalog
- **AI**: Databricks Mosaic AI Agent, Vector Search

## 📦 설치 및 설정

### 1. 프로젝트 클론 및 의존성 설치

```bash
cd /Users/jaewoo.park/Documents/work/대한항공_RAG
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 환경 변수 설정

프로젝트 루트에 `.env` 파일을 생성하고 다음 내용을 입력합니다:

```bash
# Databricks Agent 설정
AGENT_ENDPOINT_URL=https://adb-xxxx.azuredatabricks.net/serving-endpoints/your-agent/invocations
DATABRICKS_TOKEN=your_databricks_personal_access_token

# Vector Search 설정
VECTOR_SEARCH_INDEX=koreanair_docs_index

# Unity Catalog 설정
CATALOG_NAME=koreanair_corp
SCHEMA_NAME=hr_docs
VOLUME_NAME=uploads

# Volume 베이스 경로 (로컬 테스트 시)
VOLUME_BASE_PATH=./local_volumes

# 세션 설정
SESSION_TIMEOUT_MINUTES=60
MAX_HISTORY_TURNS=5

# 파일 업로드 설정
ALLOWED_FILE_TYPES=pdf,docx,pptx,txt,xlsx
MAX_UPLOAD_MB=10

# Flask 설정
SECRET_KEY=your_random_secret_key_here
FLASK_DEBUG=True

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

## 🚀 로컬 실행 (테스트)

### 1. 로컬 테스트 디렉토리 생성

```bash
mkdir -p ./local_volumes/uploads
```

### 2. 애플리케이션 실행

```bash
python app.py
```

### 3. 브라우저에서 접속

```
http://localhost:5000
```

### 4. 로컬 테스트 시 주의사항

- 로컬에서는 실제 Unity Catalog Volume이 아닌 `./local_volumes` 디렉토리를 사용합니다
- Databricks Agent API 호출은 실제 엔드포인트를 사용하므로 유효한 토큰이 필요합니다
- 파일 업로드 기능은 로컬 파일시스템에 저장됩니다

## 📤 Databricks Apps 배포

### 1. 배포 준비

프로젝트 루트에 `databricks.yml` 파일을 생성합니다:

```yaml
# databricks.yml
bundle:
  name: koreanair-rag-app

workspace:
  host: https://adb-xxxx.azuredatabricks.net
  
resources:
  apps:
    koreanair_rag:
      name: koreanair-rag-app
      description: "대한항공 RAG 질의응답 시스템"
      
      # Python 앱 설정
      source_code_path: .
      
      # 환경변수 (민감정보는 Databricks Secrets 사용)
      config:
        env:
          - name: AGENT_ENDPOINT_URL
            value: "{{secrets/koreanair-rag/agent-endpoint-url}}"
          - name: DATABRICKS_TOKEN
            value: "{{secrets/koreanair-rag/databricks-token}}"
          - name: VECTOR_SEARCH_INDEX
            value: "koreanair_docs_index"
          - name: CATALOG_NAME
            value: "koreanair_corp"
          - name: SCHEMA_NAME
            value: "hr_docs"
          - name: VOLUME_NAME
            value: "uploads"
          - name: VOLUME_BASE_PATH
            value: "/Volumes"
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
      
      # 리소스 설정
      resources:
        - name: default
          memory: "2Gi"
          cpu: "1"
```

### 2. Databricks Secrets 설정

```bash
# Databricks CLI 설치 (필요한 경우)
pip install databricks-cli

# Databricks CLI 인증
databricks configure --token

# Secret Scope 생성
databricks secrets create-scope --scope koreanair-rag

# Secret 추가
databricks secrets put --scope koreanair-rag --key agent-endpoint-url
databricks secrets put --scope koreanair-rag --key databricks-token
```

### 3. 앱 배포

```bash
# Databricks CLI로 배포
databricks bundle deploy

# 또는 Databricks 워크스페이스 UI에서 배포
# Apps → Create App → Upload Source Code
```

### 4. 배포 확인

1. Databricks 워크스페이스에서 **Apps** 메뉴로 이동
2. 배포된 앱의 URL 확인 및 접속
3. 상태 모니터링 및 로그 확인

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

#### 4. Databricks Apps 권한

앱 사용자에게 다음 권한이 필요합니다:

- Workspace 접근 권한
- 앱 실행 권한 (앱의 **Permissions** 설정에서 관리)

### 권한 확인 스크립트

```python
# check_permissions.py
from databricks import sql
import os

def check_permissions():
    """권한 확인"""
    print("=" * 60)
    print("권한 확인 중...")
    print("=" * 60)
    
    # Databricks SQL 연결 (예시)
    connection = sql.connect(
        server_hostname=os.getenv("DATABRICKS_SERVER_HOSTNAME"),
        http_path=os.getenv("DATABRICKS_HTTP_PATH"),
        access_token=os.getenv("DATABRICKS_TOKEN")
    )
    
    cursor = connection.cursor()
    
    # Catalog 권한 확인
    cursor.execute(f"SHOW GRANTS ON CATALOG {os.getenv('CATALOG_NAME')}")
    print("\n1. Catalog 권한:")
    for row in cursor.fetchall():
        print(f"   {row}")
    
    # Schema 권한 확인
    cursor.execute(f"SHOW GRANTS ON SCHEMA {os.getenv('CATALOG_NAME')}.{os.getenv('SCHEMA_NAME')}")
    print("\n2. Schema 권한:")
    for row in cursor.fetchall():
        print(f"   {row}")
    
    # Volume 권한 확인
    cursor.execute(f"SHOW GRANTS ON VOLUME {os.getenv('CATALOG_NAME')}.{os.getenv('SCHEMA_NAME')}.{os.getenv('VOLUME_NAME')}")
    print("\n3. Volume 권한:")
    for row in cursor.fetchall():
        print(f"   {row}")
    
    cursor.close()
    connection.close()
    
    print("\n" + "=" * 60)
    print("권한 확인 완료")
    print("=" * 60)

if __name__ == "__main__":
    check_permissions()
```

## 📊 모니터링 및 로깅

### 로그 확인

#### 로컬 실행 시

- 콘솔에 실시간 로그 출력
- 로그 레벨: `LOG_LEVEL` 환경변수로 설정

#### Databricks Apps 배포 시

1. Databricks 워크스페이스에서 **Apps** 메뉴 이동
2. 앱 선택 → **Logs** 탭
3. 실시간 로그 및 히스토리 확인

### 헬스체크

앱의 상태를 확인하는 헬스체크 엔드포인트:

```
GET /health
```

응답 예시:
```json
{
  "status": "healthy",
  "active_sessions": 5
}
```

## 🧪 테스트

### API 테스트

```bash
# 새 세션 생성
curl -X POST http://localhost:5000/api/session/new

# 질문 전송
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "복리후생 제도는?", "session_id": "your-session-id"}'

# 파일 업로드
curl -X POST http://localhost:5000/api/upload \
  -F "file=@test.pdf" \
  -F "session_id=your-session-id"
```

## 🔧 트러블슈팅

### 1. Agent 호출 실패

**증상**: "Agent 호출 실패" 오류 메시지

**해결 방법**:
- `DATABRICKS_TOKEN`이 유효한지 확인
- `AGENT_ENDPOINT_URL`이 올바른지 확인
- Agent Endpoint의 Permissions 확인

### 2. 파일 업로드 실패

**증상**: 파일 업로드 시 오류 발생

**해결 방법**:
- Unity Catalog Volume 권한 확인 (`READ VOLUME`, `WRITE VOLUME`)
- `VOLUME_BASE_PATH`가 올바른지 확인
- 디스크 공간 확인

### 3. 세션 초기화

**증상**: 세션이 자주 초기화됨

**해결 방법**:
- `SESSION_TIMEOUT_MINUTES` 값 증가
- 프로덕션 환경에서는 Redis 등 외부 세션 저장소 사용 권장

## 📝 설정 커스터마이징

### 환경변수 설명

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `AGENT_ENDPOINT_URL` | Databricks Agent REST API 엔드포인트 | 필수 |
| `DATABRICKS_TOKEN` | Databricks 인증 토큰 | 필수 |
| `VECTOR_SEARCH_INDEX` | Vector Search 인덱스 이름 | `koreanair_docs_index` |
| `CATALOG_NAME` | Unity Catalog 카탈로그 이름 | `koreanair_corp` |
| `SCHEMA_NAME` | Unity Catalog 스키마 이름 | `hr_docs` |
| `VOLUME_NAME` | Unity Catalog 볼륨 이름 | `uploads` |
| `VOLUME_BASE_PATH` | 볼륨 베이스 경로 | `/Volumes` (배포) / `./local_volumes` (로컬) |
| `SESSION_TIMEOUT_MINUTES` | 세션 타임아웃 (분) | `60` |
| `MAX_HISTORY_TURNS` | 최대 히스토리 턴 수 | `5` |
| `ALLOWED_FILE_TYPES` | 허용 파일 형식 (콤마 구분) | `pdf,docx,pptx,txt,xlsx` |
| `MAX_UPLOAD_MB` | 최대 업로드 파일 크기 (MB) | `10` |
| `SECRET_KEY` | Flask 세션 암호화 키 | 자동 생성 |
| `FLASK_DEBUG` | Flask 디버그 모드 | `False` |
| `LOG_LEVEL` | 로그 레벨 | `INFO` |

## 🤝 기여

이 프로젝트는 대한항공 사내 시스템입니다. 개선 사항이나 버그는 사내 이슈 트래커에 등록해주세요.

## 📄 라이선스

대한항공 내부 사용 전용

---

## 📞 문의

기술 지원이 필요한 경우 IT 지원팀으로 문의해주세요.

