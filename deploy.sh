#!/bin/bash
# Databricks Apps 배포 스크립트

set -e

APP_NAME="jw-rag-app-v2"
WORKSPACE_PATH="/Workspace/Users/jaewoo.park@databricks.com/${APP_NAME}"

echo "============================================"
echo "대한항공 RAG 시스템 - Databricks Apps 배포"
echo "============================================"
echo ""

# 배포 전 체크
echo "📋 배포 전 체크리스트"
echo "----------------------------------------"

# 필수 파일 확인
REQUIRED_FILES=("app.py" "config.py" "requirements.txt" "app.yaml")
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file 파일이 없습니다!"
        exit 1
    fi
done

# templates 및 static 폴더 확인
if [ -d "templates" ]; then
    echo "✅ templates/"
else
    echo "❌ templates/ 폴더가 없습니다!"
    exit 1
fi

if [ -d "static" ]; then
    echo "✅ static/"
else
    echo "❌ static/ 폴더가 없습니다!"
    exit 1
fi
echo ""

# Databricks CLI 확인
if ! command -v databricks &> /dev/null; then
    echo "❌ Databricks CLI가 설치되어 있지 않습니다."
    echo "설치: pip install databricks-cli"
    exit 1
fi
echo "✅ Databricks CLI 설치 확인"
echo ""

# 배포 옵션 선택
echo "배포 옵션을 선택하세요:"
echo "1) 처음 배포 (Workspace 동기화 + 앱 배포)"
echo "2) 업데이트 배포 (기존 앱 업데이트)"
echo "3) Workspace 동기화만 (watch 모드)"
echo "4) 취소"
echo ""
read -p "선택 (1-4): " choice

case $choice in
    1)
        echo ""
        echo "🚀 처음 배포를 시작합니다..."
        echo ""
        
        # Workspace에 파일 동기화
        echo "📤 Workspace에 파일 동기화 중..."
        databricks sync . "$WORKSPACE_PATH"
        echo "✅ 동기화 완료"
        echo ""
        
        # 앱 배포
        echo "📦 앱 배포 중..."
        databricks apps deploy "$APP_NAME" --source-code-path "$WORKSPACE_PATH"
        echo ""
        echo "✅ 배포 완료!"
        echo ""
        echo "🌐 앱 URL을 확인하세요:"
        databricks apps get "$APP_NAME"
        ;;
    
    2)
        echo ""
        echo "🔄 업데이트 배포를 시작합니다..."
        echo ""
        
        # Workspace에 파일 동기화
        echo "📤 Workspace에 파일 동기화 중..."
        databricks sync . "$WORKSPACE_PATH"
        echo "✅ 동기화 완료"
        echo ""
        
        # 앱 업데이트
        echo "📦 앱 업데이트 중..."
        databricks apps deploy "$APP_NAME"
        echo ""
        echo "✅ 업데이트 완료!"
        echo ""
        echo "🌐 앱 상태:"
        databricks apps get "$APP_NAME"
        ;;
    
    3)
        echo ""
        echo "👁️  Workspace 실시간 동기화 시작 (Ctrl+C로 중지)..."
        echo ""
        databricks sync --watch . "$WORKSPACE_PATH"
        ;;
    
    4)
        echo "배포를 취소했습니다."
        exit 0
        ;;
    
    *)
        echo "잘못된 선택입니다."
        exit 1
        ;;
esac

echo ""
echo "============================================"
echo "배포 완료!"
echo "============================================"
echo ""
echo "💡 팁:"
echo "- 로그 확인: databricks apps logs $APP_NAME"
echo "- 앱 상태: databricks apps get $APP_NAME"
echo "- 앱 목록: databricks apps list"
echo ""

