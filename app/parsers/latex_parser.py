"""LaTeX表达式解析器 - 重构版"""
import re
from typing import Optional
from app.parsers.expression_tree import (
    BaseNode, NumberNode, VariableNode, OperatorNode,
    FractionNode, PowerNode, SqrtNode, AddNode, SubtractNode,
    MultiplyNode, DivideNode, EqualsNode, TrigFunctionNode,
    GreekNode, GroupNode, NodeType, PlusMinusNode, FactorialNode,
)
from app.utils.logger import logger


class LatexParser:
    """LaTeX数学表达式解析器 - 递归下降解析器"""

    GREEK_MAP = {
        r"\alpha": "阿尔法", r"\beta": "贝塔", r"\gamma": "伽马",
        r"\delta": "德尔塔", r"\epsilon": "艾普西隆", r"\zeta": "泽塔",
        r"\eta": "伊塔", r"\theta": "西塔", r"\iota": "约塔",
        r"\kappa": "卡帕", r"\lambda": "拉姆达", r"\mu": "谬",
        r"\nu": "纽", r"\xi": "克西", r"\pi": "派",
        r"\rho": "柔", r"\sigma": "西格玛", r"\tau": "陶",
        r"\upsilon": "宇普西隆", r"\phi": "弗爱", r"\chi": "卡伊",
        r"\psi": "普赛", r"\omega": "欧米伽",
        r"\Alpha": "大写阿尔法", r"\Beta": "大写贝塔",
        r"\Gamma": "大写伽马", r"\Delta": "大写德尔塔",
        r"\Theta": "大写西塔", r"\Lambda": "大写拉姆达",
        r"\Xi": "大写克西", r"\Pi": "大写派",
        r"\Sigma": "大写西格玛", r"\Phi": "大写弗爱",
        r"\Psi": "大写普赛", r"\Omega": "大写欧米伽",
    }

    TRIG_FUNCS = {"sin", "cos", "tan", "cot", "sec", "csc",
                  "arcsin", "arccos", "arctan", "log", "ln", "exp"}

    def __init__(self):
        self.pos = 0
        self.text = ""

    def parse(self, latex: str) -> Optional[BaseNode]:
        """解析LaTeX表达式"""
        try:
            latex = self._preprocess(latex)
            latex = self._convert_plusminus_to_token(latex)
            self.text = latex
            self.pos = 0
            result = self._parse_equation()
            return result
        except Exception as e:
            logger.error(f"LaTeX解析失败: {latex[:50]}, 错误: {e}")
            return None

    def _preprocess(self, latex: str) -> str:
        """预处理 - 使用括号匹配算法处理嵌套结构"""
        # 转换Unicode希腊字母
        greek_unicode = {
            "α": r"\alpha", "β": r"\beta", "γ": r"\gamma",
            "δ": r"\delta", "θ": r"\theta", "π": r"\pi",
            "σ": r"\sigma", "φ": r"\phi", "ω": r"\omega",
        }
        for k, v in greek_unicode.items():
            latex = latex.replace(k, v)

        # 转换Unicode数学符号
        latex = latex.replace("√", r"\sqrt")
        latex = latex.replace("±", "+-")   # Unicode ± -> 加减
        latex = latex.replace("\\pm", "+-")  # LaTeX \pm -> 加减
        latex = latex.replace("\\mp", "-+")  # LaTeX \mp -> 减加
        latex = latex.replace("∫", r"\int")
        latex = latex.replace("∑", r"\sum")
        latex = latex.replace("≠", r"\neq")
        latex = latex.replace("≤", r"\leq")
        latex = latex.replace("≥", r"\geq")

        # 转换上标数字
        super_map = {"⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4",
                    "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9",
                    "⁺": "+", "⁻": "-", "ⁿ": "n", "ˣ": "x"}
        for k, v in super_map.items():
            latex = latex.replace(k, v)

        # 转换下标数字
        sub_map = {"₀": "0", "₁": "1", "₂": "2", "₃": "3", "₄": "4",
                  "₅": "5", "₆": "6", "₇": "7", "₈": "8", "₉": "9",
                  "ₙ": "n", "ₓ": "x"}
        for k, v in sub_map.items():
            latex = latex.replace(k, v)

        # 处理 \frac{...}{...} - 使用括号匹配算法（替代 re.sub）
        latex = self._replace_frac(latex)

        # 处理 \sqrt{...} - 使用括号匹配算法
        latex = self._replace_sqrt(latex)

        # 清理多余空格
        latex = re.sub(r"\s+", " ", latex)

        return latex

    def _convert_plusminus_to_token(self, latex: str) -> str:
        """将 '表达式 +- 表达式' 中的 +- 替换为虚拟 token PLUSMINUS
        
        使用状态机逐字符扫描：
        - 状态 0: 正常
        - 状态 1: 刚读完 +（等待判断是 '+' 还是 '+-'）
        当处于状态 1 时看到空格，继续等待；看到 '-' 才替换为 PLUSMINUS
        """
        result = []
        i = 0
        state = 0  # 0=normal, 1=saw_plus(pending)
        
        while i < len(latex):
            c = latex[i]
            
            if state == 0:
                if c == '+':
                    state = 1
                else:
                    result.append(c)
                i += 1
            elif state == 1:
                if c == ' ':
                    # 空格：继续等待，但先不输出 '+'
                    pass
                elif c == '-':
                    # 找到 +- -> replace with PLUSMINUS
                    result.append('PLUSMINUS')
                    state = 0
                elif c == '+':
                    # 另一个 +：前一个 + 是普通加号，输出后继续等待
                    result.append('+')
                    state = 1
                else:
                    # 其他字符：前一个 + 是普通加号
                    result.append('+')
                    result.append(c)
                    state = 0
                i += 1
        
        if state == 1:
            result.append('+')
        
        return ''.join(result)

    def _find_matching_brace(self, text: str, start: int) -> int:
        """从 start 位置（跳过起始 {）找到匹配的右花括号"""
        if start >= len(text) or text[start] != "{":
            return -1
        count = 1
        i = start + 1
        while i < len(text) and count > 0:
            if text[i] == "{":
                count += 1
            elif text[i] == "}":
                count -= 1
            i += 1
        return i - 1 if count == 0 else -1

    def _replace_frac(self, latex: str) -> str:
        """用括号匹配算法替换 \\frac{num}{den}"""
        result = []
        i = 0
        while i < len(latex):
            # 查找 \frac
            if i < len(latex) - 5 and latex[i:i+5] == r"\frac":
                brace_start = i + 5
                # 找分子 { }
                num_end = self._find_matching_brace(latex, brace_start)
                if num_end != -1:
                    numerator = latex[brace_start+1:num_end]
                    # 找分母
                    after_num = num_end + 1
                    if after_num < len(latex) and latex[after_num] == "{":
                        den_end = self._find_matching_brace(latex, after_num)
                        if den_end != -1:
                            denominator = latex[after_num+1:den_end]
                            result.append(f"FRAC_START {numerator} DIVIDE {denominator} FRAC_END")
                            i = den_end + 1
                            continue
                # 未找到完整格式，跳过 \frac
                result.append(latex[i])
                i += 1
            else:
                result.append(latex[i])
                i += 1
        return "".join(result)

    def _replace_sqrt(self, latex: str) -> str:
        """用括号匹配算法替换 \\sqrt{...}"""
        result = []
        i = 0
        while i < len(latex):
            # 查找 \sqrt
            if i < len(latex) - 5 and latex[i:i+5] == r"\sqrt":
                brace_start = i + 5
                # 判断是否有 [...]
                if brace_start < len(latex) and latex[brace_start] == "[":
                    # 跳过 [...], 找 ]
                    j = brace_start + 1
                    while j < len(latex) and latex[j] != "]":
                        j += 1
                    brace_start = j + 1
                # 找 { }
                if brace_start < len(latex) and latex[brace_start] == "{":
                    end = self._find_matching_brace(latex, brace_start)
                    if end != -1:
                        content = latex[brace_start+1:end]
                        result.append(f"SQRT {content}")
                        i = end + 1
                        continue
                # 格式不对，跳过
                result.append(latex[i])
                i += 1
            else:
                result.append(latex[i])
                i += 1
        return "".join(result)

    def _parse_equation(self) -> Optional[BaseNode]:
        """解析等式或表达式"""
        left = self._parse_additive()
        if left and self._skip("="):
            right = self._parse_additive()
            if right:
                return EqualsNode(left, right)
        return left

    def _parse_additive(self) -> Optional[BaseNode]:
        """解析加减和加减号"""
        left = self._parse_multiplicative()
        while True:
            if self._skip("+"):
                # 检查是否是 PLUSMINUS（加减号）
                if self._skip("-"):
                    if left:
                        right = self._parse_multiplicative()
                        if right:
                            left = PlusMinusNode(left, right)
                    else:
                        self._skip("-")  # consume
                else:
                    right = self._parse_multiplicative()
                    if left and right:
                        left = AddNode(left, right)
                    else:
                        left = right or left
            elif self._skip("-"):
                right = self._parse_multiplicative()
                if left and right:
                    left = SubtractNode(left, right)
                else:
                    left = right or left
            elif self._skip("PLUSMINUS"):
                if left:
                    right = self._parse_multiplicative()
                    if right:
                        left = PlusMinusNode(left, right)
            else:
                break
        return left

    def _parse_multiplicative(self) -> Optional[BaseNode]:
        """解析乘除（含隐式乘法如 2a 表示 2*a）"""
        left = self._parse_power()
        while True:
            # 先检查是否还有内容
            if self.pos >= len(self.text):
                break

            matched = False
            # 检查 PLUSMINUS（加减号）- 在隐式乘法之前处理
            if self._skip("PLUSMINUS"):
                matched = True
                right = self._parse_power()
                if left and right:
                    left = PlusMinusNode(left, right)
                else:
                    left = right or left
            if self._skip("*") or self._skip("·"):
                matched = True
                right = self._parse_power()
                if left and right:
                    left = MultiplyNode(left, right)
                else:
                    left = right or left
            elif self._skip("/") or self._skip("DIVIDE"):
                matched = True
                right = self._parse_power()
                if left and right:
                    left = DivideNode(left, right)
                else:
                    left = right or left
            elif self._is_implicit_mult():
                matched = True
                right = self._parse_power()
                if left and right:
                    left = MultiplyNode(left, right)
                else:
                    left = right or left

            if not matched:
                break
        return left

    def _is_implicit_mult(self) -> bool:
        """检测是否是隐式乘法（如 2a 表示 2*a）

        条件：
        1. 当前是字母开头
        2. 前一个已解析的token是数字或变量（不是操作符如DIVIDE）
        """
        if self.pos >= len(self.text):
            return False
        c = self.text[self.pos]
        if not (c.isalpha() or c == "\\"):
            return False
        # 检查前面的内容是否看起来是数字
        # 查找前一个token
        before = self.text[:self.pos].strip()
        if not before:
            return False
        # 如果前面是 DIVIDE, +, -, (, FRAC_START, PLUSMINUS 等，不做隐式乘法
        forbidden = ["DIVIDE", "FRAC_START", "FRAC_END", "+", "-", "(", "^", "SQRT", "PLUSMINUS"]
        for f in forbidden:
            if before.endswith(f) or before.rstrip().endswith(f):
                return False
        return True

    def _parse_power(self) -> Optional[BaseNode]:
        """解析幂运算"""
        base = self._parse_unary()
        if base and self._skip("^"):
            exp = self._parse_unary()
            if base and exp:
                return PowerNode(base, exp)
        return base

    def _parse_unary(self) -> Optional[BaseNode]:
        """解析一元运算"""
        if self._skip("+"):
            return self._parse_unary()
        if self._skip("-"):
            operand = self._parse_unary()
            if operand:
                if isinstance(operand, NumberNode):
                    return NumberNode("-" + operand.value)
                return MultiplyNode(NumberNode("-1"), operand)
        result = self._parse_primary()
        # 阶乘后缀: n! -> n的阶乘
        if result and self._skip("!"):
            return FactorialNode(result)
        return result

    def _parse_primary(self) -> Optional[BaseNode]:
        """解析基本元素"""
        self._skip_whitespace()

        # 处理 FRAC_END - 直接返回None，表示分数解析结束
        if self._skip("FRAC_END"):
            return None

        # 处理特殊标记
        if self._skip("FRAC_START"):
            # 收集分子文本（直到 DIVIDE 为止）
            num_start = self.pos
            while self.pos < len(self.text) and not self.text[self.pos:].startswith("DIVIDE"):
                self.pos += 1
            num_text = self.text[num_start:self.pos].strip()

            # 跳过 DIVIDE
            self._skip("DIVIDE")

            # 收集分母文本（直到 FRAC_END 为止）
            den_start = self.pos
            while self.pos < len(self.text) and not self.text[self.pos:].startswith("FRAC_END"):
                self.pos += 1
            den_text = self.text[den_start:self.pos].strip()

            # 跳过 FRAC_END
            self._skip("FRAC_END")

            # 解析分子和分母
            # 临时切换文本进行解析
            old_text = self.text
            old_pos = self.pos

            # 解析分子
            numerator = self._parse_single_expr(num_text) if num_text else None
            # 解析分母
            denominator = self._parse_single_expr(den_text) if den_text else None

            if numerator and denominator:
                return FractionNode(numerator, denominator)
            return numerator or denominator

        if self._skip("SQRT"):
            arg = self._parse_primary()
            if arg:
                return SqrtNode(arg)
            return None

        if self._skip("("):
            content = self._parse_equation()
            self._skip(")")
            return GroupNode(content) if content else None

        if self._peek().isdigit():
            return self._parse_number()

        if self._peek().isalpha() or self._peek() == "\\":
            return self._parse_symbol()

        return None

    def _parse_number(self) -> Optional[BaseNode]:
        """解析数字"""
        start = self.pos
        while self.pos < len(self.text) and (self.text[self.pos].isdigit() or self.text[self.pos] == "."):
            self.pos += 1
        return NumberNode(self.text[start:self.pos]) if start < self.pos else None

    def _parse_symbol(self) -> Optional[BaseNode]:
        """解析符号"""
        # LaTeX命令
        if self._skip("\\"):
            name = ""
            while self.pos < len(self.text) and self.text[self.pos].isalpha():
                name += self.text[self.pos]
                self.pos += 1

            # 完整的LaTeX命令（带反斜杠）
            full_name = "\\" + name

            # 希腊字母
            if full_name in self.GREEK_MAP:
                return GreekNode(self.GREEK_MAP[full_name], full_name)

            # 三角函数
            if name in self.TRIG_FUNCS:
                arg = self._parse_primary()
                if arg:
                    return TrigFunctionNode(name, arg)
                return VariableNode(name)

            return VariableNode(name)

        # 普通变量名
        name = ""
        while self.pos < len(self.text) and (self.text[self.pos].isalpha() or self.text[self.pos].isdigit() or self.text[self.pos] == "_"):
            name += self.text[self.pos]
            self.pos += 1

        if name:
            return VariableNode(name)
        return None

    def _parse_single_expr(self, expr_text: str) -> Optional[BaseNode]:
        """用独立解析器解析单个表达式文本"""
        if not expr_text:
            return None
        # 临时保存状态
        old_text = self.text
        old_pos = self.pos
        # 设置新文本
        self.text = expr_text
        self.pos = 0
        # 解析
        result = self._parse_additive()
        # 恢复状态
        self.text = old_text
        self.pos = old_pos
        return result

    def _peek(self) -> str:
        """查看当前字符"""
        self._skip_whitespace()
        return self.text[self.pos] if self.pos < len(self.text) else ""

    def _skip(self, s: str) -> bool:
        """跳过指定字符串"""
        self._skip_whitespace()
        if self.text[self.pos:self.pos + len(s)] == s:
            self.pos += len(s)
            return True
        return False

    def _skip_whitespace(self):
        """跳过空白"""
        while self.pos < len(self.text) and self.text[self.pos] in " \t":
            self.pos += 1


