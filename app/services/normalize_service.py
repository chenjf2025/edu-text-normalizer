"""规范化服务 - 核心服务"""
import time
import hashlib
from typing import Optional, Dict, Any, List
from app.normalizers.math_normalizer import MathNormalizer
from app.normalizers.chemistry_normalizer import ChemistryNormalizer
from app.normalizers.physics_normalizer import PhysicsNormalizer
from app.normalizers.biology_normalizer import BiologyNormalizer
from app.normalizers.chinese_normalizer import ChineseNormalizer
from app.detectors.math_detector import MathDetector
from app.detectors.chemistry_detector import ChemistryDetector
from app.detectors.physics_detector import PhysicsDetector
from app.detectors.common_detector import CommonDetector
from app.services.cache_service import get_cache_service, CacheService
from app.utils.logger import logger


class NormalizeService:
    """规范化服务 - 核心大脑"""

    def __init__(self, cache_service: Optional[CacheService] = None):
        """
        初始化规范化服务

        Args:
            cache_service: 缓存服务
        """
        self.cache = cache_service or get_cache_service()

        # 初始化检测器
        self.detectors = {
            "math": MathDetector(),
            "chemistry": ChemistryDetector(),
            "physics": PhysicsDetector(),
            "common": CommonDetector(),
        }

        # 初始化规范化器
        self.normalizers = {
            "math": MathNormalizer(),
            "chemistry": ChemistryNormalizer(),
            "physics": PhysicsNormalizer(),
            "biology": BiologyNormalizer(),
            "chinese": ChineseNormalizer(),
        }

        logger.info("规范化服务初始化完成")

    def normalize(self, text: str, force_subject: Optional[str] = None) -> Dict[str, Any]:
        """
        规范化文本 - 主要入口

        Args:
            text: 输入文本
            force_subject: 强制指定学科

        Returns:
            {
                "subject": "math|chemistry|physics|biology|common",
                "normalized_text": "规范化后的文本",
                "fallback": False,
                "process_time_ms": 15.3
            }
        """
        start_time = time.time()
        original_text = text

        try:
            # 1. 检查缓存
            cache_key = self._make_cache_key(text, force_subject)
            logger.info(f"[DEBUG] 输入文本: [{text}]")
            logger.info(f"[DEBUG] 缓存key: [{cache_key}]")
            cached = self.cache.get(cache_key)
            if cached:
                logger.info(f"[DEBUG] 缓存命中! normalized_text=[{cached.get('normalized_text')}]")
                cached["cached"] = True
                return cached

            # 2. 识别学科
            subject = force_subject or self._detect_subject(text)
            logger.info(f"[DEBUG] 识别学科: [{subject}]")

            # 3. 选择规范化器
            normalizer = self.normalizers.get(subject)
            logger.info(f"[DEBUG] 使用规范化器: [{type(normalizer).__name__}]")

            if normalizer:
                normalized = normalizer.normalize(text)
                logger.info(f"[DEBUG] 规范化结果: [{normalized}]")
            else:
                # 默认中文规范化
                normalized = self.normalizers["chinese"].normalize(text)

            # 4. 构建结果
            result = {
                "subject": subject,
                "normalized_text": normalized,
                "fallback": False,
                "original_text": original_text,
                "process_time_ms": round((time.time() - start_time) * 1000, 2),
                "cached": False,
            }

            # 5. 存入缓存
            self.cache.set(cache_key, result)

            logger.info(
                f"规范化完成 | 学科:{subject} | "
                f"耗时:{result['process_time_ms']}ms | "
                f"文本:{text[:50]}..."
            )

            return result

        except Exception as e:
            logger.error(f"规范化失败: {text}, 错误: {e}")
            return {
                "subject": "unknown",
                "normalized_text": text,  # 回退
                "fallback": True,
                "original_text": original_text,
                "process_time_ms": round((time.time() - start_time) * 1000, 2),
                "error": str(e),
            }

    def _detect_subject(self, text: str) -> str:
        """
        检测学科 - 路由器

        Args:
            text: 输入文本

        Returns:
            学科名称
        """
        # 学科优先级：物理 > 数学 > 化学 > 生物 > 普通
        # 物理单位（如m/s^2）可能含上标数字，需要优先于数学检测
        if self.detectors["physics"].detect(text):
            return "physics"

        # 数学优先(因为数学公式特征最明显)
        if self.detectors["math"].detect(text):
            return "math"

        # 化学（需要排除LaTeX干扰）
        if self.detectors["chemistry"].detect(text):
            # 双重检查：如果同时匹配生物术语，跳过化学
            if not self.normalizers["biology"].detect(text):
                return "chemistry"

        # 生物
        if self.normalizers["biology"].detect(text):
            return "biology"

        # 默认中文
        return "common"

    def _make_cache_key(self, text: str, subject: Optional[str] = None) -> str:
        """生成缓存key"""
        content = f"{subject or 'auto'}:{text}"
        return hashlib.md5(content.encode()).hexdigest()

    def batch_normalize(self, texts: List[str],
                       force_subjects: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        批量规范化

        Args:
            texts: 文本列表
            force_subjects: 强制学科列表(可选)

        Returns:
            结果列表
        """
        results = []
        for i, text in enumerate(texts):
            subject = force_subjects[i] if force_subjects and i < len(force_subjects) else None
            result = self.normalize(text, force_subject=subject)
            results.append(result)
        return results

    def get_service_info(self) -> Dict[str, Any]:
        """获取服务信息"""
        return {
            "service": "EduTextNormalizer",
            "version": "1.0.0",
            "normalizers": list(self.normalizers.keys()),
            "detectors": list(self.detectors.keys()),
            "cache_enabled": self.cache is not None,
        }