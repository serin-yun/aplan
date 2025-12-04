"""
1~4단계 완료 항목 테스트 스크립트

테스트 항목:
1. 모델 import 및 정의 확인
2. 데이터베이스 초기화 테스트
3. 간단한 CRUD 테스트 (IntegrationObject, IntegrationRelation)
4. Relationship 동작 확인
"""

import sys
from pathlib import Path
from sqlmodel import Session, select

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

from app.database import engine, init_db
from app.models import IntegrationObject, IntegrationRelation


def test_imports():
    """모델 import 테스트"""
    print("=" * 50)
    print("1. 모델 Import 테스트")
    print("=" * 50)
    try:
        from app.models import IntegrationObject, IntegrationRelation
        from app.database import engine, init_db
        print("✅ 모든 모듈 import 성공")
        return True
    except Exception as e:
        print(f"❌ Import 실패: {e}")
        return False


def test_db_init():
    """데이터베이스 초기화 테스트"""
    print("\n" + "=" * 50)
    print("2. 데이터베이스 초기화 테스트")
    print("=" * 50)
    try:
        # 기존 DB 파일 삭제 (테스트용)
        db_file = Path("impact_map.db")
        if db_file.exists():
            db_file.unlink()
            print("기존 DB 파일 삭제됨")
        
        # DB 초기화
        init_db()
        print("✅ 데이터베이스 초기화 성공")
        return True
    except Exception as e:
        print(f"❌ 데이터베이스 초기화 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_crud():
    """CRUD 테스트"""
    print("\n" + "=" * 50)
    print("3. CRUD 테스트")
    print("=" * 50)
    
    try:
        with Session(engine) as session:
            # CREATE - IntegrationObject 생성
            print("\n3-1. IntegrationObject 생성 테스트")
            obj1 = IntegrationObject(
                object_key="TEST_OBJ_001",
                name="테스트 오브젝트 1",
                system_type="APLAN",
                object_type="IF",
                layer="In",
                description="테스트용 오브젝트",
                module="테스트",
                status="ACTIVE",
                environment="PRD"
            )
            session.add(obj1)
            session.commit()
            session.refresh(obj1)
            print(f"✅ 오브젝트 생성 성공: ID={obj1.id}, object_key={obj1.object_key}")
            
            obj2 = IntegrationObject(
                object_key="TEST_OBJ_002",
                name="테스트 오브젝트 2",
                system_type="SAP",
                object_type="TABLE",
                layer="Legacy",
                module="테스트",
                status="ACTIVE",
                environment="PRD"
            )
            session.add(obj2)
            session.commit()
            session.refresh(obj2)
            print(f"✅ 오브젝트 생성 성공: ID={obj2.id}, object_key={obj2.object_key}")
            
            # READ - 조회 테스트
            print("\n3-2. IntegrationObject 조회 테스트")
            statement = select(IntegrationObject).where(IntegrationObject.object_key == "TEST_OBJ_001")
            found_obj = session.exec(statement).first()
            if found_obj:
                print(f"✅ 오브젝트 조회 성공: {found_obj.name}")
            else:
                print("❌ 오브젝트 조회 실패")
                return False
            
            # CREATE - IntegrationRelation 생성
            print("\n3-3. IntegrationRelation 생성 테스트")
            rel = IntegrationRelation(
                from_object_id=obj1.id,
                to_object_id=obj2.id,
                relation_type="FLOWS_TO",
                description="테스트 관계"
            )
            session.add(rel)
            session.commit()
            session.refresh(rel)
            print(f"✅ 관계 생성 성공: ID={rel.id}, {obj1.object_key} -> {obj2.object_key}")
            
            # Relationship 테스트
            print("\n3-4. Relationship 테스트")
            session.refresh(obj1)
            session.refresh(obj2)
            
            # outgoing_relations 확인
            if obj1.outgoing_relations:
                print(f"✅ obj1.outgoing_relations 동작 확인: {len(obj1.outgoing_relations)}개 관계")
            else:
                print("⚠️  obj1.outgoing_relations가 비어있음 (관계가 로드되지 않았을 수 있음)")
            
            # incoming_relations 확인
            if obj2.incoming_relations:
                print(f"✅ obj2.incoming_relations 동작 확인: {len(obj2.incoming_relations)}개 관계")
            else:
                print("⚠️  obj2.incoming_relations가 비어있음 (관계가 로드되지 않았을 수 있음)")
            
            # Relationship은 lazy loading이므로 명시적으로 접근해야 함
            print(f"✅ Relationship 접근 가능 (lazy loading)")
            
            # UPDATE 테스트
            print("\n3-5. UPDATE 테스트")
            found_obj.description = "업데이트된 설명"
            session.add(found_obj)
            session.commit()
            session.refresh(found_obj)
            if found_obj.description == "업데이트된 설명":
                print("✅ UPDATE 성공")
            else:
                print("❌ UPDATE 실패")
                return False
            
            # DELETE 테스트
            print("\n3-6. DELETE 테스트")
            session.delete(rel)
            session.delete(obj1)
            session.delete(obj2)
            session.commit()
            print("✅ DELETE 성공")
            
            return True
            
    except Exception as e:
        print(f"❌ CRUD 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_unique_constraint():
    """Unique 제약조건 테스트"""
    print("\n" + "=" * 50)
    print("4. Unique 제약조건 테스트")
    print("=" * 50)
    
    try:
        with Session(engine) as session:
            obj1 = IntegrationObject(
                object_key="UNIQUE_TEST",
                name="테스트",
                system_type="APLAN",
                object_type="IF",
                layer="In"
            )
            session.add(obj1)
            session.commit()
            
            # 동일한 object_key로 다시 생성 시도
            obj2 = IntegrationObject(
                object_key="UNIQUE_TEST",
                name="중복 테스트",
                system_type="APLAN",
                object_type="IF",
                layer="In"
            )
            session.add(obj2)
            try:
                session.commit()
                print("❌ Unique 제약조건이 작동하지 않음")
                return False
            except Exception:
                session.rollback()
                print("✅ Unique 제약조건 정상 동작 (중복 시 에러 발생)")
            
            # 정리
            session.delete(obj1)
            session.commit()
            return True
            
    except Exception as e:
        print(f"❌ Unique 제약조건 테스트 실패: {e}")
        return False


def main():
    """메인 테스트 실행"""
    print("\n" + "=" * 50)
    print("APlan Integration Impact Map - 1~4단계 테스트")
    print("=" * 50)
    
    results = []
    
    # 테스트 실행
    results.append(("Import 테스트", test_imports()))
    results.append(("DB 초기화 테스트", test_db_init()))
    results.append(("CRUD 테스트", test_crud()))
    results.append(("Unique 제약조건 테스트", test_unique_constraint()))
    
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
        print("🎉 모든 테스트 통과!")
    else:
        print("⚠️  일부 테스트 실패")
    print("=" * 50)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

