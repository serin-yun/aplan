# 서버 재시작 가이드

## 🔄 서버 재시작 방법

### 방법 1: 기존 프로세스 종료 후 재시작 (권장)

#### 1단계: 실행 중인 서버 종료

**PowerShell에서 실행:**
```powershell
# Python/uvicorn 프로세스 찾기
Get-Process | Where-Object {$_.ProcessName -like "*python*"}

# 모든 Python 프로세스 종료 (주의: 다른 Python 프로그램도 종료됨)
Get-Process | Where-Object {$_.ProcessName -like "*python*"} | Stop-Process -Force

# 또는 특정 포트(8000)를 사용하는 프로세스만 종료
netstat -ano | findstr :8000
# 위 명령어로 나온 PID를 확인한 후:
# Stop-Process -Id <PID> -Force
```

#### 2단계: 서버 재시작

```powershell
# 프로젝트 디렉토리로 이동 (이미 있다면 생략)
cd C:\Cursor\aplan

# 서버 실행
python -m uvicorn app.main:app --reload --port 8000
```

---

### 방법 2: 터미널에서 Ctrl+C로 종료 후 재시작

1. 서버가 실행 중인 터미널 창에서 **Ctrl + C** 키를 누릅니다
2. 서버가 종료되면 다음 명령어로 재시작:
   ```powershell
   python -m uvicorn app.main:app --reload --port 8000
   ```

---

### 방법 3: 자동 재시작 (--reload 옵션 사용)

**이미 `--reload` 옵션으로 실행 중이라면:**
- 코드 파일을 수정하면 자동으로 서버가 재시작됩니다
- 별도의 재시작이 필요 없습니다

**확인 방법:**
- 코드를 수정하고 저장하면 터미널에 "Reloading..." 메시지가 표시됩니다

---

## ✅ 서버 실행 확인

서버가 정상적으로 실행되었는지 확인:

```powershell
# 방법 1: 브라우저에서 접속
# http://localhost:8000/docs

# 방법 2: PowerShell에서 확인
curl http://localhost:8000/docs

# 방법 3: 포트 확인
netstat -ano | findstr :8000
```

**정상 실행 시:**
- StatusCode: 200 OK
- 브라우저에서 API 문서 페이지가 표시됨

---

## 🚨 문제 해결

### 포트가 이미 사용 중인 경우

```powershell
# 포트 8000을 사용하는 프로세스 찾기
netstat -ano | findstr :8000

# PID 확인 후 종료
Stop-Process -Id <PID> -Force

# 또는 다른 포트 사용
python -m uvicorn app.main:app --reload --port 8001
```

### 서버가 시작되지 않는 경우

1. **의존성 확인:**
   ```powershell
   pip install -r requirements.txt
   ```

2. **Python 버전 확인:**
   ```powershell
   python --version
   # Python 3.11 이상 권장
   ```

3. **에러 메시지 확인:**
   - 터미널에 표시되는 에러 메시지를 확인하세요

---

## 📝 빠른 참조

### 서버 시작
```powershell
cd C:\Cursor\aplan
python -m uvicorn app.main:app --reload --port 8000
```

### 서버 종료
- 터미널에서: **Ctrl + C**
- PowerShell에서: `Get-Process | Where-Object {$_.ProcessName -like "*python*"} | Stop-Process -Force`

### 서버 상태 확인
```powershell
curl http://localhost:8000/docs
```

---

## 💡 팁

1. **백그라운드 실행 (선택사항):**
   ```powershell
   Start-Process python -ArgumentList "-m", "uvicorn", "app.main:app", "--reload", "--port", "8000"
   ```

2. **로그 파일로 저장:**
   ```powershell
   python -m uvicorn app.main:app --reload --port 8000 > server.log 2>&1
   ```

3. **개발 중에는 `--reload` 옵션 사용 권장:**
   - 코드 변경 시 자동 재시작
   - 개발 효율성 향상

