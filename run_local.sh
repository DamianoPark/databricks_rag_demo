#!/bin/bash
# 로컬 개발 환경 실행 스크립트

echo "=================================="
echo "대한항공 RAG 웹앱 - 로컬 실행"
echo "=================================="

# 가상환경 활성화 확인
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  가상환경이 활성화되지 않았습니다."
    echo "다음 명령으로 가상환경을 활성화해주세요:"
    echo "  source venv/bin/activate"
    exit 1
fi

# .env 파일 존재 확인
if [ ! -f .env ]; then
    echo "⚠️  .env 파일이 없습니다."
    echo "환경변수 설정 파일을 생성해주세요."
    echo ""
    echo "예시 .env 파일 내용:"
    echo "----------------------------------------"
    echo "AGENT_ENDPOINT_URL=https://adb-xxxx.azuredatabricks.net/serving-endpoints/your-agent/invocations"
    echo "DATABRICKS_TOKEN=your_token_here"
    echo "CATALOG_NAME=koreanair_corp"
    echo "SCHEMA_NAME=hr_docs"
    echo "VOLUME_NAME=uploads"
    echo "VOLUME_BASE_PATH=./local_volumes"
    echo "FLASK_DEBUG=True"
    echo "----------------------------------------"
    exit 1
fi

# 로컬 볼륨 디렉토리 생성
echo "📁 로컬 볼륨 디렉토리 생성 중..."
mkdir -p ./local_volumes/uploads
echo "✓ 디렉토리 생성 완료"

# 설정 검증
echo ""
echo "⚙️  설정 검증 중..."
python -c "
from config import Config
import sys

try:
    Config.validate()
    Config.print_config()
    print('\n✓ 설정 검증 완료')
    sys.exit(0)
except Exception as e:
    print(f'\n✗ 설정 오류: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo ""
    echo "⚠️  설정을 확인하고 다시 시도해주세요."
    exit 1
fi

# Flask 앱 실행
echo ""
echo "🚀 Flask 앱 시작 중..."
echo "접속 주소: http://localhost:5000"
echo "종료하려면 Ctrl+C를 누르세요."
echo ""

export FLASK_APP=app.py
export FLASK_ENV=development

python app.py

