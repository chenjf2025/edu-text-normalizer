"""图片OCR识别与规范化API"""
import base64
import hashlib
import re
import time
import uuid
import io
from pathlib import Path
from typing import Optional, Union, List

import requests
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from PIL import Image
from pydantic import BaseModel, Field

from app.services.normalize_service import NormalizeService
from app.utils.logger import logger

router = APIRouter(prefix="/api", tags=["图片OCR"])

# 服务实例
_normalize_service: Optional[NormalizeService] = None
_pix2text = None


def get_service() -> NormalizeService:
    global _normalize_service
    if _normalize_service is None:
        _normalize_service = NormalizeService()
    return _normalize_service


def get_pix2text():
    """懒加载Pix2Text，启用数学公式识别"""
    global _pix2text
    if _pix2text is None:
        try:
            from pix2text import Pix2Text
            # 启用数学公式识别 (公式+文本混合)
            _pix2text = Pix2Text(
                engine='onnx',           # 使用ONNX引擎
                formul_config=dict(      # 公式识别配置
                    det_model_name='ch_PP-OCRv5_det',
                    rec_model_name='en_PP-OCRv5_formula',
                    rec_model_backend='onnx',
                ),
                text_config=dict(
                    det_model_name='ch_PP-OCRv5_det',
                    rec_model_name='ch_PP-OCRv5_rec',
                    rec_model_backend='onnx',
                ),
                use_angle_ocr=True,
            )
            logger.info("Pix2Text 初始化成功 (公式+文本模式)")
        except TypeError:
            # 旧版API不支持这些参数，回退到基础初始化
            from pix2text import Pix2Text
            _pix2text = Pix2Text()
            logger.info("Pix2Text 初始化成功 (基础模式)")
        except Exception as e:
            logger.error(f"Pix2Text 初始化失败: {e}")
            raise RuntimeError(f"Pix2Text 初始化失败: {e}")
    return _pix2text


