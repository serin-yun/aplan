"""
샘플 mapping.xlsx 파일 생성 스크립트

테스트 및 검증을 위한 샘플 데이터 생성
"""

import pandas as pd
from pathlib import Path

# 샘플 오브젝트 데이터
objects_data = {
    'object_key': [
        'IF_APLAN_SALES_001',
        'SAP_VBRP',
        'ZAP_SALES_STG',
        'BW_SOP_CUBE',
        'IF_APLAN_INV_002',
        'SAP_MARA',
        'ZAP_INV_STG',
        'BI_SALES_REPORT',
        'EAI_SAP_TO_APLAN',
        'IF_APLAN_PROD_003'
    ],
    'name': [
        'APlan 매출 인터페이스',
        'SAP 매출전표',
        '수요계획 매출 Staging',
        'BW S&OP 큐브',
        'APlan 재고 인터페이스',
        'SAP 자재마스터',
        '재고 Staging',
        'BI 매출 리포트',
        'EAI SAP-APlan 연계',
        'APlan 생산 인터페이스'
    ],
    'system_type': [
        'APLAN',
        'SAP',
        'APLAN',
        'BW',
        'APLAN',
        'SAP',
        'APLAN',
        'BI',
        'EAI',
        'APLAN'
    ],
    'object_type': [
        'IF',
        'TABLE',
        'TABLE',
        'CUBE',
        'IF',
        'TABLE',
        'TABLE',
        'REPORT',
        'IF',
        'IF'
    ],
    'layer': [
        'In',
        'Legacy',
        'Staging',
        'Legacy',
        'In',
        'Legacy',
        'Staging',
        'Out',
        'API',
        'In'
    ],
    'description': [
        'SAP 매출실적을 APlan으로 전송하는 인터페이스',
        'SAP SD 모듈의 매출전표 테이블',
        '수요계획 시스템의 매출 데이터 Staging 테이블',
        'S&OP 분석용 BW 큐브',
        'SAP 재고 정보를 APlan으로 전송하는 인터페이스',
        'SAP MM 모듈의 자재마스터 테이블',
        '재고 관리 시스템의 Staging 테이블',
        '매출 분석 리포트',
        'SAP와 APlan 간 데이터 연계 EAI',
        'SAP 생산 정보를 APlan으로 전송하는 인터페이스'
    ],
    'owner_team': [
        'ERP 플랫폼서비스팀',
        'SAP 운영팀',
        'SCI 실',
        'BI 팀',
        'ERP 플랫폼서비스팀',
        'SAP 운영팀',
        'SCI 실',
        'BI 팀',
        'EAI 팀',
        'ERP 플랫폼서비스팀'
    ],
    'module': [
        '판매',
        'SD',
        'S&OP',
        'S&OP',
        '재고',
        'MM',
        '재고',
        '판매',
        '연계',
        '생산'
    ],
    'status': [
        'ACTIVE',
        'ACTIVE',
        'ACTIVE',
        'ACTIVE',
        'ACTIVE',
        'ACTIVE',
        'ACTIVE',
        'ACTIVE',
        'ACTIVE',
        'ACTIVE'
    ],
    'tags': [
        '수요계획,판매,SD',
        '매출,전표',
        'Staging,매출',
        'S&OP,분석',
        '재고,MM',
        '자재,마스터',
        'Staging,재고',
        '리포트,매출',
        '연계,EAI',
        '생산,PP'
    ],
    'environment': [
        'PRD',
        'PRD',
        'PRD',
        'PRD',
        'PRD',
        'PRD',
        'PRD',
        'PRD',
        'PRD',
        'PRD'
    ]
}

# 샘플 관계 데이터
relations_data = {
    'from_key': [
        'SAP_VBRP',
        'IF_APLAN_SALES_001',
        'ZAP_SALES_STG',
        'BW_SOP_CUBE',
        'SAP_MARA',
        'IF_APLAN_INV_002',
        'ZAP_INV_STG',
        'EAI_SAP_TO_APLAN',
        'SAP_VBRP',
        'IF_APLAN_PROD_003'
    ],
    'to_key': [
        'IF_APLAN_SALES_001',
        'ZAP_SALES_STG',
        'BW_SOP_CUBE',
        'BI_SALES_REPORT',
        'IF_APLAN_INV_002',
        'ZAP_INV_STG',
        'BW_SOP_CUBE',
        'IF_APLAN_SALES_001',
        'EAI_SAP_TO_APLAN',
        'ZAP_SALES_STG'
    ],
    'relation_type': [
        'FLOWS_TO',
        'FLOWS_TO',
        'FLOWS_TO',
        'FLOWS_TO',
        'FLOWS_TO',
        'FLOWS_TO',
        'FLOWS_TO',
        'FLOWS_TO',
        'FLOWS_TO',
        'FLOWS_TO'
    ],
    'description': [
        'SAP 매출전표 → APlan 매출 인터페이스',
        'APlan 매출 인터페이스 → Staging 적재',
        'Staging → BW 큐브 적재',
        'BW 큐브 → BI 리포트 생성',
        'SAP 자재마스터 → APlan 재고 인터페이스',
        'APlan 재고 인터페이스 → Staging 적재',
        '재고 Staging → BW 큐브 적재',
        'EAI 연계 → APlan 매출 인터페이스',
        'SAP 매출전표 → EAI 연계',
        'APlan 생산 인터페이스 → 매출 Staging'
    ],
    'status': [
        'ACTIVE',
        'ACTIVE',
        'ACTIVE',
        'ACTIVE',
        'ACTIVE',
        'ACTIVE',
        'ACTIVE',
        'ACTIVE',
        'ACTIVE',
        'ACTIVE'
    ]
}

def create_sample_mapping():
    """샘플 mapping.xlsx 파일 생성"""
    output_file = Path("mapping.xlsx")
    
    # DataFrame 생성
    df_objects = pd.DataFrame(objects_data)
    df_relations = pd.DataFrame(relations_data)
    
    # Excel 파일로 저장
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        df_objects.to_excel(writer, sheet_name='objects', index=False)
        df_relations.to_excel(writer, sheet_name='relations', index=False)
    
    print(f"✅ 샘플 mapping.xlsx 파일 생성 완료: {output_file}")
    print(f"   - Objects: {len(df_objects)}개")
    print(f"   - Relations: {len(df_relations)}개")
    print(f"\n다음 명령어로 데이터를 로딩하세요:")
    print(f"   python load_mapping.py")


if __name__ == "__main__":
    create_sample_mapping()

