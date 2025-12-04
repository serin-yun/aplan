# 빠른 테스트 가이드

## 🚀 서버 실행

```bash
# 1. 데이터 로딩 (처음 한 번만)
python load_mapping.py

# 2. 서버 실행
uvicorn app.main:app --reload
```

---

## 📍 접속 URL

### 웹 UI
- **검색 화면**: http://localhost:8000/objects
- **API 문서 (Swagger)**: http://localhost:8000/docs
- **API 문서 (ReDoc)**: http://localhost:8000/redoc

---

## 🧪 테스트 시나리오

### 시나리오 1: 기본 검색 및 필터링

#### 1-1. 전체 오브젝트 조회
**URL**: http://localhost:8000/objects

**테스트 방법**:
1. 브라우저에서 위 URL 접속
2. 검색 버튼을 누르지 않고 페이지 로드 확인

**예상 결과**:
- 모든 오브젝트가 테이블에 표시됨
- 컬럼: object_key, name, system_type, object_type, layer, module, status

---

#### 1-2. 키워드 검색
**URL**: http://localhost:8000/objects?q=매출

**테스트 방법**:
1. 검색 화면에서 "키워드" 입력란에 "매출" 입력
2. "검색" 버튼 클릭
3. 또는 위 URL 직접 접속

**예상 결과**:
- "매출"이 포함된 오브젝트만 필터링됨
- 예: "IF_APLAN_SALES_001", "SAP_VBRP", "ZAP_SALES_STG" 등

---

#### 1-3. 시스템 타입 필터
**URL**: http://localhost:8000/objects?system_type=SAP

**테스트 방법**:
1. "시스템 타입" 드롭다운에서 "SAP" 선택
2. "검색" 버튼 클릭
3. 또는 위 URL 직접 접속

**예상 결과**:
- system_type이 "SAP"인 오브젝트만 표시
- 예: "SAP_VBRP", "SAP_MARA"

---

#### 1-4. 오브젝트 타입 필터
**URL**: http://localhost:8000/objects?object_type=IF

**테스트 방법**:
1. "오브젝트 타입" 드롭다운에서 "IF" 선택
2. "검색" 버튼 클릭
3. 또는 위 URL 직접 접속

**예상 결과**:
- object_type이 "IF"인 오브젝트만 표시
- 예: "IF_APLAN_SALES_001", "IF_APLAN_INV_002", "IF_APLAN_PROD_003"

---

#### 1-5. 복합 필터
**URL**: http://localhost:8000/objects?q=매출&system_type=APLAN&object_type=IF

**테스트 방법**:
1. 키워드: "매출", 시스템 타입: "APLAN", 오브젝트 타입: "IF" 모두 선택
2. "검색" 버튼 클릭
3. 또는 위 URL 직접 접속

**예상 결과**:
- 모든 조건을 만족하는 오브젝트만 표시
- 예: "IF_APLAN_SALES_001" (매출 + APLAN + IF)

---

### 시나리오 2: 오브젝트 상세 화면

#### 2-1. 상세 화면 접근
**URL**: http://localhost:8000/objects/1

**테스트 방법**:
1. 검색 결과 테이블에서 임의의 오브젝트 행 클릭
2. 또는 위 URL 직접 접속 (1은 오브젝트 ID)

**예상 결과**:
- **좌측 패널**: 오브젝트 기본 정보
  - object_key, name, system_type, object_type, layer
  - module, owner_team, status, environment
  - tags, description
- **우측 상단**: 영향도 분석
  - Upstream 리스트 (상위 오브젝트)
  - Downstream 리스트 (하위 오브젝트)
- **우측 하단**: Mermaid 다이어그램

---

#### 2-2. 영향도 정보 확인
**URL**: http://localhost:8000/objects/1

**테스트 방법**:
1. 상세 화면에서 "영향도 분석" 섹션 확인
2. Upstream과 Downstream 테이블 확인

**예상 결과**:
- **Upstream**: 이 오브젝트로 데이터를 전송하는 상위 오브젝트
  - 예: "IF_APLAN_SALES_001"의 Upstream → "SAP_VBRP"
- **Downstream**: 이 오브젝트에서 데이터를 받는 하위 오브젝트
  - 예: "IF_APLAN_SALES_001"의 Downstream → "ZAP_SALES_STG"

---

#### 2-3. Mermaid 다이어그램 확인
**URL**: http://localhost:8000/objects/1?depth=2

**테스트 방법**:
1. 상세 화면에서 "영향도 다이어그램" 섹션 확인
2. Mermaid 코드 textarea 확인
3. "Copy Mermaid Code" 버튼 클릭 테스트
4. 실제 다이어그램 렌더링 확인

**예상 결과**:
- Mermaid 코드가 textarea에 표시됨
- 버튼 클릭 시 코드가 클립보드에 복사됨
- 다이어그램이 시각적으로 렌더링됨
- 중심 오브젝트가 노란색으로 강조됨

---

#### 2-4. Depth 파라미터 테스트
**URL (depth=1)**: http://localhost:8000/objects/1?depth=1
**URL (depth=2)**: http://localhost:8000/objects/1?depth=2

**테스트 방법**:
1. 같은 오브젝트에 대해 depth=1과 depth=2 비교
2. URL 파라미터로 직접 변경

**예상 결과**:
- **depth=1**: 직접 연결된 오브젝트만 표시 (1단계)
- **depth=2**: 한 단계 이웃까지 확장 표시 (2단계, 더 많은 관계)

---

### 시나리오 3: 영향도 탐색 (네비게이션)

