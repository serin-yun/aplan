"""
영향도 분석 서비스

MRD 9장 요구사항:
- 그래프 탐색: depth 1~2까지 지원
- Mermaid 다이어그램 생성: flowchart LR 형식
"""

from typing import List, Dict, Set, Tuple
from sqlmodel import Session, select
from app.models import IntegrationObject, IntegrationRelation


class ImpactGraph:
    """영향도 그래프 데이터 구조"""
    def __init__(self, center_object: IntegrationObject):
        self.center_object = center_object
        self.upstream: List[IntegrationObject] = []
        self.downstream: List[IntegrationObject] = []
        self.upstream_level2: List[IntegrationObject] = []  # depth=2일 때만 사용
        self.downstream_level2: List[IntegrationObject] = []  # depth=2일 때만 사용


def get_impact_graph(session: Session, object_id: int, depth: int = 1) -> ImpactGraph:
    """
    특정 오브젝트 기준 영향도 그래프 탐색
    
    MRD 9.1 요구사항:
    - depth=1: 직접 연결된 상하위만 탐색
      - outgoing_relations → downstream
      - incoming_relations → upstream
    - depth=2: upstream/downstream의 한 단계 이웃까지 확장
    
    Args:
        session: 데이터베이스 세션
        object_id: 중심 오브젝트 ID
        depth: 탐색 깊이 (1 또는 2)
    
    Returns:
        ImpactGraph: 중심 오브젝트와 upstream/downstream 리스트
    """
    if depth not in [1, 2]:
        raise ValueError("depth는 1 또는 2만 허용됩니다")
    
    # 중심 오브젝트 조회
    statement = select(IntegrationObject).where(IntegrationObject.id == object_id)
    center_object = session.exec(statement).first()
    if not center_object:
        raise ValueError(f"오브젝트 ID {object_id}를 찾을 수 없습니다")
    
    graph = ImpactGraph(center_object)
    
    # depth=1: 직접 연결된 관계 탐색
    # Upstream: 이 오브젝트로 들어오는 관계 (incoming_relations)
    statement = select(IntegrationRelation).where(
        IntegrationRelation.to_object_id == object_id,
        IntegrationRelation.status == "ACTIVE"
    )
    incoming_relations = session.exec(statement).all()
    
    upstream_ids: Set[int] = set()
    for rel in incoming_relations:
        statement = select(IntegrationObject).where(IntegrationObject.id == rel.from_object_id)
        upstream_obj = session.exec(statement).first()
        if upstream_obj and upstream_obj.status == "ACTIVE":
            graph.upstream.append(upstream_obj)
            upstream_ids.add(upstream_obj.id)
    
    # Downstream: 이 오브젝트에서 나가는 관계 (outgoing_relations)
    statement = select(IntegrationRelation).where(
        IntegrationRelation.from_object_id == object_id,
        IntegrationRelation.status == "ACTIVE"
    )
    outgoing_relations = session.exec(statement).all()
    
    downstream_ids: Set[int] = set()
    for rel in outgoing_relations:
        statement = select(IntegrationObject).where(IntegrationObject.id == rel.to_object_id)
        downstream_obj = session.exec(statement).first()
        if downstream_obj and downstream_obj.status == "ACTIVE":
            graph.downstream.append(downstream_obj)
            downstream_ids.add(downstream_obj.id)
    
    # depth=2: 한 단계 더 확장
    if depth == 2:
        # Upstream의 upstream 탐색
        for upstream_id in upstream_ids:
            statement = select(IntegrationRelation).where(
                IntegrationRelation.to_object_id == upstream_id,
                IntegrationRelation.status == "ACTIVE"
            )
            upstream_relations = session.exec(statement).all()
            for rel in upstream_relations:
                if rel.from_object_id not in upstream_ids and rel.from_object_id != object_id:
                    statement = select(IntegrationObject).where(IntegrationObject.id == rel.from_object_id)
                    upstream_level2_obj = session.exec(statement).first()
                    if upstream_level2_obj and upstream_level2_obj.status == "ACTIVE":
                        if upstream_level2_obj not in graph.upstream_level2:
                            graph.upstream_level2.append(upstream_level2_obj)
        
        # Downstream의 downstream 탐색
        for downstream_id in downstream_ids:
            statement = select(IntegrationRelation).where(
                IntegrationRelation.from_object_id == downstream_id,
                IntegrationRelation.status == "ACTIVE"
            )
            downstream_relations = session.exec(statement).all()
            for rel in downstream_relations:
                if rel.to_object_id not in downstream_ids and rel.to_object_id != object_id:
                    statement = select(IntegrationObject).where(IntegrationObject.id == rel.to_object_id)
                    downstream_level2_obj = session.exec(statement).first()
                    if downstream_level2_obj and downstream_level2_obj.status == "ACTIVE":
                        if downstream_level2_obj not in graph.downstream_level2:
                            graph.downstream_level2.append(downstream_level2_obj)
    
    return graph


