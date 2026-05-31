"""数学规范化器 - 核心组件"""
import re
from typing import Optional, List
from app.normalizers.base_normalizer import BaseNormalizer
from app.parsers.ast_builder import ASTBuilder
from app.utils.logger import logger


class MathNormalizer(BaseNormalizer):
    """数学公式规范化器 - 核心大脑"""

    def __init__(self):
        super().__init__()
        self.ast_builder = ASTBuilder()

    def detect(self, text: str) -> bool:
        """检测是否包含数学公式"""
        math_patterns = [
            r"\\[a-zA-Z]+\{",  # LaTeX命令带花括号
            r"\\[a-zA-Z]+(?:\b|[^a-zA-Z])",  # LaTeX命令不带花括号（希腊字母等）
            r"[\^_√∫∑]",  # Unicode数学符号
            r"[²³⁴⁵⁶⁷⁸⁹⁰ⁱⁿˣ]+",  # 上标
            r"[₀-₉ₙₓ]+",  # 下标
        ]
        for p in math_patterns:
            if re.search(p, text):
                return True
        return False

    def normalize(self, text: str) -> str:
        """规范化数学文本为可朗读形式 - 核心方法"""
        try:
            processed = self._preprocess(text)
            segments = self._split_segments(processed)
            results = []
            for segment in segments:
                if self._is_math_segment(segment):
                    speech = self._normalize_math(segment)
                    results.append(speech)
                else:
                    results.append(segment)
            final = self._merge_results(results)
            return final
        except Exception as e:
            logger.error(f"数学规范化失败: {text}, 错误: {e}")
            return text

    def _preprocess(self, text: str) -> str:
        """预处理文本"""
        # Unicode上标转换
        super_map = {"⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4",
                    "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9",
                    "⁺": "+", "⁻": "-", "ⁿ": "n", "ˣ": "x"}
        text = re.sub(r'([a-zA-Z0-9])([⁰¹²³⁴⁵⁶⁷⁸⁹ⁿˣ])',
                     lambda m: m.group(1) + '^' + super_map[m.group(2)], text)
        for k, v in super_map.items():
            text = text.replace(k, v)

        # Unicode下标
        sub_map = {"₀": "0", "₁": "1", "₂": "2", "₃": "3", "₄": "4",
                  "₅": "5", "₆": "6", "₇": "7", "₈": "8", "₉": "9",
                  "ₙ": "n", "ₓ": "x"}
        for k, v in sub_map.items():
            text = text.replace(k, v)

        # 希腊字母Unicode
        greek_map = {
            "α": r"\alpha", "β": r"\beta", "γ": r"\gamma", "δ": r"\delta",
            "ε": r"\epsilon", "η": r"\eta", "θ": r"\theta", "λ": r"\lambda",
            "μ": r"\mu", "π": r"\pi", "σ": r"\sigma", "φ": r"\phi",
            "ψ": r"\psi", "ω": r"\omega",
        }
        for k, v in greek_map.items():
            text = text.replace(k, v)

        # Unicode数学符号
        symbol_map = {"√": r"\sqrt", "∫": r"\int", "∑": r"\sum",
                     "≠": r"\neq", "≤": r"\leq", "≥": r"\geq"}
        for k, v in symbol_map.items():
            text = text.replace(k, v)

        return text

    def _split_segments(self, text: str) -> List[str]:
        """将文本分割为数学段和非数学段"""
        segments = []
        current = []
        in_math = False
        i = 0
        while i < len(text):
            c = text[i]
            # 检测数学区域开始
            if not in_math:
                if c == '$' or (c == '\\' and i + 1 < len(text) and text[i:i+2] in [r'\(', r'\[', r'\\(']):
                    if c == '$':
                        segments.append(text[i])
                        i += 1
                        in_math = True
                        continue
                    elif text[i:i+2] in [r'\(', r'\[', r'\\(']:
                        if current:
                            segments.append(''.join(current))
                            current = []
                        segments.append(text[i:i+2])
                        i += 2
                        in_math = True
                        continue
                current.append(c)
            else:
                # 在数学区域内
                if c == '$':
                    segments.append('$')
                    i += 1
                    in_math = False
                    continue
                elif text[i:i+2] in [r'\)', r'\]', r'\\)', r'\\]']:
                    segments.append(text[i:i+2])
                    i += 2
                    in_math = False
                    continue
                current.append(c)
            i += 1
        if current:
            segments.append(''.join(current))
        return segments if segments else [text]

    def _is_math_segment(self, segment: str) -> bool:
        """判断片段是否为数学内容"""
        if segment in ['$', r'\(', r'\[', r'\\(', r'\)', r'\]', r'\\)', r'\\]']:
            return False
        if segment.startswith('$') or segment.startswith(('\\(', '\\[', '\\\\(')):
            return True
        math_chars = r'\^√∫∑≠≤≥\frac\sqrt\sum\int\alpha\beta\gamma\pi'
        return bool(re.search(r'\\?[a-zA-Z_]+\^?|[√∫∑]|\\frac|\\sqrt', segment))

    def _normalize_math(self, text: str) -> str:
        """核心数学规范化"""
        cleaned = self._clean_math_wrapper(text)
        result = self._rule_based_normalize(cleaned)
        return result

    def _clean_math_wrapper(self, text: str) -> str:
        """去除数学包装符号"""
        text = re.sub(r'^\$+|\$+$', '', text)
        text = re.sub(r'^\\?\($|\\?\)$', '', text)
        text = re.sub(r'^\\?\[|\\?\]$', '', text)
        return text.strip()

    def _rule_based_normalize(self, text: str) -> str:
        """基于规则的规范化，使用嵌套花括号解析"""
        result = text

        # 1. 处理嵌套 \frac
        result = self._replace_frac_nested(result)

        # 2. 处理其他 LaTeX 命令
        result = self._to_speech_recursive(result)

        # 3. 清理多余空格
        result = re.sub(r'\s+', '', result)
        result = re.sub(r'点\.', '点', result)
        result = re.sub(r'等于等于', '等于', result)
        result = re.sub(r'除以除以', '除以', result)
        result = re.sub(r'加减加减', '加减', result)
        result = re.sub(r'加\.?减', '加减', result)
        result = re.sub(r'减\.?加', '加减', result)

        return result

    def _extract_balanced(self, text: str, start: int) -> tuple:
        """从start位置开始提取配对花括号内容（不包括外层花括号）
        Returns: (内容, 下一个位置) 或 (None, start) 如果没找到
        """
        if start >= len(text) or text[start] != '{':
            return None, start
        depth = 1
        i = start + 1
        while i < len(text) and depth > 0:
            if text[i] == '{':
                depth += 1
            elif text[i] == '}':
                depth -= 1
                if depth == 0:
                    return text[start + 1:i], i + 1
            i += 1
        return None, start

    def _replace_frac_nested(self, text: str) -> str:
        """处理嵌套花括号的 \frac
        例如：\frac{-b \pm \sqrt{b^{ 2} - 4 a c}}{2 a}
        分两步：(1) 提取分子；(2) 判断是否有分母
        """
        i = 0
        result = []
        while i < len(text):
            # 查找 \frac
            frac_pos = text.find(r'\frac', i)
            if frac_pos == -1:
                result.append(text[i:])
                break

            result.append(text[i:frac_pos])
            i = frac_pos + 5  # past '\frac'

            # 跳过空白
            while i < len(text) and text[i] in ' \t\n':
                i += 1

            if i >= len(text) or text[i] != '{':
                result.append(r'\frac')
                continue

            # (1) 提取分子内容（不包括花括号）
            numerator, next_pos = self._extract_balanced(text, i)
            if numerator is None:
                result.append(r'\frac')
                continue

            # next_pos 指向分子 } 之后的第一个字符
            j = next_pos

            # (2) 在分子 } 之后找非空白字符，看是否有分母
            skip_ws = j
            while skip_ws < len(text) and text[skip_ws] in ' \t\n':
                skip_ws += 1

            if skip_ws < len(text) and text[skip_ws] == '{':
                # 有分母
                denom_content, denom_next = self._extract_balanced(text, skip_ws)
                if denom_content is not None:
                    num_speech = self._to_speech_recursive(numerator)
                    denom_speech = self._to_speech_recursive(denom_content)
                    result.append(f"({num_speech}除以{denom_speech})")
                    j = denom_next
                else:
                    result.append(r'\frac')
                    result.append('{' + numerator + '}')
                    j = skip_ws + 1
            else:
                # 没有分母，只有分子
                num_speech = self._to_speech_recursive(numerator)
                result.append(f"({num_speech})")

            i = j

        return ''.join(result)

    def _to_speech_recursive(self, expr: str) -> str:
        """递归地将表达式转为朗读文本，处理嵌套花括号"""
        if not expr:
            return expr
        expr = expr.strip()
        if not expr:
            return ""

        # 递归去掉首尾配对花括号
        while expr.startswith('{') and expr.endswith('}') and self._is_balanced(expr[1:-1]):
            expr = expr[1:-1].strip()

        if not expr:
            return ""

        # 递归处理嵌套的 frac
        expr = self._replace_frac_nested(expr)

        # 处理 \sqrt{...} 完整配对
        while r'\sqrt{' in expr:
            expr = self._process_sqrt(expr)

        # 先规范化花括号内的空格（OCR输出如 b^{ 2}）
        expr = re.sub(r'\{\s+', '{', expr)
        expr = re.sub(r'\s+\}', '}', expr)

        # 处理幂：顺序很重要！
        # 1. base^{exp} 形式：b^{2} -> b的2次方
        expr = re.sub(r'([a-zA-Z0-9])\s*\^\s*\{([^{}]*)\}',
                       r'\1的\2次方', expr)
        # 2. {base}^{exp} 形式：{b}^{2} -> b的2次方
        expr = re.sub(r'\{([^{}]*)\}\s*\^\s*\{([^{}]*)\}',
                       lambda m: f"{m.group(1)}的{m.group(2)}次方", expr)
        # 3. base^exp 无括号形式：b^2 -> b的2次方
        expr = re.sub(r'([a-zA-Z0-9])\s*\^\s*([a-zA-Z0-9]+)',
                       r'\1的\2次方', expr)

        # 希腊字母和符号
        greek = {
            r'\alpha': '阿尔法', r'\beta': '贝塔', r'\gamma': '伽马',
            r'\delta': '德尔塔', r'\epsilon': '艾普西隆', r'\theta': '西塔',
            r'\lambda': '拉姆达', r'\mu': '谬', r'\pi': '派',
            r'\sigma': '西格玛', r'\phi': '弗爱', r'\omega': '欧米伽',
            r'\eta': '伊塔', r'\rho': '柔', r'\tau': '陶',
            r'\upsilon': '宇普西隆', r'\psi': '普赛', r'\chi': '卡伊',
            r'\pm': '加减', r'\times': '乘', r'\div': '除以',
        }
        for latex, cn in greek.items():
            expr = expr.replace(latex, cn)
        # 运算符
        expr = expr.replace('+', '加').replace('-', '减')
        expr = expr.replace('*', '乘').replace('/', '除以')
        expr = expr.replace('=', '等于')
        return expr

    def _process_sqrt(self, text: str) -> str:
        """处理第一个 \sqrt{...} 配对，将其转为 根号下..."""
        start = text.find(r'\sqrt{')
        if start == -1:
            return text
        # 找到匹配的 }
        i = start + 6  # past '\sqrt{'
        depth = 1
        content_chars = []
        while i < len(text) and depth > 0:
            c = text[i]
            if c == '{':
                depth += 1
                content_chars.append(c)
            elif c == '}':
                depth -= 1
                if depth == 0:
                    break
                content_chars.append(c)
            else:
                content_chars.append(c)
            i += 1
        content = ''.join(content_chars)
        # 递归处理根号内的内容
        inner = self._to_speech_recursive(content)
        return text[:start] + '根号下' + inner + text[i+1:]

    def _is_balanced(self, text: str) -> bool:
        """检查字符串中的花括号是否配对"""
        depth = 0
        for c in text:
            if c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth < 0:
                    return False
        return depth == 0

    def _merge_results(self, results: List[str]) -> str:
        """合并分段处理结果"""
        merged = ''.join(results)
        # 清理多余标点
        merged = re.sub(r'。+', '。', merged)
        merged = re.sub(r'，+', '，', merged)
        merged = re.sub(r'、+', '、', merged)
        return merged.strip()