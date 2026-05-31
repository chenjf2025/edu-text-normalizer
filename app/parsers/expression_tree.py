"""表达式AST节点定义"""
from abc import ABC, abstractmethod
from typing import List, Optional, Any
from enum import Enum


class NodeType(Enum):
    """AST节点类型"""
    NUMBER = "number"
    VARIABLE = "variable"
    OPERATOR = "operator"
    FRACTION = "fraction"
    POWER = "power"
    ROOT = "root"
    SUBSCRIPT = "subscript"
    SUPERSCRIPT = "superscript"
    ADD = "add"
    SUBTRACT = "subtract"
    PLUSMINUS = "plusminus"
    MULTIPLY = "multiply"
    DIVIDE = "divide"
    EQUALS = "equals"
    SIN = "sin"
    COS = "cos"
    TAN = "tan"
    LOG = "log"
    LN = "ln"
    EXP = "exp"
    INTEGRAL = "integral"
    SUM = "sum"
    LIMIT = "limit"
    DERIVATIVE = "derivative"
    GREEK = "greek"
    FUNCTION = "function"
    GROUP = "group"
    ABS = "abs"
    SQRT = "sqrt"


class BaseNode(ABC):
    """AST节点基类"""

    def __init__(self, node_type: NodeType):
        self.node_type = node_type

    @abstractmethod
    def to_speech(self) -> str:
        """转换为语音文本"""
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}>"


class NumberNode(BaseNode):
    """数字节点"""

    def __init__(self, value: str | float):
        super().__init__(NodeType.NUMBER)
        # 统一存储为字符串以便比较
        self.value = str(value)

    def to_speech(self) -> str:
        # 处理中文数字朗读
        val = self.value
        # 负数
        if val.startswith("-"):
            return f"负{self._num_to_chinese(val[1:])}"
        return self._num_to_chinese(val)
    
    def _num_to_chinese(self, num_str: str) -> str:
        """将数字字符串转换为中文朗读"""
        # 处理小数点
        if "." in num_str:
            parts = num_str.split(".")
            integer = parts[0] or "0"
            decimal = parts[1] if len(parts) > 1 else ""
            result = integer
            if decimal:
                result += "点" + "".join(decimal)
            return result
        # 特殊处理整数
        try:
            val = int(num_str)
            if val == 0:
                return "0"
            return str(val)
        except ValueError:
            return num_str


class VariableNode(BaseNode):
    """变量节点"""

    def __init__(self, name: str, subscript: Optional[str] = None):
        super().__init__(NodeType.VARIABLE)
        self.name = name
        self.subscript = subscript

    def to_speech(self) -> str:
        if self.subscript:
            return f"{self.name}下标{self.subscript}"
        return self.name


class OperatorNode(BaseNode):
    """运算符节点"""

    def __init__(self, symbol: str):
        super().__init__(NodeType.OPERATOR)
        self.symbol = symbol

    def to_speech(self) -> str:
        op_map = {
            "+": "加",
            "-": "减",
            "*": "乘",
            "/": "除",
            "=": "等于",
            "==": "等于",
            "!=": "不等于",
            "<": "小于",
            ">": "大于",
            "<=": "小于等于",
            ">=": "大于等于",
        }
        return op_map.get(self.symbol, self.symbol)


class FractionNode(BaseNode):
    """分数节点"""

    def __init__(self, numerator: BaseNode, denominator: BaseNode):
        super().__init__(NodeType.FRACTION)
        self.numerator = numerator
        self.denominator = denominator

    def to_speech(self) -> str:
        num_speech = self.numerator.to_speech()
        den_speech = self.denominator.to_speech()
        # 如果分子是负数开头，朗读为"负..."
        if num_speech.startswith("-"):
            num_speech = "负" + num_speech[1:]
        # 如果分母是乘法节点（如 2*a），表示"整体除以"
        if isinstance(self.denominator, MultiplyNode):
            return f"{num_speech}整体除以{den_speech}"
        # 如果分母是单个数字（如 2），表示"整体除以"更自然
        if isinstance(self.denominator, NumberNode):
            return f"{num_speech}整体除以{den_speech}"
        # 如果分母是单个变量（如 a），表示"整体除以"
        if isinstance(self.denominator, VariableNode):
            return f"{num_speech}整体除以{den_speech}"
        # 其他情况（如复合表达式），也加整体
        return f"{num_speech}整体除以{den_speech}"


