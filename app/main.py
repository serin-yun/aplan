"""
FastAPI 메인 애플리케이션

MRD 4.1 요구사항:
- FastAPI 웹 프레임워크 사용
- Jinja2 템플릿 엔진 설정
- Static 파일 서빙
- uvicorn app.main:app --reload 실행 가능
"""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from app.database import init_db
from app.routers import objects

# FastAPI 앱 인스턴스 생성
app = FastAPI(
    title="APlan Integration Impact Map",
    description="APlan과 연계된 시스템의 인터페이스 영향도 분석 도구",
    version="1.0.0"
)

# 데이터베이스 초기화 (애플리케이션 시작 시)
@app.on_event("startup")
def startup_event():
    """애플리케이션 시작 시 실행"""
    init_db()


# 템플릿 디렉토리 설정
templates_dir = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# Static 파일 디렉토리 설정 (CSS, JS 등)
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# 라우터 등록
app.include_router(objects.router, tags=["objects"])


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root():
    """루트 경로 - 검색 화면으로 리다이렉트"""
    return RedirectResponse(url="/objects")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

