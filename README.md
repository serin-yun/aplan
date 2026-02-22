# APlan Integration Impact Map

APlan과 연계된 Legacy 시스템(SAP, BW, IAM, NPD, CDP)과 연계 툴(EAI)의 인터페이스·테이블·리포트 메타데이터를 관리하고, 오브젝트 간 영향도를 시각화하는 웹 도구입니다.

## 🎯 주요 기능

- **메타데이터 관리**: 엑셀 파일 기반 오브젝트 및 관계 정보 관리
- **인터랙티브 그래프**: vis.js Network를 활용한 시각적 영향도 분석
- **전체 시스템 맵**: 모든 오브젝트와 관계를 한눈에 볼 수 있는 전체 맵
- **영향도 분석**: 특정 오브젝트 기준 Upstream/Downstream 영향도 탐색
- **필터링 및 검색**: 시스템 타입, 레이어, 모듈별 필터링 및 검색 기능

## 🚀 빠른 시작

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. 샘플 데이터 생성 (선택사항)
python create_sample_mapping.py

# 3. 메타데이터 로딩
python load_mapping.py

# 4. 서버 실행
uvicorn app.main:app --reload
```

## 📍 접속 URL

- **대시보드**: http://localhost:8000/dashboard
- **검색 화면**: http://localhost:8000/objects
- **전체 맵(요약)**: http://localhost:8000/objects/overview?view=business
- **전체 맵(요약/리더)**: http://localhost:8000/objects/overview?view=leader
- **전체 맵(요약/운영)**: http://localhost:8000/objects/overview?view=ops
- **전체 맵(전수)**: http://localhost:8000/objects/overview?mode=full&view=ops
- **Flow 목록**: http://localhost:8000/flows?view=business
- **Flow 상세**: http://localhost:8000/flows/{flow_key}?view=business
- **Flow 리포트**: http://localhost:8000/flows/{flow_key}/report?view=leader
- **API 문서**: http://localhost:8000/docs

## ✅ 커밋 1 검증 시나리오

- http://localhost:8000/objects/overview?view=business 접속 → 전수 그래프 없이 요약 지도 + 카드만 노출
- 상단 PRIMARY FLOW 버튼 또는 첫 카드 클릭 → `/flows/{flow_key}?view=business`로 이동
- http://localhost:8000/objects/overview?mode=full&view=ops 접속 → 기존 전수 맵 유지

## ✅ 커밋 2 검증 시나리오

- http://localhost:8000/flows/{flow_key}?view=business 접속 → Stepper 중심 화면으로 흐름 이해
- http://localhost:8000/flows/{flow_key}/report?view=leader 접속 → 1페이지 인쇄/PDF 저장 가능
- http://localhost:8000/flows/{flow_key}?view=ops 접속 → 운영 정보 기본 ON 확인

## 👥 사용자별 추천 사용 시나리오

- 현업: overview → 카드 클릭 → stepper 확인
- 리더: overview → report 인쇄/PDF
- 운영/PM: flow 상세에서 운영정보 ON → 기술 확인

## 📋 기술 스택

- **Backend**: FastAPI, SQLModel, SQLite
- **Frontend**: Jinja2, Bootstrap 5, vis.js Network
- **Language**: Python 3.11+

## 📁 프로젝트 구조

```
aplan/
├── app/                        # 애플리케이션 코드
│   ├── main.py                 # FastAPI 애플리케이션
│   ├── models.py               # 데이터 모델
│   ├── database.py             # 데이터베이스 설정
│   ├── routers/                # API 라우터
│   │   ├── dashboard.py        # 대시보드 라우터
│   │   ├── objects.py          # 오브젝트 API 라우터
│   │   └── upload.py           # 파일 업로드 라우터
│   └── services/
│       └── impact_service.py   # 영향도 분석 서비스
├── templates/                  # HTML 템플릿
├── static/                     # 정적 파일 (CSS, JS)
├── create_sample_mapping.py    # 샘플 데이터 생성 스크립트
├── create_template.py          # 템플릿 파일 생성 스크립트
├── load_mapping.py             # 데이터 로딩 스크립트
├── migrate_add_owner.py        # DB 마이그레이션 스크립트
├── mapping_template.xlsx       # 엑셀 템플릿
└── requirements.txt            # Python 의존성
```

## 📚 문서

| 문서 | 설명 |
|------|------|
| [MAPPING_GUIDE.md](./MAPPING_GUIDE.md) | 엑셀 파일 작성 완전 가이드 (object_key 채번 규칙 포함) |
| [START_SERVER.md](./START_SERVER.md) | 서버 구동 및 문제 해결 가이드 |
| [TEST_SCENARIOS.md](./TEST_SCENARIOS.md) | 테스트 시나리오 및 체크리스트 |
| [GIT_SETUP.md](./GIT_SETUP.md) | Git 형상관리 설정 가이드 |
| [MRD.md](./MRD.md) | 프로젝트 요구사항 문서 |

## 🔧 개발

### 데이터베이스 초기화

```bash
# 데이터베이스 파일 삭제 후 재생성
rm impact_map.db  # 또는 Windows: del impact_map.db
python load_mapping.py
```

## 📄 라이선스

내부 사용 프로젝트
