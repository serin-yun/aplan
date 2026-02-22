# mapping.xlsx 파일 작성 완전 가이드

> **이 가이드는 mapping.xlsx 파일을 처음부터 끝까지 작성하는 방법을 단계별로 안내합니다.**

---

## 📋 목차

1. [빠른 시작](#빠른-시작)
2. [object_key 채번 규칙](#object_key-채번-규칙)
3. [파일 구조 이해하기](#파일-구조-이해하기)
4. [단계별 작성 가이드](#단계별-작성-가이드)
5. [실무 작성 예시](#실무-작성-예시)
6. [검증 및 업로드](#검증-및-업로드)
7. [문제 해결](#문제-해결)

---

## 빠른 시작

### 가장 쉬운 방법 (3단계)

```powershell
# 1단계: 템플릿 생성
python create_template.py

# 2단계: 생성된 mapping_template.xlsx 파일 열어서 데이터 입력

# 3단계: 데이터 로딩
python load_mapping.py
```

**또는 샘플 파일로 시작:**

```powershell
# 샘플 파일 생성 (예시 데이터 포함)
python create_sample_mapping.py

# 데이터 로딩
python load_mapping.py
```

---

## object_key 채번 규칙

### 🎯 핵심 원칙

1. **유일성**: 전체 시스템에서 유일해야 함
2. **가독성**: 의미를 바로 알 수 있어야 함
3. **일관성**: 같은 패턴을 유지해야 함
4. **형식**: 대문자, 언더스코어(`_`)로 구분

### 📝 채번 패턴 (5가지)

#### 패턴 1: 인터페이스/커스텀 오브젝트
```
IF_APLAN_SALES_001
IF_APLAN_INV_002
TABLE_APLAN_STG_001
```
**형식**: `{오브젝트타입}_{시스템}_{업무도메인}_{순번}`

**언제 사용?**
- APlan, BI, EAI 등 커스텀 시스템의 인터페이스/테이블
- 새로 생성하는 오브젝트

---

#### 패턴 2: SAP 표준 테이블
```
SAP_VBRP
SAP_MARA
SAP_MKPF
```
**형식**: `{시스템}_{SAP테이블명}`

**언제 사용?**
- SAP 표준 테이블/뷰
- 기존 시스템의 표준 오브젝트

---

#### 패턴 3: 커스텀 개발 (Z로 시작)
```
ZAP_SALES_STG
ZAP_INV_STG
ZSAP_SD_CUST_001
```
**형식**: `Z{시스템}_{업무도메인}_{타입}_{순번}`

**언제 사용?**
- 커스텀 개발된 테이블/인터페이스
- Z로 시작하는 커스텀 오브젝트

---

#### 패턴 4: BW/BI 큐브/리포트
```
BW_SOP_CUBE
BI_SALES_REPORT
BW_INV_DSO
```
**형식**: `{시스템}_{업무도메인}_{타입}`

**언제 사용?**
- BW 큐브, DSO, InfoObject
- BI 리포트, 대시보드

---

#### 패턴 5: EAI 연계
```
EAI_SAP_TO_APLAN
EAI_APLAN_TO_BI
```
**형식**: `EAI_{시스템1}_TO_{시스템2}`

**언제 사용?**
- 시스템 간 데이터 연계
- EAI/ESB를 통한 인터페이스

---

### 🔍 object_key 결정 프로세스

```
오브젝트를 식별했나요?
    ↓
SAP 표준 테이블/뷰인가?
    ├─ 예 → SAP_{테이블명} (예: SAP_VBRP)
    └─ 아니오 ↓
커스텀 개발 오브젝트인가? (Z로 시작)
    ├─ 예 → Z{시스템}_{도메인}_{타입}_{순번} (예: ZAP_SALES_STG)
    └─ 아니오 ↓
인터페이스인가?
    ├─ 예 → IF_{시스템}_{도메인}_{순번} (예: IF_APLAN_SALES_001)
    └─ 아니오 ↓
BW/BI 오브젝트인가?
    ├─ 예 → {시스템}_{도메인}_{타입} (예: BW_SOP_CUBE)
    └─ 아니오 ↓
EAI 연계인가?
    └─ 예 → EAI_{시스템1}_TO_{시스템2} (예: EAI_SAP_TO_APLAN)
```

---

### 📊 시스템별 채번 예시

| 시스템 | object_key 예시 | 설명 |
|--------|----------------|------|
| **APlan** | `IF_APLAN_SALES_001` | APlan 매출 인터페이스 |
| | `ZAP_SALES_STG` | APlan 판매 Staging 테이블 |
| **SAP** | `SAP_VBRP` | SAP 매출전표 테이블 |
| | `SAP_MARA` | SAP 자재마스터 테이블 |
| **BW/BI** | `BW_SOP_CUBE` | BW S&OP 큐브 |
| | `BI_SALES_REPORT` | BI 매출 리포트 |
| **EAI** | `EAI_SAP_TO_APLAN` | SAP → APlan 연계 |

---

## 파일 구조 이해하기

### 📁 파일 개요

- **파일명**: `mapping.xlsx` (반드시 이 이름)
- **형식**: Microsoft Excel (.xlsx)
- **시트**: 2개 필요 (`objects`, `relations`)

### 📊 시트 구조

#### 시트 1: `objects` (오브젝트 정보)
- 각 오브젝트(인터페이스, 테이블, 리포트 등)의 정보를 담는 시트
- **15개 컬럼** (필수 5개 + 선택 10개)

#### 시트 2: `relations` (관계 정보)
- 오브젝트 간 데이터 흐름 관계를 정의하는 시트
- **8개 컬럼** (필수 2개 + 선택 6개)

---

## 단계별 작성 가이드

### 1단계: 파일 준비

#### 방법 A: 템플릿 사용 (권장)
```powershell
python create_template.py
```
→ `mapping_template.xlsx` 파일이 생성됩니다. 이 파일을 열어서 사용하세요.

#### 방법 B: Excel에서 직접 생성
1. Excel 실행 → 새 통합 문서
2. 첫 번째 시트 이름을 `objects`로 변경
3. 새 시트 추가 → 이름을 `relations`로 변경
4. `mapping.xlsx`로 저장

---

### 2단계: 헤더 입력

#### `objects` 시트 (1행에 입력)

| A | B | C | D | E | F | G | H | I | J | K | L | M | N | O |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| object_key | name | system_type | object_type | layer | description | owner_team | **owner** | module | status | tags | environment | source_doc | source_sheet | source_row |

**복사용 텍스트:**
```
object_key	name	system_type	object_type	layer	description	owner_team	owner	module	status	tags	environment	source_doc	source_sheet	source_row
```

#### `relations` 시트 (1행에 입력)

| A | B | C | D | E | F | G | H |
|---|---|---|---|---|---|---|---|
| from_key | to_key | relation_type | description | status | source_doc | source_sheet | source_row |

**복사용 텍스트:**
```
from_key	to_key	relation_type	description	status	source_doc	source_sheet	source_row
```

---

### 3단계: objects 시트 데이터 입력 (2행부터)

#### 필수 필드 (5개) - 반드시 입력

| 컬럼 | 설명 | 허용 값 | 예시 |
|------|------|---------|------|
| **object_key** | 업무상 유일키 | 위 채번 규칙 참고 | `IF_APLAN_SALES_001` |
| **name** | 표시 이름 | 한글/영문 | `APlan 매출 인터페이스` |
| **system_type** | 시스템 타입 | `SAP`, `APLAN`, `BW`, `BI`, `EAI`, `IAM`, `NPD`, `CDP`, `LEGACY` | `APLAN` |
| **object_type** | 오브젝트 타입 | `IF`, `TABLE`, `VIEW`, `JOB`, `REPORT`, `UI` | `IF` |
| **layer** | 레이어 | `Legacy`, `API`, `Cust`, `In`, `Staging`, `Out`, `UI` | `In` |

#### 선택 필드 (10개) - 필요시 입력

| 컬럼 | 설명 | 예시 | 기본값 |
|------|------|------|--------|
| description | 설명 | `SAP 매출실적을 APlan으로 전송하는 인터페이스` | 빈 값 |
| owner_team | 담당 조직/팀 | `ERP 플랫폼서비스팀` | 빈 값 |
| **owner** | 담당자 이름 | `홍길동` | 빈 값 |
| module | 업무 도메인 | `판매`, `재고`, `S&OP` | 빈 값 |
| status | 상태 | `ACTIVE`, `DRAFT`, `DEPRECATED` | `ACTIVE` |
| tags | 태그 (콤마 구분) | `수요계획,판매,SD` | 빈 값 |
| environment | 환경 | `PRD`, `QAS`, `DEV` | `PRD` |
| source_doc | 소스 문서명 | 자동 입력됨 | 파일명 |
| source_sheet | 소스 시트명 | 자동 입력됨 | `objects` |
| source_row | 소스 행 번호 | 자동 계산됨 | 행 번호 |

**💡 작성 팁:**
- `description`: 무엇을 하는 오브젝트인지 명확히 작성
- `owner`: 실제 담당자 이름 (여러 명은 콤마로 구분)
- `tags`: 검색에 유용한 키워드 포함

---

### 4단계: relations 시트 데이터 입력 (2행부터)

#### 필수 필드 (2개)

| 컬럼 | 설명 | 예시 |
|------|------|------|
| **from_key** | 출발 오브젝트의 object_key | `SAP_VBRP` |
| **to_key** | 도착 오브젝트의 object_key | `IF_APLAN_SALES_001` |

**⚠️ 중요:**
- `from_key`와 `to_key`는 반드시 `objects` 시트에 존재하는 `object_key` 값이어야 합니다
- 데이터 흐름 방향: `from_key` → `to_key` (출발 → 도착)

#### 선택 필드 (6개)

| 컬럼 | 설명 | 예시 | 기본값 |
|------|------|------|--------|
| relation_type | 관계 타입 | `FLOWS_TO` | `FLOWS_TO` |
| description | 관계 설명 | `SAP 매출전표 → APlan 매출 인터페이스` | 빈 값 |
| status | 상태 | `ACTIVE`, `DRAFT`, `DEPRECATED` | `ACTIVE` |
| source_doc | 소스 문서명 | 자동 입력됨 | 파일명 |
| source_sheet | 소스 시트명 | 자동 입력됨 | `relations` |
| source_row | 소스 행 번호 | 자동 계산됨 | 행 번호 |

---

## 실무 작성 예시

### 📝 예시 1: SAP 매출 데이터를 APlan으로 전송하는 인터페이스

#### Step 1: 오브젝트 식별

1. **SAP 매출전표 테이블** (SAP 표준)
   - object_key: `SAP_VBRP` (패턴 2)
   - system_type: `SAP`
   - object_type: `TABLE`
   - layer: `Legacy`

2. **APlan 매출 인터페이스** (새로 만드는 인터페이스)
   - object_key: `IF_APLAN_SALES_001` (패턴 1)
   - system_type: `APLAN`
   - object_type: `IF`
   - layer: `In`

3. **APlan 매출 Staging 테이블** (커스텀 개발)
   - object_key: `ZAP_SALES_STG` (패턴 3)
   - system_type: `APLAN`
   - object_type: `TABLE`
   - layer: `Staging`

#### Step 2: objects 시트 작성

| object_key | name | system_type | object_type | layer | description | owner_team | owner | module | status | tags | environment |
|------------|------|-------------|-------------|-------|-------------|------------|-------|--------|--------|------|-------------|
| SAP_VBRP | SAP 매출전표 | SAP | TABLE | Legacy | SAP SD 모듈의 매출전표 테이블 | SAP 운영팀 | 김철수 | 판매 | ACTIVE | SAP,SD,매출 | PRD |
| IF_APLAN_SALES_001 | APlan 매출 인터페이스 | APLAN | IF | In | SAP 매출실적을 APlan으로 전송하는 인터페이스 | ERP 플랫폼서비스팀 | 홍길동 | 판매 | ACTIVE | 수요계획,판매,인터페이스 | PRD |
| ZAP_SALES_STG | 수요계획 매출 Staging | APLAN | TABLE | Staging | 매출 데이터 Staging 테이블 | ERP 플랫폼서비스팀 | 이영희 | 판매 | ACTIVE | 수요계획,Staging,매출 | PRD |

#### Step 3: relations 시트 작성

| from_key | to_key | relation_type | description | status |
|----------|--------|---------------|-------------|--------|
| SAP_VBRP | IF_APLAN_SALES_001 | FLOWS_TO | SAP 매출전표 → APlan 매출 인터페이스 | ACTIVE |
| IF_APLAN_SALES_001 | ZAP_SALES_STG | FLOWS_TO | APlan 매출 인터페이스 → 수요계획 Staging 적재 | ACTIVE |

**데이터 흐름:**
```
SAP_VBRP → IF_APLAN_SALES_001 → ZAP_SALES_STG
```

---

### 📝 예시 2: 재고 관리 시스템 연계

#### objects 시트

| object_key | name | system_type | object_type | layer | description | owner_team | owner | module | status |
|------------|------|-------------|-------------|-------|-------------|------------|-------|--------|--------|
| SAP_MARA | SAP 자재마스터 | SAP | TABLE | Legacy | SAP MM 모듈의 자재마스터 테이블 | SAP 운영팀 | 박민수 | 재고 | ACTIVE |
| IF_APLAN_INV_002 | APlan 재고 인터페이스 | APLAN | IF | In | SAP 재고 정보를 APlan으로 전송 | ERP 플랫폼서비스팀 | 정수진 | 재고 | ACTIVE |
| ZAP_INV_STG | 재고 Staging | APLAN | TABLE | Staging | 재고 관리 시스템의 Staging 테이블 | SCI 실 | 최영호 | 재고 | ACTIVE |

#### relations 시트

| from_key | to_key | relation_type | description | status |
|----------|--------|---------------|-------------|--------|
| SAP_MARA | IF_APLAN_INV_002 | FLOWS_TO | SAP 자재마스터 → APlan 재고 인터페이스 | ACTIVE |
| IF_APLAN_INV_002 | ZAP_INV_STG | FLOWS_TO | APlan 재고 인터페이스 → Staging 적재 | ACTIVE |

---

## 검증 및 업로드

### ✅ 작성 전 체크리스트

#### objects 시트
- [ ] 파일명이 `mapping.xlsx`인가?
- [ ] 시트 이름이 정확히 `objects`인가? (대소문자 구분)
- [ ] 헤더가 1행에 있는가?
- [ ] 컬럼 순서가 올바른가? (15개 컬럼)
- [ ] 필수 컬럼 5개가 모두 있는가?
- [ ] `object_key` 값이 중복되지 않는가?
- [ ] `object_key`가 대문자로 작성되었는가?
- [ ] `system_type`, `object_type`, `layer` 값이 허용된 값인가?

#### relations 시트
- [ ] 시트 이름이 정확히 `relations`인가?
- [ ] 헤더가 1행에 있는가?
- [ ] 필수 컬럼 2개(`from_key`, `to_key`)가 있는가?
- [ ] `from_key`와 `to_key`가 `objects` 시트에 존재하는가?
- [ ] 데이터 흐름 방향이 올바른가? (from → to)

---

### 🚀 파일 업로드 및 로딩

#### 1단계: 파일 배치
`mapping.xlsx` 파일을 프로젝트 루트 디렉토리에 배치:
```
C:\Cursor\aplan\mapping.xlsx
```

#### 2단계: 데이터 로딩
```powershell
cd C:\Cursor\aplan
python load_mapping.py
```

#### 3단계: 로딩 결과 확인

**정상 로딩 시:**
```
INFO - 데이터베이스 초기화 중...
INFO - 엑셀 파일 읽기: mapping.xlsx
INFO - Objects 시트 로딩 중...
INFO - 생성: IF_APLAN_SALES_001
INFO - 생성: SAP_VBRP
...
INFO - Objects 로딩 완료: 10개
INFO - Relations 시트 로딩 중...
INFO - 관계 생성: SAP_VBRP -> IF_APLAN_SALES_001
...
INFO - 데이터베이스 커밋 완료
```

**오류 발생 시:** 아래 "문제 해결" 섹션 참고

---

## 문제 해결

### ❌ 오류 1: "필수 컬럼이 없습니다"

**원인:**
- 컬럼명 오타
- 컬럼 순서 오류
- 헤더 행 위치 오류

**해결:**
1. 헤더가 1행에 있는지 확인
2. 컬럼명이 정확한지 확인 (대소문자 구분)
3. 컬럼 순서 확인 (위 가이드 참고)

---

### ❌ 오류 2: "from_key 'XXX'에 해당하는 오브젝트를 찾을 수 없습니다"

**원인:**
- `relations` 시트의 `from_key` 값이 `objects` 시트에 없음
- 오타 또는 대소문자 불일치

**해결:**
1. `objects` 시트에서 해당 `object_key`가 존재하는지 확인
2. 대소문자, 공백, 특수문자 확인
3. Excel에서 정확히 복사/붙여넣기

---

### ❌ 오류 3: "to_key 'XXX'에 해당하는 오브젝트를 찾을 수 없습니다"

**원인:**
- `relations` 시트의 `to_key` 값이 `objects` 시트에 없음

**해결:**
- 위와 동일

---

### ❌ 오류 4: object_key 중복

**원인:**
- 같은 `object_key`가 여러 번 사용됨

**해결:**
1. Excel에서 중복 검색 (Ctrl+F)
2. 각 오브젝트에 고유한 `object_key` 부여
3. 순번을 다르게 사용 (예: `001`, `002`, `003`)

---

### ⚠️ 자주 하는 실수

| 문제점 | 잘못된 예시 | 올바른 예시 |
|--------|------------|------------|
| 소문자 사용 | `if_aplan_sales_001` | `IF_APLAN_SALES_001` |
| 공백 사용 | `IF APLAN SALES 001` | `IF_APLAN_SALES_001` |
| 하이픈 사용 | `IF-APLAN-SALES-001` | `IF_APLAN_SALES_001` |
| 순번 누락 | `IF_APLAN_SALES` | `IF_APLAN_SALES_001` |
| 중복 | `IF_APLAN_SALES_001` (2개) | 각각 다른 순번 사용 |
| 관계 오류 | `UNKNOWN_TABLE` → `IF_APLAN_001` | objects에 존재하는 key 사용 |

---

## 💡 유용한 팁

1. **템플릿 사용**: `python create_template.py`로 템플릿 생성 후 작성
2. **순번 관리**: 같은 도메인의 오브젝트는 순번을 연속으로 부여
3. **명명 규칙 문서화**: 팀 내부에서 채번 규칙을 문서화하여 공유
4. **검증**: `python load_mapping.py` 실행 전 Excel에서 중복 확인
5. **백업**: 중요한 데이터는 백업 후 작업
6. **단계별 작성**: objects 시트 먼저 완성 후 relations 시트 작성

---

## 📚 빠른 참조

### 허용 값 요약

**system_type**: `SAP`, `APLAN`, `BW`, `BI`, `EAI`, `IAM`, `NPD`, `CDP`, `LEGACY`

**object_type**: `IF`, `TABLE`, `VIEW`, `JOB`, `REPORT`, `UI`

**layer**: `Legacy`, `API`, `Cust`, `In`, `Staging`, `Out`, `UI`

**status**: `ACTIVE`, `DRAFT`, `DEPRECATED`

**environment**: `PRD`, `QAS`, `DEV`

**relation_type**: `FLOWS_TO` (현재는 이것만 사용)

---

## 🎯 요약

### 작성 순서
1. ✅ 템플릿 생성 또는 Excel에서 파일 생성
2. ✅ 헤더 입력 (1행)
3. ✅ objects 시트 작성 (2행부터)
   - object_key 채번 규칙에 따라 작성
   - 필수 필드 5개 입력
   - 선택 필드 필요시 입력
4. ✅ relations 시트 작성 (2행부터)
   - from_key/to_key는 objects 시트의 object_key 사용
5. ✅ 검증 체크리스트 확인
6. ✅ 파일 저장 (`mapping.xlsx`)
7. ✅ 데이터 로딩 (`python load_mapping.py`)

### 핵심 포인트
- **object_key**: 유일성, 대문자, 언더스코어 구분
- **컬럼 순서**: 반드시 가이드 순서대로
- **관계**: from_key/to_key는 objects에 존재해야 함
- **검증**: 로딩 전 중복 및 오타 확인

---

**이제 mapping.xlsx 파일을 작성할 준비가 되었습니다!** 🎉