class PowerNode(BaseNode):
    """幂节点"""

    def __init__(self, base: BaseNode, exponent: BaseNode):
        super().__init__(NodeType.POWER)
        self.base = base
        self.exponent = exponent

    def to_speech(self) -> str:
        base_speech = self.base.to_speech()
        exp_speech = self.exponent.to_speech()
        # 特殊指数朗读
        exp_int = None
        if isinstance(self.exponent, NumberNode):
            try:
                exp_int = int(self.exponent.value)
            except ValueError:
                pass
        
        if exp_int == 2:
            return f"{base_speech}的平方"
        elif exp_int == 3:
            return f"{base_speech}的立方"
        elif exp_int == 0.5 or exp_int == 0:
            return f"{base_speech}的{exp_speech}次方"
        else:
            return f"{base_speech}的{exp_speech}次方"


class RootNode(BaseNode):
    """根号节点"""

    def __init__(self, degree: Optional[BaseNode], radicand: BaseNode):
        super().__init__(NodeType.ROOT)
        self.degree = degree
        self.radicand = radicand

    def to_speech(self) -> str:
        radicand_speech = self.radicand.to_speech()
        if self.degree:
            degree_speech = self.degree.to_speech()
            return f"{degree_speech}次根号下{self.radicand.to_speech()}"
        return f"根号下{radicand_speech}"


class SqrtNode(BaseNode):
    """平方根节点"""

    def __init__(self, radicand: BaseNode):
        super().__init__(NodeType.SQRT)
        self.radicand = radicand

    def to_speech(self) -> str:
        return f"根号下{self.radicand.to_speech()}"


class AddNode(BaseNode):
    """加法节点"""

    def __init__(self, left: BaseNode, right: BaseNode):
        super().__init__(NodeType.ADD)
        self.left = left
        self.right = right

    def to_speech(self) -> str:
        return f"{self.left.to_speech()}加{self.right.to_speech()}"


class SubtractNode(BaseNode):
    """减法节点"""

    def __init__(self, left: BaseNode, right: BaseNode):
        super().__init__(NodeType.SUBTRACT)
        self.left = left
        self.right = right

    def to_speech(self) -> str:
        return f"{self.left.to_speech()}减{self.right.to_speech()}"


class PlusMinusNode(BaseNode):
    """加减节点 (±) - 左右子树分别是加和减的结果"""

    def __init__(self, left: BaseNode, right: BaseNode):
        super().__init__(NodeType.PLUSMINUS)
        self.left = left
        self.right = right

    def to_speech(self) -> str:
        left_speech = self.left.to_speech()
        right_speech = self.right.to_speech()
        return f"{left_speech}加减{right_speech}"


class MultiplyNode(BaseNode):
    """乘法节点"""

    def __init__(self, left: BaseNode, right: BaseNode):
        super().__init__(NodeType.MULTIPLY)
        self.left = left
        self.right = right

    def to_speech(self) -> str:
        # 处理 -1
        if isinstance(self.left, NumberNode):
            val = self.left.value
            if val == "-1.0" or val == "-1":
                return f"负{self.right.to_speech()}"
            elif val == "1.0" or val == "1":
                return self.right.to_speech()
            else:
                return f"{self.left.to_speech()}倍{self.right.to_speech()}"
        # 变量在左边
        if isinstance(self.left, VariableNode) and isinstance(self.right, VariableNode):
            return f"{self.left.to_speech()}{self.right.to_speech()}"
        return f"{self.left.to_speech()}乘{self.right.to_speech()}"


class DivideNode(BaseNode):
    """除法节点"""

    def __init__(self, left: BaseNode, right: BaseNode):
        super().__init__(NodeType.DIVIDE)
        self.left = left
        self.right = right

    def to_speech(self) -> str:
        return f"{self.left.to_speech()}除以{self.right.to_speech()}"


class EqualsNode(BaseNode):
    """等式节点"""

    def __init__(self, left: BaseNode, right: BaseNode):
        super().__init__(NodeType.EQUALS)
        self.left = left
        self.right = right

    def to_speech(self) -> str:
        return f"{self.left.to_speech()}等于{self.right.to_speech()}"


class TrigFunctionNode(BaseNode):
    """三角函数节点"""

    def __init__(self, func_name: str, argument: BaseNode):
        super().__init__(NodeType.FUNCTION)
        self.func_name = func_name
        self.argument = argument

    def to_speech(self) -> str:
        func_map = {
            "sin": "正弦",
            "cos": "余弦",
            "tan": "正切",
            "cot": "余切",
            "sec": "正割",
            "csc": "余割",
            "arcsin": "反正弦",
            "arccos": "反余弦",
            "arctan": "反正切",
        }
        return f"{func_map.get(self.func_name, self.func_name)}({self.argument.to_speech()})"


