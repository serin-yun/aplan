from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.database import get_session
from app.services.flow_service import build_flow_graph, build_flow_summary, collect_flows

router = APIRouter(prefix="/api/flows", tags=["flows"])


@router.get("/{flow_key}/summary")
async def get_flow_summary(
    flow_key: str,
    session: Session = Depends(get_session),
):
    flows = collect_flows(session=session)
    objects = flows.get(flow_key, [])
    if not objects:
        raise HTTPException(status_code=404, detail="Flow를 찾을 수 없습니다.")
    return build_flow_summary(flow_key=flow_key, objects=objects)


@router.get("/{flow_key}/graph")
async def get_flow_graph(
    flow_key: str,
    session: Session = Depends(get_session),
):
    flows = collect_flows(session=session)
    objects = flows.get(flow_key, [])
    if not objects:
        raise HTTPException(status_code=404, detail="Flow를 찾을 수 없습니다.")
    return build_flow_graph(flow_key=flow_key, objects=objects)


