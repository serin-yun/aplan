from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.database import get_session
from app.services.flow_service import build_flow_cards, build_flow_diagram, get_flow_by_key, list_flows

router = APIRouter(prefix="/api/flows", tags=["flows"])


@router.get("/")
async def get_flows(
    q: Optional[str] = Query(None, description="검색어"),
    flow_type: Optional[str] = Query(None, description="Type 필터"),
    system: Optional[str] = Query(None, description="시스템 필터"),
    module: Optional[str] = Query(None, description="모듈 필터"),
    session: Session = Depends(get_session),
):
    flows = list_flows(session=session, q=q, flow_type=flow_type, system=system, module=module)
    return build_flow_cards(flows)


@router.get("/{flow_key}/diagram")
async def get_flow_diagram(
    flow_key: str,
    session: Session = Depends(get_session),
):
    flow = get_flow_by_key(session=session, flow_key=flow_key)
    if not flow:
        raise HTTPException(status_code=404, detail="Flow를 찾을 수 없습니다.")
    return build_flow_diagram(flow=flow)


