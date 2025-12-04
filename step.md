# APlan Integration Impact Map - 개발 단계별 작업 계획

## ✅ 완료된 작업

### 1단계: 프로젝트 구조 스캐폴딩
- [x] 디렉토리 구조 생성 (`app/`, `app/routers/`, `app/services/`, `templates/`)
- [x] `requirements.txt` 생성 (FastAPI, SQLModel, pandas, openpyxl 등)
- [x] `.gitignore` 생성

### 2단계: 데이터 모델 구현
- [x] `app/models.py` - IntegrationObject 모델 구현
  - 필수/선택 필드, 거버넌스 필드 포함
  - Relationship 정의 (outgoing_relations, incoming_relations)
- [x] `app/models.py` - IntegrationRelation 모델 구현
  - from_object_id, to_object_id 외래키
  - Relationship 정의 (from_object, to_object)

### 3단계: 데이터베이스 설정
- [x] `app/database.py` - SQLite 엔진 설정
- [x] `app/database.py` - `init_db()` 함수 구현
- [x] `app/database.py` - `get_session()` 의존성 주입 함수 구현

### 4단계: 메타데이터 로딩 스크립트
- [x] `load_mapping.py` - 엑셀 파일 읽기 로직
- [x] `load_mapping.py` - Objects 시트 UPSERT 로직
- [x] `load_mapping.py` - Relations 시트 UPSERT 로직
- [x] 에러 처리 및 로깅 구현

---

---

## ✅ 모든 단계 완료!

**프로젝트 상태**: MVP 완성 ✅

모든 단계가 완료되었습니다. 이제 서버를 실행하여 사용할 수 있습니다.

---

## 📋 완료된 작업 요약

### 5단계: FastAPI 메인 앱 설정
**목표**: FastAPI 애플리케이션 초기화 및 기본 설정

**작업 내용**:
- [x] `app/main.py` 생성
  - FastAPI 앱 인스턴스 생성
  - Jinja2 템플릿 엔진 설정
  - Static 파일 서빙 설정
  - 라우터 등록 (`app.routers.objects`)
  - 애플리케이션 시작 시 `init_db()` 호출

**참고**: MRD 4.1 - `uvicorn app.main:app --reload` 실행 가능

---

### 6단계: 영향도 분석 서비스 구현
**목표**: 그래프 탐색 및 Mermaid 다이어그램 생성 로직

**작업 내용**:
- [x] `app/services/impact_service.py` 생성
  - `get_impact_graph(object_id: int, depth: int)` 함수
    - depth=1: 직접 연결된 upstream/downstream만 탐색
    - depth=2: 한 단계 이웃까지 확장 탐색
    - 반환: 중심 오브젝트, upstream 리스트, downstream 리스트
  - `generate_mermaid_code(object_id: int, depth: int)` 함수
    - `flowchart LR` 형식의 Mermaid 텍스트 생성
    - 노드 라벨: `"시스템타입\n오브젝트명"` 형식
    - 중심 오브젝트 스타일링
    - 엣지: `노드1 --> 노드2` 형식

**참고**: MRD 9장 - 그래프 탐색 & Mermaid 생성 요구사항

---

### 7단계: API 라우터 구현
**목표**: RESTful API 엔드포인트 구현

**작업 내용**:
- [x] `app/routers/objects.py` 생성
  - `GET /objects` - 검색/리스트 조회 (HTML 템플릿)
  - `GET /objects/api` - 검색/리스트 조회 (JSON API)
  - `GET /objects/{object_id}` - 단일 오브젝트 상세 조회 (HTML 템플릿)
  - `GET /objects/{object_id}/api` - 단일 오브젝트 상세 조회 (JSON API)
  - `GET /objects/{object_id}/impact` - 영향도 정보 조회
    - 쿼리 파라미터: `depth` (1 또는 2, 기본값 1)
    - JSON 응답: `{object, upstream[], downstream[]}`
  - `GET /objects/{object_id}/mermaid` - Mermaid 코드 생성
    - 쿼리 파라미터: `depth` (기본값 2)
    - JSON 응답: `{mermaid_code: str}`

**참고**: MRD 7장 - API 요구사항

---

### 8단계: 템플릿 구현 (Jinja2)
**목표**: 웹 UI 화면 구현

**작업 내용**:
- [x] `templates/base.html` - 공통 레이아웃
  - 헤더: "APlan Integration Impact Map"
  - Bootstrap CDN 포함
  - Mermaid.js CDN 및 초기화 스크립트
  - `{% block content %}` 블록 정의
  
