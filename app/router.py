"""路由器"""
from fastapi import APIRouter
from app.api import normalize_api, image_api

def create_router() -> APIRouter:
    """创建路由"""
    api_router = APIRouter()

    # 挂载API路由
    api_router.include_router(normalize_api.router)
    api_router.include_router(image_api.router)

    return api_router