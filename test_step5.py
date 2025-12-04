"""
5단계 테스트: FastAPI 메인 앱 설정
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def test_fastapi_app():
    """FastAPI 앱 생성 및 기본 설정 테스트"""
    print("=" * 50)
    print("5단계: FastAPI 메인 앱 테스트")
    print("=" * 50)
    
    try:
        from app.main import app
        print("✅ FastAPI 앱 import 성공")
        
        # 앱 정보 확인
        print(f"✅ 앱 제목: {app.title}")
        print(f"✅ 앱 버전: {app.version}")
        
        # 라우터 확인
        routes = [route.path for route in app.routes]
        print(f"✅ 등록된 라우트: {routes}")
        
        # 데이터베이스 초기화 확인
        from app.database import engine
        print("✅ 데이터베이스 엔진 설정 확인")
        
        print("\n✅ 5단계 테스트 통과!")
        print("\n다음 명령어로 서버를 실행할 수 있습니다:")
        print("  uvicorn app.main:app --reload")
        
        return True
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_fastapi_app()
    sys.exit(0 if success else 1)

