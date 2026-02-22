"""
데이터베이스 마이그레이션 스크립트: owner 컬럼 추가

기존 데이터베이스에 owner 컬럼을 추가합니다.
기존 데이터는 보존됩니다.
"""

import sqlite3
import logging
from pathlib import Path

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 데이터베이스 파일 경로
DB_FILE = "impact_map.db"


def check_column_exists(cursor: sqlite3.Cursor, table_name: str, column_name: str) -> bool:
    """컬럼이 존재하는지 확인"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns


def migrate_add_owner_column():
    """owner 컬럼 추가 마이그레이션"""
    db_path = Path(DB_FILE)
    
    if not db_path.exists():
        logger.warning(f"데이터베이스 파일이 없습니다: {DB_FILE}")
        logger.info("데이터베이스는 다음에 생성될 때 자동으로 owner 컬럼이 포함됩니다.")
        return
    
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # integration_objects 테이블에 owner 컬럼이 있는지 확인
        if check_column_exists(cursor, "integration_objects", "owner"):
            logger.info("✅ owner 컬럼이 이미 존재합니다. 마이그레이션이 필요하지 않습니다.")
            conn.close()
            return
        
        logger.info("owner 컬럼 추가 중...")
        
        # SQLite는 ALTER TABLE ADD COLUMN을 지원합니다
        # owner 컬럼 추가 (NULL 허용, TEXT 타입)
        cursor.execute("""
            ALTER TABLE integration_objects 
            ADD COLUMN owner TEXT
        """)
        
        conn.commit()
        logger.info("✅ owner 컬럼이 성공적으로 추가되었습니다.")
        
        # 확인: 컬럼이 제대로 추가되었는지 확인
        if check_column_exists(cursor, "integration_objects", "owner"):
            logger.info("✅ 컬럼 추가 확인 완료")
        else:
            logger.error("❌ 컬럼 추가 확인 실패")
        
        conn.close()
        
    except sqlite3.Error as e:
        logger.error(f"❌ 데이터베이스 오류: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ 마이그레이션 오류: {e}")
        raise


if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("데이터베이스 마이그레이션 시작")
    logger.info("=" * 50)
    
    try:
        migrate_add_owner_column()
        logger.info("=" * 50)
        logger.info("✅ 마이그레이션 완료!")
        logger.info("=" * 50)
    except Exception as e:
        logger.error("=" * 50)
        logger.error(f"❌ 마이그레이션 실패: {e}")
        logger.error("=" * 50)
        exit(1)