class UnicodeMathParser:
    """Unicode数学表达式解析器"""

    GREEK_UNICODE = {
        "α": "阿尔法", "β": "贝塔", "γ": "伽马", "δ": "德尔塔",
        "ε": "艾普西隆", "ζ": "泽塔", "η": "伊塔", "θ": "西塔",
        "ι": "约塔", "κ": "卡帕", "λ": "拉姆达", "μ": "谬",
        "ν": "纽", "ξ": "克西", "π": "派", "ρ": "柔",
        "σ": "西格玛", "τ": "陶", "υ": "宇普西隆", "φ": "弗爱",
        "χ": "卡伊", "ψ": "普赛", "ω": "欧米伽",
        "Γ": "大写伽马", "Δ": "大写德尔塔", "Θ": "大写西塔",
        "Λ": "大写拉姆达", "Ξ": "大写克西", "Π": "大写派",
        "Σ": "大写西格玛", "Φ": "大写弗爱", "Ψ": "大写普赛", "Ω": "大写欧米伽",
    }

    def parse(self, text: str) -> Optional[BaseNode]:
        """解析Unicode数学文本"""
        try:
            # 转换Unicode希腊字母
            for sym, name in self.GREEK_UNICODE.items():
                text = text.replace(sym, name)

            parser = LatexParser()
            return parser.parse(text)
        except Exception as e:
            logger.error(f"Unicode解析失败: {text[:50]}, 错误: {e}")
            return None