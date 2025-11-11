"""
대한항공 RAG 웹앱
Flask 기반 Databricks Apps 배포용 애플리케이션
"""
import os
import uuid
import logging
import json
from datetime import datetime, timedelta
from pathlib import Path

from flask import Flask, render_template, request, jsonify
import requests
import re

from config import Config

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask 앱 초기화
app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24).hex())

# 세션 저장소 (실제 운영 시 Redis 등 사용 권장)
chat_sessions = {}


class SessionManager:
    """세션 및 채팅 히스토리 관리"""
    
    @staticmethod
    def get_or_create_session(session_id=None):
        """세션 가져오기 또는 생성"""
        if not session_id or session_id not in chat_sessions:
            session_id = str(uuid.uuid4())
            chat_sessions[session_id] = {
                'id': session_id,
                'created_at': datetime.now(),
                'last_access': datetime.now(),
                'history': [],
                'uploaded_files': []
            }
            logger.info(f"새 세션 생성: {session_id}")
        else:
            chat_sessions[session_id]['last_access'] = datetime.now()
        
        return session_id, chat_sessions[session_id]
    
    @staticmethod
    def add_to_history(session_id, role, content):
        """히스토리에 대화 추가"""
        if session_id in chat_sessions:
            chat_sessions[session_id]['history'].append({
                'role': role,
                'content': content,
                'timestamp': datetime.now().isoformat()
            })
            
            # 최대 턴 수 제한
            max_turns = Config.MAX_HISTORY_TURNS * 2  # user + assistant 각각
            if len(chat_sessions[session_id]['history']) > max_turns:
                chat_sessions[session_id]['history'] = \
                    chat_sessions[session_id]['history'][-max_turns:]
    
    @staticmethod
    def clear_old_sessions():
        """만료된 세션 정리"""
        now = datetime.now()
        timeout = timedelta(minutes=Config.SESSION_TIMEOUT_MINUTES)
        expired = [
            sid for sid, data in chat_sessions.items()
            if now - data['last_access'] > timeout
        ]
        for sid in expired:
            del chat_sessions[sid]
            logger.info(f"만료된 세션 삭제: {sid}")


