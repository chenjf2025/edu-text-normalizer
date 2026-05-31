"""
EduTextNormalizer - 教育场景智能文本规范化引擎
主入口
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.router import create_router
from app.config import config
from app.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    logger.info("=" * 50)
    logger.info("EduTextNormalizer 服务启动")
    logger.info(f"端口: {config.APP.port}")
    logger.info("=" * 50)
    yield
    logger.info("EduTextNormalizer 服务关闭")


def create_app() -> FastAPI:
    """创建FastAPI应用"""
    app = FastAPI(
        title="EduTextNormalizer",
        description="面向教育场景的多学科智能文本规范化引擎",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS - 允许所有来源
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 挂载路由（API）
    app.include_router(create_router())

    # 根路径返回index.html
    @app.get("/", include_in_schema=False)
    async def root():
        static_dir = Path(__file__).parent.parent / "static"
        return FileResponse(str(static_dir / "index.html"))

    # 挂载静态文件目录（仅用于 /static/ 路径）
    static_dir = Path(__file__).parent.parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    return app


# 创建应用实例
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=config.APP.host,
        port=config.APP.port,
        reload=config.APP.reload,
        log_level="info",
    )