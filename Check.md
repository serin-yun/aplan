# 현재 구현 기능 체크리스트

아래 내용은 코드 기준으로 **이미 구현된 기능**만 정리했습니다.  
핵심 기능 선별/제거 판단을 위해 사용하세요.

## 1) 핵심 기능 (유지 후보)

- **메타데이터 저장 모델**
  - `IntegrationObject`, `IntegrationRelation` 기반 오브젝트/관계 저장
  - 상태(`ACTIVE/DRAFT/DEPRECATED`), 시스템/모듈/레이어/태그 등 속성 지원
- **엑셀 기반 메타데이터 로딩**
  - `mapping.xlsx`의 `objects`/`relations` 시트 로딩
  - 업서트 방식으로 DB 반영
- **오브젝트 검색 화면**
  - 키워드/필터 기반 검색
  - 결과 리스트 화면 제공
- **오브젝트 상세 + 영향도**
  - Upstream/Downstream 영향도 탐색 (depth 1~2)
  - Mermaid 다이어그램 생성/렌더링
- **기본 API**
  - 오브젝트 검색/상세/영향도/mermaid API 제공

## 2) 시각화/맵 기능

- **전체 시스템 맵**
  - Overview 화면 (요약/클러스터)
  - Mermaid 전체 맵 생성 API
- **vis.js 네트워크 그래프**
  - 전체 맵 네트워크 데이터 API
  - 특정 오브젝트 중심 영향도 네트워크 API

## 3) Flow 기능 (확장 기능)

- **Flow 목록/검색 화면**
  - flow_key 기반 카드 뷰, 검색/필터
- **Flow 상세 화면**
  - Stepper 기반 흐름 표시
  - 운영정보(legacy/IF/STG 등) 패널
- **Flow 리포트 화면**
  - 인쇄/PDF용 요약 리포트
- **Flow API**
  - Flow 목록 카드 API
  - Flow 다이어그램 API

## 4) 데이터 업로드/생성 (운영 편의)

- **엑셀 업로드 UI**
  - 파일 검증(확장자/용량/시트/필수컬럼)
  - 업로드 후 DB 로딩
- **Relations 자동 생성**
  - relations 비어있을 때 tags 기반 자동 생성
- **정의서 기반 mapping 생성**
  - `Inbound.xlsx` + `Legacy.xlsx` 업로드 → mapping.xlsx 생성
- **Interface.xlsx 기반 mapping 생성**
  - 인터페이스 시트 기반 objects/relations 생성
- **Flow 데이터 자동 로딩**
  - interface/flow 시트가 있으면 Flow 테이블 자동 적재

## 5) 대시보드/통계

- **대시보드 화면**
  - 데이터 로딩 여부/기본 통계
  - 최근 오브젝트 목록
- **통계 API**
  - 시스템/레이어/모듈/오브젝트 타입 집계

## 6) 주요 화면 URL

- `/dashboard` 대시보드
- `/objects` 오브젝트 검색
- `/objects/{id}` 오브젝트 상세/영향도
- `/objects/overview` 전체 맵(요약)
- `/flows` flow 목록
- `/flows/{flow_key}` flow 상세
- `/flows/{flow_key}/report` flow 리포트

## 7) 핵심 기능 선별 가이드 (참고)

- **최소 핵심**: 오브젝트 검색 + 상세/영향도 + 엑셀 로딩
- **고급 기능**: overview/네트워크/flow/업로드 자동 생성/리포트

## 8) 보기 모드 통합 기준 (1가지로 통합)

보고용/업무흐름/운영분석을 **단일 모드**로 통합할 경우, 아래 기준으로 정리됩니다.

- **통합 모드 정의**: “핵심 흐름 + 필요 최소 운영정보”만 노출
- **포함**: 인터페이스 흐름(요약 라인), 주요 테이블/IF, 영향도(1~2 depth)
- **제외**: 리더 전용 요약 지표, 과도한 기술 상세(세부 프로그램/로그 테이블 등)
- **목표 사용자**: 현업/운영이 모두 이해 가능한 수준
