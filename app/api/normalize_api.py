"""规范化API"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import time
import base64
import io
from PIL import Image
from app.services.normalize_service import NormalizeService
from app.utils.logger import logger

router = APIRouter(prefix="/api", tags=["规范化"])

# 服务实例
_normalize_service: Optional[NormalizeService] = None


def get_service() -> NormalizeService:
    """获取服务实例"""
    global _normalize_service
    if _normalize_service is None:
        _normalize_service = NormalizeService()
    return _normalize_service


class NormalizeRequest(BaseModel):
    """规范化请求"""
    text: str = Field(..., description="待规范化的文本")
    subject: Optional[str] = Field(None, description="强制指定学科(math|chemistry|physics|biology|common)")


class BatchNormalizeRequest(BaseModel):
    """批量规范化请求"""
    texts: List[str] = Field(..., description="文本列表")
    subjects: Optional[List[str]] = Field(None, description="学科列表(可选)")


class NormalizeResponse(BaseModel):
    """规范化响应"""
    subject: str = Field(..., description="识别出的学科")
    normalized_text: str = Field(..., description="规范化后的文本")
    fallback: bool = Field(False, description="是否回退(解析失败时)")
    original_text: Optional[str] = Field(None, description="原始文本")
    process_time_ms: float = Field(..., description="处理耗时(毫秒)")
    cached: bool = Field(False, description="是否来自缓存")


@router.post("/normalize", response_model=NormalizeResponse)
async def normalize_text(request: NormalizeRequest) -> NormalizeResponse:
    """
    规范化文本为可朗读形式

    - 输入任意学科文本
    - 自动识别数学公式、化学式、物理单位等
    - 输出适合TTS的自然语言
    """
    try:
        service = get_service()
        result = service.normalize(request.text, force_subject=request.subject)

        return NormalizeResponse(
            subject=result["subject"],
            normalized_text=result["normalized_text"],
            fallback=result.get("fallback", False),
            original_text=result.get("original_text"),
            process_time_ms=result["process_time_ms"],
            cached=result.get("cached", False),
        )
    except Exception as e:
        logger.error(f"API规范化失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/normalize/batch", response_model=List[NormalizeResponse])
async def batch_normalize(request: BatchNormalizeRequest) -> List[NormalizeResponse]:
    """
    批量规范化文本
    """
    try:
        service = get_service()
        results = service.batch_normalize(request.texts, force_subjects=request.subjects)

        return [
            NormalizeResponse(
                subject=r["subject"],
                normalized_text=r["normalized_text"],
                fallback=r.get("fallback", False),
                original_text=r.get("original_text"),
                process_time_ms=r["process_time_ms"],
                cached=r.get("cached", False),
            )
            for r in results
        ]
    except Exception as e:
        logger.error(f"API批量规范化失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """健康检查"""
    try:
        service = get_service()
        info = service.get_service_info()
        return {
            "status": "healthy",
            "service": info["service"],
            "version": info["version"],
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@router.get("/debug/normalize")
async def debug_normalize(text: str) -> Dict[str, Any]:
    """调试端点：直接调用normalizer，不走service层缓存"""
    import sys
    sys.path.insert(0, str(__file__).rsplit('/', 2)[0])
    from app.normalizers.math_normalizer import MathNormalizer

    normalizer = MathNormalizer()
    # 直接规范化
    result = normalizer.normalize(text)
    return {
        "input": text,
        "input_repr": repr(text),
        "input_bytes": [hex(b) for b in text.encode('utf-8')],
        "output": result,
        "output_repr": repr(result),
        "output_bytes": [hex(b) for b in result.encode('utf-8')],
    }


@router.get("/info")
async def service_info() -> Dict[str, Any]:
    """获取服务信息"""
    service = get_service()
    return service.get_service_info()


class ImageNormalizeRequest(BaseModel):
    """图片规范化请求"""
    image: str = Field(..., description="Base64编码的图片数据")


@router.post("/normalize/image")
async def normalize_image(request: ImageNormalizeRequest) -> Dict[str, Any]:
    """
    上传图片进行OCR识别和规范化
    
    - 支持数学公式、化学式、物理单位等图片识别
    - 自动规范化文本为可朗读形式
    """
    try:
        # 解码图片
        image_data = base64.b64decode(request.image)
        img = Image.open(io.BytesIO(image_data))
        
        # OCR识别
        ocr_text, ocr_method = _ocr_image(img)
        
        if not ocr_text:
            return {
                "ocr_text": "",
                "normalized_text": "",
                "subject": "unknown",
                "fallback": True,
                "error": "未识别到文字",
            }
        
        # 规范化
        service = get_service()
        result = service.normalize(ocr_text)
        
        return {
            "ocr_text": ocr_text,
            "normalized_text": result["normalized_text"],
            "subject": result["subject"],
            "fallback": result.get("fallback", False),
            "process_time_ms": result["process_time_ms"],
            "ocr_method": ocr_method,
        }
    except Exception as e:
        logger.error(f"图片规范化失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _ocr_image(img: Image.Image) -> tuple:
    """
    综合多引擎OCR识别
    
    Returns:
        (识别文本, 方法名)
    """
    # 导入OCR引擎
    from app.utils.ocr_engine import recognize_image, clean_latex_text
    
    try:
        result = recognize_image(img)
        
        if result["text"]:
            # 清理LaTeX噪音
            cleaned = clean_latex_text(result["text"])
            return cleaned, result["method"]
        
        return "", "failed"
    except Exception as e:
        logger.error(f"OCR识别失败: {e}")
        return "", "failed"