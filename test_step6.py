"""
6단계 테스트: 영향도 분석 서비스
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlmodel import Session
from app.database import engine, init_db
from app.models import IntegrationObject, IntegrationRelation
from app.services.impact_service import get_impact_graph, generate_mermaid_code


def setup_test_data(session: Session):
    """테스트용 데이터 생성"""
    # 중심 오브젝트
    center = IntegrationObject(
        object_key="CENTER_OBJ",
        name="중심 오브젝트",
        system_type="APLAN",
        object_type="IF",
        layer="In",
        status="ACTIVE"
    )
    session.add(center)
    session.flush()
    
    # Upstream 오브젝트들
    upstream1 = IntegrationObject(
        object_key="UPSTREAM_1",
        name="Upstream 1",
        system_type="SAP",
        object_type="TABLE",
        layer="Legacy",
        status="ACTIVE"
    )
    upstream2 = IntegrationObject(
        object_key="UPSTREAM_2",
        name="Upstream 2",
        system_type="BW",
        object_type="CUBE",
        layer="Legacy",
        status="ACTIVE"
    )
    session.add(upstream1)
    session.add(upstream2)
    session.flush()
    
    # Downstream 오브젝트들
    downstream1 = IntegrationObject(
        object_key="DOWNSTREAM_1",
        name="Downstream 1",
        system_type="APLAN",
        object_type="TABLE",
        layer="Staging",
        status="ACTIVE"
    )
    downstream2 = IntegrationObject(
        object_key="DOWNSTREAM_2",
        name="Downstream 2",
        system_type="BI",
        object_type="REPORT",
        layer="Out",
        status="ACTIVE"
    )
    session.add(downstream1)
    session.add(downstream2)
    session.flush()
    
    # Level 2 오브젝트들 (depth=2 테스트용)
    upstream_level2 = IntegrationObject(
        object_key="UPSTREAM_L2",
        name="Upstream Level 2",
        system_type="LEGACY",
        object_type="TABLE",
        layer="Legacy",
        status="ACTIVE"
    )
    downstream_level2 = IntegrationObject(
        object_key="DOWNSTREAM_L2",
        name="Downstream Level 2",
        system_type="CDP",
        object_type="VIEW",
        layer="Out",
        status="ACTIVE"
    )
    session.add(upstream_level2)
    session.add(downstream_level2)
    session.flush()
    
    # 관계 생성
    # Upstream -> Center
    rel1 = IntegrationRelation(
        from_object_id=upstream1.id,
        to_object_id=center.id,
        relation_type="FLOWS_TO",
        status="ACTIVE"
    )
    rel2 = IntegrationRelation(
        from_object_id=upstream2.id,
        to_object_id=center.id,
        relation_type="FLOWS_TO",
        status="ACTIVE"
    )
    # Center -> Downstream
    rel3 = IntegrationRelation(
        from_object_id=center.id,
        to_object_id=downstream1.id,
        relation_type="FLOWS_TO",
        status="ACTIVE"
    )
    rel4 = IntegrationRelation(
        from_object_id=center.id,
        to_object_id=downstream2.id,
        relation_type="FLOWS_TO",
        status="ACTIVE"
    )
    # Level 2 관계
    rel5 = IntegrationRelation(
        from_object_id=upstream_level2.id,
        to_object_id=upstream1.id,
        relation_type="FLOWS_TO",
        status="ACTIVE"
    )
    rel6 = IntegrationRelation(
        from_object_id=downstream1.id,
        to_object_id=downstream_level2.id,
        relation_type="FLOWS_TO",
        status="ACTIVE"
    )
    
    session.add_all([rel1, rel2, rel3, rel4, rel5, rel6])
    session.commit()
    
    return center.id


def test_impact_graph_depth1():
    """depth=1 그래프 탐색 테스트"""
    print("=" * 50)
    print("6-1. depth=1 그래프 탐색 테스트")
    print("=" * 50)
    
    # 기존 세션 모두 닫기
    engine.dispose()
    
    # 기존 DB 초기화
    from pathlib import Path
    import time
    db_file = Path("impact_map.db")
    if db_file.exists():
        try:
            db_file.unlink()
        except PermissionError:
            time.sleep(0.1)
            try:
                db_file.unlink()
            except:
                pass
    init_db()
    
    with Session(engine) as session:
        center_id = setup_test_data(session)
        
        graph = get_impact_graph(session, center_id, depth=1)
        
        print(f"✅ 중심 오브젝트: {graph.center_object.object_key}")
        print(f"✅ Upstream 개수: {len(graph.upstream)} (예상: 2)")
        print(f"✅ Downstream 개수: {len(graph.downstream)} (예상: 2)")
        
        if len(graph.upstream) != 2:
            print(f"❌ Upstream 개수 불일치: {len(graph.upstream)}")
            return False
        
        if len(graph.downstream) != 2:
            print(f"❌ Downstream 개수 불일치: {len(graph.downstream)}")
            return False
        
        print("✅ depth=1 테스트 통과")
        return True


def test_impact_graph_depth2():
    """depth=2 그래프 탐색 테스트"""
    print("\n" + "=" * 50)
    print("6-2. depth=2 그래프 탐색 테스트")
    print("=" * 50)
    
    # 기존 세션 모두 닫기
    engine.dispose()
    
    # 기존 DB 초기화
    from pathlib import Path
    import time
    db_file = Path("impact_map.db")
    if db_file.exists():
        try:
            db_file.unlink()
        except PermissionError:
            time.sleep(0.1)
            try:
                db_file.unlink()
            except:
                pass
    init_db()
    
    with Session(engine) as session:
        center_id = setup_test_data(session)
        
        graph = get_impact_graph(session, center_id, depth=2)
        
        print(f"✅ 중심 오브젝트: {graph.center_object.object_key}")
        print(f"✅ Upstream 개수: {len(graph.upstream)} (예상: 2)")
        print(f"✅ Downstream 개수: {len(graph.downstream)} (예상: 2)")
        print(f"✅ Upstream Level 2 개수: {len(graph.upstream_level2)} (예상: 1)")
        print(f"✅ Downstream Level 2 개수: {len(graph.downstream_level2)} (예상: 1)")
        
        if len(graph.upstream_level2) != 1:
            print(f"❌ Upstream Level 2 개수 불일치: {len(graph.upstream_level2)}")
            return False
        
        if len(graph.downstream_level2) != 1:
            print(f"❌ Downstream Level 2 개수 불일치: {len(graph.downstream_level2)}")
            return False
        
        print("✅ depth=2 테스트 통과")
        return True


def test_mermaid_generation():
    """Mermaid 코드 생성 테스트"""
    print("\n" + "=" * 50)
    print("6-3. Mermaid 코드 생성 테스트")
    print("=" * 50)
    
    # 기존 세션 모두 닫기
    engine.dispose()
    
    # 기존 DB 초기화
    from pathlib import Path
    import time
    db_file = Path("impact_map.db")
    if db_file.exists():
        try:
            db_file.unlink()
        except PermissionError:
            time.sleep(0.1)
            try:
                db_file.unlink()
            except:
                pass
    init_db()
    
    with Session(engine) as session:
        center_id = setup_test_data(session)
        
        mermaid_code = generate_mermaid_code(session, center_id, depth=2)
        
        print("생성된 Mermaid 코드:")
        print("-" * 50)
        print(mermaid_code)
        print("-" * 50)
        
        # 기본 검증
        if "flowchart LR" not in mermaid_code:
            print("❌ flowchart LR 형식이 아님")
            return False
        
        if "CENTER_OBJ" not in mermaid_code:
            print("❌ 중심 오브젝트가 포함되지 않음")
            return False
        
        if "UPSTREAM_1" not in mermaid_code:
            print("❌ Upstream 오브젝트가 포함되지 않음")
            return False
        
        if "DOWNSTREAM_1" not in mermaid_code:
            print("❌ Downstream 오브젝트가 포함되지 않음")
            return False
        
        if "classDef center" not in mermaid_code:
            print("❌ 중심 오브젝트 스타일이 포함되지 않음")
            return False
        
        print("✅ Mermaid 코드 생성 테스트 통과")
        return True


def main():
    """메인 테스트 실행"""
    print("\n" + "=" * 50)
    print("6단계: 영향도 분석 서비스 테스트")
    print("=" * 50)
    
    results = []
    results.append(("depth=1 그래프 탐색", test_impact_graph_depth1()))
    results.append(("depth=2 그래프 탐색", test_impact_graph_depth2()))
    results.append(("Mermaid 코드 생성", test_mermaid_generation()))
    
    # 결과 요약
    print("\n" + "=" * 50)
    print("테스트 결과 요약")
    print("=" * 50)
    for name, result in results:
        status = "✅ 통과" if result else "❌ 실패"
        print(f"{name}: {status}")
    
    all_passed = all(result for _, result in results)
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 6단계 테스트 모두 통과!")
    else:
        print("⚠️  일부 테스트 실패")
    print("=" * 50)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

