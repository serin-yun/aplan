# mapping.xlsx 파일 양식 가이드

## 📋 파일 개요

- **파일명**: `mapping.xlsx` (반드시 이 이름으로 저장)
- **파일 형식**: Microsoft Excel (.xlsx)
- **필수 시트**: `objects`, `relations` (두 개의 시트 필요)

---

## 📊 시트 1: `objects` (오브젝트 정보)

### 컬럼 구조 (왼쪽부터 순서대로)

| 순번 | 컬럼명 | 필수여부 | 설명 | 예시 값 | 기본값 |
|------|--------|---------|------|---------|--------|
| 1 | `object_key` | ✅ **필수** | 업무상 유일키 | `IF_APLAN_SALES_001` | - |
| 2 | `name` | ✅ **필수** | 표시 이름 (한글/영문) | `APlan 매출 인터페이스` | - |
| 3 | `system_type` | ✅ **필수** | 시스템 타입 | `SAP`, `APLAN`, `BW`, `BI`, `EAI`, `IAM`, `NPD`, `CDP`, `LEGACY` | - |
| 4 | `object_type` | ✅ **필수** | 오브젝트 타입 | `IF`, `TABLE`, `VIEW`, `JOB`, `REPORT`, `UI` | - |
| 5 | `layer` | ✅ **필수** | 레이어 | `Legacy`, `API`, `Cust`, `In`, `Staging`, `Out`, `UI` | - |
| 6 | `description` | 선택 | 설명 | `SAP 매출실적을 APlan으로 전송하는 인터페이스` | 빈 값 |
| 7 | `owner_team` | 선택 | 담당 조직/팀 | `ERP 플랫폼서비스팀` | 빈 값 |
| 8 | `module` | 선택 | 업무 도메인 | `S&OP`, `재고`, `판매`, `생산`, `구매` | 빈 값 |
| 9 | `status` | 선택 | 상태 | `ACTIVE`, `DRAFT`, `DEPRECATED` | `ACTIVE` |
| 10 | `tags` | 선택 | 태그 (콤마 구분) | `수요계획,판매,SD` | 빈 값 |
| 11 | `environment` | 선택 | 환경 | `PRD`, `QAS`, `DEV` | `PRD` |
| 12 | `source_doc` | 선택 | 소스 문서명 | `APlan_IF_Mapping_2025Q1.xlsx` | 파일명 자동 |
| 13 | `source_sheet` | 선택 | 소스 시트명 | `objects` | `objects` |
| 14 | `source_row` | 선택 | 소스 행 번호 | `2` | 자동 계산 |

### 예시 데이터

| object_key | name | system_type | object_type | layer | description | owner_team | module | status | tags | environment |
|------------|------|-------------|-------------|-------|-------------|------------|--------|--------|------|-------------|
| IF_APLAN_SALES_001 | APlan 매출 인터페이스 | APLAN | IF | In | SAP 매출실적을 APlan으로 전송 | ERP 플랫폼서비스팀 | 판매 | ACTIVE | 수요계획,판매 | PRD |
| SAP_VBRP | SAP 매출전표 | SAP | TABLE | Legacy | SAP SD 모듈 매출전표 테이블 | SAP 운영팀 | 판매 | ACTIVE | SAP,SD | PRD |
| ZAP_SALES_STG | 수요계획 매출 Staging | APLAN | TABLE | Staging | 매출 데이터 Staging 테이블 | ERP 플랫폼서비스팀 | 판매 | ACTIVE | 수요계획,Staging | PRD |

### 주의사항

1. **컬럼 순서**: 반드시 위 순서대로 배치해야 합니다
2. **object_key**: 중복 불가, 유일한 값이어야 합니다
3. **필수 컬럼**: `object_key`, `name`, `system_type`, `object_type`, `layer`는 반드시 입력
4. **system_type 값**: `SAP`, `APLAN`, `BW`, `BI`, `EAI`, `IAM`, `NPD`, `CDP`, `LEGACY` 중 하나
5. **object_type 값**: `IF`, `TABLE`, `VIEW`, `JOB`, `REPORT`, `UI` 중 하나
6. **status 값**: `ACTIVE`, `DRAFT`, `DEPRECATED` 중 하나
7. **environment 값**: `PRD`, `QAS`, `DEV` 중 하나

---

## 🔗 시트 2: `relations` (관계 정보)

### 컬럼 구조 (왼쪽부터 순서대로)

| 순번 | 컬럼명 | 필수여부 | 설명 | 예시 값 | 기본값 |
|------|--------|---------|------|---------|--------|
| 1 | `from_key` | ✅ **필수** | 출발 오브젝트의 object_key | `SAP_VBRP` | - |
| 2 | `to_key` | ✅ **필수** | 도착 오브젝트의 object_key | `IF_APLAN_SALES_001` | - |
| 3 | `relation_type` | 선택 | 관계 타입 | `FLOWS_TO` | `FLOWS_TO` |
| 4 | `description` | 선택 | 관계 설명 | `SAP SD 매출실적 → APlan 수요계획 Staging 적재` | 빈 값 |
| 5 | `status` | 선택 | 상태 | `ACTIVE`, `DRAFT`, `DEPRECATED` | `ACTIVE` |
| 6 | `source_doc` | 선택 | 소스 문서명 | `APlan_IF_Mapping_2025Q1.xlsx` | 파일명 자동 |
| 7 | `source_sheet` | 선택 | 소스 시트명 | `relations` | `relations` |
| 8 | `source_row` | 선택 | 소스 행 번호 | `2` | 자동 계산 |

