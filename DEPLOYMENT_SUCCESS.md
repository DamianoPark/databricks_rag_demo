# ✅ Databricks Apps 배포 완료!

## 🎉 배포 성공

대한항공 RAG 시스템이 성공적으로 Databricks Apps에 배포되었습니다!

---

## 📊 배포 정보

### 앱 정보
- **앱 이름**: `jw-rag-app-v2`
- **앱 ID**: `6b0f33b6-997b-4b8b-83dc-4b65d8575b7f`
- **상태**: ✅ `RUNNING` (App is running)
- **컴퓨트 상태**: ✅ `ACTIVE` (App compute is running)

### 접속 정보
- **앱 URL**: 🌐 **https://jw-rag-app-v2-1444828305810485.aws.databricksapps.com**
- **배포 시간**: 2025-11-11 16:10:09 (KST)
- **배포자**: jaewoo.park@databricks.com

### Service Principal 정보
- **Service Principal ID**: `73856643325882`
- **Service Principal Name**: `app-40zbx9 jw-rag-app-v2`
- **Client ID**: `6b0f33b6-997b-4b8b-83dc-4b65d8575b7f`

### 소스 코드 위치
- **Workspace 경로**: `/Workspace/Users/jaewoo.park@databricks.com/jw-rag-app-v2`
- **배포 아티팩트**: `/Workspace/Users/6b0f33b6-997b-4b8b-83dc-4b65d8575b7f/src/01f0becd6f5f1370a58b9ffc92bc49b0`

---

## 🚀 다음 단계

### 1. 앱 접속 및 테스트

브라우저에서 다음 URL을 열어 앱을 확인하세요:

```
https://jw-rag-app-v2-1444828305810485.aws.databricksapps.com
```

### 2. Unity Catalog 권한 설정

Service Principal에 필요한 권한을 부여하세요:

```sql
-- Catalog 권한
GRANT USE CATALOG ON CATALOG koreanair_corp TO `app-40zbx9 jw-rag-app-v2`;

-- Schema 권한
GRANT USE SCHEMA ON SCHEMA koreanair_corp.hr_docs TO `app-40zbx9 jw-rag-app-v2`;

-- Volume 권한 (읽기/쓰기)
GRANT READ VOLUME, WRITE VOLUME 
ON VOLUME koreanair_corp.hr_docs.uploads 
TO `app-40zbx9 jw-rag-app-v2`;
```

### 3. Agent Endpoint 권한 설정

1. Databricks UI > **Serving** > **Endpoints**로 이동
2. 사용 중인 Agent Endpoint 선택
3. **Permissions** 탭 클릭
4. `app-40zbx9 jw-rag-app-v2`에게 **Can Query** 권한 부여

### 4. Databricks Secrets 설정 (이미 완료된 경우 건너뛰기)

```bash
# Secret Scope 생성 (최초 1회)
databricks secrets create-scope --scope koreanair-rag

# Agent Endpoint URL 설정
databricks secrets put-secret --scope koreanair-rag --key agent-endpoint-url \
  --string-value "https://your-workspace.azuredatabricks.net/serving-endpoints/your-agent/invocations"

# Databricks Token 설정
databricks secrets put-secret --scope koreanair-rag --key databricks-token \
  --string-value "dapi..."
```

### 5. 로그 확인

Databricks UI에서 로그를 확인하세요:

1. **Apps** 메뉴로 이동
2. `jw-rag-app-v2` 클릭
3. **Logs** 탭에서 실시간 로그 확인

앱이 시작되지 않거나 오류가 발생하면 로그를 확인하여 문제를 해결하세요.

---

## 🔄 앱 업데이트 방법

### 코드 수정 후 재배포

```bash
# 1. 로컬에서 코드 수정
# 2. Workspace와 동기화
databricks sync . /Workspace/Users/jaewoo.park@databricks.com/jw-rag-app-v2

# 3. 앱 재배포 (간단한 명령)
databricks apps deploy jw-rag-app-v2
```

### 실시간 동기화 (개발 중)

코드를 수정할 때마다 자동으로 Workspace에 동기화:

```bash
# 백그라운드에서 실행
databricks sync --watch . /Workspace/Users/jaewoo.park@databricks.com/jw-rag-app-v2 &
```

---

## 📊 앱 관리 명령어

### 앱 상태 확인

```bash
databricks apps get jw-rag-app-v2
```

### 앱 중지

```bash
databricks apps stop jw-rag-app-v2
```

### 앱 시작

```bash
databricks apps start jw-rag-app-v2
```

### 배포 이력 확인

```bash
databricks apps list-deployments jw-rag-app-v2
```

### 특정 배포 정보 확인

```bash
databricks apps get-deployment jw-rag-app-v2 01f0becd6f5f1370a58b9ffc92bc49b0
```

---

## 🛠️ 트러블슈팅

### 앱이 시작되지 않는 경우

1. **Databricks UI에서 로그 확인**
   - Apps > jw-rag-app-v2 > Logs

2. **일반적인 문제**
   - ❌ 패키지 누락: `requirements.txt` 확인
   - ❌ 권한 부족: Unity Catalog 및 Agent Endpoint 권한 확인
   - ❌ Secrets 미설정: `koreanair-rag` scope의 secrets 확인
   - ❌ 포트 문제: `app.yaml`에서 `--server.port=8080` 확인

3. **앱 재시작**
   ```bash
   databricks apps stop jw-rag-app-v2
   databricks apps start jw-rag-app-v2
   ```

### 권한 오류가 발생하는 경우

```sql
-- 현재 권한 확인
SHOW GRANTS ON CATALOG koreanair_corp;
SHOW GRANTS ON SCHEMA koreanair_corp.hr_docs;
SHOW GRANTS ON VOLUME koreanair_corp.hr_docs.uploads;
```

---

## 📝 체크리스트

배포 후 확인해야 할 사항:

- [ ] 앱 URL 접속 확인
- [ ] Unity Catalog 권한 부여 (Catalog, Schema, Volume)
- [ ] Agent Endpoint 권한 부여
- [ ] Databricks Secrets 설정 확인
- [ ] 파일 업로드 기능 테스트
- [ ] 질의응답 기능 테스트
- [ ] 로그에서 오류 확인

---

## 🎯 성능 모니터링

### 리소스 사용량

현재 컴퓨트 설정:
- **메모리**: 6GB
- **CPU**: 2 vCPU
- **비용**: 약 0.5 DBU/시간

### 스케일링

앱 사용량이 증가하면 `app.yaml`에서 리소스를 조정하고 재배포하세요:

```yaml
resources:
  - name: default
    memory: "12Gi"  # 메모리 증가
    cpu: "4"        # CPU 증가
```

---

## 📞 지원

문제가 발생하거나 질문이 있으시면:

1. **로그 확인**: Databricks UI > Apps > jw-rag-app-v2 > Logs
2. **문서 참조**: `DEPLOYMENT_GUIDE.md`, `README.md`
3. **IT 지원팀**: 사내 IT 지원 채널로 문의

---

## 🎉 축하합니다!

대한항공 RAG 시스템이 성공적으로 Databricks Apps에 배포되었습니다!

**앱 URL**: https://jw-rag-app-v2-1444828305810485.aws.databricksapps.com

이제 사내 사용자들이 안전하고 편리하게 문서 검색 서비스를 이용할 수 있습니다. 🚀✈️

---

**배포일**: 2025년 11월 11일  
**배포자**: jaewoo.park@databricks.com  
**버전**: Streamlit v1.0

