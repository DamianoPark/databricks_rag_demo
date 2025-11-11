# Databricks Apps 배포 가이드

## 📋 사전 준비사항

### 1. Databricks CLI 설치 및 인증

```bash
# Databricks CLI 설치 (최신 버전)
pip install databricks-cli

# 인증 설정
databricks configure --token
```

프롬프트에서 다음 정보를 입력:
- **Databricks Host**: `https://your-workspace.azuredatabricks.net`
- **Token**: Personal Access Token (User Settings > Developer > Access Tokens에서 생성)

### 2. Databricks Secrets 설정

민감한 정보(토큰, 엔드포인트 URL)는 Secrets로 관리합니다.

```bash
# Secret Scope 생성
databricks secrets create-scope --scope koreanair-rag

# Secret 추가
databricks secrets put --scope koreanair-rag --key agent-endpoint-url
# 편집기가 열리면 Agent Endpoint URL 입력 후 저장

databricks secrets put --scope koreanair-rag --key databricks-token
# 편집기가 열리면 Databricks Token 입력 후 저장
```

또는 값을 직접 지정:

```bash
databricks secrets put-secret --scope koreanair-rag --key agent-endpoint-url --string-value "https://your-workspace.azuredatabricks.net/serving-endpoints/your-agent/invocations"

databricks secrets put-secret --scope koreanair-rag --key databricks-token --string-value "dapi..."
```

Secret 확인:

```bash
databricks secrets list --scope koreanair-rag
```

## 🚀 배포 프로세스

### 1단계: Workspace에서 기존 내용 가져오기 (선택사항)

템플릿이나 기존 앱이 있는 경우:

```bash
cd /Users/jaewoo.park/Documents/work/대한항공_RAG

databricks workspace export-dir /Workspace/Users/jaewoo.park@databricks.com/jw-rag-app-v2 .
```

### 2단계: 로컬에서 앱 테스트

```bash
# 가상환경 활성화
source venv/bin/activate

# Streamlit 앱 실행
streamlit run streamlit_app.py

# 브라우저에서 http://localhost:8501 접속하여 테스트
```

### 3단계: Workspace와 동기화

프로젝트를 Databricks Workspace와 실시간 동기화:

```bash
databricks sync --watch . /Workspace/Users/jaewoo.park@databricks.com/jw-rag-app-v2
```

> 💡 이 명령은 백그라운드에서 계속 실행되며, 로컬 파일 변경 시 자동으로 Workspace에 동기화됩니다.

동기화 상태 확인:

```bash
# 다른 터미널에서
databricks workspace ls /Workspace/Users/jaewoo.park@databricks.com/jw-rag-app-v2
```

### 4단계: Databricks Apps에 배포

```bash
databricks apps deploy jw-rag-app-v2 --source-code-path /Workspace/Users/jaewoo.park@databricks.com/jw-rag-app-v2
```

배포 완료 후 출력되는 URL로 접속하여 확인합니다.

### 5단계: 후속 배포 (업데이트)

이미 배포된 앱을 업데이트할 때:

```bash
# 파일 수정 후
databricks apps deploy jw-rag-app-v2
```

## 📊 배포 확인 및 모니터링

### 앱 상태 확인

```bash
# 앱 목록 조회
databricks apps list

# 특정 앱 상태 확인
databricks apps get jw-rag-app-v2
```

### 로그 확인

Databricks UI에서:
1. **Apps** 메뉴로 이동
2. `jw-rag-app-v2` 선택
3. **Logs** 탭에서 실시간 로그 확인

또는 CLI로:

```bash
databricks apps logs jw-rag-app-v2
```

## 🐛 일반적인 문제 및 해결 방법

### 1. 누락된 패키지 또는 잘못된 패키지 버전

**증상**: 앱 시작 시 `ModuleNotFoundError`

**해결**:
```bash
# requirements.txt에 패키지 추가
echo "missing-package==1.0.0" >> requirements.txt

# 재배포
databricks apps deploy jw-rag-app-v2
```

### 2. 권한 문제

**증상**: `PermissionDenied` 또는 `403 Forbidden`

**해결**:

Unity Catalog 권한 부여:

```sql
-- Catalog 권한
GRANT USE CATALOG ON CATALOG koreanair_corp TO `app-40zbx9 jw-rag-app-v2`;

-- Schema 권한
GRANT USE SCHEMA ON SCHEMA koreanair_corp.hr_docs TO `app-40zbx9 jw-rag-app-v2`;

-- Volume 권한
GRANT READ VOLUME, WRITE VOLUME ON VOLUME koreanair_corp.hr_docs.uploads TO `app-40zbx9 jw-rag-app-v2`;
```