def generate_mermaid_code(session: Session, object_id: int, depth: int = 2) -> str:
    """
    Mermaid 다이어그램 텍스트 생성
    
    MRD 9.2 요구사항:
    - 포맷: flowchart LR
    - 노드 라벨: "시스템타입\n오브젝트명" 형식
    - 중심 오브젝트는 별도 스타일 적용 가능
    
    Args:
        session: 데이터베이스 세션
        object_id: 중심 오브젝트 ID
        depth: 탐색 깊이 (기본값 2)
    
    Returns:
        str: Mermaid 다이어그램 코드
    """
    graph = get_impact_graph(session, object_id, depth)
    
    # 노드 ID 생성 함수 (Mermaid에서 사용할 안전한 ID)
    def safe_node_id(obj: IntegrationObject) -> str:
        """오브젝트를 Mermaid 노드 ID로 변환 (공백, 특수문자 제거)"""
        return obj.object_key.replace("-", "_").replace(".", "_").replace(" ", "_")
    
    # 노드 라벨 생성 함수
    def node_label(obj: IntegrationObject) -> str:
        """오브젝트를 Mermaid 노드 라벨로 변환"""
        # "시스템타입\n오브젝트명" 형식
        return f"{obj.system_type}\\n{obj.name}"
    
    lines = ["flowchart LR"]
    
    # 모든 노드 수집
    all_nodes: List[IntegrationObject] = [graph.center_object]
    all_nodes.extend(graph.upstream)
    all_nodes.extend(graph.downstream)
    if depth == 2:
        all_nodes.extend(graph.upstream_level2)
        all_nodes.extend(graph.downstream_level2)
    
    # 중복 제거 (ID 기준)
    seen_ids: Set[int] = set()
    unique_nodes: List[IntegrationObject] = []
    for node in all_nodes:
        if node.id not in seen_ids:
            seen_ids.add(node.id)
            unique_nodes.append(node)
    
    # 노드 정의
    center_node_id = safe_node_id(graph.center_object)
    for node in unique_nodes:
        node_id = safe_node_id(node)
        label = node_label(node)
        if node.id == graph.center_object.id:
            # 중심 오브젝트는 별도 스타일 적용
            lines.append(f'  {node_id}["{label}"]:::center')
        else:
            lines.append(f'  {node_id}["{label}"]')
    
    # 엣지 정의
    # Upstream 엣지 (역방향으로 표시: upstream -> center)
    for upstream_obj in graph.upstream:
        upstream_id = safe_node_id(upstream_obj)
        lines.append(f'  {upstream_id} --> {center_node_id}')
    
    # Downstream 엣지 (정방향으로 표시: center -> downstream)
    for downstream_obj in graph.downstream:
        downstream_id = safe_node_id(downstream_obj)
        lines.append(f'  {center_node_id} --> {downstream_id}')
    
    # depth=2일 때 level2 엣지
    if depth == 2:
        # Upstream level2 -> Upstream
        for upstream_obj in graph.upstream:
            upstream_id = safe_node_id(upstream_obj)
            for upstream_level2_obj in graph.upstream_level2:
                # upstream_level2_obj가 upstream_obj의 upstream인지 확인
                statement = select(IntegrationRelation).where(
                    IntegrationRelation.from_object_id == upstream_level2_obj.id,
                    IntegrationRelation.to_object_id == upstream_obj.id,
                    IntegrationRelation.status == "ACTIVE"
                )
                rel = session.exec(statement).first()
                if rel:
                    upstream_level2_id = safe_node_id(upstream_level2_obj)
                    lines.append(f'  {upstream_level2_id} --> {upstream_id}')
        
        # Downstream -> Downstream level2
        for downstream_obj in graph.downstream:
            downstream_id = safe_node_id(downstream_obj)
            for downstream_level2_obj in graph.downstream_level2:
                # downstream_obj가 downstream_level2_obj의 upstream인지 확인
                statement = select(IntegrationRelation).where(
                    IntegrationRelation.from_object_id == downstream_obj.id,
                    IntegrationRelation.to_object_id == downstream_level2_obj.id,
                    IntegrationRelation.status == "ACTIVE"
                )
                rel = session.exec(statement).first()
                if rel:
                    downstream_level2_id = safe_node_id(downstream_level2_obj)
                    lines.append(f'  {downstream_id} --> {downstream_level2_id}')
    
    # 중심 오브젝트 스타일 정의
    lines.append("")
    lines.append('  classDef center fill:#ffeb3b,stroke:#f57f17,stroke-width:3px')
    
    return "\n".join(lines)


