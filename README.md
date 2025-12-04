# APlan Integration Impact Map

APlan과 연계된 Legacy 시스템(SAP, BW, IAM, NPD, CDP)과 연계 툴(EAI)의 인터페이스·테이블·리포트 메타데이터를 관리하고, 오브젝트 간 영향도를 시각화하는 웹 도구입니다.

## 🎯 주요 기능

- **메타데이터 관리**: 엑셀 파일 기반 오브젝트 및 관계 정보 관리
- **인터랙티브 그래프**: vis.js Network를 활용한 시각적 영향도 분석
- **전체 시스템 맵**: 모든 오브젝트와 관계를 한눈에 볼 수 있는 전체 맵
- **영향도 분석**: 특정 오브젝트 기준 Upstream/Downstream 영향도 탐색
- **필터링 및 검색**: 시스템 타입, 레이어, 모듈별 필터링 및 검색 기능

## 🚀 빠른 시작

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 데이터 로딩

```bash
# 샘플 데이터 생성 (선택사항)
python create_sample_mapping.py

# 메타데이터 로딩
python load_mapping.py
```

### 3. 서버 실행

```bash
uvicorn app.main:app --reload
```

### 4. 접속

- **검색 화면**: http://localhost:8000/objects
- **전체 맵**: http://localhost:8000/objects/overview
- **API 문서**: http://localhost:8000/docs

## 📋 기술 스택

- **Backend**: FastAPI, SQLModel, SQLite
- **Frontend**: Jinja2, Bootstrap 5, vis.js Network
- **Language**: Python 3.11+

## 📁 프로젝트 구조

```
aplan/
├── app/
│   ├── main.py              # FastAPI 애플리케이션
│   ├── models.py            # 데이터 모델
│   ├── database.py          # 데이터베이스 설정
│   ├── routers/
│   │   └── objects.py       # API 라우터
│   └── services/
│       └── impact_service.py # 영향도 분석 서비스
├── templates/               # HTML 템플릿
├── mapping.xlsx            # 메타데이터 엑셀 파일
├── load_mapping.py         # 데이터 로딩 스크립트
└── requirements.txt       # Python 의존성
```

## 📝 데이터 업로드

메타데이터는 `mapping.xlsx` 파일을 통해 관리됩니다.

- **파일 양식**: `MAPPING_FILE_FORMAT.md` 참고
- **템플릿 파일**: `mapping_template.xlsx` 사용

자세한 내용은 [MAPPING_FILE_FORMAT.md](./MAPPING_FILE_FORMAT.md)를 참고하세요.

## 📚 문서

- [MRD.md](./MRD.md) - 프로젝트 요구사항 문서
- [QUICK_TEST_GUIDE.md](./QUICK_TEST_GUIDE.md) - 빠른 테스트 가이드
- [MAPPING_FILE_FORMAT.md](./MAPPING_FILE_FORMAT.md) - 엑셀 파일 양식 가이드
- [SERVER_RESTART.md](./SERVER_RESTART.md) - 서버 재시작 가이드

## 🔧 개발

### 테스트 실행

```bash
# 개별 테스트
python test_step10.py

# 전체 테스트
python -m pytest
```

### 데이터베이스 초기화

```bash
# 데이터베이스 파일 삭제 후 재생성
rm impact_map.db
python load_mapping.py
```

## 📄 라이선스

내부 사용 프로젝트

## 👥 기여자

- 프로젝트 관리: 운영/PM 팀

