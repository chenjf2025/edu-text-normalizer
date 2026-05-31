"""正则表达式辅助工具"""
import regex
from typing import List, Tuple, Optional


class RegexHelper:
    """常用正则模式集合"""

    GREEK_PATTERNS = {
        "alpha": r"\balpha\b",
        "beta": r"\bbeta\b",
        "gamma": r"\bgamma\b",
        "delta": r"\bdelta\b",
        "epsilon": r"\bepsilon\b",
        "theta": r"\btheta\b",
        "lambda": r"\blambda\b",
        "mu": r"\bmu\b",
        "pi": r"\bpi\b",
        "sigma": r"\bsigma\b",
        "phi": r"\bphi\b",
        "omega": r"\bomega\b",
    }

    MATH_SYMBOLS = {
        "integral": r"∫|\\int",
        "sum": r"∑|\\sum",
        "product": r"∏|\\prod",
        "infinity": r"∞|\\infty",
        "plus_minus": r"±|\\pm",
        "not_equal": r"≠|\\neq",
        "less_equal": r"≤|\\leq",
        "greater_equal": r"≥|\\geq",
        "approx": r"≈|\\approx",
        "sqrt": r"√|\\sqrt",
        "forall": r"∀|\\forall",
        "exists": r"∃|\\exists",
        "partial": r"∂|\\partial",
        "nabla": r"∇|\\nabla",
    }

    LATEX_FRAC = r"\\frac\s*\{[^}]+\}\s*\{[^}]+\}"
    LATEX_SQRT = r"\\sqrt(?:\[[^\]]+\])?\s*\{[^}]+\}"
    LATEX_POWER = r"\^|\^{[^}]+}"
    LATEX_SUBSCRIPT = r"_[^{]|_[^{]{[^}]+}"
    LATEX_BEGINS = r"\\\(|\\\[|\$(?:[^\$]+\$)?"

    @classmethod
    def find_all_matches(cls, pattern: str, text: str) -> List[Tuple[str, int, int]]:
        """查找所有匹配项"""
        results = []
        for m in regex.finditer(pattern, text, regex.IGNORECASE):
            results.append((m.group(), m.start(), m.end()))
        return results

    @classmethod
    def contains_math(cls, text: str) -> bool:
        """检测是否包含数学表达式"""
        patterns = [
            cls.LATEX_FRAC,
            cls.LATEX_SQRT,
            cls.LATEX_POWER,
            r"[²³⁴⁵⁶⁷⁸⁹⁰]",
            r"[∫∑√±≠≤≥≈]",
            r"\\frac|\\sqrt|\\int|\\sum",
            r"\^\{|\^\d|\^\w",
        ]
        for p in patterns:
            if regex.search(p, text):
                return True
        return False

    @classmethod
    def contains_chemistry(cls, text: str) -> bool:
        """检测是否包含化学式"""
        # 元素符号大写+可选小写+数字 (如 H2O, NaCl, CO2)
        pattern = r"^[A-Z][a-z]?\d*(?:[A-Z][a-z]?\d*)*$"
        if regex.search(pattern, text):
            return True
        # 下标数字 (如 H₂O)
        if regex.search(r"[₀₁₂₃₄₅₆₇₈₉]|\\d", text):
            return True
        return False

    @classmethod
    def contains_physics(cls, text: str) -> bool:
        """检测是否包含物理单位"""
        pattern = r"\d+([.,]\d+)?\s*(m|s|kg|A|K|mol|cd|Hz|N|J|W|V|Ω|F|Pa|T|H|Wb|S)\s*(/\s*(s|m|kg|A|K|Hz|N|J|W|V|Ω|F|Pa|T|H|Wb|S)\s*)?"
        if regex.search(pattern, text):
            return True
        return False