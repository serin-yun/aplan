"""
Objects API 라우터

MRD 7장 요구사항:
- GET /objects - 검색/리스트 조회 (템플릿 렌더링)
- GET /objects/{object_id} - 단일 오브젝트 상세 조회 (템플릿 렌더링)
- GET /objects/{object_id}/impact - 영향도 정보 조회 (JSON API)
- GET /objects/{object_id}/mermaid - Mermaid 코드 생성 (JSON API)
"""

from typing import Optional, List, Set
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select, or_
from pydantic import BaseModel, Field, ConfigDict
from pathlib import Path

from app.database import get_session
from app.models import IntegrationObject, IntegrationRelation
from app.services.impact_service import get_impact_graph, generate_mermaid_code, generate_full_map_mermaid_code

router = APIRouter(prefix="/objects", tags=["objects"])

# 템플릿 디렉토리 설정
templates_dir = Path(__file__).parent.parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


# 응답 모델 정의
class ObjectListItem(BaseModel):
    """오브젝트 리스트 항목 (검색 결과용)"""
    id: int
    object_key: str
    name: str
    system_type: str
    object_type: str
    layer: str
    description: Optional[str] = None
    status: str
    module: Optional[str] = None

    class Config:
        from_attributes = True


class ImpactResponse(BaseModel):
    """영향도 정보 응답"""
    object: dict
    upstream: List[dict]
    downstream: List[dict]


class MermaidResponse(BaseModel):
    """Mermaid 코드 응답"""
    mermaid_code: str


class NetworkNode(BaseModel):
    """vis.js Network 노드 데이터"""
    id: int
    label: str
    title: str
    group: str
    color: Optional[dict] = None
    shape: Optional[str] = "box"
    font: Optional[dict] = None
    size: Optional[int] = None
    degree: Optional[int] = None  # 연결도 (연결된 엣지 수)


class NetworkEdge(BaseModel):
    """vis.js Network 엣지 데이터"""
    model_config = ConfigDict(populate_by_name=True)
    
    from_: int = Field(alias="from", serialization_alias="from")
    to: int
    arrows: str = "to"
    smooth: Optional[dict] = None
    color: Optional[dict] = None
    width: Optional[int] = None
    from_system: Optional[str] = None  # 출발 노드의 시스템 타입


class NetworkDataResponse(BaseModel):
    """vis.js Network 데이터 응답"""
    nodes: List[NetworkNode]
    edges: List[NetworkEdge]
    stats: dict


@router.get("", response_class=HTMLResponse, include_in_schema=False)
async def get_objects_html(
    request: Request,
    q: Optional[str] = Query(None, description="키워드 검색 (object_key, name, description)"),
    system_type: Optional[str] = Query(None, description="시스템 타입 필터"),
    object_type: Optional[str] = Query(None, description="오브젝트 타입 필터"),
    limit: int = Query(50, ge=1, le=200, description="최대 결과 수"),
    session: Session = Depends(get_session)
):
    """
    오브젝트 검색/리스트 조회 (HTML 템플릿 렌더링)
    
    MRD 7.1, 8.2 요구사항:
    - 검색 화면 템플릿 렌더링
    """
    statement = select(IntegrationObject).where(IntegrationObject.status == "ACTIVE")
    
    # 키워드 검색
    if q:
        search_term = f"%{q}%"
        statement = statement.where(
            or_(
                IntegrationObject.object_key.ilike(search_term),
                IntegrationObject.name.ilike(search_term),
                IntegrationObject.description.ilike(search_term)
            )
        )
    
    # 필터 적용
    if system_type:
        statement = statement.where(IntegrationObject.system_type == system_type)
    
    if object_type:
        statement = statement.where(IntegrationObject.object_type == object_type)
    
    # 정렬 및 제한
    statement = statement.order_by(IntegrationObject.object_key).limit(limit)
    
    objects = session.exec(statement).all()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "objects": objects,
            "q": q,
            "system_type": system_type,
            "object_type": object_type
        }
    )