#### 3-1. Upstream 탐색
**테스트 방법**:
1. "IF_APLAN_SALES_001" 오브젝트 상세 화면 접속
   - URL: http://localhost:8000/objects/1 (ID는 실제 값으로 변경)
2. Upstream 리스트에서 "SAP_VBRP" 클릭

**예상 결과**:
- "SAP_VBRP" 오브젝트 상세 화면으로 이동
- 이 오브젝트의 Downstream에 "IF_APLAN_SALES_001"이 표시됨

---

#### 3-2. Downstream 탐색
**테스트 방법**:
1. "IF_APLAN_SALES_001" 오브젝트 상세 화면 접속
2. Downstream 리스트에서 "ZAP_SALES_STG" 클릭

**예상 결과**:
- "ZAP_SALES_STG" 오브젝트 상세 화면으로 이동
- 이 오브젝트의 Upstream에 "IF_APLAN_SALES_001"이 표시됨

---

#### 3-3. 전체 영향도 체인 확인
**테스트 방법**:
1. 다음 순서로 오브젝트들을 클릭하며 이동:
   - "SAP_VBRP" → "IF_APLAN_SALES_001" → "ZAP_SALES_STG" → "BW_SOP_CUBE"
2. 각 오브젝트의 상세 화면에서 연결 관계 확인

**예상 결과**:
- 각 오브젝트의 상세 화면에서 연결 관계 확인 가능
- Mermaid 다이어그램에서 전체 데이터 흐름 시각화 확인
- 데이터가 SAP → APlan → Staging → BW로 흐르는 구조 확인

---

## 🔌 API 엔드포인트 테스트

### API 문서에서 테스트
**URL**: http://localhost:8000/docs

**테스트 방법**:
1. 브라우저에서 위 URL 접속
2. 각 API 엔드포인트를 클릭하여 "Try it out" 버튼 클릭
3. 파라미터 입력 후 "Execute" 버튼 클릭
4. 응답 확인

---

### 주요 API 엔드포인트

#### 1. GET /objects/api
**URL**: http://localhost:8000/objects/api

**쿼리 파라미터 예시**:
- 전체: http://localhost:8000/objects/api
- 키워드: http://localhost:8000/objects/api?q=매출
- 필터: http://localhost:8000/objects/api?system_type=SAP&object_type=TABLE

**예상 응답**: JSON 배열 형태
```json
[
  {
    "id": 1,
    "object_key": "IF_APLAN_SALES_001",
    "name": "APlan 매출 인터페이스",
    "system_type": "APLAN",
    "object_type": "IF",
    "layer": "In",
    "status": "ACTIVE"
  }
]
```

---

#### 2. GET /objects/{object_id}/api
**URL**: http://localhost:8000/objects/1/api

**예상 응답**: JSON 객체 형태 (전체 필드 포함)

---

#### 3. GET /objects/{object_id}/impact
**URL**: http://localhost:8000/objects/1/impact?depth=2

**쿼리 파라미터**:
- `depth`: 1 또는 2 (기본값: 1)

**예상 응답**:
```json
{
  "object": { ... },
  "upstream": [ ... ],
  "downstream": [ ... ]
}
```

---

#### 4. GET /objects/{object_id}/mermaid
**URL**: http://localhost:8000/objects/1/mermaid?depth=2

**쿼리 파라미터**:
- `depth`: 1 또는 2 (기본값: 2)

**예상 응답**:
```json
{
  "mermaid_code": "flowchart LR\n  ..."
}
```

---

## 📋 빠른 테스트 체크리스트

### 기본 기능
- [ ] 검색 화면 접속 (http://localhost:8000/objects)
- [ ] 키워드 검색 동작 확인
- [ ] 시스템 타입 필터 동작 확인
- [ ] 오브젝트 타입 필터 동작 확인
- [ ] 복합 필터 동작 확인

### 상세 화면
- [ ] 오브젝트 상세 화면 접속
- [ ] 기본 정보 표시 확인
- [ ] Upstream 리스트 표시 확인
- [ ] Downstream 리스트 표시 확인
- [ ] Mermaid 다이어그램 렌더링 확인
- [ ] Mermaid 코드 복사 기능 확인

### 네비게이션
- [ ] Upstream 오브젝트 클릭 이동 확인
- [ ] Downstream 오브젝트 클릭 이동 확인
- [ ] 전체 영향도 체인 탐색 확인

### API
- [ ] GET /objects/api 동작 확인
- [ ] GET /objects/{id}/api 동작 확인
- [ ] GET /objects/{id}/impact 동작 확인
- [ ] GET /objects/{id}/mermaid 동작 확인

---

## 🎯 추천 테스트 순서

1. **기본 검색 테스트** (5분)
   - 전체 조회 → 키워드 검색 → 필터 테스트

2. **상세 화면 테스트** (5분)
   - 상세 화면 접속 → 영향도 정보 확인 → 다이어그램 확인

3. **영향도 탐색 테스트** (5분)
   - Upstream/Downstream 클릭 → 전체 체인 탐색

4. **API 테스트** (5분)
   - API 문서에서 각 엔드포인트 테스트

**총 소요 시간**: 약 20분

---

## 💡 테스트 팁

1. **오브젝트 ID 확인**: 검색 화면에서 오브젝트를 클릭하면 URL에 ID가 표시됩니다.
2. **브라우저 개발자 도구**: F12를 눌러 콘솔에서 에러 확인 가능
3. **API 문서 활용**: http://localhost:8000/docs 에서 모든 API를 직접 테스트 가능
4. **샘플 데이터**: `create_sample_mapping.py`로 생성된 10개 오브젝트, 10개 관계로 테스트 가능

---

**문제 발생 시**: `test.md` 파일의 "문제 해결" 섹션 참고

