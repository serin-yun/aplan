"""
데이터베이스 설정 및 초기화

MRD 4.1 요구사항:
- SQLite 사용 (sqlite:///./impact_map.db)
- 추후 PostgreSQL 확장 가능하도록 구성
"""

from sqlmodel import SQLModel, create_engine, Session
from app.models import IntegrationObject, IntegrationRelation

# SQLite 데이터베이스 URL
DATABASE_URL = "sqlite:///./impact_map.db"

# SQLModel 엔진 생성
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite 멀티스레드 지원
    echo=False  # SQL 쿼리 로그 출력 여부 (디버깅 시 True)
)


def init_db() -> None:
    """
    데이터베이스 테이블 생성
    
    MRD 3.1 요구사항:
    - IntegrationObject, IntegrationRelation 테이블 생성
    """
    SQLModel.metadata.create_all(engine)


def get_session():
    """
    데이터베이스 세션 생성 (의존성 주입용)
    
    FastAPI에서 사용:
    ```python
    def get_db():
        with Session(engine) as session:
            yield session
    ```
    """
    with Session(engine) as session:
        yield session









