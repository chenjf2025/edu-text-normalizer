"""简单数学表达式解析器 - 栈式解析，避免递归"""
import re
from typing import Optional, List, Tuple
from app.parsers.expression_tree import (
    BaseNode, EqualsNode, DivideNode, MultiplyNode, AddNode,
    SubtractNode, GroupNode, VariableNode, NumberNode, PowerNode, NodeType
)


class SimpleMathParser:
    """解析简单数学表达式如 (a+b)^2"""
    
    def parse(self, expression: str) -> Optional[BaseNode]:
        """解析简单数学表达式"""
        expression = expression.strip()
        
        # Unicode 上标转换
        expression = self._normalize_unicode(expression)
        
        # 预处理：隐式乘法 (a+b)c -> (a+b)*c, a(b+c) -> a*(b+c)
        expression = re.sub(r"\)\s*([a-zA-Z\(])", r")*\1", expression)
        expression = re.sub(r"([a-zA-Z0-9])\s*\(([^)])", r"\1*(\2", expression)
        
        # 解析等号两侧
        if "=" in expression:
            parts = expression.split("=", 1)
            left = self._parse_expr(parts[0].strip())
            right = self._parse_expr(parts[1].strip())
            if left and right:
                return EqualsNode(left, right)
            return right or left
        else:
            return self._parse_expr(expression)
    
    def _normalize_unicode(self, expr: str) -> str:
        """转换 Unicode 上标"""
        super_map = {"⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4",
                    "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9",
                    "ⁿ": "n", "ˣ": "x"}
        expr = re.sub(r'([a-zA-Z0-9])([⁰¹²³⁴⁵⁶⁷⁸⁹ⁿˣ])', 
                     lambda m: m.group(1) + '^' + super_map[m.group(2)], expr)
        expr = re.sub(r'(?<![a-zA-Z0-9])([⁰¹²³⁴⁵⁶⁷⁸⁹ⁿˣ])', 
                     lambda m: '^' + super_map[m.group(1)], expr)
        for k, v in super_map.items():
            expr = expr.replace(k, v)
        return expr
    
    def _parse_expr(self, expr: str) -> Optional[BaseNode]:
        """解析表达式（支持等号、加减和括号）"""
        expr = expr.strip()
        if not expr:
            return None
        
        # 解析等号
        if "=" in expr:
            parts = expr.split("=", 1)
            left = self._parse_expr(parts[0].strip())
            right = self._parse_expr(parts[1].strip())
            if left and right:
                return EqualsNode(left, right)
            return right or left
        
        # 解析加法和减法
        parts = self._split_add_sub(expr)
        if not parts:
            return None
        
        if len(parts) == 1:
            return self._parse_term(parts[0])
        
        # 构建加减运算树
        result = self._parse_term(parts[0])
        i = 1
        while i < len(parts):
            op = parts[i]
            term = parts[i + 1] if i + 1 < len(parts) else None
            if term:
                right = self._parse_term(term)
                if op == "+" and right and result:
                    result = AddNode(result, right)
                elif op == "-" and right and result:
                    result = SubtractNode(result, right)
                elif right and not result:
                    result = right
            i += 2
        return result
    
    def _split_add_sub(self, expr: str) -> List[str]:
        """分割加减表达式"""
        tokens = []
        current = ""
        depth = 0
        i = 0
        
        while i < len(expr):
            c = expr[i]
            if c == "(":
                depth += 1
                current += c
            elif c == ")":
                depth -= 1
                current += c
            elif c in "+-" and depth == 0:
                # 跳过开头的负号（单目负号）
                if c == "-" and not current.strip():
                    current += c
                elif current.strip():
                    tokens.append(current.strip())
                    tokens.append(c)
                    current = ""
                else:
                    tokens.append(c)
                    current = ""
            else:
                current += c
            i += 1
        
        if current.strip():
            tokens.append(current.strip())
        
        return tokens
    
    def _parse_term(self, term: str) -> Optional[BaseNode]:
        """解析项（处理乘除和指数）"""
        term = term.strip()
        if not term:
            return None
        
        # 处理负号开头
        if term.startswith("-"):
            inner = self._parse_factor(term[1:])
            if inner:
                return MultiplyNode(NumberNode(-1.0), inner)
            return None
        
        # 简单变量或数字
        if re.match(r"^[0-9]+(\.[0-9]+)?$", term):
            return NumberNode(float(term))
        if re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", term):
            return VariableNode(term)
        
        # 括号组
        if term.startswith("(") and term.endswith(")"):
            inner = term[1:-1]
            node = self._parse_expr(inner)
            return GroupNode(node) if node else None
        
        # 处理除法
        div_parts = self._split_operator(term, "/")
        if len(div_parts) > 1:
            left = self._parse_mul_div(div_parts[0])
            right = self._parse_mul_div(div_parts[1])
            if left and right:
                return DivideNode(left, right)
            return left or right
        
        # 处理乘法
        mul_parts = self._split_operator(term, "*")
        if len(mul_parts) > 1:
            result = self._parse_power(mul_parts[0])
            for p in mul_parts[1:]:
                right = self._parse_power(p)
                if result and right:
                    result = MultiplyNode(result, right)
                elif right:
                    result = right
            return result
        
        # 处理指数
        return self._parse_power(term)
    
    def _split_operator(self, expr: str, op: str) -> List[str]:
        """按运算符分割（考虑括号）"""
        parts = []
        current = ""
        depth = 0
        i = 0
        
        while i < len(expr):
            c = expr[i]
            if c == "(":
                depth += 1
                current += c
            elif c == ")":
                depth -= 1
                current += c
            elif c == op and depth == 0:
                if current.strip():
                    parts.append(current.strip())
                current = ""
            else:
                current += c
            i += 1
        
        if current.strip():
            parts.append(current.strip())
        
        return parts if parts else [expr]
    
    def _parse_mul_div(self, expr: str) -> Optional[BaseNode]:
        """解析乘除表达式"""
        expr = expr.strip()
        if not expr:
            return None
        
        # 简单变量或数字
        if re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", expr):
            return VariableNode(expr)
        if re.match(r"^-?[0-9]+(\.[0-9]+)?$", expr):
            return NumberNode(float(expr))
        
        # 括号组
        if expr.startswith("(") and expr.endswith(")"):
            inner = expr[1:-1]
            node = self._parse_expr(inner)
            return GroupNode(node) if node else None
        
        # 指数表达式
        if "^" in expr:
            return self._parse_power(expr)
        
        return VariableNode(expr)
    
    def _parse_power(self, expr: str) -> Optional[BaseNode]:
        """解析指数表达式"""
        expr = expr.strip()
        if not expr:
            return None
        
        # 找最右边的 ^
        depth = 0
        split_pos = -1
        for i in range(len(expr) - 1, -1, -1):
            c = expr[i]
            if c == ")":
                depth += 1
            elif c == "(":
                depth -= 1
            elif c == "^" and depth == 0:
                split_pos = i
                break
            elif c in "+-" and depth == 0:
                break
        
        if split_pos > 0:
            base_str = expr[:split_pos].strip()
            exp_str = expr[split_pos+1:].strip()
            base = self._parse_factor(base_str)
            exp = self._parse_factor(exp_str)
            if base and exp:
                return PowerNode(base, exp)
            return base
        
        return self._parse_factor(expr)
    
    def _parse_factor(self, expr: str) -> Optional[BaseNode]:
        """解析因子"""
        expr = expr.strip()
        if not expr:
            return None
        
        # 数字
        if re.match(r"^[0-9]+(\.[0-9]+)?$", expr):
            return NumberNode(float(expr))
        
        # 变量
        if re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", expr):
            return VariableNode(expr)
        
        # 括号组
        if expr.startswith("(") and expr.endswith(")"):
            inner = expr[1:-1]
            node = self._parse_expr(inner)
            return GroupNode(node) if node else None
        
        # 指数表达式
        if "^" in expr:
            parts = expr.split("^", 1)
            if len(parts) == 2:
                base = self._parse_factor(parts[0])
                exp = self._parse_factor(parts[1])
                if base and exp:
                    return PowerNode(base, exp)
        
        return VariableNode(expr) if expr else None