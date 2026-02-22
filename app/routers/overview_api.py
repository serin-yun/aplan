from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.database import get_session
from app.services.overview_service import build_cluster_network

router = APIRouter(prefix="/api", tags=["overview"])


@router.get("/overview/cluster")
async def get_overview_cluster(
    session: Session = Depends(get_session),
):
    return build_cluster_network(session=session)
