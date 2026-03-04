from typing import Optional
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from app.database import get_session
from app.services.flow_service import build_flow_cards, build_flow_summary_line, get_flow_by_key, list_flows
from app.services.overview_service import normalize_view_mode

router = APIRouter(prefix="/flows", tags=["flows"])

templates_dir = Path(__file__).parent.parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


@router.get("", response_class=HTMLResponse, include_in_schema=False)
async def flow_list(
    request: Request,
    q: Optional[str] = Query(None, description="검색어 (인터페이스명/항목ID/IF ID/테이블)"),
    flow_type: Optional[str] = Query(None, description="Type 필터 (Inbound/Outbound)"),
    system: Optional[str] = Query(None, description="시스템 필터"),
    module: Optional[str] = Query(None, description="모듈 필터"),
    view: Optional[str] = Query(None, description="보기 모드 (business|executive|ops)"),
    session: Session = Depends(get_session),
):
    view_mode = normalize_view_mode(view)
    flows = list_flows(session=session, q=q, flow_type=flow_type, system=system, module=module)
    cards = build_flow_cards(flows)
    return templates.TemplateResponse(
        "flows.html",
        {
            "request": request,
            "view_mode": view_mode,
            "cards": cards,
            "q": q,
            "flow_type": flow_type,
            "system": system,
            "module": module,
        },
    )


@router.get("/{flow_key}", response_class=HTMLResponse, include_in_schema=False)
async def flow_detail(
    request: Request,
    flow_key: str,
    view: Optional[str] = Query(None, description="보기 모드 (business|executive|ops)"),
    session: Session = Depends(get_session),
):
    view_mode = normalize_view_mode(view)
    flow = get_flow_by_key(session=session, flow_key=flow_key)
    if not flow:
        raise HTTPException(status_code=404, detail="Flow를 찾을 수 없습니다.")
    return templates.TemplateResponse(
        "flow_detail.html",
        {
            "request": request,
            "flow_key": flow_key,
            "view_mode": view_mode,
            "flow": flow,
        },
    )


@router.get("/{flow_key}/report", response_class=HTMLResponse, include_in_schema=False)
async def flow_report(
    request: Request,
    flow_key: str,
    view: Optional[str] = Query(None, description="보기 모드 (business|executive|ops)"),
    session: Session = Depends(get_session),
):
    view_mode = normalize_view_mode(view)
    flow = get_flow_by_key(session=session, flow_key=flow_key)
    if not flow:
        raise HTTPException(status_code=404, detail="Flow를 찾을 수 없습니다.")
    summary_line = build_flow_summary_line(flow)
    return templates.TemplateResponse(
        "flow_report.html",
        {
            "request": request,
            "flow_key": flow_key,
            "view_mode": view_mode,
            "flow": flow,
            "summary_line": summary_line,
        },
    )
