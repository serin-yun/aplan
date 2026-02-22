"""
IntegrationObject 및 IntegrationRelation 모델 정의

MRD 5장 요구사항:
- IntegrationObject: 인터페이스/테이블/리포트/Job 등 모든 오브젝트 표현
- IntegrationRelation: 오브젝트 간 데이터 흐름/참조 관계(그래프 엣지) 표현
"""

from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship


class IntegrationObjectBase(SQLModel):
    """IntegrationObject 기본 필드 (공통)"""
    object_key: str = Field(unique=True, index=True, description="업무상 유일키 (예: IF_APLAN_SALES_001)")
    name: str = Field(description="표시 이름 (한글/영문 모두 가능)")
    system_type: str = Field(description="시스템 타입 (SAP, APLAN, BW, BI, EAI, IAM, NPD, CDP, LEGACY)")
    object_type: str = Field(description="오브젝트 타입 (IF, TABLE, VIEW, JOB, REPORT, UI)")
    layer: str = Field(description="레이어 (Legacy, API, Cust, In, Staging, Out, UI)")
    description: Optional[str] = Field(default=None, description="설명")
    owner_team: Optional[str] = Field(default=None, description="담당 조직/팀")
    owner: Optional[str] = Field(default=None, description="담당자 (개인 이름)")
    module: Optional[str] = Field(default=None, description="업무 도메인 (S&OP, 재고, 판매, 생산, 구매)")
    status: str = Field(default="ACTIVE", description="상태 (ACTIVE, DRAFT, DEPRECATED)")
    tags: Optional[str] = Field(default=None, description="콤마 구분 키워드 (예: 수요계획,판매,SD)")
    environment: str = Field(default="PRD", description="환경 (PRD, QAS, DEV)")
    
    # 소스/거버넌스 필드
    source_doc: Optional[str] = Field(default=None, description="엑셀 파일명")
    source_sheet: Optional[str] = Field(default=None, description="엑셀 시트명")
    source_row: Optional[int] = Field(default=None, description="엑셀 행 번호")


class IntegrationObject(IntegrationObjectBase, table=True):
    """IntegrationObject 테이블 모델"""
    __tablename__ = "integration_objects"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # 관계: outgoing_relations (이 오브젝트가 출발점인 관계들)
    outgoing_relations: List["IntegrationRelation"] = Relationship(
        back_populates="from_object",
        sa_relationship_kwargs={"foreign_keys": "IntegrationRelation.from_object_id"}
    )
    
    # 관계: incoming_relations (이 오브젝트가 도착점인 관계들)
    incoming_relations: List["IntegrationRelation"] = Relationship(
        back_populates="to_object",
        sa_relationship_kwargs={"foreign_keys": "IntegrationRelation.to_object_id"}
    )


class IntegrationRelationBase(SQLModel):
    """IntegrationRelation 기본 필드 (공통)"""
    relation_type: str = Field(default="FLOWS_TO", description="관계 타입 (MVP에서는 FLOWS_TO만 사용)")
    description: Optional[str] = Field(default=None, description="관계 설명")
    status: str = Field(default="ACTIVE", description="상태 (ACTIVE, DRAFT, DEPRECATED)")
    
    # 소스/거버넌스 필드
    source_doc: Optional[str] = Field(default=None, description="엑셀 파일명")
    source_sheet: Optional[str] = Field(default=None, description="엑셀 시트명")
    source_row: Optional[int] = Field(default=None, description="엑셀 행 번호")


class IntegrationRelation(IntegrationRelationBase, table=True):
    """IntegrationRelation 테이블 모델"""
    __tablename__ = "integration_relations"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    from_object_id: int = Field(foreign_key="integration_objects.id", description="출발 오브젝트 ID")
    to_object_id: int = Field(foreign_key="integration_objects.id", description="도착 오브젝트 ID")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # 관계: from_object (출발 오브젝트)
    from_object: IntegrationObject = Relationship(
        back_populates="outgoing_relations",
        sa_relationship_kwargs={"foreign_keys": "IntegrationRelation.from_object_id"}
    )
    
    # 관계: to_object (도착 오브젝트)
    to_object: IntegrationObject = Relationship(
        back_populates="incoming_relations",
        sa_relationship_kwargs={"foreign_keys": "IntegrationRelation.to_object_id"}
    )

