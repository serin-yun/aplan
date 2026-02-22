# 서버 구동 가이드

## 🚀 빠른 시작 (테스트용)

### 1단계: 의존성 확인 및 설치

```powershell
# Python 버전 확인 (3.11 이상 필요)
python --version

# 의존성 설치
pip install -r requirements.txt
```

### 2단계: 데이터 준비 (선택사항)

```powershell
# 샘플 데이터 생성 (테스트용)
python create_sample_mapping.py

# 데이터베이스에 데이터 로딩
python load_mapping.py
```

**참고**: 
- `mapping.xlsx` 파일이 이미 있다면 `load_mapping.py`만 실행하면 됩니다.
- 샘플 데이터가 필요하다면 `create_sample_mapping.py`를 먼저 실행하세요.

### 3단계: 서버 실행

#### 방법 1: 기본 실행 (권장)
```powershell
uvicorn app.main:app --reload
```

#### 방법 2: 포트 지정 실행
```powershell
uvicorn app.main:app --reload --port 8000
```

#### 방법 3: 호스트 및 포트 지정
```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 방법 4: Python 모듈로 직접 실행
```powershell
python -m uvicorn app.main:app --reload
```

### 4단계: 접속 확인

서버가 정상적으로 실행되면 다음과 같은 메시지가 표시됩니다:

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx] using WatchFiles
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**접속 URL**:
- 대시보드: http://localhost:8000/dashboard
- 검색: http://localhost:8000/objects
- 전체 맵: http://localhost:8000/objects/overview
- API 문서: http://localhost:8000/docs

---

## 🔧 서버 옵션 설명

### `--reload` 옵션
- 코드 변경 시 자동으로 서버 재시작
- 개발 중에 유용함
- **프로덕션 환경에서는 사용하지 마세요**

### `--port` 옵션
- 서버 포트 지정 (기본값: 8000)
- 다른 포트를 사용하려면: `--port 8080`

### `--host` 옵션
- 서버 호스트 지정
- `0.0.0.0`: 모든 네트워크 인터페이스에서 접속 가능
- `127.0.0.1` 또는 생략: 로컬에서만 접속 가능

---

## 📋 전체 테스트 시나리오

### 시나리오 A: 처음 시작하는 경우

```powershell
# 1. 의존성 설치
pip install -r requirements.txt

# 2. 샘플 데이터 생성
python create_sample_mapping.py

# 3. 데이터 로딩
python load_mapping.py

# 4. 서버 실행
uvicorn app.main:app --reload

# 5. 브라우저에서 접속
# http://localhost:8000/dashboard
```

### 시나리오 B: 데이터만 업데이트하는 경우

```powershell
# 1. mapping.xlsx 파일 수정 또는 교체

# 2. 데이터 로딩 (서버 실행 전)
python load_mapping.py

# 3. 서버 실행
uvicorn app.main:app --reload
```

### 시나리오 C: 코드 변경 후 재시작

```powershell
# --reload 옵션이 있으면 자동 재시작되지만,
# 수동으로 재시작하려면:

# 1. 서버 중지 (Ctrl+C)

# 2. 서버 재시작
uvicorn app.main:app --reload
```

---

## 🛠️ 문제 해결

### 문제 1: 포트가 이미 사용 중입니다

**에러 메시지**:
```
ERROR:    [Errno 10048] error while attempting to bind on address ('127.0.0.1', 8000)
```

**해결 방법**:
```powershell
# 다른 포트 사용
uvicorn app.main:app --reload --port 8001
```

### 문제 2: 모듈을 찾을 수 없습니다

**에러 메시지**:
```
ModuleNotFoundError: No module named 'app'
```

**해결 방법**:
```powershell
# 프로젝트 루트 디렉토리에서 실행 확인
# 현재 디렉토리 확인
pwd

# 프로젝트 루트로 이동 (필요시)
cd C:\Cursor\aplan
```

### 문제 3: 데이터베이스 오류

**에러 메시지**:
```
sqlite3.OperationalError: no such table
```

**해결 방법**:
```powershell
# 데이터베이스 재생성
Remove-Item impact_map.db -ErrorAction SilentlyContinue
python load_mapping.py
```

### 문제 4: 의존성 오류

**에러 메시지**:
```
ModuleNotFoundError: No module named 'fastapi'
```

**해결 방법**:
```powershell
# 의존성 재설치
pip install -r requirements.txt

# 또는 개별 설치
pip install fastapi uvicorn sqlmodel pandas openpyxl jinja2
```

---

## 📊 서버 상태 확인

### 정상 실행 확인

서버가 정상적으로 실행되면:

1. **콘솔 메시지 확인**
   ```
   INFO:     Uvicorn running on http://127.0.0.1:8000
   INFO:     Application startup complete.
   ```

2. **브라우저에서 접속 테스트**
   - http://localhost:8000/dashboard 접속
   - 페이지가 정상적으로 로드되는지 확인

3. **API 문서 확인**
   - http://localhost:8000/docs 접속
   - Swagger UI가 표시되는지 확인

---

## 🔄 서버 중지 및 재시작

### 서버 중지
```
Ctrl + C (PowerShell에서)
```

### 서버 재시작
```powershell
# 중지 후 다시 실행
uvicorn app.main:app --reload
```

---

## 💡 개발 팁

### 1. 자동 재로드 활성화
- `--reload` 옵션 사용 시 코드 변경이 자동 감지됨
- 파일 저장 시 서버가 자동으로 재시작됨

### 2. 로그 확인
- 서버 콘솔에서 모든 요청 로그 확인 가능
- 에러 발생 시 콘솔에 상세 정보 표시

### 3. 디버깅 모드
```powershell
# 더 자세한 로그를 보려면
uvicorn app.main:app --reload --log-level debug
```

### 4. 백그라운드 실행 (선택사항)
```powershell
# PowerShell에서 백그라운드 실행
Start-Process powershell -ArgumentList "-NoExit", "-Command", "uvicorn app.main:app --reload"
```

---

## 📝 체크리스트

서버 실행 전 확인사항:

- [ ] Python 3.11 이상 설치됨
- [ ] 의존성 설치 완료 (`pip install -r requirements.txt`)
- [ ] `mapping.xlsx` 파일 존재 (또는 샘플 데이터 생성)
- [ ] 데이터 로딩 완료 (`python load_mapping.py`)
- [ ] 포트 8000이 사용 가능함
- [ ] 프로젝트 루트 디렉토리에서 명령어 실행

---

## 🎯 빠른 테스트 명령어 (한 줄)

```powershell
# 모든 준비 작업을 한 번에 (데이터가 없는 경우)
python create_sample_mapping.py; python load_mapping.py; uvicorn app.main:app --reload

# 데이터가 이미 있는 경우
uvicorn app.main:app --reload
```

---

**서버 실행 후**: http://localhost:8000/dashboard 에서 테스트를 시작하세요!








