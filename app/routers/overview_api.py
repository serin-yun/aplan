from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.database import get_session
from app.services.overview_service import build_cluster_network, build_exec_summary, build_lineage_graph

router = APIRouter(prefix="/api", tags=["overview"])


@router.get("/overview/cluster")
async def get_overview_cluster(
    session: Session = Depends(get_session),
):
    return build_cluster_network(session=session)


@router.get("/overview/lineage")
async def get_overview_lineage(
    view: str | None = None,
    session: Session = Depends(get_session),
):
    return build_lineage_graph(session=session, view_mode=view or "business")


@router.get("/overview/executive")
async def get_overview_executive(
    session: Session = Depends(get_session),
):
    return build_exec_summary(session=session)
