"""
애플리케이션 설정
"""
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()


class Config:
    """애플리케이션 설정 클래스"""
    
    # Databricks Agent 설정
    AGENT_ENDPOINT_URL = os.environ.get(
        'AGENT_ENDPOINT_URL',
        'https://adb-xxxx.azuredatabricks.net/serving-endpoints/hr-agent/invocations'
    )
    
    DATABRICKS_TOKEN = os.environ.get('DATABRICKS_TOKEN', '')
    
    # Vector Search 설정
    VECTOR_SEARCH_INDEX = os.environ.get(
        'VECTOR_SEARCH_INDEX',
        'koreanair_docs_index'
    )
    
    # Unity Catalog 설정
    CATALOG_NAME = os.environ.get('CATALOG_NAME', 'koreanair_corp')
    SCHEMA_NAME = os.environ.get('SCHEMA_NAME', 'hr_docs')
    VOLUME_NAME = os.environ.get('VOLUME_NAME', 'uploads')
    
    # Volume 베이스 경로
    # Databricks Apps에서는 Files API를 통해 /Volumes/... 경로 사용
    # 로컬 테스트에서는 ./local_volumes 사용
    VOLUME_BASE_PATH = os.environ.get(
        'VOLUME_BASE_PATH',
        f'/Volumes/{CATALOG_NAME}/{SCHEMA_NAME}/{VOLUME_NAME}' 
        if os.environ.get('DATABRICKS_TOKEN') 
        else './local_volumes'
    )
    
    # 세션 설정
    SESSION_TIMEOUT_MINUTES = int(os.environ.get('SESSION_TIMEOUT_MINUTES', 60))
    MAX_HISTORY_TURNS = int(os.environ.get('MAX_HISTORY_TURNS', 5))
    
    # 파일 업로드 설정
    ALLOWED_FILE_TYPES = set(
        os.environ.get('ALLOWED_FILE_TYPES', 'pdf,docx,pptx,txt,xlsx').split(',')
    )
    MAX_UPLOAD_MB = int(os.environ.get('MAX_UPLOAD_MB', 10))
    
    # Flask 설정
    SECRET_KEY = os.environ.get('SECRET_KEY', None)
    MAX_CONTENT_LENGTH = MAX_UPLOAD_MB * 1024 * 1024  # bytes
    
    # 로깅 레벨
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    @classmethod
    def validate(cls):
        """필수 설정 검증"""
        errors = []
        
        if not cls.DATABRICKS_TOKEN:
            errors.append("DATABRICKS_TOKEN이 설정되지 않았습니다")
        
        if 'xxxx' in cls.AGENT_ENDPOINT_URL:
            errors.append("AGENT_ENDPOINT_URL을 실제 엔드포인트로 설정해주세요")
        
        if errors:
            raise ValueError("설정 오류:\n" + "\n".join(f"- {e}" for e in errors))
        
        return True
    
    @classmethod
    def print_config(cls):
        """설정 출력 (디버깅용)"""
        print("=" * 60)
        print("애플리케이션 설정")
        print("=" * 60)
        print(f"Agent Endpoint: {cls.AGENT_ENDPOINT_URL}")
        print(f"Vector Search Index: {cls.VECTOR_SEARCH_INDEX}")
        print(f"Catalog: {cls.CATALOG_NAME}")
        print(f"Schema: {cls.SCHEMA_NAME}")
        print(f"Volume: {cls.VOLUME_NAME}")
        print(f"Volume Base Path: {cls.VOLUME_BASE_PATH}")
        print(f"Session Timeout: {cls.SESSION_TIMEOUT_MINUTES}분")
        print(f"Max History Turns: {cls.MAX_HISTORY_TURNS}")
        print(f"Allowed File Types: {', '.join(cls.ALLOWED_FILE_TYPES)}")
        print(f"Max Upload Size: {cls.MAX_UPLOAD_MB}MB")
        print(f"Token 설정: {'✓' if cls.DATABRICKS_TOKEN else '✗'}")
        print("=" * 60)

