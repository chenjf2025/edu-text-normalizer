"""文本处理辅助工具"""
import re
from typing import List, Optional


class TextHelper:
    """通用文本处理工具"""

    @staticmethod
    def clean_text(text: str) -> str:
        """清理文本，移除多余空格"""
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @staticmethod
    def split_sentences(text: str) -> List[str]:
        """分割句子"""
        # 按中英文句号、问号、感叹号分割
        sentences = re.split(r"[。！？.?!]", text)
        return [s.strip() for s in sentences if s.strip()]

    @staticmethod
    def extract_latex_blocks(text: str) -> List[tuple[str, str]]:
        """提取LaTeX块"""
        blocks = []
        # $...$ 行内公式
        for m in re.finditer(r"\$([^\$]+)\$", text):
            blocks.append(("inline", m.group(1)))
        # $$...$$ 显示公式
        for m in re.finditer(r"\$\$([^\$]+)\$\$", text):
            blocks.append(("display", m.group(1)))
        # \(...\)
        for m in re.finditer(r"\\\((.+?)\\\)", text):
            blocks.append(("parens", m.group(1)))
        # \[...\]
        for m in re.finditer(r"\\\[(.+?)\\\\]", text):
            blocks.append(("bracket", m.group(1)))
        return blocks

    @staticmethod
    def is_pure_chinese(text: str) -> bool:
        """判断是否纯中文"""
        return bool(re.match(r"^[\u4e00-\u9fff]+$", text))

    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """规范化空白字符"""
        text = re.sub(r"[\u200b-\u200f\u2028-\u202f\ufeff]", "", text)
        text = re.sub(r"\s+", " ", text)
        return text

    @staticmethod
    def contains_chinese(text: str) -> bool:
        """判断是否包含中文"""
        return bool(re.search(r"[\u4e00-\u9fff]", text))

    @staticmethod
    def super_to_normal(text: str) -> str:
        """上标转普通"""
        super_map = {
            "⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4",
            "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9",
            "⁺": "+", "⁻": "-", "⁼": "=", "⁽": "(", "⁾": ")",
            "ⁿ": "n", "ˣ": "x"
        }
        for k, v in super_map.items():
            text = text.replace(k, v)
        return text

    @staticmethod
    def sub_to_normal(text: str) -> str:
        """下标转普通"""
        sub_map = {
            "₀": "0", "₁": "1", "₂": "2", "₃": "3", "₄": "4",
            "₅": "5", "₆": "6", "₇": "7", "₈": "8", "₉": "9",
            "₊": "+", "₋": "-", "₌": "=", "₍": "(", "₎": ")",
            "ₙ": "n", "ₓ": "x"
        }
        for k, v in sub_map.items():
            text = text.replace(k, v)
        return text