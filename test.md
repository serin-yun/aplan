# APlan Integration Impact Map - 테스트 가이드

## 📋 목차
1. [사전 준비](#사전-준비)
2. [서버 구동 방법](#서버-구동-방법)
3. [테스트 시나리오](#테스트-시나리오)
4. [API 엔드포인트 테스트](#api-엔드포인트-테스트)
5. [문제 해결](#문제-해결)

---

## 사전 준비

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

필요한 패키지:
- fastapi==0.115.0
- uvicorn[standard]==0.32.0
- sqlmodel==0.0.22
- jinja2==3.1.4
- pandas==2.2.3
- openpyxl==3.1.5
- python-multipart==0.0.12
- httpx (테스트용)

### 2. 샘플 데이터 생성 (선택사항)
```bash
python create_sample_mapping.py
```

이 명령어는 `mapping.xlsx` 파일을 생성합니다:
- `objects` 시트: 10개 샘플 오브젝트
- `relations` 시트: 10개 샘플 관계

### 3. 메타데이터 로딩
```bash
python load_mapping.py
```

이 명령어는 `mapping.xlsx` 파일을 읽어서 SQLite 데이터베이스(`impact_map.db`)에 데이터를 로딩합니다.

**예상 출력:**
```
INFO - 데이터베이스 초기화 중...
INFO - 엑셀 파일 읽기: mapping.xlsx
INFO - Objects 시트 로딩 중...
INFO - 생성: IF_APLAN_SALES_001
...
INFO - Objects 로딩 완료: 10개
INFO - Relations 시트 로딩 중...
INFO - 관계 생성: SAP_VBRP -> IF_APLAN_SALES_001
...
INFO - 데이터베이스 커밋 완료
```

---

## 서버 구동 방법

### 기본 실행
```bash
uvicorn app.main:app --reload
```

### 옵션 설명
- `--reload`: 코드 변경 시 자동 재시작 (개발 모드)
- `--host 0.0.0.0`: 모든 네트워크 인터페이스에서 접근 가능
- `--port 8000`: 포트 번호 지정 (기본값: 8000)

### 전체 명령어 예시
```bash
# 개발 모드 (자동 재시작)
uvicorn app.main:app --reload

# 프로덕션 모드 (특정 호스트/포트)
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 워커 프로세스 지정 (프로덕션)
uvicorn app.main:app --workers 4
```

### 서버 실행 확인
서버가 정상적으로 실행되면 다음과 같은 메시지가 표시됩니다:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx] using WatchFiles
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 접속 URL
- **웹 UI (검색 화면)**: http://localhost:8000/objects
- **API 문서 (Swagger UI)**: http://localhost:8000/docs
- **API 문서 (ReDoc)**: http://localhost:8000/redoc
- **루트 경로**: http://localhost:8000 (자동으로 `/objects`로 리다이렉트)

---

## 테스트 시나리오

### 시나리오 1: 웹 UI 검색 기능 테스트

#### 1-1. 기본 검색 화면 접근
1. 브라우저에서 http://localhost:8000/objects 접속
2. **예상 결과**:
   - "APlan Integration Impact Map" 헤더 표시
   - 검색 폼 표시 (키워드, system_type, object_type 드롭다운)
   - 오브젝트 리스트 테이블 표시

#### 1-2. 키워드 검색
1. 검색 폼의 "키워드" 입력란에 "매출" 입력
2. "검색" 버튼 클릭
3. **예상 결과**:
   - 매출 관련 오브젝트만 필터링되어 표시
   - 예: "IF_APLAN_SALES_001", "SAP_VBRP", "ZAP_SALES_STG" 등

#### 1-3. 시스템 타입 필터
1. "시스템 타입" 드롭다운에서 "SAP" 선택
2. "검색" 버튼 클릭
3. **예상 결과**:
   - system_type이 "SAP"인 오브젝트만 표시
   - 예: "SAP_VBRP", "SAP_MARA"

#### 1-4. 오브젝트 타입 필터
1. "오브젝트 타입" 드롭다운에서 "IF" 선택
2. "검색" 버튼 클릭
3. **예상 결과**:
   - object_type이 "IF"인 오브젝트만 표시
   - 예: "IF_APLAN_SALES_001", "IF_APLAN_INV_002"

#### 1-5. 복합 필터
1. 키워드: "매출", 시스템 타입: "APLAN", 오브젝트 타입: "IF" 선택
2. "검색" 버튼 클릭
3. **예상 결과**:
   - 모든 조건을 만족하는 오브젝트만 표시
   - 예: "IF_APLAN_SALES_001"

---

### 시나리오 2: 오브젝트 상세 화면 테스트

#### 2-1. 상세 화면 접근
1. 검색 결과 테이블에서 임의의 오브젝트 행 클릭
2. 또는 URL 직접 입력: http://localhost:8000/objects/{object_id}
3. **예상 결과**:
   - 좌측 패널: 오브젝트 기본 정보 표시
     - object_key, name, system_type, object_type, layer
     - module, owner_team, status, environment
     - tags, description
   - 우측 상단: 영향도 분석 섹션
     - Upstream 리스트 (상위 오브젝트)
     - Downstream 리스트 (하위 오브젝트)
   - 우측 하단: Mermaid 다이어그램 영역

#### 2-2. 영향도 정보 확인
1. 상세 화면에서 "영향도 분석" 섹션 확인
2. **예상 결과**:
   - Upstream 테이블에 이 오브젝트로 데이터를 전송하는 상위 오브젝트 표시
   - Downstream 테이블에 이 오브젝트에서 데이터를 받는 하위 오브젝트 표시
   - 각 항목 클릭 시 해당 오브젝트 상세 화면으로 이동

#### 2-3. Mermaid 다이어그램 확인
1. 상세 화면에서 "영향도 다이어그램" 섹션 확인
2. **예상 결과**:
   - Mermaid 코드가 textarea에 표시됨
   - "Copy Mermaid Code" 버튼 클릭 시 코드 복사
   - 실제 다이어그램이 렌더링되어 표시됨
   - 중심 오브젝트가 노란색으로 강조 표시됨

#### 2-4. 다이어그램 depth 변경
1. URL에 `?depth=1` 또는 `?depth=2` 파라미터 추가
2. 예: http://localhost:8000/objects/1?depth=2
3. **예상 결과**:
   - depth=1: 직접 연결된 오브젝트만 표시
   - depth=2: 한 단계 이웃까지 확장 표시

---

### 시나리오 3: 영향도 탐색 테스트

#### 3-1. Upstream 탐색
1. "IF_APLAN_SALES_001" 오브젝트 상세 화면 접근
2. Upstream 리스트에서 "SAP_VBRP" 클릭
3. **예상 결과**:
   - "SAP_VBRP" 오브젝트 상세 화면으로 이동
   - 이 오브젝트의 Downstream에 "IF_APLAN_SALES_001"이 표시됨

#### 3-2. Downstream 탐색
1. "IF_APLAN_SALES_001" 오브젝트 상세 화면 접근
2. Downstream 리스트에서 "ZAP_SALES_STG" 클릭
3. **예상 결과**:
   - "ZAP_SALES_STG" 오브젝트 상세 화면으로 이동
   - 이 오브젝트의 Upstream에 "IF_APLAN_SALES_001"이 표시됨

#### 3-3. 전체 영향도 체인 확인
1. "SAP_VBRP" → "IF_APLAN_SALES_001" → "ZAP_SALES_STG" → "BW_SOP_CUBE" 순서로 클릭
2. **예상 결과**:
   - 각 오브젝트의 상세 화면에서 연결 관계 확인 가능
   - Mermaid 다이어그램에서 전체 흐름 시각화 확인

---

### 시나리오 4: Mermaid 다이어그램 기능 테스트

#### 4-1. 다이어그램 코드 복사
1. 상세 화면에서 Mermaid 코드 textarea 확인
2. "Copy Mermaid Code" 버튼 클릭
3. **예상 결과**:
   - 버튼이 "Copied!"로 변경됨 (2초 후 원래대로 복귀)
   - 클립보드에 Mermaid 코드가 복사됨

#### 4-2. 다이어그램 렌더링 확인
1. 상세 화면에서 Mermaid 다이어그램 영역 확인
2. **예상 결과**:
   - flowchart LR 형식의 다이어그램이 렌더링됨
   - 노드: "시스템타입\n오브젝트명" 형식
   - 엣지: 화살표로 연결 관계 표시
   - 중심 오브젝트가 노란색으로 강조됨

#### 4-3. depth별 다이어그램 비교
1. 같은 오브젝트에 대해 `?depth=1`과 `?depth=2` 비교
2. **예상 결과**:
   - depth=1: 직접 연결된 오브젝트만 표시
   - depth=2: 더 많은 오브젝트와 관계가 표시됨

---

## API 엔드포인트 테스트

### API 문서 접근
1. 브라우저에서 http://localhost:8000/docs 접속
2. Swagger UI에서 모든 API 엔드포인트 확인 및 테스트 가능

### 주요 API 엔드포인트

#### 1. GET /objects/api
**설명**: 오브젝트 검색/리스트 조회 (JSON)

**쿼리 파라미터**:
- `q` (optional): 키워드 검색
- `system_type` (optional): 시스템 타입 필터
- `object_type` (optional): 오브젝트 타입 필터
- `limit` (optional, default: 50): 최대 결과 수

**테스트 예시**:
```bash
# 전체 조회
curl http://localhost:8000/objects/api

# 키워드 검색
curl "http://localhost:8000/objects/api?q=매출"

# 필터 조합
curl "http://localhost:8000/objects/api?system_type=SAP&object_type=TABLE"
```

**예상 응답**:
```json
[
  {
    "id": 1,
    "object_key": "IF_APLAN_SALES_001",
    "name": "APlan 매출 인터페이스",
    "system_type": "APLAN",
    "object_type": "IF",
    "layer": "In",
    "description": "SAP 매출실적을 APlan으로 전송하는 인터페이스",
    "status": "ACTIVE",
    "module": "판매"
  },
  ...
]
```

---

#### 2. GET /objects/{object_id}/api
**설명**: 단일 오브젝트 상세 조회 (JSON)

**테스트 예시**:
```bash
curl http://localhost:8000/objects/1/api
```

**예상 응답**:
```json
{
  "id": 1,
  "object_key": "IF_APLAN_SALES_001",
  "name": "APlan 매출 인터페이스",
  "system_type": "APLAN",
  "object_type": "IF",
  "layer": "In",
  "description": "SAP 매출실적을 APlan으로 전송하는 인터페이스",
  "owner_team": "ERP 플랫폼서비스팀",
  "module": "판매",
  "status": "ACTIVE",
  "tags": "수요계획,판매,SD",
  "environment": "PRD",
  ...
}
```

---

#### 3. GET /objects/{object_id}/impact
**설명**: 오브젝트 영향도 정보 조회

**쿼리 파라미터**:
- `depth` (optional, default: 1): 탐색 깊이 (1 또는 2)

**테스트 예시**:
```bash
# depth=1 (기본값)
curl http://localhost:8000/objects/1/impact

# depth=2
curl "http://localhost:8000/objects/1/impact?depth=2"
```

**예상 응답**:
```json
{
  "object": {
    "id": 1,
    "object_key": "IF_APLAN_SALES_001",
    "name": "APlan 매출 인터페이스",
    ...
  },
  "upstream": [
    {
      "id": 2,
      "object_key": "SAP_VBRP",
      "name": "SAP 매출전표",
      "system_type": "SAP",
      ...
    }
  ],
  "downstream": [
    {
      "id": 3,
      "object_key": "ZAP_SALES_STG",
      "name": "수요계획 매출 Staging",
      "system_type": "APLAN",
      ...
    }
  ]
}
```

---

#### 4. GET /objects/{object_id}/mermaid
**설명**: Mermaid 다이어그램 코드 생성

**쿼리 파라미터**:
- `depth` (optional, default: 2): 탐색 깊이 (1 또는 2)

**테스트 예시**:
```bash
curl "http://localhost:8000/objects/1/mermaid?depth=2"
```

**예상 응답**:
```json
{
  "mermaid_code": "flowchart LR\n  IF_APLAN_SALES_001[\"APLAN\\nAPlan 매출 인터페이스\"]:::center\n  SAP_VBRP[\"SAP\\nSAP 매출전표\"]\n  ZAP_SALES_STG[\"APLAN\\n수요계획 매출 Staging\"]\n  SAP_VBRP --> IF_APLAN_SALES_001\n  IF_APLAN_SALES_001 --> ZAP_SALES_STG\n\n  classDef center fill:#ffeb3b,stroke:#f57f17,stroke-width:3px"
}
```

---

## 자동화 테스트

### 단위 테스트 실행
```bash
# 1-4단계 테스트 (모델, DB, 로딩 스크립트)
python test_step1_4.py

# 5단계 테스트 (FastAPI 앱)
python test_step5.py

# 6단계 테스트 (영향도 분석 서비스)
python test_step6.py

# 7단계 테스트 (API 라우터)
python test_step7.py

# 8-9단계 테스트 (템플릿)
python test_step8_9.py

# 10단계 테스트 (전체 통합)
python test_step10.py
```

### 모든 테스트 한번에 실행
```bash
# Windows PowerShell
python test_step1_4.py; python test_step5.py; python test_step6.py; python test_step7.py; python test_step8_9.py; python test_step10.py

# Linux/Mac
python test_step1_4.py && python test_step5.py && python test_step6.py && python test_step7.py && python test_step8_9.py && python test_step10.py
```

---

## 문제 해결

### 문제 1: 모듈을 찾을 수 없음
**에러**: `ModuleNotFoundError: No module named 'xxx'`

**해결 방법**:
```bash
pip install -r requirements.txt
```

### 문제 2: 데이터베이스 파일이 잠겨있음
**에러**: `PermissionError: [WinError 32] 다른 프로세스가 파일을 사용 중`

**해결 방법**:
1. 서버를 종료 (Ctrl+C)
2. `impact_map.db` 파일이 다른 프로세스에서 사용 중인지 확인
3. 필요시 파일 삭제 후 `load_mapping.py` 재실행

### 문제 3: 포트가 이미 사용 중
**에러**: `Address already in use`

**해결 방법**:
```bash
# 다른 포트 사용
uvicorn app.main:app --reload --port 8001

# 또는 기존 프로세스 종료
# Windows: netstat -ano | findstr :8000
# Linux/Mac: lsof -i :8000
```

### 문제 4: 엑셀 파일을 찾을 수 없음
**에러**: `엑셀 파일을 찾을 수 없습니다: mapping.xlsx`

**해결 방법**:
```bash
# 샘플 데이터 생성
python create_sample_mapping.py
```

### 문제 5: Mermaid 다이어그램이 렌더링되지 않음
**원인**: 인터넷 연결 문제 (CDN 사용)

**해결 방법**:
1. 인터넷 연결 확인
2. 브라우저 콘솔에서 에러 확인 (F12)
3. 추후 로컬 호스팅으로 전환 가능 (MRD 참고)

---

## 성능 테스트

### 데이터 규모
- 초기 데이터: 100~200개 오브젝트, 200~500개 관계 가정
- 현재 샘플: 10개 오브젝트, 10개 관계

### 예상 응답 시간
- `/objects`: 즉시 응답 (< 100ms)
- `/objects/{id}`: 즉시 응답 (< 100ms)
- `/objects/{id}/impact`: 즉시 응답 (< 200ms)
- `/objects/{id}/mermaid`: 즉시 응답 (< 200ms)

---

## 추가 테스트 시나리오

### 엣지 케이스 테스트

#### 1. 존재하지 않는 오브젝트 ID 접근
```
GET /objects/99999
```
**예상 결과**: 404 에러

#### 2. 빈 검색 결과
```
GET /objects?q=존재하지않는키워드
```
**예상 결과**: "검색 결과가 없습니다" 메시지 표시

#### 3. 관계가 없는 오브젝트
- Upstream/Downstream이 없는 오브젝트의 상세 화면 확인
- **예상 결과**: "Upstream 오브젝트가 없습니다", "Downstream 오브젝트가 없습니다" 메시지 표시

---

## 테스트 체크리스트

### 기능 테스트
- [ ] 검색 화면 접근 및 렌더링
- [ ] 키워드 검색 기능
- [ ] 시스템 타입 필터
- [ ] 오브젝트 타입 필터
- [ ] 복합 필터 조합
- [ ] 상세 화면 접근 및 렌더링
- [ ] 기본 정보 표시
- [ ] Upstream 리스트 표시
- [ ] Downstream 리스트 표시
- [ ] Mermaid 다이어그램 렌더링
- [ ] Mermaid 코드 복사 기능
- [ ] depth 파라미터 동작 (1, 2)
- [ ] 오브젝트 간 네비게이션 (클릭 이동)

### API 테스트
- [ ] GET /objects/api
- [ ] GET /objects/{id}/api
- [ ] GET /objects/{id}/impact
- [ ] GET /objects/{id}/mermaid
- [ ] 404 에러 처리
- [ ] 쿼리 파라미터 검증

### 통합 테스트
- [ ] 데이터 로딩 (load_mapping.py)
- [ ] 서버 시작 및 종료
- [ ] 전체 워크플로우 (검색 → 상세 → 영향도 확인)

---

## 참고 자료

- **MRD 문서**: `MRD.md` - 전체 요구사항
- **개발 가이드**: `step.md` - 단계별 개발 계획
- **API 문서**: http://localhost:8000/docs (서버 실행 후)

---

**마지막 업데이트**: 2025-12-04

