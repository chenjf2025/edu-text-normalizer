"""AST构建器 - 高级AST构建"""
import re
from typing import Optional, List, Dict
from app.parsers.expression_tree import (
    BaseNode, NumberNode, VariableNode, FractionNode, PowerNode,
    SqrtNode, AddNode, SubtractNode, MultiplyNode, DivideNode,
    EqualsNode, PlusMinusNode, FactorialNode, GroupNode, NodeType
)
from app.parsers.latex_parser import LatexParser, UnicodeMathParser
from app.parsers.simple_math_parser import SimpleMathParser
from app.utils.logger import logger


class ASTBuilder:
    """AST(抽象语法树)构建器 - 核心组件"""

    def __init__(self):
        self.latex_parser = LatexParser()
        self.unicode_parser = UnicodeMathParser()

    def build(self, expression: str) -> Optional[BaseNode]:
        """
        构建AST - 核心方法

        Args:
            expression: 数学表达式字符串 (LaTeX或Unicode)

        Returns:
            AST根节点，失败返回None
        """
        try:
            # 1. 检测表达式类型
            expr_type = self._detect_type(expression)

            # 2. 根据类型选择解析器
            if expr_type == "latex":
                return self.latex_parser.parse(expression)
            elif expr_type == "unicode":
                return self.unicode_parser.parse(expression)
            elif expr_type == "mixed":
                # 混合类型：先尝试LaTeX
                result = self.latex_parser.parse(expression)
                if not result:
                    # 回退到Unicode
                    result = self.unicode_parser.parse(expression)
                return result
            elif expr_type == "simple":
                # 简单数学表达式解析器
                return SimpleMathParser().parse(expression)
            else:
                return None
        except Exception as e:
            logger.error(f"AST构建失败: {expression}, 错误: {e}")
            return None

    def _detect_type(self, expression: str) -> str:
        """检测表达式类型"""
        # LaTeX特征
        latex_features = ["\\frac", "\\sqrt", "\\int", "\\sum",
                         "\\sin", "\\cos", "\\tan", "\\lim",
                         "\\alpha", "\\beta", "\\gamma", "^", "_"]
        unicode_math = ["∫", "∑", "√", "∞", "±", "≠", "≤", "≥",
                       "α", "β", "γ", "δ", "θ", "π", "σ"]

        has_latex = any(f in expression for f in latex_features)
        has_unicode = any(f in expression for f in unicode_math)

        if has_latex:
            return "latex"
        elif has_unicode:
            return "unicode"
        elif "^" in expression or "_" in expression:
            return "unicode"
        elif re.search(r"[=+\-*/()]", expression):
            # 简单数学表达式：包含等号、括号、运算符等
            return "simple"
        else:
            return "unknown"

    def ast_to_speech(self, node: Optional[BaseNode]) -> str:
        """
        将AST转换为朗读文本 - 核心方法

        Args:
            node: AST根节点

        Returns:
            适合TTS的朗读文本
        """
        if node is None:
            return ""
        try:
            speech = node.to_speech()
            # 智能优化
            speech = self._optimize_speech(speech)
            return speech
        except Exception as e:
            logger.error(f"AST转语音失败: {e}")
            return ""

    def _optimize_speech(self, speech: str) -> str:
        """优化朗读文本"""
        # 移除多余空格
        speech = " ".join(speech.split())

        # 优化连接词
        replacements = [
            ("除以除以", "除以"),
            ("乘以乘以", "乘以"),
            ("加加", "加"),
            ("减减", "减"),
            ("的的", "的"),
        ]
        for old, new in replacements:
            speech = speech.replace(old, new)

        return speech

    def build_and_speak(self, expression: str) -> str:
        """
        一键构建并转换为语音 - 主要入口

        Args:
            expression: 数学表达式

        Returns:
            朗读文本
        """
        ast = self.build(expression)
        return self.ast_to_speech(ast)