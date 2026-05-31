"""规范化器基类"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import regex


class BaseNormalizer(ABC):
    """规范化器基类"""

    def __init__(self):
        self.name = self.__class__.__name__.replace("Normalizer", "").lower()

    @abstractmethod
    def detect(self, text: str) -> bool:
        """
        检测文本是否需要该规范化器处理

        Args:
            text: 输入文本

        Returns:
            True if this normalizer should process the text
        """
        pass

    @abstractmethod
    def normalize(self, text: str) -> str:
        """
        规范化文本为可朗读形式

        Args:
            text: 输入文本

        Returns:
            规范化后的可朗读文本
        """
        pass

    def get_info(self, text: str) -> Dict[str, Any]:
        """获取规范化信息"""
        return {
            "normalizer": self.name,
            "detected": self.detect(text)
        }

    def _clean_text(self, text: str) -> str:
        """清理文本"""
        text = text.strip()
        text = regex.sub(r"\s+", " ", text)
        return text