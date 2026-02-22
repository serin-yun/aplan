from typing import Optional
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from app.database import get_session
from app.services.flow_service import build_flow_index, build_flow_summary, collect_flows, filter_flow_cards
from app.services.overview_service import normalize_view_mode

router = APIRouter(prefix="/flows", tags=["flows"])

templates_dir = Path(__file__).parent.parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


@router.get("", response_class=HTMLResponse, include_in_schema=False)
async def flow_list(
    request: Request,
    q: Optional[str] = Query(None, description="검색어 (인터페이스명/항목ID/IF ID/테이블)"),
    system_type: Optional[str] = Query(None, description="시스템 타입 필터"),
    module: Optional[str] = Query(None, description="모듈 필터"),
    view: Optional[str] = Query(None, description="보기 모드 (business|leader|ops)"),
    session: Session = Depends(get_session),
):
    view_mode = normalize_view_mode(view)
    index = build_flow_index(session=session)
    cards = filter_flow_cards(cards=index["cards"], q=q, system_type=system_type, module=module)
    return templates.TemplateResponse(
        "flows.html",
        {
            "request": request,
            "view_mode": view_mode,
            "cards": cards,
            "primary_flow_key": index["primary_flow_key"],
            "q": q,
            "system_type": system_type,
            "module": module,
        },
    )


@router.get("/{flow_key}", response_class=HTMLResponse, include_in_schema=False)
async def flow_detail(
    request: Request,
    flow_key: str,
    view: Optional[str] = Query(None, description="보기 모드 (business|leader|ops)"),
    session: Session = Depends(get_session),
):
    view_mode = normalize_view_mode(view)
    flows = collect_flows(session=session)
    objects = flows.get(flow_key, [])
    if not objects:
        raise HTTPException(status_code=404, detail="Flow를 찾을 수 없습니다.")
    summary = build_flow_summary(flow_key=flow_key, objects=objects)
    return templates.TemplateResponse(
        "flow_detail.html",
        {
            "request": request,
            "flow_key": flow_key,
            "view_mode": view_mode,
            "summary": summary,
        },
    )


@router.get("/{flow_key}/report", response_class=HTMLResponse, include_in_schema=False)
async def flow_report(
    request: Request,
    flow_key: str,
    view: Optional[str] = Query(None, description="보기 모드 (business|leader|ops)"),
    session: Session = Depends(get_session),
):
    view_mode = normalize_view_mode(view)
    flows = collect_flows(session=session)
    objects = flows.get(flow_key, [])
    if not objects:
        raise HTTPException(status_code=404, detail="Flow를 찾을 수 없습니다.")
    summary = build_flow_summary(flow_key=flow_key, objects=objects)
    return templates.TemplateResponse(
        "flow_report.html",
        {
            "request": request,
            "flow_key": flow_key,
            "view_mode": view_mode,
            "summary": summary,
        },
    )