@router.get("/api", response_model=List[ObjectListItem])
async def get_objects_api(
    q: Optional[str] = Query(None, description="키워드 검색 (object_key, name, description)"),
    system_type: Optional[str] = Query(None, description="시스템 타입 필터"),
    object_type: Optional[str] = Query(None, description="오브젝트 타입 필터"),
    limit: int = Query(50, ge=1, le=200, description="최대 결과 수"),
    session: Session = Depends(get_session)
):
    """
    오브젝트 검색/리스트 조회 (JSON API)
    
    MRD 7.1 요구사항:
    - q: object_key, name, description LIKE 검색
    - system_type, object_type 필터
    - limit: 최대 결과 수 (기본값 50)
    """
    statement = select(IntegrationObject).where(IntegrationObject.status == "ACTIVE")
    
    # 키워드 검색
    if q:
        search_term = f"%{q}%"
        statement = statement.where(
            or_(
                IntegrationObject.object_key.ilike(search_term),
                IntegrationObject.name.ilike(search_term),
                IntegrationObject.description.ilike(search_term)
            )
        )
    
    # 필터 적용
    if system_type:
        statement = statement.where(IntegrationObject.system_type == system_type)
    
    if object_type:
        statement = statement.where(IntegrationObject.object_type == object_type)
    
    # 정렬 및 제한
    statement = statement.order_by(IntegrationObject.object_key).limit(limit)
    
    objects = session.exec(statement).all()
    return objects


@router.get("/overview", response_class=HTMLResponse, include_in_schema=False)
async def get_overview_map(
    request: Request,
    session: Session = Depends(get_session)
):
    """
    전체 시스템 맵 화면
    
    모든 오브젝트와 관계를 한눈에 볼 수 있는 전체 맵을 표시합니다.
    """
    from app.services.impact_service import generate_full_map_mermaid_code
    
    mermaid_code = generate_full_map_mermaid_code(session)
    
    # 통계 정보
    statement = select(IntegrationObject).where(IntegrationObject.status == "ACTIVE")
    objects = session.exec(statement).all()
    object_count = len(objects)
    
    statement = select(IntegrationRelation).where(IntegrationRelation.status == "ACTIVE")
    relations = session.exec(statement).all()
    relation_count = len(relations)
    
    # 시스템 타입별 통계
    system_stats = {}
    for obj in objects:
        system = obj.system_type
        system_stats[system] = system_stats.get(system, 0) + 1
    
    return templates.TemplateResponse(
        "overview.html",
        {
            "request": request,
            "mermaid_code": mermaid_code,
            "object_count": object_count,
            "relation_count": relation_count,
            "system_stats": system_stats
        }
    )


@router.get("/{object_id}", response_class=HTMLResponse, include_in_schema=False)
async def get_object_html(
    request: Request,
    object_id: int,
    depth: int = Query(2, ge=1, le=2, description="탐색 깊이 (1 또는 2, 기본값 2)"),
    session: Session = Depends(get_session)
):
    """
    단일 오브젝트 상세 조회 (HTML 템플릿 렌더링)
    
    MRD 7.2, 8.3 요구사항:
    - 상세/영향도 화면 템플릿 렌더링
    - 영향도 정보 및 Mermaid 다이어그램 포함
    """
    statement = select(IntegrationObject).where(IntegrationObject.id == object_id)
    obj = session.exec(statement).first()
    
    if not obj:
        raise HTTPException(status_code=404, detail=f"오브젝트 ID {object_id}를 찾을 수 없습니다")
    
    # 영향도 정보 조회
    try:
        graph = get_impact_graph(session, object_id, depth)
        
        # 객체를 딕셔너리로 변환
        def obj_to_dict(obj: IntegrationObject) -> dict:
            return {
                "id": obj.id,
                "object_key": obj.object_key,
                "name": obj.name,
                "system_type": obj.system_type,
                "object_type": obj.object_type,
                "layer": obj.layer,
                "description": obj.description,
                "module": obj.module,
                "status": obj.status,
                "owner_team": obj.owner_team,
                "environment": obj.environment,
                "tags": obj.tags
            }
        
        upstream = [obj_to_dict(obj) for obj in graph.upstream]
        downstream = [obj_to_dict(obj) for obj in graph.downstream]
    except ValueError:
        upstream = []
        downstream = []
    
    # Mermaid 코드 생성
    try:
        mermaid_code = generate_mermaid_code(session, object_id, depth)
    except ValueError:
        mermaid_code = "flowchart LR\n  Error[\"오브젝트를 찾을 수 없습니다\"]"
    
    return templates.TemplateResponse(
        "object_detail.html",
        {
            "request": request,
            "object": obj,
            "upstream": upstream,
            "downstream": downstream,
            "mermaid_code": mermaid_code
        }
    )