### 예시 데이터

| from_key | to_key | relation_type | description | status |
|----------|--------|---------------|-------------|--------|
| SAP_VBRP | IF_APLAN_SALES_001 | FLOWS_TO | SAP 매출전표 → APlan 매출 인터페이스 | ACTIVE |
| IF_APLAN_SALES_001 | ZAP_SALES_STG | FLOWS_TO | APlan 매출 인터페이스 → 수요계획 Staging | ACTIVE |
| ZAP_SALES_STG | BW_SOP_CUBE | FLOWS_TO | 수요계획 Staging → BW S&OP 큐브 | ACTIVE |

### 주의사항

1. **from_key와 to_key**: 반드시 `objects` 시트에 존재하는 `object_key` 값이어야 합니다
2. **데이터 흐름 방향**: `from_key` → `to_key` (출발 → 도착)
3. **순환 참조**: 같은 오브젝트끼리 연결 가능 (예: A → B → A)
4. **relation_type**: 현재는 `FLOWS_TO`만 사용 (향후 확장 가능)

---

## 📝 엑셀 파일 작성 가이드

### 1단계: 파일 생성

1. Microsoft Excel 실행
2. 새 통합 문서 생성
3. 파일명을 `mapping.xlsx`로 저장

### 2단계: 시트 생성 및 이름 변경

1. 기본 시트 이름을 `objects`로 변경
2. 새 시트 추가 후 이름을 `relations`로 변경

### 3단계: 헤더 입력

#### `objects` 시트:
```
A1: object_key
B1: name
C1: system_type
D1: object_type
E1: layer
F1: description
G1: owner_team
H1: module
I1: status
J1: tags
K1: environment
L1: source_doc
M1: source_sheet
N1: source_row
```

#### `relations` 시트:
```
A1: from_key
B1: to_key
C1: relation_type
D1: description
E1: status
F1: source_doc
G1: source_sheet
H1: source_row
```

### 4단계: 데이터 입력

- 2행부터 데이터 입력
- 필수 컬럼은 반드시 입력
- 선택 컬럼은 필요시 입력 (빈 값 가능)

### 5단계: 파일 저장

- 파일명: `mapping.xlsx`
- 위치: 프로젝트 루트 디렉토리 (`C:\Cursor\aplan\`)

---

## ✅ 검증 체크리스트

업로드 전 확인사항:

- [ ] 파일명이 `mapping.xlsx`인가?
- [ ] `objects` 시트가 존재하는가?
- [ ] `relations` 시트가 존재하는가?
- [ ] `objects` 시트의 필수 컬럼이 모두 있는가? (object_key, name, system_type, object_type, layer)
- [ ] `relations` 시트의 필수 컬럼이 모두 있는가? (from_key, to_key)
- [ ] `object_key` 값이 중복되지 않는가?
- [ ] `relations`의 `from_key`와 `to_key`가 `objects` 시트에 존재하는가?
- [ ] 컬럼 순서가 올바른가?
- [ ] 헤더 행이 1행에 있는가?

---

## 🚀 파일 업로드 및 로딩

### 1단계: 파일 배치

`mapping.xlsx` 파일을 프로젝트 루트 디렉토리에 배치:
```
C:\Cursor\aplan\mapping.xlsx
```

### 2단계: 데이터 로딩

PowerShell에서 실행:
```powershell
cd C:\Cursor\aplan
python load_mapping.py
```

### 3단계: 로딩 결과 확인

정상적으로 로딩되면 다음과 같은 메시지가 표시됩니다:
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

---

## 📋 샘플 파일 생성

테스트용 샘플 파일을 생성하려면:

```powershell
python create_sample_mapping.py
```

이 명령어를 실행하면 `mapping.xlsx` 샘플 파일이 생성됩니다.

---

## ⚠️ 주의사항

1. **파일명**: 반드시 `mapping.xlsx`로 저장해야 합니다
2. **시트명**: 시트 이름은 정확히 `objects`와 `relations`여야 합니다 (대소문자 구분)
3. **컬럼명**: 컬럼명은 정확히 일치해야 합니다 (대소문자 구분)
4. **데이터 타입**: 
   - 숫자 필드(`source_row`)는 숫자로 입력
   - 나머지는 텍스트로 입력
5. **빈 값 처리**: 선택 컬럼은 빈 값으로 두어도 됩니다
6. **특수문자**: `object_key`에는 특수문자 사용 가능하지만, 공백은 피하는 것을 권장

---

## 🔍 문제 해결

### 오류: "필수 컬럼이 없습니다"
- 컬럼명이 정확한지 확인
- 컬럼 순서가 올바른지 확인
- 헤더 행이 1행에 있는지 확인

### 오류: "from_key 'XXX'에 해당하는 오브젝트를 찾을 수 없습니다"
- `relations` 시트의 `from_key` 값이 `objects` 시트의 `object_key`와 정확히 일치하는지 확인
- 대소문자, 공백, 특수문자 확인

### 오류: "to_key 'XXX'에 해당하는 오브젝트를 찾을 수 없습니다"
- `relations` 시트의 `to_key` 값이 `objects` 시트의 `object_key`와 정확히 일치하는지 확인

---

## 📞 추가 도움말

문제가 발생하면 다음을 확인하세요:
1. 로딩 스크립트의 로그 메시지 확인
2. 엑셀 파일의 데이터 형식 확인
3. `QUICK_TEST_GUIDE.md` 파일 참고