class DatabricksAgentClient:
    """Databricks Agent API 클라이언트"""
    
    def __init__(self):
        self.endpoint_url = Config.AGENT_ENDPOINT_URL

    def _resolve_token(self) -> str:
        """환경 변수에서 Databricks 토큰을 해석한다.
        우선순위:
        1) Config.DATABRICKS_TOKEN
        2) 환경 변수 DATABRICKS_TOKEN
        3) 환경 변수 DATABRICKS_APP_TOKEN (선택적 백업 키)
        """
        token = (Config.DATABRICKS_TOKEN or
                 os.environ.get('DATABRICKS_TOKEN') or
                 os.environ.get('DATABRICKS_APP_TOKEN'))
        return token or ""

    def _build_headers(self, streaming=False) -> dict:
        token = self._resolve_token()
        if not token:
            raise ValueError(
                "Databricks 토큰이 설정되지 않았습니다. "
                "Apps 환경 변수에 DATABRICKS_TOKEN을 설정하세요 (예: {{secrets/<scope>/databricks-token}})."
            )
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        if streaming:
            headers['Accept'] = 'text/event-stream'
        return headers
    
    def query(self, question, history=None, uploaded_files=None):
        """에이전트에 질의"""
        try:
            # Databricks Agent Framework 입력 형식
            # 'input' 필드에 메시지 배열 전달
            messages = []
            
            # 히스토리 추가 (있는 경우)
            if history:
                for item in history:
                    messages.append({
                        'role': item.get('role', 'user'),
                        'content': item.get('content', '')
                    })
            
            # 현재 질문 추가
            messages.append({
                'role': 'user',
                'content': question
            })
            
            # API 요청 페이로드 (input 필드 사용)
            payload = {
                'input': messages
            }
            
            # Context 정보 추가 (선택사항)
            if uploaded_files:
                payload['custom_inputs'] = {
                    'uploaded_files': uploaded_files
                }
            
            logger.info(f"Agent 호출: {question[:50]}...")
            logger.debug(f"요청 페이로드: {payload}")
            
            response = requests.post(
                self.endpoint_url,
                json=payload,
                headers=self._build_headers(),
                timeout=60
            )
            
            if not response.ok:
                error_detail = response.text
                logger.error(f"Agent API 에러 (status {response.status_code}): {error_detail}")
                # 401 진단 메시지 보강
                if response.status_code == 401:
                    logger.error(
                        "401 Unauthorized: 토큰이 누락/잘못되었습니다. "
                        "Apps 설정에서 DATABRICKS_TOKEN을 앱의 Service Principal 토큰으로 주입했는지 확인하세요."
                    )
                response.raise_for_status()
            
            result = response.json()
            logger.info("Agent 응답 수신 완료")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Agent 호출 실패: {str(e)}")
            raise Exception(f"Agent 호출 실패: {str(e)}")
        except ValueError as e:
            # 토큰 미설정 등 사전 검증 실패
            logger.error(str(e))
            raise
    
    def query_stream(self, question, history=None, uploaded_files=None):
        """에이전트에 스트리밍 질의 (제너레이터)"""
        try:
            # Databricks Agent Framework 입력 형식
            messages = []
            
            # 히스토리 추가 (있는 경우)
            if history:
                for item in history:
                    messages.append({
                        'role': item.get('role', 'user'),
                        'content': item.get('content', '')
                    })
            
            # 현재 질문 추가
            messages.append({
                'role': 'user',
                'content': question
            })
            
            # API 요청 페이로드 (stream=true 추가)
            payload = {
                'input': messages,
                'stream': True  # 스트리밍 활성화
            }
            
            # Context 정보 추가 (선택사항)
            if uploaded_files:
                payload['custom_inputs'] = {
                    'uploaded_files': uploaded_files
                }
            
            logger.info(f"Agent 스트리밍 호출: {question[:50]}...")
            logger.debug(f"요청 페이로드: {payload}")
            
            # 스트리밍 요청
            response = requests.post(
                self.endpoint_url,
                json=payload,
                headers=self._build_headers(streaming=True),
                timeout=120,
                stream=True  # requests 라이브러리의 스트리밍 모드
            )
            
            if not response.ok:
                error_detail = response.text
                logger.error(f"Agent API 에러 (status {response.status_code}): {error_detail}")
                if response.status_code == 401:
                    logger.error(
                        "401 Unauthorized: 토큰이 누락/잘못되었습니다. "
                        "Apps 설정에서 DATABRICKS_TOKEN을 앱의 Service Principal 토큰으로 주입했는지 확인하세요."
                    )
                response.raise_for_status()
            
            # SSE 스트림 파싱 및 yield
            for line in response.iter_lines():
                if not line:
                    continue
                
                line_str = line.decode('utf-8')
                
                # SSE 형식: "data: {...}"
                if line_str.startswith('data: '):
                    data_str = line_str[6:]  # "data: " 제거
                    
                    # [DONE] 신호 확인
                    if data_str.strip() == '[DONE]':
                        logger.info("스트리밍 완료")
                        break
                    
                    try:
                        event_data = json.loads(data_str)
                        yield event_data
                    except json.JSONDecodeError as e:
                        logger.warning(f"JSON 파싱 실패: {data_str[:100]}")
                        continue
            
            logger.info("Agent 스트리밍 응답 수신 완료")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Agent 스트리밍 호출 실패: {str(e)}")
            raise Exception(f"Agent 스트리밍 호출 실패: {str(e)}")
        except ValueError as e:
            # 토큰 미설정 등 사전 검증 실패
            logger.error(str(e))
            raise


