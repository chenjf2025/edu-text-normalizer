"""数学公式检测器"""
import regex
from typing import List, Dict, Any
from app.detectors.base_detector import BaseDetector


class MathDetector(BaseDetector):
    """数学公式检测器"""

    PATTERNS = {
        "latex_frac": r"\\frac\s*\{[^}]+\}\s*\{[^}]+\}",
        "latex_sqrt": r"\\sqrt(?:\[[^\]]+\])?\s*\{[^}]+\}",
        "latex_power": r"\^{[^}]+}|\^\d|\^\w",
        "latex_integral": r"\\int",
        "latex_sum": r"\\sum",
        "latex_lim": r"\\lim",
        "latex_trig": r"\\(?:sin|cos|tan|cot|sec|csc|arcsin|arccos|arctan)\s*(?:\{[^}]+\}|\()[^()]+(?:\}|\))",
        "latex_log": r"\\(?:log|ln|exp)\s*(?:\{[^}]+\}|\()[^()]+(?:\}|\))",
        "unicode_sqrt": r"√[⁰¹²³⁴⁵⁶⁷⁸⁹ⁿˣ]",
        "unicode_integral": r"∫",
        "unicode_sum": r"∑",
        "unicode_greek": r"[αβγδεζηθικλμνξπρστυφχψωΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ]",
        "unicode_operators": r"[∫∑∏√∞±≠≤≥≈∂∇∈∉⊂⊃∪∩]",
        "super_digits": r"[²³⁴⁵⁶⁷⁸⁹⁰¹⁺⁻⁽⁾ⁿˣ]",
        "division": r"/\s*\d|/\s*[a-zA-Z]",
        "parentheses_expr": r"\([^)]+\)\s*[a-z]",
        # 简单代数表达式：a=b, x=y, a+b=c, x+y=z
        "simple_algebra": r"[a-zA-Z]\s*[=\+\-]\s*[a-zA-Z0-9]",
    }

    def detect(self, text: str) -> bool:
        """检测是否包含数学公式"""
        # 先检查是否有数学特征
        has_latex = bool(regex.search(r"\\[a-zA-Z]+", text))
        has_greek = bool(regex.search(r"[α-ωΑ-Ω]", text))
        has_math_ops = bool(regex.search(r"[√∫∑∏∞±≠≤≥≈∂∇²³⁴⁵⁶⁷⁸⁹⁰¹]", text))

        # 简单代数表达式检测（单字符=单字符/数字，如 x=y, a+b=c）
        # 这个不需要 LaTeX 或数学符号也能检测
        has_simple_algebra = bool(regex.search(r"[a-zA-Z]\s*[=\+\-]\s*[a-zA-Z0-9]", text))

        # 检测 x^2 形式的幂运算
        has_power = bool(regex.search(r"[a-zA-Z0-9]\s*\^\s*[a-zA-Z0-9]", text))

        if has_simple_algebra or has_power:
            # 排除已知的物理公式模式
            physics_patterns = [
                (r"E\s*=\s*m\s*c\s*\^?\s*2", True),
                (r"F\s*=\s*m\s*a", True),
                (r"P\s*=\s*I\s*U", True),
                (r"U\s*=\s*I\s*R", True),
                (r"v\s*=\s*s\s*/\s*t", True),
            ]
            for p, _ in physics_patterns:
                if regex.search(p, text, regex.IGNORECASE):
                    return False
            return True

        if not (has_latex or has_greek or has_math_ops):
            return False

        # 进一步验证是否是数学表达式
        math_latex_cmds = {
            r"\frac", r"\sqrt", r"\sin", r"\cos", r"\tan", r"\cot", r"\sec",
            r"\csc", r"\log", r"\ln", r"\exp", r"\int", r"\sum", r"\prod",
            r"\lim", r"\alpha", r"\beta", r"\gamma", r"\delta", r"\theta",
            r"\pi", r"\sigma", r"\omega", r"\phi", r"\lambda", r"\mu",
            r"\pm", r"\times", r"\div", r"\neq", r"\leq", r"\geq",
        }
        for cmd in math_latex_cmds:
            if cmd in text:
                return True

        # 检查LaTeX模式
        latex_patterns = [
            r"\\\^",        # 幂
            r"\\frac",      # 分数
            r"\\sqrt",      # 根号
            r"\\int",       # 积分
            r"\\sum",       # 求和
            r"\\lim",       # 极限
        ]
        for p in latex_patterns:
            if regex.search(p, text):
                return True

        # 上标数字（平方、立方等）
        if regex.search(r"[²³⁴⁵⁶⁷⁸⁹⁰¹]", text):
            return True

        return False

    def extract(self, text: str) -> List[str]:
        """提取数学表达式"""
        expressions = []

        # 提取LaTeX公式块
        latex_blocks = regex.findall(
            r"\\\((.+?)\\\)|\\\[" + r"(.+?)\\\]|\$([^\$]+)\$",
            text
        )
        for block in latex_blocks:
            for part in block:
                if part and self._is_math_expr(part):
                    expressions.append(part)

        # 提取独立表达式
        for pattern_name, pattern in self.PATTERNS.items():
            matches = regex.findall(pattern, text)
            expressions.extend(matches)

        return list(set(expressions))

    def _is_math_expr(self, text: str) -> bool:
        """判断是否为数学表达式"""
        math_chars = set(r"\[]{}()+-*/=^_√∫∑αβγδθπσω²³⁴⁵⁶⁷⁸⁹⁰")
        return any(c in math_chars for c in text)

    def get_info(self, text: str) -> Dict[str, Any]:
        """获取详细检测信息"""
        expressions = self.extract(text)
        return {
            "name": "math",
            "detected": self.detect(text),
            "count": len(expressions),
            "expressions": expressions,
            "has_unicode": bool(regex.search(r"[√∫∑α-ω]", text)),
            "has_latex": bool(regex.search(r"\\[a-zA-Z]+", text)),
        }