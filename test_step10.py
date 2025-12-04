"""
10단계 테스트: 전체 기능 통합 테스트
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from fastapi.testclient import TestClient
from app.main import app


def test_full_integration():
    """전체 기능 통합 테스트"""
    print("=" * 50)
    print("10단계: 전체 기능 통합 테스트")
    print("=" * 50)
    
    client = TestClient(app)
    
    # 1. 검색 화면 접근
    print("\n1. 검색 화면 테스트")
    response = client.get("/objects")
    assert response.status_code == 200
    assert "APlan Integration Impact Map" in response.text
    assert "오브젝트 검색" in response.text
    print("   ✅ 검색 화면 렌더링 성공")
    
    # 2. 검색 기능 테스트
    print("\n2. 검색 기능 테스트")
    response = client.get("/objects?q=매출")
    assert response.status_code == 200
    assert "매출" in response.text
    print("   ✅ 키워드 검색 동작 확인")
    
    response = client.get("/objects?system_type=SAP")
    assert response.status_code == 200
    print("   ✅ system_type 필터 동작 확인")
    
    # 3. API 엔드포인트 테스트
    print("\n3. API 엔드포인트 테스트")
    response = client.get("/objects/api")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    print(f"   ✅ GET /objects/api: {len(data)}개 결과")
    
    # 첫 번째 오브젝트 ID 가져오기
    first_obj_id = data[0]["id"]
    
    # 4. 상세 화면 테스트
    print("\n4. 상세 화면 테스트")
    response = client.get(f"/objects/{first_obj_id}")
    assert response.status_code == 200
    assert "영향도 분석" in response.text
    assert "영향도 다이어그램" in response.text
    print("   ✅ 상세 화면 렌더링 성공")
    
    # 5. 영향도 API 테스트
    print("\n5. 영향도 API 테스트")
    response = client.get(f"/objects/{first_obj_id}/impact?depth=2")
    assert response.status_code == 200
    data = response.json()
    assert "object" in data
    assert "upstream" in data
    assert "downstream" in data
    print(f"   ✅ 영향도 정보: upstream {len(data['upstream'])}, downstream {len(data['downstream'])}")
    
    # 6. Mermaid API 테스트
    print("\n6. Mermaid API 테스트")
    response = client.get(f"/objects/{first_obj_id}/mermaid?depth=2")
    assert response.status_code == 200
    data = response.json()
    assert "mermaid_code" in data
    assert "flowchart LR" in data["mermaid_code"]
    print("   ✅ Mermaid 코드 생성 성공")
    
    # 7. 상세 화면에서 Mermaid 다이어그램 확인
    print("\n7. 상세 화면 Mermaid 다이어그램 확인")
    response = client.get(f"/objects/{first_obj_id}?depth=2")
    assert response.status_code == 200
    assert "flowchart LR" in response.text
    assert "mermaid" in response.text.lower()
    print("   ✅ Mermaid 다이어그램 영역 확인")
    
    print("\n" + "=" * 50)
    print("🎉 전체 기능 통합 테스트 통과!")
    print("=" * 50)
    print("\n서버 실행 명령어:")
    print("  uvicorn app.main:app --reload")
    print("\n브라우저 접속:")
    print("  http://localhost:8000/objects")
    print("\nAPI 문서:")
    print("  http://localhost:8000/docs")
    
    return True


if __name__ == "__main__":
    try:
        success = test_full_integration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

