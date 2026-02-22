"""
메타데이터 엑셀 파일을 데이터베이스에 로딩하는 스크립트

MRD 6.4 요구사항:
- mapping.xlsx의 objects/relations 시트를 읽어서 DB에 UPSERT
- objects: object_key 기준으로 UPSERT
- relations: from_key/to_key로 IntegrationObject 조회 후 (from_object_id, to_object_id, relation_type) 기준으로 UPSERT
"""

import pandas as pd
import logging
from datetime import datetime
from pathlib import Path
from sqlmodel import Session, select
from app.database import engine, init_db
from app.models import IntegrationObject, IntegrationRelation

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 엑셀 파일 경로
MAPPING_FILE = "mapping.xlsx"


def load_objects(session: Session, df: pd.DataFrame, source_doc: str) -> dict[str, int]:
    """
    objects 시트를 읽어서 IntegrationObject 테이블에 UPSERT
    
    MRD 6.2 요구사항:
    - object_key 기준으로 조회
    - 존재하면 UPDATE, 없으면 INSERT
    - source_doc/source_sheet/source_row 기본값 처리
    
    Returns:
        dict[str, int]: object_key -> object_id 매핑 딕셔너리
    """
    object_key_to_id = {}
    
    # 필수 컬럼 확인
    required_columns = ['object_key', 'name', 'system_type', 'object_type', 'layer']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"필수 컬럼이 없습니다: {missing_columns}")
    
    for idx, row in df.iterrows():
        object_key = str(row['object_key']).strip()
        if not object_key:
            logger.warning(f"행 {idx + 2}: object_key가 비어있어 스킵합니다.")
            continue
        
        # 기존 오브젝트 조회
        statement = select(IntegrationObject).where(IntegrationObject.object_key == object_key)
        existing_obj = session.exec(statement).first()
        
        # 데이터 준비
        obj_data = {
            'object_key': object_key,
            'name': str(row.get('name', '')).strip(),
            'system_type': str(row.get('system_type', '')).strip(),
            'object_type': str(row.get('object_type', '')).strip(),
            'layer': str(row.get('layer', '')).strip(),
            'description': str(row.get('description', '')).strip() if pd.notna(row.get('description')) else None,
            'owner_team': str(row.get('owner_team', '')).strip() if pd.notna(row.get('owner_team')) else None,
            'owner': str(row.get('owner', '')).strip() if pd.notna(row.get('owner')) else None,
            'module': str(row.get('module', '')).strip() if pd.notna(row.get('module')) else None,
            'status': str(row.get('status', 'ACTIVE')).strip() if pd.notna(row.get('status')) else 'ACTIVE',
            'tags': str(row.get('tags', '')).strip() if pd.notna(row.get('tags')) else None,
            'environment': str(row.get('environment', 'PRD')).strip() if pd.notna(row.get('environment')) else 'PRD',
            'source_doc': str(row.get('source_doc', source_doc)).strip() if pd.notna(row.get('source_doc')) else source_doc,
            'source_sheet': str(row.get('source_sheet', 'objects')).strip() if pd.notna(row.get('source_sheet')) else 'objects',
            'source_row': int(row.get('source_row', idx + 2)) if pd.notna(row.get('source_row')) else idx + 2,
        }
        
        if existing_obj:
            # UPDATE
            for key, value in obj_data.items():
                setattr(existing_obj, key, value)
            existing_obj.updated_at = datetime.utcnow()
            session.add(existing_obj)
            object_key_to_id[object_key] = existing_obj.id
            logger.info(f"업데이트: {object_key}")
        else:
            # INSERT
            new_obj = IntegrationObject(**obj_data)
            session.add(new_obj)
            session.flush()  # ID 생성
            object_key_to_id[object_key] = new_obj.id
            logger.info(f"생성: {object_key}")
    
    return object_key_to_id


