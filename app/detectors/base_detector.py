"""检测器基类"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import regex


class BaseDetector(ABC):
    """检测器基类"""

    def __init__(self):
        self.name = self.__class__.__name__.replace("Detector", "")

    @abstractmethod
    def detect(self, text: str) -> bool:
        """
        检测文本是否包含该学科内容

        Args:
            text: 输入文本

        Returns:
            True if detected
        """
        pass

    @abstractmethod
    def extract(self, text: str) -> list:
        """
        提取该学科相关的表达式

        Args:
            text: 输入文本

        Returns:
            提取的表达式列表
        """
        pass

    def get_info(self, text: str) -> Dict[str, Any]:
        """获取检测信息"""
        return {
            "name": self.name,
            "detected": self.detect(text),
            "count": len(self.extract(text)) if self.detect(text) else 0
        }