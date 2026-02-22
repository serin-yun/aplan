"""
mapping.xlsx 템플릿 파일 생성 스크립트

업로드용 빈 양식 엑셀 파일 생성
"""

import pandas as pd
from pathlib import Path

def create_template():
    """빈 템플릿 mapping.xlsx 파일 생성"""
    
    # objects 시트 헤더만 있는 빈 DataFrame
    objects_columns = [
        'object_key',
        'name',
        'system_type',
        'object_type',
        'layer',
        'description',
        'owner_team',
        'owner',
        'module',
        'status',
        'tags',
        'environment',
        'source_doc',
        'source_sheet',
        'source_row'
    ]
    
    # relations 시트 헤더만 있는 빈 DataFrame
    relations_columns = [
        'from_key',
        'to_key',
        'relation_type',
        'description',
        'status',
        'source_doc',
        'source_sheet',
        'source_row'
    ]
    
    # 빈 DataFrame 생성 (헤더만)
    df_objects = pd.DataFrame(columns=objects_columns)
    df_relations = pd.DataFrame(columns=relations_columns)
    
    # 템플릿 파일명
    template_file = Path("mapping_template.xlsx")
    
    # Excel 파일로 저장
    with pd.ExcelWriter(template_file, engine='openpyxl') as writer:
        df_objects.to_excel(writer, sheet_name='objects', index=False)
        df_relations.to_excel(writer, sheet_name='relations', index=False)
        
        # 시트 스타일링 (선택사항)
        workbook = writer.book
        worksheet_objects = writer.sheets['objects']
        worksheet_relations = writer.sheets['relations']
        
        # 헤더 행 스타일링 (굵게, 배경색)
        from openpyxl.styles import Font, PatternFill, Alignment
        
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=11)
        header_alignment = Alignment(horizontal="center", vertical="center")
        
        # objects 시트 헤더 스타일링
        for cell in worksheet_objects[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = header_alignment
        
        # relations 시트 헤더 스타일링
        for cell in worksheet_relations[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = header_alignment
        
        # 컬럼 너비 자동 조정
        for column in worksheet_objects.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 30)
            worksheet_objects.column_dimensions[column_letter].width = adjusted_width
        
        for column in worksheet_relations.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 30)
            worksheet_relations.column_dimensions[column_letter].width = adjusted_width
    
    print(f"✅ 템플릿 파일 생성 완료: {template_file}")
    print(f"\n📋 파일 구조:")
    print(f"   - 시트 1: 'objects' ({len(objects_columns)}개 컬럼)")
    print(f"   - 시트 2: 'relations' ({len(relations_columns)}개 컬럼)")
    print(f"\n💡 사용 방법:")
    print(f"   1. {template_file} 파일을 열어서 데이터를 입력하세요")
    print(f"   2. 완성 후 파일명을 'mapping.xlsx'로 저장하세요")
    print(f"   3. 프로젝트 루트 디렉토리에 배치하세요")
    print(f"   4. 'python load_mapping.py' 명령어로 데이터를 로딩하세요")

if __name__ == "__main__":
    create_template()