@router.get("/{object_id}/api", response_model=IntegrationObject)
async def get_object_api(
    object_id: int,
    session: Session = Depends(get_session)
):
    """
    단일 오브젝트 상세 조회 (JSON API)
    
    MRD 7.2 요구사항:
    - IntegrationObject 전체 필드 반환
    """
    statement = select(IntegrationObject).where(IntegrationObject.id == object_id)
    obj = session.exec(statement).first()
    
    if not obj:
        raise HTTPException(status_code=404, detail=f"오브젝트 ID {object_id}를 찾을 수 없습니다")
    
    return obj


@router.get("/{object_id}/impact", response_model=ImpactResponse)
async def get_object_impact(
    object_id: int,
    depth: int = Query(1, ge=1, le=2, description="탐색 깊이 (1 또는 2)"),
    session: Session = Depends(get_session)
):
    """
    오브젝트 영향도 정보 조회
    
    MRD 7.3 요구사항:
    - depth: 1 또는 2 (기본값 1)
    - 반환: object, upstream[], downstream[]
    """
    try:
        graph = get_impact_graph(session, object_id, depth)
        
        # 객체를 딕셔너리로 변환
        def obj_to_dict(obj: IntegrationObject) -> dict:
            return {
                "id": obj.id,
                "object_key": obj.object_key,
                "name": obj.name,
                "system_type": obj.system_type,
                "object_type": obj.object_type,
                "layer": obj.layer,
                "description": obj.description,
                "module": obj.module,
                "status": obj.status,
                "owner_team": obj.owner_team,
                "environment": obj.environment,
                "tags": obj.tags
            }
        
        return ImpactResponse(
            object=obj_to_dict(graph.center_object),
            upstream=[obj_to_dict(obj) for obj in graph.upstream],
            downstream=[obj_to_dict(obj) for obj in graph.downstream]
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{object_id}/mermaid", response_model=MermaidResponse)
async def get_object_mermaid(
    object_id: int,
    depth: int = Query(2, ge=1, le=2, description="탐색 깊이 (1 또는 2, 기본값 2)"),
    session: Session = Depends(get_session)
):
    """
    오브젝트 영향도 Mermaid 다이어그램 코드 생성
    
    MRD 7.4 요구사항:
    - depth: 1 또는 2 (기본값 2)
    - 반환: mermaid_code (flowchart LR 형식)
    """
    try:
        mermaid_code = generate_mermaid_code(session, object_id, depth)
        return MermaidResponse(mermaid_code=mermaid_code)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/overview/network", response_model=NetworkDataResponse)
async def get_overview_network(
    system_type: Optional[str] = Query(None, description="시스템 타입 필터"),
    layer: Optional[str] = Query(None, description="레이어 필터"),
    module: Optional[str] = Query(None, description="모듈 필터"),
    session: Session = Depends(get_session)
):
    """
    전체 시스템 맵 vis.js Network 데이터 생성 (JSON API)
    
    필터링 옵션:
    - system_type: 시스템 타입 필터
    - layer: 레이어 필터
    - module: 모듈 필터
    """
    from app.models import IntegrationRelation
    
    # 시스템 타입별 색상 매핑 (부드러운 파스텔 톤)
    system_colors = {
        "SAP": {"background": "#81c784", "border": "#66bb6a", "highlight": {"background": "#a5d6a7", "border": "#66bb6a"}},
        "APLAN": {"background": "#64b5f6", "border": "#42a5f5", "highlight": {"background": "#90caf9", "border": "#42a5f5"}},
        "BW": {"background": "#ffb74d", "border": "#ffa726", "highlight": {"background": "#ffcc80", "border": "#ffa726"}},
        "BI": {"background": "#ba68c8", "border": "#ab47bc", "highlight": {"background": "#ce93d8", "border": "#ab47bc"}},
        "EAI": {"background": "#ef5350", "border": "#e53935", "highlight": {"background": "#ff8a80", "border": "#e53935"}},
        "IAM": {"background": "#4dd0e1", "border": "#26c6da", "highlight": {"background": "#80deea", "border": "#26c6da"}},
        "NPD": {"background": "#fff176", "border": "#ffeb3b", "highlight": {"background": "#fff59d", "border": "#ffeb3b"}},
        "CDP": {"background": "#4db6ac", "border": "#26a69a", "highlight": {"background": "#80cbc4", "border": "#26a69a"}},
        "LEGACY": {"background": "#a1887f", "border": "#8d6e63", "highlight": {"background": "#bcaaa4", "border": "#8d6e63"}},
    }
    
    # 필터링된 오브젝트 조회
    statement = select(IntegrationObject).where(IntegrationObject.status == "ACTIVE")
    
    if system_type:
        statement = statement.where(IntegrationObject.system_type == system_type)
    if layer:
        statement = statement.where(IntegrationObject.layer == layer)
    if module:
        statement = statement.where(IntegrationObject.module == module)
    
    objects = session.exec(statement).all()
    object_ids = {obj.id for obj in objects}
    
    # 필터링된 관계 조회 (양쪽 오브젝트가 모두 필터에 포함되어야 함)
    statement = select(IntegrationRelation).where(IntegrationRelation.status == "ACTIVE")
    all_relations = session.exec(statement).all()
    
    filtered_relations = [
        rel for rel in all_relations
        if rel.from_object_id in object_ids and rel.to_object_id in object_ids
    ]
    
    # 각 노드의 연결도 계산 (연결된 엣지 수)
    node_degrees = {}
    for rel in filtered_relations:
        node_degrees[rel.from_object_id] = node_degrees.get(rel.from_object_id, 0) + 1
        node_degrees[rel.to_object_id] = node_degrees.get(rel.to_object_id, 0) + 1
    
    # 노드 생성
    nodes = []
    for obj in objects:
        color = system_colors.get(obj.system_type, {"background": "#999999", "border": "#666666", "highlight": {"background": "#aaaaaa", "border": "#888888"}})
        degree = node_degrees.get(obj.id, 0)
        
        # 연결도에 따른 크기 계산 (20~60px 범위)
        size = max(30, min(60, 30 + degree * 3))
        
        nodes.append(NetworkNode(
            id=obj.id,
            label=f"{obj.name}\n[{obj.system_type}]",
            title=f"object_key: {obj.object_key}\n이름: {obj.name}\n시스템: {obj.system_type}\n타입: {obj.object_type}\n레이어: {obj.layer}\n모듈: {obj.module or 'N/A'}\n설명: {obj.description or 'N/A'}\n연결 수: {degree}개",
            group=obj.system_type,
            color=color,
            shape="box",
            font={"size": 16, "color": "#212121", "face": "Arial", "bold": True},  # 파스텔 톤에 맞게 어두운 텍스트
            size=size,
            degree=degree
        ))
    
    # 엣지 생성 (시스템 타입별 색상)
    edges = []
    for rel in filtered_relations:
        # 출발 노드의 시스템 타입 찾기
        from_obj = next((o for o in objects if o.id == rel.from_object_id), None)
        from_system = from_obj.system_type if from_obj else "UNKNOWN"
        
        # 시스템 타입별 엣지 색상
        edge_color = system_colors.get(from_system, {}).get("background", "#848484")
        
        edges.append(NetworkEdge(
            from_=rel.from_object_id,
            to=rel.to_object_id,
            arrows="to",
            smooth={"type": "continuous"},
            color={"color": edge_color, "highlight": "#ff0000"},
            width=2,
            from_system=from_system
        ))
    
    # 통계 정보
    stats = {
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "system_types": {}
    }
    
    for obj in objects:
        system = obj.system_type
        stats["system_types"][system] = stats["system_types"].get(system, 0) + 1
    
    return NetworkDataResponse(nodes=nodes, edges=edges, stats=stats)


@router.get("/{object_id}/network", response_model=NetworkDataResponse)
async def get_object_network(
    object_id: int,
    depth: int = Query(2, ge=1, le=2, description="탐색 깊이 (1 또는 2, 기본값 2)"),
    session: Session = Depends(get_session)
):
    """
    오브젝트 영향도 vis.js Network 데이터 생성 (JSON API)
    
    특정 오브젝트를 중심으로 한 영향도 그래프를 vis.js Network 형식으로 반환합니다.
    """
    try:
        graph = get_impact_graph(session, object_id, depth)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    # 시스템 타입별 색상 매핑 (부드러운 파스텔 톤)
    system_colors = {
        "SAP": {"background": "#81c784", "border": "#66bb6a", "highlight": {"background": "#a5d6a7", "border": "#66bb6a"}},
        "APLAN": {"background": "#64b5f6", "border": "#42a5f5", "highlight": {"background": "#90caf9", "border": "#42a5f5"}},
        "BW": {"background": "#ffb74d", "border": "#ffa726", "highlight": {"background": "#ffcc80", "border": "#ffa726"}},
        "BI": {"background": "#ba68c8", "border": "#ab47bc", "highlight": {"background": "#ce93d8", "border": "#ab47bc"}},
        "EAI": {"background": "#ef5350", "border": "#e53935", "highlight": {"background": "#ff8a80", "border": "#e53935"}},
        "IAM": {"background": "#4dd0e1", "border": "#26c6da", "highlight": {"background": "#80deea", "border": "#26c6da"}},
        "NPD": {"background": "#fff176", "border": "#ffeb3b", "highlight": {"background": "#fff59d", "border": "#ffeb3b"}},
        "CDP": {"background": "#4db6ac", "border": "#26a69a", "highlight": {"background": "#80cbc4", "border": "#26a69a"}},
        "LEGACY": {"background": "#a1887f", "border": "#8d6e63", "highlight": {"background": "#bcaaa4", "border": "#8d6e63"}},
    }
    
    # 모든 노드 수집
    all_nodes: List[IntegrationObject] = [graph.center_object]
    all_nodes.extend(graph.upstream)
    all_nodes.extend(graph.downstream)
    if depth == 2:
        all_nodes.extend(graph.upstream_level2)
        all_nodes.extend(graph.downstream_level2)
    
    # 중복 제거
    seen_ids: Set[int] = set()
    unique_nodes: List[IntegrationObject] = []
    for node in all_nodes:
        if node.id not in seen_ids:
            seen_ids.add(node.id)
            unique_nodes.append(node)
    
    # 각 노드의 연결도 계산
    node_degrees = {}
    center_id = graph.center_object.id
    
    # Upstream 엣지
    for upstream_obj in graph.upstream:
        node_degrees[upstream_obj.id] = node_degrees.get(upstream_obj.id, 0) + 1
        node_degrees[center_id] = node_degrees.get(center_id, 0) + 1
    
    # Downstream 엣지
    for downstream_obj in graph.downstream:
        node_degrees[center_id] = node_degrees.get(center_id, 0) + 1
        node_degrees[downstream_obj.id] = node_degrees.get(downstream_obj.id, 0) + 1
    
    # depth=2일 때 level2 엣지도 계산
    if depth == 2:
        for upstream_obj in graph.upstream:
            for upstream_level2_obj in graph.upstream_level2:
                statement = select(IntegrationRelation).where(
                    IntegrationRelation.from_object_id == upstream_level2_obj.id,
                    IntegrationRelation.to_object_id == upstream_obj.id,
                    IntegrationRelation.status == "ACTIVE"
                )
                rel = session.exec(statement).first()
                if rel:
                    node_degrees[upstream_level2_obj.id] = node_degrees.get(upstream_level2_obj.id, 0) + 1
                    node_degrees[upstream_obj.id] = node_degrees.get(upstream_obj.id, 0) + 1
        
        for downstream_obj in graph.downstream:
            for downstream_level2_obj in graph.downstream_level2:
                statement = select(IntegrationRelation).where(
                    IntegrationRelation.from_object_id == downstream_obj.id,
                    IntegrationRelation.to_object_id == downstream_level2_obj.id,
                    IntegrationRelation.status == "ACTIVE"
                )
                rel = session.exec(statement).first()
                if rel:
                    node_degrees[downstream_obj.id] = node_degrees.get(downstream_obj.id, 0) + 1
                    node_degrees[downstream_level2_obj.id] = node_degrees.get(downstream_level2_obj.id, 0) + 1
    
    # 노드 생성
    nodes = []
    for obj in unique_nodes:
        color = system_colors.get(obj.system_type, {"background": "#999999", "border": "#666666", "highlight": {"background": "#aaaaaa", "border": "#888888"}})
        is_center = obj.id == center_id
        degree = node_degrees.get(obj.id, 0)
        
        # 중심 오브젝트는 강조 (부드러운 파스텔 골드)
        if is_center:
            color = {"background": "#ffd54f", "border": "#ffc107", "highlight": {"background": "#ffe082", "border": "#ffc107"}}
            size = 70  # 중심 노드는 더 크게
        else:
            # 연결도에 따른 크기 계산 (30~60px 범위)
            size = max(30, min(60, 30 + degree * 3))
        
        nodes.append(NetworkNode(
            id=obj.id,
            label=f"{obj.name}\n[{obj.system_type}]",
            title=f"object_key: {obj.object_key}\n이름: {obj.name}\n시스템: {obj.system_type}\n타입: {obj.object_type}\n레이어: {obj.layer}\n모듈: {obj.module or 'N/A'}\n설명: {obj.description or 'N/A'}\n연결 수: {degree}개",
            group=obj.system_type,
            color=color,
            shape="box",
            font={"size": 16, "color": "#212121", "face": "Arial", "bold": True},  # 파스텔 톤에 맞게 어두운 텍스트
            size=size,
            degree=degree
        ))
    
    # 엣지 생성
    edges = []
    center_node_id = graph.center_object.id
    
    # Upstream 엣지
    for upstream_obj in graph.upstream:
        from_system = upstream_obj.system_type
        edge_color = system_colors.get(from_system, {}).get("background", "#848484")
        edges.append(NetworkEdge(
            from_=upstream_obj.id,
            to=center_node_id,
            arrows="to",
            smooth={"type": "continuous"},
            color={"color": edge_color, "highlight": "#ff0000"},
            width=2,
            from_system=from_system
        ))
    
    # Downstream 엣지
    for downstream_obj in graph.downstream:
        from_system = graph.center_object.system_type
        edge_color = system_colors.get(from_system, {}).get("background", "#848484")
        edges.append(NetworkEdge(
            from_=center_node_id,
            to=downstream_obj.id,
            arrows="to",
            smooth={"type": "continuous"},
            color={"color": edge_color, "highlight": "#ff0000"},
            width=2,
            from_system=from_system
        ))
    
    # depth=2일 때 level2 엣지
    if depth == 2:
        # Upstream level2 -> Upstream
        for upstream_obj in graph.upstream:
            for upstream_level2_obj in graph.upstream_level2:
                # 관계 확인
                statement = select(IntegrationRelation).where(
                    IntegrationRelation.from_object_id == upstream_level2_obj.id,
                    IntegrationRelation.to_object_id == upstream_obj.id,
                    IntegrationRelation.status == "ACTIVE"
                )
                rel = session.exec(statement).first()
                if rel:
                    from_system = upstream_level2_obj.system_type
                    edge_color = system_colors.get(from_system, {}).get("background", "#848484")
                    edges.append(NetworkEdge(
                        from_=upstream_level2_obj.id,
                        to=upstream_obj.id,
                        arrows="to",
                        smooth={"type": "continuous"},
                        color={"color": edge_color, "highlight": "#ff0000"},
                        width=2,
                        from_system=from_system
                    ))
        
        # Downstream -> Downstream level2
        for downstream_obj in graph.downstream:
            for downstream_level2_obj in graph.downstream_level2:
                # 관계 확인
                statement = select(IntegrationRelation).where(
                    IntegrationRelation.from_object_id == downstream_obj.id,
                    IntegrationRelation.to_object_id == downstream_level2_obj.id,
                    IntegrationRelation.status == "ACTIVE"
                )
                rel = session.exec(statement).first()
                if rel:
                    from_system = downstream_obj.system_type
                    edge_color = system_colors.get(from_system, {}).get("background", "#848484")
                    edges.append(NetworkEdge(
                        from_=downstream_obj.id,
                        to=downstream_level2_obj.id,
                        arrows="to",
                        smooth={"type": "continuous"},
                        color={"color": edge_color, "highlight": "#ff0000"},
                        width=2,
                        from_system=from_system
                    ))
    
    # 통계 정보
    stats = {
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "upstream_count": len(graph.upstream),
        "downstream_count": len(graph.downstream),
        "center_object_id": center_id
    }
    
    return NetworkDataResponse(nodes=nodes, edges=edges, stats=stats)


@router.get("/overview/mermaid", response_model=MermaidResponse)
async def get_overview_mermaid(
    session: Session = Depends(get_session)
):
    """
    전체 시스템 맵 Mermaid 코드 생성 (JSON API)
    """
    from app.services.impact_service import generate_full_map_mermaid_code
    
    mermaid_code = generate_full_map_mermaid_code(session)
    return MermaidResponse(mermaid_code=mermaid_code)