def load_relations(session: Session, df: pd.DataFrame, object_key_to_id: dict[str, int], source_doc: str) -> None:
    """
    relations 시트를 읽어서 IntegrationRelation 테이블에 UPSERT
    
    MRD 6.3 요구사항:
    - from_key/to_key로 IntegrationObject.object_key 조회
    - 매칭 실패 시 WARNING 로그 출력 후 스킵
    - (from_object_id, to_object_id, relation_type) 조합 기준으로 UPSERT
    - relations 시트가 비어있으면 objects 행 순서대로 자동 매핑
    """
    # relations 시트가 비어있으면 tags 기준으로 역순 자동 매핑
    if df.empty or len(df) == 0:
        logger.info("relations 시트가 비어있습니다. tags 기준 역순으로 자동 관계 생성...")
        
        # objects_df를 다시 읽어서 tags 정보 가져오기
        objects_df = pd.read_excel(source_doc, sheet_name='objects')
        
        # tags별로 object_key 그룹화 (순서 유지)
        tags_groups = {}
        for idx, row in objects_df.iterrows():
            object_key = str(row['object_key']).strip()
            tags = str(row.get('tags', '')).strip() if pd.notna(row.get('tags')) else ''
            
            if tags not in tags_groups:
                tags_groups[tags] = []
            tags_groups[tags].append(object_key)
        
        relation_count = 0
        for tags, keys in tags_groups.items():
            if len(keys) < 2:
                continue
            
            logger.info(f"tags '{tags}' 그룹 역순 관계 생성: {len(keys)}개 오브젝트")
            
            # 역순으로 관계 생성: D->C, C->B, B->A
            for i in range(len(keys) - 1, 0, -1):
                from_key = keys[i]
                to_key = keys[i - 1]
                
                from_object_id = object_key_to_id.get(from_key)
                to_object_id = object_key_to_id.get(to_key)
                
                if not from_object_id or not to_object_id:
                    continue
                
                relation_type = 'FLOWS_TO'
                
                # 기존 관계 조회
                statement = select(IntegrationRelation).where(
                    IntegrationRelation.from_object_id == from_object_id,
                    IntegrationRelation.to_object_id == to_object_id,
                    IntegrationRelation.relation_type == relation_type
                )
                existing_rel = session.exec(statement).first()
                
                rel_data = {
                    'from_object_id': from_object_id,
                    'to_object_id': to_object_id,
                    'relation_type': relation_type,
                    'status': 'ACTIVE',
                    'source_doc': source_doc,
                    'source_sheet': 'auto_generated',
                    'source_row': relation_count + 1,
                }
                
                if existing_rel:
                    for key, value in rel_data.items():
                        setattr(existing_rel, key, value)
                    existing_rel.updated_at = datetime.utcnow()
                    session.add(existing_rel)
                    logger.info(f"자동 관계 업데이트: {from_key} -> {to_key} (tags: {tags})")
                else:
                    new_rel = IntegrationRelation(**rel_data)
                    session.add(new_rel)
                    logger.info(f"자동 관계 생성: {from_key} -> {to_key} (tags: {tags})")
                
                relation_count += 1
        
        logger.info(f"자동 관계 생성 완료: {relation_count}개")
        return
    
    # 필수 컬럼 확인
    required_columns = ['from_key', 'to_key']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"필수 컬럼이 없습니다: {missing_columns}")
    
    for idx, row in df.iterrows():
        from_key = str(row['from_key']).strip()
        to_key = str(row['to_key']).strip()
        
        if not from_key or not to_key:
            logger.warning(f"행 {idx + 2}: from_key 또는 to_key가 비어있어 스킵합니다.")
            continue
        
        # object_key -> object_id 매핑 확인
        from_object_id = object_key_to_id.get(from_key)
        to_object_id = object_key_to_id.get(to_key)
        
        if not from_object_id:
            logger.warning(f"행 {idx + 2}: from_key '{from_key}'에 해당하는 오브젝트를 찾을 수 없습니다. 스킵합니다.")
            continue
        
        if not to_object_id:
            logger.warning(f"행 {idx + 2}: to_key '{to_key}'에 해당하는 오브젝트를 찾을 수 없습니다. 스킵합니다.")
            continue
        
        relation_type = str(row.get('relation_type', 'FLOWS_TO')).strip() if pd.notna(row.get('relation_type')) else 'FLOWS_TO'
        
        # 기존 관계 조회
        statement = select(IntegrationRelation).where(
            IntegrationRelation.from_object_id == from_object_id,
            IntegrationRelation.to_object_id == to_object_id,
            IntegrationRelation.relation_type == relation_type
        )
        existing_rel = session.exec(statement).first()
        
        # 데이터 준비
        rel_data = {
            'from_object_id': from_object_id,
            'to_object_id': to_object_id,
            'relation_type': relation_type,
            'description': str(row.get('description', '')).strip() if pd.notna(row.get('description')) else None,
            'status': str(row.get('status', 'ACTIVE')).strip() if pd.notna(row.get('status')) else 'ACTIVE',
            'source_doc': str(row.get('source_doc', source_doc)).strip() if pd.notna(row.get('source_doc')) else source_doc,
            'source_sheet': str(row.get('source_sheet', 'relations')).strip() if pd.notna(row.get('source_sheet')) else 'relations',
            'source_row': int(row.get('source_row', idx + 2)) if pd.notna(row.get('source_row')) else idx + 2,
        }
        
        if existing_rel:
            # UPDATE
            for key, value in rel_data.items():
                setattr(existing_rel, key, value)
            existing_rel.updated_at = datetime.utcnow()
            session.add(existing_rel)
            logger.info(f"관계 업데이트: {from_key} -> {to_key}")
        else:
            # INSERT
            new_rel = IntegrationRelation(**rel_data)
            session.add(new_rel)
            logger.info(f"관계 생성: {from_key} -> {to_key}")


def main():
    """
    메인 실행 함수
    """
    # 엑셀 파일 존재 확인
    mapping_path = Path(MAPPING_FILE)
    if not mapping_path.exists():
        logger.error(f"엑셀 파일을 찾을 수 없습니다: {MAPPING_FILE}")
        return
    
    # 데이터베이스 초기화
    logger.info("데이터베이스 초기화 중...")
    init_db()
    
    # 엑셀 파일 읽기
    logger.info(f"엑셀 파일 읽기: {MAPPING_FILE}")
    try:
        df_objects = pd.read_excel(MAPPING_FILE, sheet_name='objects')
        df_relations = pd.read_excel(MAPPING_FILE, sheet_name='relations')
    except Exception as e:
        logger.error(f"엑셀 파일 읽기 실패: {e}")
        return
    
    source_doc = mapping_path.name
    
    # 데이터베이스 세션 생성
    with Session(engine) as session:
        try:
            # Objects 로딩
            logger.info("Objects 시트 로딩 중...")
            object_key_to_id = load_objects(session, df_objects, source_doc)
            logger.info(f"Objects 로딩 완료: {len(object_key_to_id)}개")
            
            # Relations 로딩
            logger.info("Relations 시트 로딩 중...")
            load_relations(session, df_relations, object_key_to_id, source_doc)
            
            # 커밋
            session.commit()
            logger.info("데이터베이스 커밋 완료")
            
        except Exception as e:
            session.rollback()
            logger.error(f"오류 발생: {e}")
            raise


if __name__ == "__main__":
    main()


