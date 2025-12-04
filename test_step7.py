"""
7단계 테스트: API 라우터
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from fastapi.testclient import TestClient
from sqlmodel import Session
from app.main import app
from app.database import engine, init_db
from app.models import IntegrationObject, IntegrationRelation


def setup_test_data(session: Session):
    """테스트용 데이터 생성"""
    obj1 = IntegrationObject(
        object_key="TEST_IF_001",
        name="테스트 인터페이스 1",
        system_type="APLAN",
        object_type="IF",
        layer="In",
        description="테스트용 인터페이스",
        module="테스트",
        status="ACTIVE"
    )
    obj2 = IntegrationObject(
        object_key="SAP_TABLE_001",
        name="SAP 테이블 1",
        system_type="SAP",
        object_type="TABLE",
        layer="Legacy",
        module="테스트",
        status="ACTIVE"
    )
    obj3 = IntegrationObject(
        object_key="BW_CUBE_001",
        name="BW 큐브 1",
        system_type="BW",
        object_type="CUBE",
        layer="Legacy",
        status="ACTIVE"
    )
    
    session.add_all([obj1, obj2, obj3])
    session.flush()
    
    # 관계 생성
    rel = IntegrationRelation(
        from_object_id=obj2.id,
        to_object_id=obj1.id,
        relation_type="FLOWS_TO",
        status="ACTIVE"
    )
    session.add(rel)
    session.commit()
    
    return obj1.id, obj2.id, obj3.id


def test_get_objects():
    """GET /objects 테스트"""
    print("=" * 50)
    print("7-1. GET /objects 테스트")
    print("=" * 50)
    
    # 기존 세션 닫기
    engine.dispose()
    
    # DB 초기화
    from pathlib import Path
    import time
    db_file = Path("impact_map.db")
    if db_file.exists():
        try:
            db_file.unlink()
        except:
            time.sleep(0.1)
            try:
                db_file.unlink()
            except:
                pass
    init_db()
    
    # 테스트 데이터 생성
    with Session(engine) as session:
        obj1_id, obj2_id, obj3_id = setup_test_data(session)
    
    client = TestClient(app)
    
    # 전체 조회
    response = client.get("/objects")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3
    print(f"✅ 전체 조회 성공: {len(data)}개")
    
    # 키워드 검색
    response = client.get("/objects?q=테스트")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    print(f"✅ 키워드 검색 성공: {len(data)}개")
    
    # system_type 필터
    response = client.get("/objects?system_type=SAP")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert all(obj["system_type"] == "SAP" for obj in data)
    print(f"✅ system_type 필터 성공: {len(data)}개")
    
    # object_type 필터
    response = client.get("/objects?object_type=IF")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert all(obj["object_type"] == "IF" for obj in data)
    print(f"✅ object_type 필터 성공: {len(data)}개")
    
    print("✅ GET /objects 테스트 통과")
    return True


def test_get_object():
    """GET /objects/{object_id} 테스트"""
    print("\n" + "=" * 50)
    print("7-2. GET /objects/{object_id} 테스트")
    print("=" * 50)
    
    # 기존 세션 닫기
    engine.dispose()
    
    # DB 초기화
    from pathlib import Path
    import time
    db_file = Path("impact_map.db")
    if db_file.exists():
        try:
            db_file.unlink()
        except:
            time.sleep(0.1)
            try:
                db_file.unlink()
            except:
                pass
    init_db()
    
    # 테스트 데이터 생성
    with Session(engine) as session:
        obj1_id, obj2_id, obj3_id = setup_test_data(session)
    
    client = TestClient(app)
    
    # 정상 조회
    response = client.get(f"/objects/{obj1_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == obj1_id
    assert data["object_key"] == "TEST_IF_001"
    print(f"✅ 오브젝트 조회 성공: {data['name']}")
    
    # 존재하지 않는 ID
    response = client.get("/objects/99999")
    assert response.status_code == 404
    print("✅ 404 에러 처리 확인")
    
    print("✅ GET /objects/{object_id} 테스트 통과")
    return True


def test_get_object_impact():
    """GET /objects/{object_id}/impact 테스트"""
    print("\n" + "=" * 50)
    print("7-3. GET /objects/{object_id}/impact 테스트")
    print("=" * 50)
    
    # 기존 세션 닫기
    engine.dispose()
    
    # DB 초기화
    from pathlib import Path
    import time
    db_file = Path("impact_map.db")
    if db_file.exists():
        try:
            db_file.unlink()
        except:
            time.sleep(0.1)
            try:
                db_file.unlink()
            except:
                pass
    init_db()
    
    # 테스트 데이터 생성
    with Session(engine) as session:
        obj1_id, obj2_id, obj3_id = setup_test_data(session)
    
    client = TestClient(app)
    
    # depth=1 테스트
    response = client.get(f"/objects/{obj1_id}/impact?depth=1")
    assert response.status_code == 200
    data = response.json()
    assert "object" in data
    assert "upstream" in data
    assert "downstream" in data
    assert data["object"]["id"] == obj1_id
    assert len(data["upstream"]) >= 1  # obj2가 upstream
    print(f"✅ depth=1 영향도 조회 성공: upstream {len(data['upstream'])}, downstream {len(data['downstream'])}")
    
    # depth=2 테스트
    response = client.get(f"/objects/{obj1_id}/impact?depth=2")
    assert response.status_code == 200
    data = response.json()
    assert "object" in data
    assert "upstream" in data
    assert "downstream" in data
    print(f"✅ depth=2 영향도 조회 성공: upstream {len(data['upstream'])}, downstream {len(data['downstream'])}")
    
    # 존재하지 않는 ID
    response = client.get("/objects/99999/impact")
    assert response.status_code == 404
    print("✅ 404 에러 처리 확인")
    
    print("✅ GET /objects/{object_id}/impact 테스트 통과")
    return True


def test_get_object_mermaid():
    """GET /objects/{object_id}/mermaid 테스트"""
    print("\n" + "=" * 50)
    print("7-4. GET /objects/{object_id}/mermaid 테스트")
    print("=" * 50)
    
    # 기존 세션 닫기
    engine.dispose()
    
    # DB 초기화
    from pathlib import Path
    import time
    db_file = Path("impact_map.db")
    if db_file.exists():
        try:
            db_file.unlink()
        except:
            time.sleep(0.1)
            try:
                db_file.unlink()
            except:
                pass
    init_db()
    
    # 테스트 데이터 생성
    with Session(engine) as session:
        obj1_id, obj2_id, obj3_id = setup_test_data(session)
    
    client = TestClient(app)
    
    # Mermaid 코드 생성 테스트
    response = client.get(f"/objects/{obj1_id}/mermaid?depth=2")
    assert response.status_code == 200
    data = response.json()
    assert "mermaid_code" in data
    assert "flowchart LR" in data["mermaid_code"]
    assert "TEST_IF_001" in data["mermaid_code"] or "CENTER_OBJ" in data["mermaid_code"]
    print("✅ Mermaid 코드 생성 성공")
    print(f"생성된 코드 길이: {len(data['mermaid_code'])} 문자")
    
    # 존재하지 않는 ID
    response = client.get("/objects/99999/mermaid")
    assert response.status_code == 404
    print("✅ 404 에러 처리 확인")
    
    print("✅ GET /objects/{object_id}/mermaid 테스트 통과")
    return True


def main():
    """메인 테스트 실행"""
    print("\n" + "=" * 50)
    print("7단계: API 라우터 테스트")
    print("=" * 50)
    
    results = []
    results.append(("GET /objects", test_get_objects()))
    results.append(("GET /objects/{id}", test_get_object()))
    results.append(("GET /objects/{id}/impact", test_get_object_impact()))
    results.append(("GET /objects/{id}/mermaid", test_get_object_mermaid()))
    
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
        print("🎉 7단계 테스트 모두 통과!")
    else:
        print("⚠️  일부 테스트 실패")
    print("=" * 50)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

