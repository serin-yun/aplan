"""
대시보드 라우터

홈 대시보드 페이지 및 통계 정보 제공
"""

from pathlib import Path
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select, func
from app.database import get_session
from app.models import IntegrationObject, IntegrationRelation

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# 템플릿 디렉토리 설정
templates_dir = Path(__file__).parent.parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


@router.get("", response_class=HTMLResponse, include_in_schema=False)
async def get_dashboard(
    request: Request,
    session: Session = Depends(get_session)
):
    """
    대시보드 홈페이지
    
    프로세스 가이드, 통계 정보, 빠른 작업 링크 제공
    """
    # 파일 존재 여부 확인
    mapping_file = Path("mapping.xlsx")
    file_exists = mapping_file.exists()
    
    # 템플릿 파일 존재 여부 확인
    template_file = Path("mapping_template.xlsx")
    mapping_template_exists = template_file.exists()
    
    # 데이터 로딩 여부 확인 (오브젝트가 있는지)
    statement = select(func.count(IntegrationObject.id))
    total_objects = session.exec(statement).first() or 0
    data_loaded = total_objects > 0
    
    # 통계 정보 조회
    statement = select(func.count(IntegrationRelation.id))
    total_relations = session.exec(statement).first() or 0
    
    # 시스템 타입별 통계
    statement = select(IntegrationObject.system_type).distinct()
    system_types = session.exec(statement).all()
    system_types_count = len(system_types)
    
    # 모듈별 통계
    statement = select(IntegrationObject.module).distinct().where(IntegrationObject.module.isnot(None))
    modules = session.exec(statement).all()
    modules_count = len(modules)
    
    # 최근 오브젝트 (최근 업데이트된 순서)
    recent_objects = []
    if data_loaded:
        statement = select(IntegrationObject)\
            .order_by(IntegrationObject.updated_at.desc())\
            .limit(5)
        recent_objects = list(session.exec(statement).all())
    
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "file_exists": file_exists,
            "mapping_template_exists": mapping_template_exists,
            "data_loaded": data_loaded,
            "total_objects": total_objects,
            "total_relations": total_relations,
            "system_types_count": system_types_count,
            "modules_count": modules_count,
            "recent_objects": recent_objects
        }
    )


@router.get("/guide", response_class=HTMLResponse, include_in_schema=False)
async def get_guide(request: Request):
    """사용 가이드 페이지"""
    return templates.TemplateResponse("guide.html", {"request": request})


@router.get("/api/stats")
async def get_stats(session: Session = Depends(get_session)):
    """
    통계 정보 API
    
    시스템 타입별, 레이어별, 모듈별 통계를 제공합니다.
    """
    # 시스템 타입별 통계
    statement = select(IntegrationObject.system_type, func.count(IntegrationObject.id))\
        .where(IntegrationObject.status == "ACTIVE")\
        .group_by(IntegrationObject.system_type)
    system_type_results = session.exec(statement).all()
    system_types = {row[0]: row[1] for row in system_type_results}
    
    # 레이어별 통계
    statement = select(IntegrationObject.layer, func.count(IntegrationObject.id))\
        .where(IntegrationObject.status == "ACTIVE")\
        .group_by(IntegrationObject.layer)
    layer_results = session.exec(statement).all()
    layers = {row[0]: row[1] for row in layer_results}
    
    # 모듈별 통계
    statement = select(IntegrationObject.module, func.count(IntegrationObject.id))\
        .where(IntegrationObject.status == "ACTIVE", IntegrationObject.module.isnot(None))\
        .group_by(IntegrationObject.module)
    module_results = session.exec(statement).all()
    modules = {row[0]: row[1] for row in module_results}
    
    # 오브젝트 타입별 통계
    statement = select(IntegrationObject.object_type, func.count(IntegrationObject.id))\
        .where(IntegrationObject.status == "ACTIVE")\
        .group_by(IntegrationObject.object_type)
    object_type_results = session.exec(statement).all()
    object_types = {row[0]: row[1] for row in object_type_results}
    
    # 전체 통계
    total_objects = session.exec(select(func.count(IntegrationObject.id))).first() or 0
    total_relations = session.exec(select(func.count(IntegrationRelation.id))).first() or 0
    
    return {
        "system_types": system_types,
        "layers": layers,
        "modules": modules,
        "object_types": object_types,
        "total_objects": total_objects,
        "total_relations": total_relations
    }