def generate_full_map_mermaid_code(session: Session) -> str:
    """
    전체 시스템 맵 Mermaid 다이어그램 생성
    
    모든 오브젝트와 관계를 한눈에 볼 수 있는 전체 맵을 생성합니다.
    
    Args:
        session: 데이터베이스 세션
    
    Returns:
        str: Mermaid 다이어그램 코드
    """
    # 모든 ACTIVE 오브젝트 조회
    statement = select(IntegrationObject).where(IntegrationObject.status == "ACTIVE")
    all_objects = session.exec(statement).all()
    
    if not all_objects:
        return "flowchart LR\n  Empty[\"데이터가 없습니다\"]"
    
    # 모든 ACTIVE 관계 조회
    statement = select(IntegrationRelation).where(IntegrationRelation.status == "ACTIVE")
    all_relations = session.exec(statement).all()
    
    # 노드 ID 생성 함수
    def safe_node_id(obj: IntegrationObject) -> str:
        """오브젝트를 Mermaid 노드 ID로 변환"""
        return obj.object_key.replace("-", "_").replace(".", "_").replace(" ", "_")
    
    # 노드 라벨 생성 함수
    def node_label(obj: IntegrationObject) -> str:
        """오브젝트를 Mermaid 노드 라벨로 변환"""
        return f"{obj.system_type}\\n{obj.name}"
    
    # 시스템 타입별 색상 매핑
    system_colors = {
        "SAP": "fill:#0f7b0f,stroke:#0a5a0a,stroke-width:2px,color:#fff",
        "APLAN": "fill:#0066cc,stroke:#004499,stroke-width:2px,color:#fff",
        "BW": "fill:#ff6600,stroke:#cc5200,stroke-width:2px,color:#fff",
        "BI": "fill:#9900cc,stroke:#7700aa,stroke-width:2px,color:#fff",
        "EAI": "fill:#cc0000,stroke:#990000,stroke-width:2px,color:#fff",
        "IAM": "fill:#009999,stroke:#007777,stroke-width:2px,color:#fff",
        "NPD": "fill:#cc9900,stroke:#997700,stroke-width:2px,color:#fff",
        "CDP": "fill:#00cc99,stroke:#00aa77,stroke-width:2px,color:#fff",
        "LEGACY": "fill:#666666,stroke:#444444,stroke-width:2px,color:#fff",
    }
    
    lines = ["flowchart TB"]  # Top to Bottom (전체 맵은 세로 방향이 더 보기 좋음)
    
    # 오브젝트를 시스템 타입별로 그룹화
    objects_by_system = {}
    for obj in all_objects:
        system = obj.system_type
        if system not in objects_by_system:
            objects_by_system[system] = []
        objects_by_system[system].append(obj)
    
    # 노드 정의 (시스템 타입별로 그룹화하여 정의)
    node_ids = set()
    for system_type, objects in objects_by_system.items():
        for obj in objects:
            node_id = safe_node_id(obj)
            if node_id not in node_ids:
                node_ids.add(node_id)
                label = node_label(obj)
                color_class = f"system_{system_type.lower()}"
                lines.append(f'  {node_id}["{label}"]:::{color_class}')
    
    # 관계 정의
    relation_set = set()  # 중복 관계 방지
    for rel in all_relations:
        # from_object와 to_object 조회
        from_obj = session.exec(select(IntegrationObject).where(IntegrationObject.id == rel.from_object_id)).first()
        to_obj = session.exec(select(IntegrationObject).where(IntegrationObject.id == rel.to_object_id)).first()
        
        if from_obj and to_obj and from_obj.status == "ACTIVE" and to_obj.status == "ACTIVE":
            from_id = safe_node_id(from_obj)
            to_id = safe_node_id(to_obj)
            relation_key = (from_id, to_id)
            
            if relation_key not in relation_set:
                relation_set.add(relation_key)
                lines.append(f'  {from_id} --> {to_id}')
    
    # 시스템 타입별 스타일 정의
    lines.append("")
    for system_type, color_style in system_colors.items():
        class_name = f"system_{system_type.lower()}"
        lines.append(f'  classDef {class_name} {color_style}')
    
    return "\n".join(lines)

