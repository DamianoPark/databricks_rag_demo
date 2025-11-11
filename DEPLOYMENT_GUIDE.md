# Databricks Apps 배포 가이드

## 📋 사전 준비

### 1. Databricks CLI 설치

```bash
pip install databricks-cli
```

### 2. Databricks 인증 설정

```bash
databricks configure
```

프롬프트에 다음 정보 입력:
- Databricks Host: `https://your-workspace.cloud.databricks.com`
- Token: Personal Access Token 또는 Service Principal Token

### 3. 필수 권한 확인

배포하려면 다음 권한이 필요합니다:
- ✅ Workspace 읽기/쓰기 권한
- ✅ Apps 생성/관리 권한
- ✅ Unity Catalog Volume 접근 권한
- ✅ Agent Endpoint 호출 권한

## 🚀 배포 방법

### 방법 1: 배포 스크립트 사용 (권장)

```bash
# 스크립트 실행
./deploy.sh

# 또는 실행 권한 부여 후
chmod +x deploy.sh
./deploy.sh
```

대화형 메뉴:
```
1) 처음 배포 (Workspace 동기화 + 앱 배포)
2) 업데이트 배포 (기존 앱 업데이트)
3) Workspace 동기화만 (watch 모드)
4) 취소
```

### 방법 2: 수동 배포

#### Step 1: Workspace 동기화

```bash
databricks sync . /Workspace/Users/your-email@company.com/your-app
```

#### Step 2: 앱 배포

**처음 배포:**
```bash
databricks apps deploy your-app-name \
  --source-code-path /Workspace/Users/your-email@company.com/your-app
```

**업데이트 배포:**
```bash
databricks apps deploy your-app-name
```

#### Step 3: 앱 상태 확인

```bash
# 앱 정보 확인
databricks apps get your-app-name

# 로그 확인
databricks apps logs your-app-name
```

## ⚙️ app.yaml 설정

배포 전 `app.yaml` 파일 수정:

### 1. 토큰 설정

```yaml
env:
  - name: DATABRICKS_TOKEN
    value: "YOUR_ACTUAL_TOKEN"  # 실제 토큰으로 변경
```

**⚠️ 중요**: 
- Git에 커밋하기 전에 토큰을 플레이스홀더로 되돌리세요!
- 더 안전한 방법은 Secret Scope 사용 (아래 참조)

### 2. Agent Endpoint 설정

```yaml
env:
  - name: AGENT_ENDPOINT_URL
    value: "https://your-workspace.cloud.databricks.com/serving-endpoints/your-agent/invocations"
```

### 3. Unity Catalog 설정

```yaml
env:
  - name: CATALOG_NAME
    value: "your_catalog"
  
  - name: SCHEMA_NAME
    value: "your_schema"
  
  - name: VOLUME_NAME
    value: "your_volume"
  
  - name: VOLUME_BASE_PATH
    value: "/Volumes/your_catalog/your_schema/your_volume"
```

## 🔐 Secret Scope 사용 (권장)

### 1. Secret Scope 생성

```bash
databricks secrets create-scope --scope your-scope
```

### 2. 토큰 저장

```bash
databricks secrets put --scope your-scope --key databricks-token
```

에디터가 열리면 토큰을 입력하고 저장

### 3. app.yaml 수정

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

이 방법을 사용하면 토큰이 코드에 노출되지 않습니다!

## 📊 배포 후 확인

### 1. 앱 상태 확인

```bash
databricks apps get your-app-name
```

예상 결과:
```json
{
  "app_status": {
    "state": "RUNNING",
    "message": "App is running"
  },
  "compute_status": {
    "state": "ACTIVE"
  },
  "url": "https://your-app.databricksapps.com"
}
```

### 2. 로그 확인

```bash
# 최근 로그 확인
databricks apps logs your-app-name

# 실시간 로그 (tail)
databricks apps logs your-app-name --follow
```

### 3. 브라우저에서 접속

앱 URL로 접속하여 정상 작동 확인:
```
https://your-app-name-xxxx.databricksapps.com
```

## 🐛 트러블슈팅

### 문제 1: 배포 실패 (권한 오류)

**증상:**
```
Error: Permission denied
```

**해결:**
1. Service Principal 권한 확인
2. Workspace ACL 설정 확인
3. Apps 권한 확인

### 문제 2: 앱이 시작되지 않음

**증상:**
```
App status: FAILED
```

**해결:**
```bash
# 로그 확인
databricks apps logs your-app-name

# 일반적인 원인:
# - 잘못된 환경 변수
# - 누락된 패키지 (requirements.txt 확인)
# - 포트 충돌 (기본 8000)
```

### 문제 3: 401 Unauthorized

**증상:**
앱이 실행되지만 Agent 호출 시 401 오류

**해결:**
1. `DATABRICKS_TOKEN` 환경 변수 확인
2. 토큰 유효성 확인 (만료 여부)
3. Service Principal 권한 확인

### 문제 4: Volume 접근 실패

**증상:**
파일 업로드 시 오류 발생

**해결:**
1. Volume 경로 확인 (`/Volumes/catalog/schema/volume`)
2. Service Principal에 Volume 쓰기 권한 부여
3. Unity Catalog 설정 확인

## 🔄 업데이트 절차

### 코드 변경 후 재배포

```bash
# 1. 변경사항 Workspace 동기화
databricks sync . /Workspace/Users/your-email@company.com/your-app

# 2. 앱 재배포
databricks apps deploy your-app-name

# 3. 상태 확인
databricks apps get your-app-name
```

### 또는 배포 스크립트 사용

```bash
./deploy.sh
# 옵션 2 선택 (업데이트 배포)
```

## 📝 체크리스트

배포 전 확인사항:

- [ ] `app.yaml`의 토큰이 실제 값으로 설정됨
- [ ] Agent Endpoint URL이 올바름
- [ ] Unity Catalog 경로가 정확함
- [ ] `requirements.txt`에 모든 패키지 포함됨
- [ ] `.databricksignore`로 불필요한 파일 제외됨
- [ ] Service Principal 권한이 설정됨

배포 후 확인사항:

- [ ] 앱 상태가 RUNNING
- [ ] 앱 URL로 접속 가능
- [ ] 채팅 기능이 정상 작동
- [ ] 파일 업로드가 정상 작동
- [ ] 로그에 오류가 없음

## 💡 팁

### Workspace 실시간 동기화

개발 중에는 watch 모드 사용:

```bash
databricks sync --watch . /Workspace/Users/your-email@company.com/your-app
```

파일 변경사항이 자동으로 동기화됩니다.

### 다중 환경 관리

개발/스테이징/프로덕션 환경 분리:

```bash
# 개발
databricks apps deploy app-dev --source-code-path /Workspace/.../app-dev

# 프로덕션
databricks apps deploy app-prod --source-code-path /Workspace/.../app-prod
```

### 빠른 롤백

문제 발생 시 이전 버전으로 롤백:

```bash
# 이전 deployment ID 확인
databricks apps get your-app-name

# 특정 deployment로 롤백 (Databricks 콘솔에서)
```

## 📚 참고 자료

- [Databricks Apps 공식 문서](https://docs.databricks.com/en/dev-tools/databricks-apps/index.html)
- [Databricks CLI 문서](https://docs.databricks.com/en/dev-tools/cli/index.html)
- [Unity Catalog 문서](https://docs.databricks.com/en/data-governance/unity-catalog/index.html)

---

**문의사항**: IT 헬프데스크