class VolumeUploader:
    """Unity Catalog Volume 파일 업로더 (Databricks Files API 사용)"""
    
    @staticmethod
    def safe_filename(filename):
        """
        원본 파일명을 최대한 유지하면서 안전하게 만듭니다.
        한글, 영문, 숫자, 일부 특수문자를 유지합니다.
        """
        # 파일명과 확장자 분리
        if '.' in filename:
            name_parts = filename.rsplit('.', 1)
            name = name_parts[0]
            ext = name_parts[1]
        else:
            name = filename
            ext = ''
        
        # 위험한 문자 제거 (경로 구분자, 제어 문자 등)
        # 허용: 한글, 영문, 숫자, 공백, 하이픈, 언더스코어, 괄호, 점
        name = re.sub(r'[/\\:*?"<>|]', '', name)
        name = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', name)
        
        # 연속된 공백을 하나로
        name = re.sub(r'\s+', ' ', name)
        
        # 앞뒤 공백 제거
        name = name.strip()
        
        # 파일명이 비어있으면 타임스탬프 사용
        if not name:
            from datetime import datetime
            name = f"file_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 확장자와 결합
        if ext:
            return f"{name}.{ext}"
        return name
    
    def __init__(self):
        base_path_str = Config.VOLUME_BASE_PATH
        logger.info(f"VolumeUploader 초기화 시작: VOLUME_BASE_PATH={base_path_str}")
        
        # Databricks Apps 환경 감지 (DATABRICKS_TOKEN이 있으면 Databricks 환경)
        self.is_databricks = bool(os.environ.get('DATABRICKS_TOKEN'))
        self.databricks_host = os.environ.get('DATABRICKS_HOST', '')
        
        # Volume 경로 설정
        if base_path_str.startswith('/Volumes'):
            self.volume_path = base_path_str
            self.use_files_api = self.is_databricks
            
            if self.use_files_api:
                logger.info(f"Databricks Files API 모드: volume_path={self.volume_path}")
                # 로컬 임시 저장소 사용 (업로드 전 임시 저장)
                self.local_temp_path = Path('/tmp/uploads')
                self.local_temp_path.mkdir(parents=True, exist_ok=True)
            else:
                # 로컬 개발 환경 - local_volumes 사용
                logger.info("로컬 개발 모드: local_volumes 사용")
                self.local_temp_path = Path('./local_volumes')
                self.local_temp_path.mkdir(parents=True, exist_ok=True)
                self.use_files_api = False
        else:
            # 일반 경로 사용 (로컬 개발)
            self.volume_path = base_path_str
            self.local_temp_path = Path(base_path_str)
            self.local_temp_path.mkdir(parents=True, exist_ok=True)
            self.use_files_api = False
            logger.info(f"로컬 파일 시스템 모드: path={self.local_temp_path}")
        
        self.allowed_extensions = Config.ALLOWED_FILE_TYPES
        self.max_size_mb = Config.MAX_UPLOAD_MB
        
        logger.info(f"VolumeUploader 초기화 완료: use_files_api={self.use_files_api}, "
                   f"local_temp_path={self.local_temp_path}, volume_path={self.volume_path}")
    
    def is_allowed_file(self, filename):
        """허용된 파일 형식 확인"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def _upload_to_volume_via_api(self, local_file_path, volume_file_path):
        """Databricks Files API를 사용하여 Volume에 파일 업로드"""
        try:
            # Databricks Files API endpoint
            # PUT /api/2.0/fs/files{path}
            # 참고: https://docs.databricks.com/api/workspace/files/upload
            
            token = os.environ.get('DATABRICKS_TOKEN')
            if not token:
                raise ValueError("DATABRICKS_TOKEN이 설정되지 않았습니다")
            
            # Databricks 호스트 URL 추출 (AGENT_ENDPOINT_URL에서 파싱)
            agent_url = Config.AGENT_ENDPOINT_URL
            if '://' in agent_url:
                host = agent_url.split('://')[1].split('/')[0]
                databricks_host = f"https://{host}"
            else:
                raise ValueError(f"유효하지 않은 AGENT_ENDPOINT_URL: {agent_url}")
            
            # Files API URL 구성
            # /api/2.0/fs/files 엔드포인트 사용
            # URL 인코딩하지 않고 직접 전달 (Databricks가 자동으로 처리)
            api_url = f"{databricks_host}/api/2.0/fs/files{volume_file_path}"
            
            headers = {
                'Authorization': f'Bearer {token}',
            }
            
            # 파일 읽기
            with open(local_file_path, 'rb') as f:
                file_content = f.read()
            
            logger.info(f"Files API 업로드 시작: {api_url}")
            logger.info(f"Volume 경로: {volume_file_path}")
            
            # PUT 요청으로 파일 업로드
            response = requests.put(
                api_url,
                headers=headers,
                data=file_content,
                timeout=120
            )
            
            if not response.ok:
                error_detail = response.text
                logger.error(f"Files API 업로드 실패 (status {response.status_code}): {error_detail}")
                raise Exception(f"Files API 업로드 실패: {error_detail}")
            
            logger.info(f"Files API 업로드 완료: {volume_file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Files API 업로드 오류: {str(e)}")
            raise
    
    def upload_file(self, file, session_id):
        """파일 업로드"""
        if not file or file.filename == '':
            raise ValueError("파일이 없습니다")
        
        if not self.is_allowed_file(file.filename):
            raise ValueError(
                f"허용되지 않은 파일 형식입니다. "
                f"허용: {', '.join(self.allowed_extensions)}"
            )
        
        # 파일 크기 확인
        file.seek(0, os.SEEK_END)
        size_mb = file.tell() / (1024 * 1024)
        file.seek(0)
        
        if size_mb > self.max_size_mb:
            raise ValueError(
                f"파일 크기가 너무 큽니다 ({size_mb:.1f}MB). "
                f"최대: {self.max_size_mb}MB"
            )
        
        # 안전한 파일명 (원본 유지)
        filename = self.safe_filename(file.filename)
        logger.info(f"원본 파일명: {file.filename} → 저장 파일명: {filename}")
        
        # 1단계: 로컬 임시 저장
        session_dir = self.local_temp_path / "uploads" / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        
        local_file_path = session_dir / filename
        file.save(str(local_file_path))
        logger.info(f"로컬 임시 저장 완료: {local_file_path}")
        
        # 2단계: Volume 경로 결정 및 업로드
        if self.use_files_api:
            # Databricks Files API 사용
            volume_file_path = f"{self.volume_path}/uploads/{session_id}/{filename}"
            
            try:
                self._upload_to_volume_via_api(str(local_file_path), volume_file_path)
                logger.info(f"Volume 업로드 완료: {volume_file_path}")
                
                # 임시 파일 삭제 (선택사항)
                # local_file_path.unlink()
                
                return {
                    'filename': filename,
                    'path': volume_file_path,
                    'size_mb': round(size_mb, 2)
                }
            except Exception as e:
                logger.error(f"Volume 업로드 실패: {str(e)}")
                # 폴백: 로컬 경로 반환
                logger.warning("폴백: 로컬 임시 경로 반환")
                return {
                    'filename': filename,
                    'path': str(local_file_path),
                    'size_mb': round(size_mb, 2),
                    'warning': 'Volume 업로드 실패, 로컬 경로 사용'
                }
        else:
            # 로컬 개발 환경 - 로컬 파일 사용
            return {
                'filename': filename,
                'path': str(local_file_path),
                'size_mb': round(size_mb, 2)
            }


# 클라이언트 인스턴스
agent_client = DatabricksAgentClient()
uploader = VolumeUploader()


@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')


@app.route('/api/chat', methods=['POST'])
def chat():
    """채팅 메시지 처리 (Non-streaming, 하위 호환성 유지)"""
    try:
        data = request.json
        question = data.get('question', '').strip()
        session_id = data.get('session_id')
        
        if not question:
            return jsonify({'error': '질문을 입력해주세요'}), 400
        
        # 세션 관리
        session_id, session_data = SessionManager.get_or_create_session(session_id)
        
        # 사용자 질문 히스토리 추가
        SessionManager.add_to_history(session_id, 'user', question)
        
        # Agent 호출
        result = agent_client.query(
            question=question,
            history=session_data['history'][:-1],  # 현재 질문 제외
            uploaded_files=session_data['uploaded_files']
        )
        
        # 응답 파싱 (Databricks Agent 응답 형식에 따라 유연하게 처리)
        logger.info(f"응답 파싱 시작, 응답 키: {list(result.keys())}")
        answer = ''
        
        # 응답 형식 1: choices 배열 (OpenAI 스타일)
        if 'choices' in result and len(result['choices']) > 0:
            choice = result['choices'][0]
            if 'message' in choice:
                answer = choice['message'].get('content', '')
            elif 'text' in choice:
                answer = choice['text']
            logger.info(f"choices 형식으로 파싱: {answer[:100] if answer else '(empty)'}")
        # 응답 형식 2: 직접 content 필드
        elif 'content' in result:
            answer = result['content']
            logger.info(f"content 형식으로 파싱: {answer[:100] if answer else '(empty)'}")
        # 응답 형식 3: answer 필드 (기존 형식)
        elif 'answer' in result:
            answer = result['answer']
            logger.info(f"answer 형식으로 파싱: {answer[:100] if answer else '(empty)'}")
        # 응답 형식 4: message 필드
        elif 'message' in result:
            answer = result['message']
            logger.info(f"message 형식으로 파싱: {answer[:100] if answer else '(empty)'}")
        # 응답 형식 5: output 필드 (Databricks Agent Framework)
        elif 'output' in result:
            output = result['output']
            if isinstance(output, dict):
                answer = output.get('content', '') or output.get('text', '') or str(output)
            elif isinstance(output, str):
                answer = output
            elif isinstance(output, list) and len(output) > 0:
                # output 리스트에서 최종 메시지 찾기 (역순으로 검색)
                for item in reversed(output):
                    if isinstance(item, dict):
                        # type이 'message'이고 role이 'assistant'인 항목 찾기
                        if item.get('type') == 'message' and item.get('role') == 'assistant':
                            content = item.get('content', [])
                            if isinstance(content, list):
                                # content 배열에서 text 추출
                                text_parts = []
                                for content_item in content:
                                    if isinstance(content_item, dict):
                                        if 'text' in content_item:
                                            text_parts.append(content_item['text'])
                                answer = '\n\n'.join(text_parts)
                                if answer:
                                    break
                        # 또는 직접 content/text 필드가 있는 경우
                        elif 'content' in item:
                            answer = item['content']
                            break
                        elif 'text' in item:
                            answer = item['text']
                            break
                
                # 답변을 찾지 못한 경우 첫 번째 항목 사용 (fallback)
                if not answer and len(output) > 0:
                    answer = str(output[0])
            logger.info(f"output 형식으로 파싱: {answer[:100] if answer else '(empty)'}")
        else:
            logger.warning(f"알 수 없는 응답 형식. 전체 응답: {result}")
            answer = str(result)
        
        logger.info(f"최종 답변 길이: {len(answer)} chars")
        
        # 응답 히스토리 추가
        SessionManager.add_to_history(session_id, 'assistant', answer)
        
        return jsonify({
            'session_id': session_id,
            'answer': answer,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"채팅 처리 오류: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    """채팅 메시지 스트리밍 처리 (SSE)"""
    # request context 밖에서 데이터 읽기
    data = request.json
    question = data.get('question', '').strip()
    session_id = data.get('session_id')
    
    def generate():
        try:
            
            if not question:
                yield f"data: {json.dumps({'error': '질문을 입력해주세요'})}\n\n"
                return
            
            # 세션 관리
            session_id, session_data = SessionManager.get_or_create_session(session_id)
            
            # 사용자 질문 히스토리 추가
            SessionManager.add_to_history(session_id, 'user', question)
            
            # 세션 ID 전송
            yield f"data: {json.dumps({'type': 'session', 'session_id': session_id})}\n\n"
            
            # 누적 응답 텍스트
            accumulated_text = ''
            
            # Agent 스트리밍 호출
            for event in agent_client.query_stream(
                question=question,
                history=session_data['history'][:-1],  # 현재 질문 제외
                uploaded_files=session_data['uploaded_files']
            ):
                # 이벤트 타입별 처리
                event_type = event.get('event_type') or event.get('type')
                
                # Delta 텍스트 추출
                delta_text = ''
                
                # Databricks Agent 응답 형식 파싱
                if 'delta' in event:
                    delta = event['delta']
                    if isinstance(delta, dict):
                        delta_text = delta.get('text', '') or delta.get('content', '')
                    elif isinstance(delta, str):
                        delta_text = delta
                
                # 또는 직접 content 필드
                elif 'content' in event:
                    content = event['content']
                    if isinstance(content, list):
                        # content 배열에서 text 추출
                        for item in content:
                            if isinstance(item, dict) and 'text' in item:
                                delta_text += item['text']
                    elif isinstance(content, dict):
                        delta_text = content.get('text', '')
                    elif isinstance(content, str):
                        delta_text = content
                
                # 또는 choices (OpenAI 스타일)
                elif 'choices' in event and len(event['choices']) > 0:
                    choice = event['choices'][0]
                    if 'delta' in choice:
                        delta_text = choice['delta'].get('content', '')
                    elif 'text' in choice:
                        delta_text = choice['text']
                
                # 텍스트가 있으면 전송
                if delta_text:
                    accumulated_text += delta_text
                    yield f"data: {json.dumps({'type': 'delta', 'text': delta_text})}\n\n"
                
                # 완료 이벤트 확인
                if event_type in ['response.completed', 'message.completed', 'done']:
                    logger.info("스트리밍 완료 이벤트 수신")
                    break
            
            # 응답 히스토리 추가
            SessionManager.add_to_history(session_id, 'assistant', accumulated_text)
            
            # 완료 신호
            yield f"data: {json.dumps({'type': 'done', 'full_text': accumulated_text})}\n\n"
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            logger.error(f"스트리밍 처리 오류: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    return app.response_class(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',  # Nginx 버퍼링 비활성화
            'Connection': 'keep-alive'
        }
    )


@app.route('/api/upload', methods=['POST'])
def upload():
    """파일 업로드 처리"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': '파일이 없습니다'}), 400
        
        file = request.files['file']
        session_id = request.form.get('session_id')
        
        if not session_id:
            return jsonify({'error': '세션 ID가 필요합니다'}), 400
        
        # 세션 확인
        session_id, session_data = SessionManager.get_or_create_session(session_id)
        
        # 파일 업로드
        file_info = uploader.upload_file(file, session_id)
        
        # 세션에 파일 정보 추가
        session_data['uploaded_files'].append(file_info)
        
        return jsonify({
            'success': True,
            'file': file_info
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"파일 업로드 오류: {str(e)}")
        return jsonify({'error': '파일 업로드 중 오류가 발생했습니다'}), 500


@app.route('/api/session/new', methods=['POST'])
def new_session():
    """새 세션 시작"""
    try:
        session_id = str(uuid.uuid4())
        chat_sessions[session_id] = {
            'id': session_id,
            'created_at': datetime.now(),
            'last_access': datetime.now(),
            'history': [],
            'uploaded_files': []
        }
        
        return jsonify({
            'session_id': session_id,
            'message': '새 세션이 시작되었습니다'
        })
        
    except Exception as e:
        logger.error(f"세션 생성 오류: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/session/<session_id>/history', methods=['GET'])
def get_history(session_id):
    """세션 히스토리 조회"""
    try:
        if session_id not in chat_sessions:
            return jsonify({'error': '세션을 찾을 수 없습니다'}), 404
        
        return jsonify({
            'session_id': session_id,
            'history': chat_sessions[session_id]['history'],
            'uploaded_files': chat_sessions[session_id]['uploaded_files']
        })
        
    except Exception as e:
        logger.error(f"히스토리 조회 오류: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """헬스체크"""
    SessionManager.clear_old_sessions()
    return jsonify({
        'status': 'healthy',
        'active_sessions': len(chat_sessions)
    })


@app.route('/debug/auth', methods=['GET'])
def debug_auth():
    """인증 관련 디버그 엔드포인트 (민감정보는 마스킹)"""
    try:
        agent_endpoint = Config.AGENT_ENDPOINT_URL
        token_env = bool(os.environ.get('DATABRICKS_TOKEN'))
        token_config = bool(Config.DATABRICKS_TOKEN)
        token_alt = bool(os.environ.get('DATABRICKS_APP_TOKEN'))
        token_preview = None
        # 토큰 길이만 표시하고 나머지는 마스킹
        raw = (Config.DATABRICKS_TOKEN or os.environ.get('DATABRICKS_TOKEN') or os.environ.get('DATABRICKS_APP_TOKEN') or '')
        if raw:
            token_preview = f"dapi***{raw[-6:]}"
        return jsonify({
            'agent_endpoint_url': agent_endpoint,
            'token_present': token_env or token_config or token_alt,
            'token_sources': {
                'config': token_config,
                'env_DATABRICKS_TOKEN': token_env,
                'env_DATABRICKS_APP_TOKEN': token_alt,
            },
            'token_preview': token_preview
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/debug/volume', methods=['GET'])
def debug_volume():
    """Volume 경로 디버그 엔드포인트"""
    try:
        volume_path = Config.VOLUME_BASE_PATH
        
        # 기본 정보
        info = {
            'configured_path': volume_path,
            'uploader_local_temp_path': str(uploader.local_temp_path),
            'uploader_volume_path': str(uploader.volume_path),
            'use_files_api': uploader.use_files_api,
            'is_databricks': uploader.is_databricks,
            'is_volume_path': volume_path.startswith('/Volumes'),
            'checks': {}
        }
        
        # 로컬 임시 경로 확인
        local_temp_path = uploader.local_temp_path
        info['checks']['local_temp_exists'] = local_temp_path.exists()
        info['checks']['local_temp_writable'] = os.access(str(local_temp_path), os.W_OK) if local_temp_path.exists() else False
        
        # 로컬 임시 경로 쓰기 테스트
        test_file = local_temp_path / '__test__.txt'
        try:
            test_file.write_text('test')
            info['checks']['can_write_local'] = True
            test_file.unlink()
        except Exception as e:
            info['checks']['can_write_local'] = False
            info['checks']['write_local_error'] = str(e)
        
        # Volume 직접 접근 테스트 (실패 예상)
        if volume_path.startswith('/Volumes'):
            info['checks']['volume_direct_exists'] = os.path.exists(volume_path)
            info['checks']['volume_direct_writable'] = os.access(volume_path, os.W_OK) if os.path.exists(volume_path) else False
            
            # Files API 사용 여부
            if uploader.use_files_api:
                info['files_api_status'] = 'enabled'
                info['files_api_note'] = 'Volume 업로드는 Databricks Files API를 통해 수행됩니다'
            else:
                info['files_api_status'] = 'disabled'
                info['files_api_note'] = '로컬 개발 모드 - Files API 미사용'
        
        # /Volumes 디렉토리 확인
        if os.path.exists('/Volumes'):
            try:
                volumes_list = os.listdir('/Volumes')
                info['volumes_root'] = {
                    'exists': True,
                    'catalogs': volumes_list[:10]  # 처음 10개만
                }
            except Exception as e:
                info['volumes_root'] = {
                    'exists': True,
                    'list_error': str(e)
                }
        else:
            info['volumes_root'] = {
                'exists': False,
                'note': '/Volumes 경로는 Databricks 런타임 내에서만 사용 가능'
            }
        
        # 환경 변수 확인
        info['env_vars'] = {
            'VOLUME_BASE_PATH': os.environ.get('VOLUME_BASE_PATH', 'not set'),
            'CATALOG_NAME': os.environ.get('CATALOG_NAME', 'not set'),
            'SCHEMA_NAME': os.environ.get('SCHEMA_NAME', 'not set'),
            'VOLUME_NAME': os.environ.get('VOLUME_NAME', 'not set'),
            'DATABRICKS_TOKEN': 'set' if os.environ.get('DATABRICKS_TOKEN') else 'not set'
        }
        
        return jsonify(info)
        
    except Exception as e:
        logger.error(f"Volume 디버그 오류: {str(e)}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # 로컬 개발용
    port = int(os.environ.get('PORT', 5000))
    app.run(
        host='0.0.0.0',
        port=port,
        debug=os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    )