def download_image(url: str) -> Image.Image:
    """从URL下载图片"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return Image.open(io.BytesIO(response.content))
    except Exception as e:
        raise ValueError(f"无法从URL下载图片: {e}")


def load_image_from_base64(data: str) -> Image.Image:
    """从Base64加载图片"""
    try:
        if "," in data:
            data = data.split(",", 1)[1]
        image_data = base64.b64decode(data)
        return Image.open(io.BytesIO(image_data))
    except Exception as e:
        raise ValueError(f"无法解析Base64图片: {e}")


def ocr_image(image: Image.Image, p2t) -> dict:
    """使用Pix2Text OCR图片"""
    try:
        result = p2t(image)
        return result
    except Exception as e:
        logger.error(f"Pix2Text OCR失败: {e}")
        raise RuntimeError(f"OCR识别失败: {e}")


def extract_math_text(result) -> List[str]:
    """从OCR结果中提取数学文本

    支持新旧两种Pix2Text格式:
    - 新版 >=1.1: Page对象 with elements
    - 旧版 dict格式: {'text': ..., 'formula': ...}
    """
    math_texts = []

    # 新版 Pix2Text (>=1.1) 返回 Page 对象
    if hasattr(result, 'elements'):
        for element in result.elements:
            # 跳过非文本元素
            elem_type = getattr(element, 'type', None) or getattr(element, 'category', None)
            # 获取文本内容
            text = getattr(element, 'text', None)
            if not text:
                # 尝试从 attrs 获取
                attrs = getattr(element, 'attrs', {}) or {}
                text = attrs.get('text', '')
            
            if text:
                text = text.strip()
                if text and text != '$$' and len(text) > 0:
                    # 清理LaTeX空格指令，保留公式结构
                    text = text.replace('\\,', ' ').replace('\\;', ' ').replace('\\ ', ' ')
                    text = text.replace('\\quad', ' ').replace('\\qquad', ' ')
                    # 合并多余空格
                    text = re.sub(r'\s+', ' ', text)
                    # 去掉首尾空白，但保留内部结构
                    text = text.strip()
                    if text:
                        math_texts.append(text)
            
            # 优先从 meta 提取更准确的识别结果（meta.text 通常没有末尾换行）
            meta = getattr(element, 'meta', None)
            if meta:
                meta_text = None
                if isinstance(meta, list) and len(meta) > 0:
                    meta_text = meta[0].get('text') if isinstance(meta[0], dict) else None
                elif isinstance(meta, dict):
                    meta_text = meta.get('text')
                if meta_text and meta_text.strip() not in [t.strip() for t in math_texts]:
                    mt = meta_text.strip()
                    mt = mt.replace('\\,', ' ').replace('\\;', ' ').replace('\\ ', ' ')
                    mt = re.sub(r'\s+', ' ', mt).strip()
                    if mt:
                        math_texts.append(mt)
        
        return math_texts

    # 旧版 dict 格式
    if isinstance(result, dict):
        if "formula" in result and result["formula"]:
            math_texts.append(result["formula"])
        if "img_res" in result:
            for item in result["img_res"]:
                if isinstance(item, dict) and "text" in item:
                    math_texts.append(item["text"])
                elif isinstance(item, str):
                    math_texts.append(item)
        if "text_res" in result:
            for item in result["text_res"]:
                if isinstance(item, dict) and "text" in item:
                    math_texts.append(item["text"])
                elif isinstance(item, str):
                    math_texts.append(item)
        if "text" in result and result["text"]:
            math_texts.append(result["text"])
        # 兜底: 遍历所有值找 latex/公式
        for val in result.values():
            if isinstance(val, str) and ('\\frac' in val or '\\sqrt' in val or '\\int' in val or '^{' in val):
                if val not in math_texts:
                    math_texts.append(val)

    elif isinstance(result, list):
        for item in result:
            if isinstance(item, dict):
                if "text" in item:
                    math_texts.append(item["text"])
                if "content" in item:
                    math_texts.append(item["content"])
            elif isinstance(item, str):
                math_texts.append(item)

    return math_texts


class ImageNormalizeRequest(BaseModel):
    """图片规范化请求"""
    image: Optional[str] = Field(None, description="图片URL或Base64")
    url: Optional[str] = Field(None, description="图片URL")
    base64_data: Optional[str] = Field(None, description="Base64图片数据")
    text: Optional[str] = Field(None, description="直接传递已OCR的文本")
    subject: Optional[str] = Field(None, description="指定学科(math/chemistry/physics/biology/common)，空则自动检测")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"text": "x=\\frac{-b}{2a}", "subject": "math"},
                {"url": "https://example.com/formula.png"},
            ]
        }
    }


class ImageNormalizeResponse(BaseModel):
    """图片规范化响应"""
    ocr_text: str = Field(..., description="OCR识别的文本")
    normalized_text: str = Field(..., description="规范化后的文本")
    subject: str = Field(..., description="识别出的学科")
    fallback: bool = Field(False, description="是否回退")
    process_time_ms: float = Field(..., description="处理耗时")
    ocr_method: str = Field(..., description="OCR方式(pix2text/text)")


@router.post("/normalize/image", response_model=ImageNormalizeResponse)
async def normalize_image(
    request: ImageNormalizeRequest,
) -> ImageNormalizeResponse:
    """
    图片OCR识别与规范化

    支持三种输入方式(JSON body):
    1. url: 图片URL
    2. base64: Base64编码的图片数据
    3. text: 直接传已识别的文本
    """
    start_time = time.time()
    image: Optional[Image.Image] = None
    ocr_text = ""
    ocr_method = "unknown"

    try:
        if request.url:
            image = download_image(request.url)
            ocr_method = "pix2text"
            logger.info(f"从URL下载图片: {request.url}")

        elif request.base64_data:
            image = load_image_from_base64(request.base64_data)
            ocr_method = "pix2text"
            logger.info("接收到Base64图片")

        elif request.image:
            if request.image.startswith("http"):
                image = download_image(request.image)
                ocr_method = "pix2text"
            else:
                image = load_image_from_base64(request.image)
                ocr_method = "pix2text"

        elif request.text:
            ocr_text = request.text
            ocr_method = "text"
            logger.info(f"直接使用传入文本: {request.text[:50]}...")

        else:
            raise HTTPException(
                status_code=400,
                detail="请提供图片(url/base64)或文本(text)"
            )

        if image:
            p2t = get_pix2text()
            ocr_result = ocr_image(image, p2t)
            math_texts = extract_math_text(ocr_result)
            ocr_text = " ".join(math_texts)
            logger.info(f"Pix2Text识别结果: {ocr_text[:200]}...")

        if not ocr_text.strip():
            normalized_text = ""
            subject = "common"
            fallback = False
        else:
            service = get_service()
            norm_result = service.normalize(ocr_text, force_subject=request.subject)
            normalized_text = norm_result["normalized_text"]
            subject = norm_result["subject"]
            fallback = norm_result.get("fallback", False)

        process_time = (time.time() - start_time) * 1000

        return ImageNormalizeResponse(
            ocr_text=ocr_text,
            normalized_text=normalized_text,
            subject=subject,
            fallback=fallback,
            process_time_ms=process_time,
            ocr_method=ocr_method,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"图片规范化失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/normalize/image/upload", response_model=ImageNormalizeResponse)
async def normalize_image_upload(
    file: UploadFile = File(...),
    subject: Optional[str] = Form(None, description="指定学科"),
) -> ImageNormalizeResponse:
    """上传图片文件进行OCR识别与规范化"""
    start_time = time.time()
    ocr_text = ""
    ocr_method = "pix2text"
    image: Optional[Image.Image] = None

    try:
        # 读取文件内容
        contents = await file.read()
        logger.info(f"接收到上传文件: {file.filename}, 大小: {len(contents)} bytes")

        # 验证是否为有效图片
        if len(contents) < 12:
            raise HTTPException(status_code=400, detail="上传文件太小，不是有效图片")

        # 检查文件头魔数
        PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'
        JPEG_SIGNATURE = b'\xff\xd8\xff'
        GIF_SIGNATURE = b'GIF87a'
        GIF9_SIGNATURE = b'GIF89a'
        WEBP_SIGNATURE = b'RIFF'

        is_png = contents.startswith(PNG_SIGNATURE)
        is_jpeg = contents.startswith(JPEG_SIGNATURE)
        is_gif = contents.startswith(GIF_SIGNATURE) or contents.startswith(GIF9_SIGNATURE)
        is_webp = contents.startswith(WEBP_SIGNATURE) and b'WEBP' in contents[:12]

        if not (is_png or is_jpeg or is_gif or is_webp):
            # 文件头不匹配，尝试PIL直接打开
            logger.warning(f"文件头不匹配，尝试PIL打开: {file.filename}")
            try:
                image = Image.open(io.BytesIO(contents))
                image.load()  # 强制加载完整图片数据
            except Exception as img_err:
                raise HTTPException(status_code=400, detail=f"无法识别为图片格式: {img_err}")
        else:
            image = Image.open(io.BytesIO(contents))
            image.load()  # 关键！强制PIL将数据读入内存，避免BytesIO被消费

        # 转换为RGB（去除alpha通道）
        if image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
            image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')

        # OCR
        p2t = get_pix2text()
        ocr_result = ocr_image(image, p2t)
        math_texts = extract_math_text(ocr_result)
        ocr_text = " ".join(math_texts)
        logger.info(f"Pix2Text识别结果: {ocr_text[:200]}...")

        # 规范化
        if not ocr_text.strip():
            normalized_text = ""
            subject_out = "common"
            fallback = False
        else:
            service = get_service()
            norm_result = service.normalize(ocr_text, force_subject=subject)
            normalized_text = norm_result["normalized_text"]
            subject_out = norm_result["subject"]
            fallback = norm_result.get("fallback", False)

        process_time = (time.time() - start_time) * 1000

        return ImageNormalizeResponse(
            ocr_text=ocr_text,
            normalized_text=normalized_text,
            subject=subject_out,
            fallback=fallback,
            process_time_ms=process_time,
            ocr_method=ocr_method,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"图片上传规范化失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # 确保图片被关闭释放内存
        if image:
            try:
                image.close()
            except Exception:
                pass


class MixedContentRequest(BaseModel):
    """混合内容请求"""
    text: str = Field(..., description="包含文字和图片的混合内容")
    extract_only: bool = Field(False, description="仅提取图片中的文本，不做规范化")


class MixedContentResponse(BaseModel):
    """混合内容响应"""
    original_text: str = Field(..., description="原始文本")
    extracted_texts: list = Field(..., description="从图片中提取的文本列表")
    normalized_text: str = Field(..., description="规范化后的完整文本")
    has_images: bool = Field(..., description="是否包含图片引用")
    process_time_ms: float = Field(..., description="处理耗时")


@router.post("/normalize/mixed", response_model=MixedContentResponse)
async def normalize_mixed(request: MixedContentRequest) -> MixedContentResponse:
    """混合内容规范化"""
    start_time = time.time()

    try:
        text = request.text
        extracted_texts = []
        processed_text = text

        image_patterns = [
            r'!\[.*?\]\(([^)]+\.(?:png|jpg|jpeg|gif|bmp|webp)(?:\?[^)]*)?)\)',
            r'\[.*?\]\(([^)]+\.(?:png|jpg|jpeg|gif|bmp|webp)(?:\?[^)]*)?)\)',
            r'(https?://[^\s]+\.(?:png|jpg|jpeg|gif|bmp|webp)(?:\?[^\s]*)?)',
        ]

        image_urls = []
        for pattern in image_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            image_urls.extend(matches)

        image_urls = list(set(image_urls))
        logger.info(f"发现 {len(image_urls)} 个图片URL")

        if image_urls and not request.extract_only:
            p2t = get_pix2text()
            for idx, url in enumerate(image_urls):
                try:
                    img = download_image(url)
                    img.load()
                    result = p2t(img)
                    math_texts = extract_math_text(result)
                    img_text = " ".join(math_texts)

                    if math_texts:
                        extracted_texts.append({
                            "url": url,
                            "text": img_text,
                            "index": idx
                        })
                        logger.info(f"图片{idx} OCR: {img_text[:50]}...")

                except Exception as e:
                    logger.warning(f"图片{idx} OCR失败: {e}")
                    extracted_texts.append({
                        "url": url,
                        "error": str(e),
                        "index": idx
                    })

        if extracted_texts:
            for item in extracted_texts:
                if "text" in item:
                    placeholder = f"[图片{item['index']+1}公式]"
                    processed_text = processed_text.replace(item["url"], placeholder)
                    processed_text += f" {item['text']}"

        service = get_service()
        if request.extract_only:
            normalized_text = processed_text
        else:
            norm_result = service.normalize(processed_text)
            normalized_text = norm_result["normalized_text"]

        process_time = (time.time() - start_time) * 1000

        return MixedContentResponse(
            original_text=text,
            extracted_texts=extracted_texts,
            normalized_text=normalized_text,
            has_images=len(image_urls) > 0,
            process_time_ms=process_time,
        )

    except Exception as e:
        logger.error(f"混合内容规范化失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ocr/test")
async def test_ocr():
    """测试OCR功能"""
    try:
        p2t = get_pix2text()
        return {"status": "ok", "engine": "pix2text"}
    except Exception as e:
        return {"status": "error", "error": str(e)}
