"""OCR引擎 - 多策略图片识别"""
import io
import base64
import numpy as np
from typing import Optional, Tuple, List
from PIL import Image, ImageEnhance, ImageFilter
import cv2

from app.utils.logger import logger

# 全局模型缓存（避免重复初始化）
_p2t_model = None
_cnstd_model = None
_cnocr_model = None


def _get_pix2text():
    """获取/初始化 pix2text 模型"""
    global _p2t_model
    if _p2t_model is None:
        try:
            from pix2text import Pix2Text
            _p2t_model = Pix2Text(providers=['CPUExecutionProvider'])
            logger.info("Pix2Text 模型初始化完成")
        except Exception as e:
            logger.error(f"Pix2Text 初始化失败: {e}")
            _p2t_model = False
    return _p2t_model if _p2t_model else None


def _get_cnstd():
    """获取/初始化 cnstd 检测模型"""
    global _cnstd_model
    if _cnstd_model is None:
        try:
            from cnstd import CnStd
            _cnstd_model = CnStd()
            logger.info("CnStd 模型初始化完成")
        except Exception as e:
            logger.error(f"CnStd 初始化失败: {e}")
            _cnstd_model = False
    return _cnstd_model if _cnstd_model else None


def _get_cnocr():
    """获取/初始化 cnocr 识别模型"""
    global _cnocr_model
    if _cnocr_model is None:
        try:
            from cnocr import CnOcr
            _cnocr_model = CnOcr()
            logger.info("CnOcr 模型初始化完成")
        except Exception as e:
            logger.error(f"CnOcr 初始化失败: {e}")
            _cnocr_model = False
    return _cnocr_model if _cnocr_model else None


def preprocess_image(img: Image.Image, strategy: str = "auto") -> Image.Image:
    """
    图片预处理 - 提升OCR识别率
    
    Args:
        img: PIL图片
        strategy: "auto", "formula", "text", "handwrite"
    
    Returns:
        预处理后的图片
    """
    img = img.convert("RGB")
    w, h = img.size
    
    # 转为 numpy
    arr = np.array(img)
    
    # 转灰度
    if len(arr.shape) == 3:
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    else:
        gray = arr
    
    # 自适应直方图均衡（增强对比度，对公式特别有效）
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    
    # 去噪（对截图有效）
    denoised = cv2.fastNlMeansDenoising(enhanced, h=10)
    
    # 锐化（让公式边缘更清晰）
    kernel = np.array([[-1, -1, -1],
                       [-1,  9, -1],
                       [-1, -1, -1]])
    sharpened = cv2.filter2D(denoised, -1, kernel)
    
    # 转回 PIL
    result = Image.fromarray(sharpened)
    return result


def preprocess_for_formula(img: Image.Image) -> Image.Image:
    """
    公式图片专用预处理
    
    - 增强对比度
    - 二值化（让公式更清晰）
    - 去噪
    """
    img = img.convert("RGB")
    w, h = img.size
    
    # 缩放到合适大小（公式识别最佳尺寸）
    target_w = min(w, 1200)
    if w > target_w:
        ratio = target_w / w
        img = img.resize((target_w, int(h * ratio)), Image.LANCZOS)
    
    arr = np.array(img)
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY) if len(arr.shape) == 3 else arr
    
    # 自适应直方图均衡
    clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(4, 4))
    enhanced = clahe.apply(gray)
    
    # OTSU二值化（自动阈值）
    _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # 去噪
    denoised = cv2.fastNlMeansDenoising(binary, h=15)
    
    return Image.fromarray(denoised)


