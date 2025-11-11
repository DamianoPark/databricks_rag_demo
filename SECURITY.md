# 보안 설정 가이드

## Databricks Token 설정

**중요**: 실제 토큰을 Git에 커밋하지 마세요!

### 배포 시 토큰 설정 방법

#### 방법 1: 배포 전 app.yaml 수정 (권장하지 않음)
```yaml
env:
  - name: DATABRICKS_TOKEN
    value: "YOUR_ACTUAL_TOKEN"  # 실제 토큰으로 변경
```

#### 방법 2: Secret Scope 사용 (권장)
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

### Secret Scope 생성

```bash
# Databricks CLI로 Secret Scope 생성
databricks secrets create-scope --scope your-scope

# 토큰 저장
databricks secrets put --scope your-scope --key databricks-token
```

### 로컬 개발

로컬 개발 시에는 `.env` 파일을 사용하세요:

```bash
# .env 파일 생성
DATABRICKS_TOKEN=your_actual_token_here
```

**`.env` 파일은 절대 Git에 커밋하지 마세요!** (`.gitignore`에 이미 추가되어 있음)

---

## 주의사항

1. ⚠️ **절대 실제 토큰을 Git에 커밋하지 마세요**
2. ⚠️ **토큰을 공개 저장소에 푸시하지 마세요**
3. ✅ Secret Scope를 사용하는 것이 가장 안전합니다
4. ✅ 로컬 개발은 `.env` 파일을 사용하세요

