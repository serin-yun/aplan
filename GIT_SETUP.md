# Git 형상관리 설정 가이드

## ✅ 설정 완료

Git 저장소가 초기화되었고 GitHub 원격 저장소가 연결되었습니다.

**원격 저장소**: https://github.com/serin-yun/aplan.git

---

## 📤 코드 업로드 (Push)

### 첫 업로드

```powershell
# 메인 브랜치로 푸시
git push -u origin main
```

### 이후 업로드

```powershell
# 변경사항 추가
git add .

# 커밋
git commit -m "변경 내용 설명"

# 푸시
git push
```

---

## 📥 코드 다운로드 (Pull)

```powershell
# 최신 코드 가져오기
git pull origin main
```

---

## 🔄 일반적인 작업 흐름

### 1. 변경사항 확인
```powershell
git status
```

### 2. 변경사항 스테이징
```powershell
git add .
# 또는 특정 파일만
git add app/routers/objects.py
```

### 3. 커밋
```powershell
git commit -m "기능 추가: 인터랙티브 그래프 개선"
```

### 4. 푸시
```powershell
git push
```

---

## 📋 .gitignore 설정

다음 파일들은 Git에 포함되지 않습니다:

- `impact_map.db` - 데이터베이스 파일
- `mapping.xlsx` - 실제 데이터 파일 (템플릿은 포함)
- `__pycache__/` - Python 캐시
- `*.pyc`, `*.pyo` - 컴파일된 Python 파일
- `.env` - 환경 변수 파일

---

## ⚠️ 주의사항

1. **민감한 정보**: API 키, 비밀번호 등은 절대 커밋하지 마세요
2. **데이터베이스**: `impact_map.db`는 제외되어 있습니다
3. **실제 데이터**: `mapping.xlsx`는 제외되어 있습니다 (템플릿은 포함)

---

## 🔍 유용한 Git 명령어

```powershell
# 변경 이력 확인
git log

# 원격 저장소 정보 확인
git remote -v

# 브랜치 목록
git branch

# 현재 상태 확인
git status

# 특정 파일의 변경 이력
git log --follow app/routers/objects.py
```

---

## 🚨 문제 해결

### 원격 저장소 연결 오류

```powershell
# 원격 저장소 확인
git remote -v

# 원격 저장소 재설정
git remote set-url origin https://github.com/serin-yun/aplan.git
```

### 충돌 해결

```powershell
# 최신 코드 가져오기
git pull origin main

# 충돌 발생 시 수동으로 해결 후
git add .
git commit -m "충돌 해결"
git push
```

---

## 📝 커밋 메시지 가이드

좋은 커밋 메시지 예시:

```
기능 추가: 인터랙티브 그래프 시각화 개선
- vis.js Network 도입
- 필터링 및 검색 기능 추가
- 파스텔 톤 색상 적용
```

```
버그 수정: 라우터 순서 문제 해결
- /objects/overview를 /objects/{id}보다 먼저 정의
```

```
문서: README.md 업데이트
- 설치 가이드 추가
- API 문서 링크 추가
```

