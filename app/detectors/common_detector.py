"""通用检测器"""
import regex
from typing import List, Dict, Any
from app.detectors.base_detector import BaseDetector


class CommonDetector(BaseDetector):
    """通用文本检测器 - 用于普通中文文本"""

    def detect(self, text: str) -> bool:
        """检测是否包含中文"""
        return bool(regex.search(r"[\u4e00-\u9fff]", text))

    def extract(self, text: str) -> List[str]:
        """提取中文段落"""
        # 简单分割
        paragraphs = regex.split(r"[。！？.?!]", text)
        return [p.strip() for p in paragraphs if p.strip() and regex.search(r"[\u4e00-\u9fff]", p)]

    def get_info(self, text: str) -> Dict[str, Any]:
        """获取检测信息"""
        return {
            "name": "common",
            "detected": self.detect(text),
            "chinese_ratio": self._get_chinese_ratio(text),
            "paragraphs": len(self.extract(text))
        }

    def _get_chinese_ratio(self, text: str) -> float:
        """获取中文占比"""
        chinese_chars = regex.findall(r"[\u4e00-\u9fff]", text)
        total_chars = len(text.replace(" ", ""))
        if total_chars == 0:
            return 0.0
        return len(chinese_chars) / total_chars