class LogFunctionNode(BaseNode):
    """对数函数节点"""

    def __init__(self, base: Optional[BaseNode], argument: BaseNode):
        super().__init__(NodeType.LOG)
        self.base = base
        self.argument = argument

    def to_speech(self) -> str:
        if self.base:
            return f"以{self.base.to_speech()}为底{self.argument.to_speech()}的对数"
        return f"log({self.argument.to_speech()})"


class LnFunctionNode(BaseNode):
    """自然对数节点"""

    def __init__(self, argument: BaseNode):
        super().__init__(NodeType.LN)
        self.argument = argument

    def to_speech(self) -> str:
        return f"ln({self.argument.to_speech()})"


class IntegralNode(BaseNode):
    """积分节点"""

    def __init__(self, integrand: BaseNode, variable: BaseNode,
                 lower: Optional[BaseNode] = None, upper: Optional[BaseNode] = None):
        super().__init__(NodeType.INTEGRAL)
        self.integrand = integrand
        self.variable = variable
        self.lower = lower
        self.upper = upper

    def to_speech(self) -> str:
        if self.lower and self.upper:
            return (f"从{self.lower.to_speech()}到{self.upper.to_speech()}的"
                    f"{self.integrand.to_speech()}对{self.variable.to_speech()}的积分")
        return f"{self.integrand.to_speech()}对{self.variable.to_speech()}的积分"


class SumNode(BaseNode):
    """求和节点"""

    def __init__(self, expression: BaseNode, variable: BaseNode,
                 lower: Optional[BaseNode] = None, upper: Optional[BaseNode] = None):
        super().__init__(NodeType.SUM)
        self.expression = expression
        self.variable = variable
        self.lower = lower
        self.upper = upper

    def to_speech(self) -> str:
        if self.lower and self.upper:
            return (f"从{self.lower.to_speech()}到{self.upper.to_speech()}的"
                    f"{self.expression.to_speech()}的和")
        return f"{self.expression.to_speech()}的和"


class GreekNode(BaseNode):
    """希腊字母节点"""

    def __init__(self, name: str, symbol: str):
        super().__init__(NodeType.GREEK)
        self.name = name
        self.symbol = symbol

    def to_speech(self) -> str:
        return self.name


class GroupNode(BaseNode):
    """括号组节点"""

    def __init__(self, content: BaseNode):
        super().__init__(NodeType.GROUP)
        self.content = content

    def to_speech(self) -> str:
        # 不添加括号描述，让内容自然朗读
        return self.content.to_speech()


class AbsNode(BaseNode):
    """绝对值节点"""

    def __init__(self, content: BaseNode):
        super().__init__(NodeType.ABS)
        self.content = content

    def to_speech(self) -> str:
        return f"({self.content.to_speech()})的绝对值"


class PlusMinusNode(BaseNode):
    """加减节点(±)"""

    def __init__(self, left: BaseNode, right: BaseNode):
        super().__init__(NodeType.OPERATOR)
        self.left = left
        self.right = right

    def to_speech(self) -> str:
        return f"{self.left.to_speech()}加减{self.right.to_speech()}"


class FactorialNode(BaseNode):
    """阶乘节点"""

    def __init__(self, argument: BaseNode):
        super().__init__(NodeType.FUNCTION)
        self.argument = argument

    def to_speech(self) -> str:
        return f"{self.argument.to_speech()}的阶乘"


class LimitNode(BaseNode):
    """极限节点"""

    def __init__(self, expression: BaseNode, variable: BaseNode, point: BaseNode):
        super().__init__(NodeType.LIMIT)
        self.expression = expression
        self.variable = variable
        self.point = point

    def to_speech(self) -> str:
        return f"当{self.variable.to_speech()}趋近于{self.point.to_speech()}时{self.expression.to_speech()}的极限"


class DerivativeNode(BaseNode):
    """导数节点"""

    def __init__(self, expression: BaseNode, variable: BaseNode, order: int = 1):
        super().__init__(NodeType.DERIVATIVE)
        self.expression = expression
        self.variable = variable
        self.order = order

    def to_speech(self) -> str:
        if self.order == 1:
            return f"{self.expression.to_speech()}对{self.variable.to_speech()}的导数"
        return f"{self.expression.to_speech()}对{self.variable.to_speech()}的{self.order}阶导数"