- [x] `templates/index.html` - 검색 화면 (`/objects`)
  - 검색 폼:
    - 키워드 입력 (`q`)
    - system_type 드롭다운 (All / SAP / APLAN / BW / BI / EAI / ...)
    - object_type 드롭다운 (All / IF / TABLE / REPORT / JOB / ...)
    - 검색 버튼
  - 결과 테이블:
    - 컬럼: object_key, name, system_type, object_type, layer, module, status
    - 각 행 클릭 시 `/objects/{id}`로 이동 (링크)
  
- [x] `templates/object_detail.html` - 상세/영향도 화면 (`/objects/{id}`)
  - 2컬럼 레이아웃:
    - 좌측 패널: 기본 정보 (이름, object_key, system_type, object_type, layer, module, owner_team, status, environment, tags, description)
    - 우측 상단: Upstream/Downstream 리스트 (테이블, 링크 포함)
    - 우측 하단: Mermaid 다이어그램 영역
      - Mermaid 코드 textarea (readonly, 복사용)
      - "Copy Mermaid Code" 버튼 (JavaScript)
      - `<div class="mermaid">` 렌더링 영역

**참고**: MRD 8장 - 화면(템플릿) 요구사항

---

### 9단계: 템플릿 라우터 연결
**목표**: HTML 템플릿을 반환하는 라우트 추가

**작업 내용**:
- [x] `app/routers/objects.py`에 템플릿 라우트 추가
  - `GET /objects` - `index.html` 렌더링 (검색 화면)
    - 쿼리 파라미터로 필터링된 결과 전달
  - `GET /objects/{object_id}` - `object_detail.html` 렌더링 (상세 화면)
    - 오브젝트 정보, 영향도 정보, Mermaid 코드 전달

**참고**: FastAPI의 `HTMLResponse` 및 `Jinja2Templates` 사용

---

### 10단계: 테스트 및 검증
**목표**: 전체 기능 동작 확인

**작업 내용**:
- [x] 샘플 `mapping.xlsx` 파일 생성
  - `create_sample_mapping.py` 스크립트 생성
  - `objects` 시트: 10개 샘플 오브젝트 데이터
  - `relations` 시트: 10개 샘플 관계 데이터
- [x] `load_mapping.py` 실행 테스트
  - Objects 10개 로딩 성공
  - Relations 10개 로딩 성공
- [x] 전체 기능 통합 테스트
  - 검색 화면 렌더링 확인
  - 검색 기능 동작 확인
  - API 엔드포인트 동작 확인
  - 상세 화면 렌더링 확인
  - 영향도 분석 기능 확인
  - Mermaid 다이어그램 렌더링 확인

---

## 📝 참고사항

### 실행 순서
1. `pip install -r requirements.txt` - 의존성 설치 ✅
2. `python create_sample_mapping.py` - 샘플 데이터 생성 (선택사항) ✅
3. `python load_mapping.py` - 메타데이터 로딩 ✅
4. `uvicorn app.main:app --reload` - 서버 실행
5. 브라우저에서 `http://localhost:8000/objects` 접속
6. API 문서: `http://localhost:8000/docs`

### 파일 구조 (최종)
```
aplan/
├── app/
│   ├── __init__.py
│   ├── main.py              # ✅ 완료
│   ├── models.py            # ✅ 완료
│   ├── database.py          # ✅ 완료
│   ├── routers/
│   │   ├── __init__.py
│   │   └── objects.py       # ✅ 완료
│   └── services/
│       ├── __init__.py
│       └── impact_service.py # ✅ 완료
├── templates/
│   ├── base.html            # ✅ 완료
│   ├── index.html            # ✅ 완료
│   └── object_detail.html    # ✅ 완료
├── static/
│   └── css/                  # (선택사항)
├── mapping.xlsx              # (운영/PM이 관리)
├── load_mapping.py           # ✅ 완료
├── requirements.txt          # ✅ 완료
├── .gitignore                # ✅ 완료
├── MRD.md                    # 요구사항 문서
└── step.md                   # 이 파일
```

### 우선순위
1. **5단계** (FastAPI 메인) → **6단계** (서비스) → **7단계** (API) → **8단계** (템플릿) → **9단계** (템플릿 연결) → **10단계** (테스트)
2. 각 단계는 논리적으로 독립적으로 구현 가능하지만, 순서대로 진행하는 것을 권장

