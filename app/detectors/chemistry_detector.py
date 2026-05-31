"""化学公式检测器"""
import regex
from typing import List, Dict, Any
from app.detectors.base_detector import BaseDetector


class ChemistryDetector(BaseDetector):
    """化学公式检测器"""

    # 元素符号(首字母大写，可选小写)
    ELEMENT_PATTERN = r"[A-Z][a-z]?"

    # 化学式模式
    PATTERNS = {
        "simple_formula": r"[A-Z][a-z]?\d*",  # H2O, NaCl
        "subscript_formula": r"[A-Z][a-z]?[₀₁₂₃₄₅₆₇₈₉]+",  # H₂O
        "ionic_formula": r"[A-Z][a-z]?\d*\s*[+-]",  # Na+, Fe3+
        "compound_notation": r"[A-Z][a-z]?\d*[A-Z][a-z]?\d*",  # NaCl, H2SO4
        "reaction_arrow": r"→|←|⇌|->|<-|<=>",
        "chemical_state": r"(?:(?:s|l|g|aq|固|液|气|水溶液))",
    }

    def detect(self, text: str) -> bool:
        """检测是否包含化学公式"""
        # 排除LaTeX命令
        if "\\" in text:
            return False

        # 检查是否像化学式(元素符号开头+可选数字)
        if regex.search(r"^[A-Z][a-z]?\d*$", text.strip()):
            return True
        if regex.search(r"^[A-Z][a-z]?[₀-₉]+$", text.strip()):
            return True

        # 检查化学反应式特征
        for pattern_name, pattern in self.PATTERNS.items():
            if regex.search(pattern, text):
                if pattern_name == "simple_formula":
                    # 需要更严格匹配
                    if regex.search(r"[A-Z][a-z]?\d+", text):
                        return True
                else:
                    return True
        return False

    def extract(self, text: str) -> List[str]:
        """提取化学表达式"""
        formulas = []

        # 提取简单化学式
        simple = regex.findall(r"[A-Z][a-z]?\d*(?:[A-Z][a-z]?\d*)*", text)
        for f in simple:
            if self._is_chemical_formula(f):
                formulas.append(f)

        # 提取下标化学式
        subscript = regex.findall(r"[A-Z][a-z]?[₀-₉]+", text)
        formulas.extend(subscript)

        # 提取化学式中的数字下标
        subscript_num = regex.findall(r"[₀₁₂₃₄₅₆₇₈₉]", text)
        if subscript_num and any(c.isupper() for c in text):
            formulas.append(text)

        return list(set(formulas))

    def _is_chemical_formula(self, text: str) -> bool:
        """判断是否为化学式"""
        # 必须包含至少一个大写字母
        if not regex.search(r"[A-Z]", text):
            return False

        # 排除普通英文单词
        common_words = {"the", "and", "for", "are", "but", "not", "you", "all", "can", "had", "her", "was", "one", "our", "out", "has", "his", "how", "its", "may", "new", "now", "old", "see", "two", "way", "who", "boy", "did", "get", "let", "put", "say", "she", "too", "use"}
        if text.lower() in common_words:
            return False

        # 化学式特征：通常有大写字母开头+可选小写字母+数字
        return bool(regex.match(r"^[A-Z][a-z]?\d*([A-Z][a-z]?\d*)*$", text))

    def get_info(self, text: str) -> Dict[str, Any]:
        """获取详细检测信息"""
        formulas = self.extract(text)
        return {
            "name": "chemistry",
            "detected": self.detect(text),
            "count": len(formulas),
            "formulas": formulas
        }