def ocr_with_pix2text(img: Image.Image) -> Tuple[str, float]:
    """
    使用 pix2text 识别公式
    
    Returns:
        (识别的文本, 置信度)
    """
    p2t = _get_pix2text()
    if not p2t:
        return "", 0.0
    
    try:
        # 公式预处理
        img_prep = preprocess_for_formula(img)
        
        result = p2t.recognize_formula(img_prep, return_text=True)
        
        if not result:
            return "", 0.0
        
        if isinstance(result, str):
            text = result.strip()
        elif isinstance(result, (list, tuple)):
            if isinstance(result[0], dict):
                text = result[0].get('text', '')
            else:
                text = str(result[0]).strip()
        else:
            text = str(result).strip()
        
        # 简单置信度估计：文本长度+无乱码
        confidence = 1.0 if text and not _is_garbled(text) else 0.3
        
        return text, confidence
    except Exception as e:
        logger.warning(f"Pix2Text 识别失败: {e}")
        return "", 0.0


def ocr_with_cnstd_cnocr(img: Image.Image) -> Tuple[str, float]:
    """
    使用 CnStd + CnOcr 通用文字识别
    
    Returns:
        (识别的文本, 置信度)
    """
    std = _get_cnstd()
    ocr = _get_cnocr()
    
    if not std or not ocr:
        return "", 0.0
    
    try:
        # 预处理
        w, h = img.size
        if w > 1200 or h > 1200:
            ratio = 800 / max(w, h)
            img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
        
        img_prep = preprocess_image(img)
        
        # 检测文字区域
        box_info_list = std.detect(img_prep)
        
        if not box_info_list:
            return "", 0.0
        
        all_texts = []
        total_conf = 0.0
        count = 0
        
        for box_info in box_info_list:
            try:
                # 获取坐标
                if hasattr(box_info, '__iter__') and not isinstance(box_info, str):
                    coords = list(box_info)
                    if len(coords) >= 2:
                        box = coords[0] if isinstance(coords[0], (list, tuple)) else coords
                        cropped = img_prep.crop(box)
                        ocr_result = ocr.ocr(cropped)
                        if ocr_result and ocr_result[0].get('text'):
                            text = ocr_result[0]['text']
                            conf = ocr_result[0].get('score', 0.5)
                            all_texts.append(text)
                            total_conf += conf
                            count += 1
            except Exception:
                continue
        
        if not all_texts:
            return "", 0.0
        
        return " ".join(all_texts), total_conf / count if count > 0 else 0.5
    except Exception as e:
        logger.warning(f"CnStd+CnOcr 识别失败: {e}")
        return "", 0.0


def ocr_with_mathpix_style(img: Image.Image) -> Tuple[str, float]:
    """
    数学公式识别 - 组合策略
    尝试多种预处理，取最好结果
    """
    results = []
    
    strategies = [
        ("origin", img),
        ("formula_prep", preprocess_for_formula(img)),
        ("contrast", _enhance_contrast(img)),
    ]
    
    for name, preped in strategies:
        text, conf = ocr_with_pix2text(preped)
        if text:
            results.append((text, conf, name))
    
    if not results:
        return "", 0.0
    
    # 选最佳结果
    best = max(results, key=lambda x: x[1])
    return best[0], best[1]


def _enhance_contrast(img: Image.Image) -> Image.Image:
    """增强对比度"""
    enhancer = ImageEnhance.Contrast(img)
    return enhancer.enhance(1.8)


def _is_garbled(text: str) -> bool:
    """
    检测是否是乱码文本
    
    乱码特征：
    - 大量连续字母被空格分开（如 "L e n"）
    - 包含大量生僻符号
    - 文本无法解析
    """
    if not text:
        return True
    
    # 检测字母被空格分开的情况（如 "L e n")
    spaced_letters = len([c for c in text if c.isalpha() and (text[text.index(c)-1] == ' ' if text.index(c) > 0 else False)])
    letter_count = len([c for c in text if c.isalpha()])
    
    if letter_count > 5 and spaced_letters / letter_count > 0.3:
        return True
    
    # 检测不可见字符过多
    invisible_ratio = sum(1 for c in text if c in ' \n\t\r') / len(text)
    if invisible_ratio > 0.5:
        return True
    
    return False