Agent Endpoint 권한:
1. Databricks UI > **Serving** > **Endpoints**
2. Agent 선택 > **Permissions**
3. `app-40zbx9 jw-rag-app-v2` 에게 **Can Query** 권한 부여

### 3. 환경 변수 누락

**증상**: 앱이 설정값을 찾지 못함

**해결**:
`app.yaml` 파일의 `env` 섹션 확인 및 수정:

```yaml
env:
  - name: MISSING_VAR
    value: "value"
```

### 4. Startup 시 잘못된 명령줄 실행

**증상**: 앱이 시작되지 않음

**해결**:
`app.yaml` 파일의 `command` 섹션 확인:

```yaml
command:
  - streamlit
  - run
  - streamlit_app.py
  - --server.port=8080
  - --server.address=0.0.0.0
```

### 5. 포트 바인딩 오류

**증상**: `Address already in use`

**해결**:
Databricks Apps는 자동으로 포트를 할당합니다. `app.yaml`에서 포트를 8080으로 설정했는지 확인:

```yaml
command:
  - streamlit
  - run
  - streamlit_app.py
  - --server.port=8080  # Databricks Apps 표준 포트
  - --server.address=0.0.0.0
```

## 🔄 개발 워크플로우

### 개발 → 테스트 → 배포 사이클

1. **로컬 개발**
   ```bash
   # 로컬에서 앱 수정 및 테스트
   streamlit run streamlit_app.py
   ```

2. **자동 동기화** (선택사항)
   ```bash
   # 백그라운드에서 실행
   databricks sync --watch . /Workspace/Users/jaewoo.park@databricks.com/jw-rag-app-v2 &
   ```

3. **배포**
   ```bash
   # 변경사항 배포
   databricks apps deploy jw-rag-app-v2
   ```

4. **확인**
   - 브라우저에서 앱 URL 접속
   - 로그 확인: Databricks UI > Apps > jw-rag-app-v2 > Logs

## 📁 배포 파일 체크리스트

배포 전 다음 파일들이 있는지 확인:

- ✅ `streamlit_app.py` - 메인 애플리케이션
- ✅ `config.py` - 설정 관리
- ✅ `requirements.txt` - Python 의존성
- ✅ `app.yaml` - Databricks Apps 설정
- ✅ `.streamlit/config.toml` - Streamlit 설정 (선택사항)
- ✅ `README.md` - 문서

제외할 파일 (`.gitignore` 또는 `.databricksignore`):
- ❌ `venv/` - 가상환경
- ❌ `__pycache__/` - Python 캐시
- ❌ `.env` - 로컬 환경 변수 (보안!)
- ❌ `local_volumes/` - 로컬 테스트 데이터
- ❌ `*.zip` - 백업 파일

## 🔐 보안 모범 사례

1. **절대 코드에 하드코딩하지 마세요**
   - ❌ `token = "dapi123..."`
   - ✅ `token = os.environ.get('DATABRICKS_TOKEN')`

2. **Databricks Secrets 사용**
   - 모든 민감한 정보는 Secrets로 관리
   - `app.yaml`에서 `{{secrets/scope/key}}` 형식으로 참조

3. **최소 권한 원칙**
   - 앱에 필요한 최소한의 권한만 부여
   - 정기적으로 권한 검토

4. **로그 모니터링**
   - 민감한 정보가 로그에 출력되지 않도록 주의
   - 정기적으로 로그 확인

## 📞 지원

### 배포 실패 시

1. **로그 확인**
   ```bash
   databricks apps logs jw-rag-app-v2
   ```

2. **앱 상태 확인**
   ```bash
   databricks apps get jw-rag-app-v2
   ```

3. **Workspace 파일 확인**
   ```bash
   databricks workspace ls /Workspace/Users/jaewoo.park@databricks.com/jw-rag-app-v2
   ```

4. **Secrets 확인**
   ```bash
   databricks secrets list --scope koreanair-rag
   ```

### 추가 도움말

- Databricks Apps 문서: https://docs.databricks.com/apps/
- Streamlit on Databricks: https://docs.databricks.com/apps/streamlit.html

---

## 🎉 배포 완료!

배포가 성공하면 다음과 같은 정보를 받게 됩니다:

```
✅ App deployed successfully!

App Name: jw-rag-app-v2
App ID: 6b0f33b6-997b-4b8b-83dc-4b65d8575b7f
URL: https://your-workspace.azuredatabricks.net/apps/jw-rag-app-v2
Compute: Medium - 최대 2개의 vCPU, 6GB 메모리, 0.5 DBU/시간
Created by: jaewoo.park@databricks.com
```

브라우저에서 URL을 열어 앱을 사용하세요! 🚀

