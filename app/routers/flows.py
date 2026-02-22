from typing import Optional
from pathlib import Path

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.services.overview_service import normalize_view_mode

router = APIRouter(prefix="/flows", tags=["flows"])

templates_dir = Path(__file__).parent.parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


@router.get("/{flow_key}", response_class=HTMLResponse, include_in_schema=False)
async def flow_placeholder(
    request: Request,
    flow_key: str,
    view: Optional[str] = Query(None, description="보기 모드 (business|leader|ops)"),
):
    view_mode = normalize_view_mode(view)
    return templates.TemplateResponse(
        "flow_placeholder.html",
        {
            "request": request,
            "flow_key": flow_key,
            "view_mode": view_mode,
        },
    )
