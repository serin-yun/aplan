"""
8-9단계 테스트: 템플릿 및 라우터 연결
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
    
    session.add_all([obj1, obj2])
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
    
    return obj1.id, obj2.id


def test_index_template():
    """검색 화면 템플릿 테스트"""
    print("=" * 50)
    print("8-9-1. 검색 화면 템플릿 테스트")
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
        obj1_id, obj2_id = setup_test_data(session)
    
    client = TestClient(app)
    
    # 검색 화면 접근
    response = client.get("/objects")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "APlan Integration Impact Map" in response.text
    assert "오브젝트 검색" in response.text
    print("✅ 검색 화면 렌더링 성공")
    
    # 검색 결과 확인
    assert "TEST_IF_001" in response.text or "SAP_TABLE_001" in response.text
    print("✅ 검색 결과 표시 확인")
    
    return True


def test_object_detail_template():
    """상세 화면 템플릿 테스트"""
    print("\n" + "=" * 50)
    print("8-9-2. 상세 화면 템플릿 테스트")
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
        obj1_id, obj2_id = setup_test_data(session)
    
    client = TestClient(app)
    
    # 상세 화면 접근
    response = client.get(f"/objects/{obj1_id}")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "테스트 인터페이스 1" in response.text
    assert "TEST_IF_001" in response.text
    print("✅ 상세 화면 렌더링 성공")
    
    # 영향도 정보 확인
    assert "영향도 분석" in response.text
    assert "Upstream" in response.text
    assert "Downstream" in response.text
    print("✅ 영향도 정보 표시 확인")
    
    # Mermaid 다이어그램 확인
    assert "영향도 다이어그램" in response.text
    assert "flowchart LR" in response.text
    assert "mermaid" in response.text.lower()
    print("✅ Mermaid 다이어그램 영역 확인")
    
    return True


def main():
    """메인 테스트 실행"""
    print("\n" + "=" * 50)
    print("8-9단계: 템플릿 및 라우터 연결 테스트")
    print("=" * 50)
    
    results = []
    results.append(("검색 화면 템플릿", test_index_template()))
    results.append(("상세 화면 템플릿", test_object_detail_template()))
    
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
        print("🎉 8-9단계 테스트 모두 통과!")
        print("\n서버 실행 명령어:")
        print("  uvicorn app.main:app --reload")
        print("\n브라우저에서 접속:")
        print("  http://localhost:8000/objects")
    else:
        print("⚠️  일부 테스트 실패")
    print("=" * 50)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

