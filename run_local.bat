@echo off
REM 로컬 개발 환경 실행 스크립트 (Windows)

echo ==================================
echo 대한항공 RAG 웹앱 - 로컬 실행
echo ==================================

REM 가상환경 활성화 확인
if "%VIRTUAL_ENV%"=="" (
    echo ⚠️  가상환경이 활성화되지 않았습니다.
    echo 다음 명령으로 가상환경을 활성화해주세요:
    echo   venv\Scripts\activate
    exit /b 1
)

REM .env 파일 존재 확인
if not exist .env (
    echo ⚠️  .env 파일이 없습니다.
    echo 환경변수 설정 파일을 생성해주세요.
    echo.
    echo 예시 .env 파일 내용:
    echo ----------------------------------------
    echo AGENT_ENDPOINT_URL=https://adb-xxxx.azuredatabricks.net/serving-endpoints/your-agent/invocations
    echo DATABRICKS_TOKEN=your_token_here
    echo CATALOG_NAME=koreanair_corp
    echo SCHEMA_NAME=hr_docs
    echo VOLUME_NAME=uploads
    echo VOLUME_BASE_PATH=./local_volumes
    echo FLASK_DEBUG=True
    echo ----------------------------------------
    exit /b 1
)

REM 로컬 볼륨 디렉토리 생성
echo 📁 로컬 볼륨 디렉토리 생성 중...
if not exist local_volumes\uploads mkdir local_volumes\uploads
echo ✓ 디렉토리 생성 완료

REM 설정 검증
echo.
echo ⚙️  설정 검증 중...
python -c "from config import Config; import sys; Config.validate(); Config.print_config(); print('\n✓ 설정 검증 완료')"

if errorlevel 1 (
    echo.
    echo ⚠️  설정을 확인하고 다시 시도해주세요.
    exit /b 1
)

REM Flask 앱 실행
echo.
echo 🚀 Flask 앱 시작 중...
echo 접속 주소: http://localhost:5000
echo 종료하려면 Ctrl+C를 누르세요.
echo.

set FLASK_APP=app.py
set FLASK_ENV=development

python app.py

