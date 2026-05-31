"""中文文本规范化器"""
import re
from app.normalizers.base_normalizer import BaseNormalizer
from app.utils.logger import logger


class ChineseNormalizer(BaseNormalizer):
    """中文文本规范化器 - 普通中文文本"""

    def detect(self, text: str) -> bool:
        """检测是否包含中文"""
        return bool(re.search(r"[\u4e00-\u9fff]", text))

    def normalize(self, text: str) -> str:
        """
        规范化普通中文文本

        Args:
            text: 中文文本

        Returns:
            规范化后的文本
        """
        try:
            # 清理多余空格
            result = re.sub(r"\s+", " ", text)

            # 清理特殊空白字符
            result = re.sub(r"[\u200b-\u200f\u2028-\u202f\ufeff]", "", result)

            # 清理行首行尾空白
            result = result.strip()

            return result
        except Exception as e:
            logger.error(f"中文规范化失败: {text}, 错误: {e}")
            return text