def clean_latex_text(text: str) -> str:
    """
    清理 LaTeX 识别结果中的噪音
    
    移除：
    - 连续的空格
    - 无意义的符号
    - 损坏的 LaTeX 标签
    - 单字母间空格（如 L e n → Len）
    """
    import re
    
    if not text:
        return ""
    
    # 移除连续空格和换行
    text = re.sub(r'[ \t]+', ' ', text)
    text = text.replace('\n', ' ').replace('\r', ' ')
    
    # 关键：合并被空格分开的单个字母（L e n → Len）
    # 在 LaTeX 环境中，单个字母间的空格通常是识别错误
    text = _merge_spaced_letters(text)
    
    # 清理 \operatorname* 中的空格
    text = re.sub(r'\\operatorname\*\s*\{?\s*([a-z ]+)\s*\}?', 
                   lambda m: '\\operatorname{' + ''.join(m.group(1).split()) + '}', text)
    
    # 清理 \mathrm 中的空格
    text = re.sub(r'\\mathrm\{([a-z ]+)\}', 
                   lambda m: '\\mathrm{' + ''.join(m.group(1).split()) + '}', text)
    
    # 清理 \mathbf, \mathit, \boldsymbol 等
    text = re.sub(r'\\mathbf\{([a-z ]+)\}', 
                   lambda m: '\\mathbf{' + ''.join(m.group(1).split()) + '}', text)
    text = re.sub(r'\\mathit\{([a-z ]+)\}', 
                   lambda m: '\\mathit{' + ''.join(m.group(1).split()) + '}', text)
    
    # 清理带空格的多字母组合
    text = re.sub(r'\{([a-zA-Z](?:\s+[a-zA-Z])+)\}', 
                   lambda m: '{' + ''.join(m.group(1).split()) + '}', text)
    
    # 清理 \operatorname 中的空格
    text = re.sub(r'\\operatorname\s*\{?\s*([a-z ]+)\s*\}?',
                   lambda m: '\\operatorname{' + ''.join(m.group(1).split()) + '}', text)
    
    # 移除无意义的 \otimes 等重复
    text = re.sub(r'(\\[a-zA-Z]+)\s+\1(?:\s+\1)*', r'\1', text)
    
    return text.strip()


def _merge_spaced_letters(text: str) -> str:
    """
    合并被空格分开的单个字母
    
    例如: "L e n" → "Len"
    但保留: "a b c"（普通文本中的空格）
    """
    import re
    
    # 在 LaTeX 环境 { ... } 中合并空格分开的字母
    def merge_in_braces(match):
        content = match.group(1)
        # 如果是空格分开的单个字母，合并
        letters = content.split()
        if all(c.isalpha() and len(c) == 1 for c in letters):
            return ''.join(letters)
        return content
    
    # 处理 { ... } 中的内容
    text = re.sub(r'\{([^{}]+)\}', merge_in_braces, text)
    
    # 处理 \operatorname 之类命令后的 { }
    text = re.sub(r'\\operatorname\*?\s*\{([a-z ]+)\}', 
                   lambda m: '\\operatorname{' + ''.join(m.group(1).split()) + '}', text)
    
    return text


def recognize_image(img: Image.Image) -> dict:
    """
    综合OCR识别 - 多引擎融合
    
    Returns:
        {
            "text": "识别的文本",
            "method": "best_method",
            "confidence": 0.85,
            "alternatives": [...]
        }
    """
    results = []
    
    # 1. Pix2Text 公式识别（优先）
    text1, conf1 = ocr_with_mathpix_style(img)
    if text1:
        # 清理噪音
        text1_clean = clean_latex_text(text1)
        results.append(("pix2text", text1_clean, conf1))
    
    # 2. CnStd+CnOcr 通用文字
    text2, conf2 = ocr_with_cnstd_cnocr(img)
    if text2 and text2 not in [r[1] for r in results]:
        results.append(("cnstd_cnocr", text2, conf2))
    
    if not results:
        return {
            "text": "",
            "method": "none",
            "confidence": 0.0,
            "alternatives": []
        }
    
    # 选择最佳结果
    best = max(results, key=lambda x: x[2])
    
    return {
        "text": best[1],
        "method": best[0],
        "confidence": best[2],
        "alternatives": [{"method": r[0], "text": r[1], "confidence": r[2]} for r in results]
    }