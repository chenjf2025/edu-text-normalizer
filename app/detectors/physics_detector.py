"""物理公式检测器"""
import regex
from typing import List, Dict, Any
from app.detectors.base_detector import BaseDetector


class PhysicsDetector(BaseDetector):
    """物理公式检测器"""

    # SI基本单位
    SI_UNITS = ["m", "kg", "s", "A", "K", "mol", "cd"]

    # SI导出单位
    DERIVED_UNITS = ["Hz", "N", "J", "W", "V", "Ω", "F", "Pa", "T", "H", "Wb", "S", "Bq", "Gy", "kat", "lm", "lx"]

    # 特殊物理单位
    SPECIAL_UNITS = ["Pa", "T", "Wb", "Hz", "Ω"]

    # 组合单位模式
    COMPOSITE_PATTERNS = {
        "velocity": r"\d+([.,]\d+)?\s*m/s(?:²|\^2)?\b",
        "acceleration": r"\d+([.,]\d+)?\s*m/s²\b",
        # 单字符单位 N J W V A F T 必须用 case-SENSITIVE 模式（不带 IGNORECASE）
        "force": r"\d+([.,]\d+)?\s*N(?![a-zA-Z])\b",
        "energy": r"\d+([.,]\d+)?\s*J(?![a-zA-Z])\b",
        "power": r"\d+([.,]\d+)?\s*W(?![a-zA-Z])\b",
        "voltage": r"\d+([.,]\d+)?\s*V(?![a-zA-Z])\b",
        "pressure": r"\d+([.,]\d+)?\s*Pa\b",
        "frequency": r"\d+([.,]\d+)?\s*Hz(?![a-zA-Z])\b",
        "resistance": r"\d+([.,]\d+)?\s*Ω(?![a-zA-Z])\b",
        "temperature": r"\d+([.,]\d+)?\s*K(?![a-zA-Z])\b",
        "magnetic": r"\d+([.,]\d+)?\s*T(?![a-zA-Z])\b",
    }

    # 经典物理学公式模式（无数值的物理公式）
    PHYSICS_FORMULA_PATTERNS = [
        r"E\s*=\s*m\s*c\s*\^?\s*2",  # E=mc^2
        r"E\s*=\s*m\s*c\s*2",        # E=mc2
        r"F\s*=\s*m\s*a", # F=ma
        r"P\s*=\s*I\s*U",            # P=IU
        r"U\s*=\s*I\s*R",            # U=IR (欧姆定律)
    ]

    def detect(self, text: str) -> bool:
        """检测是否包含物理单位或物理公式"""
        # 检查经典物理学公式（无数值）
        for pattern in self.PHYSICS_FORMULA_PATTERNS:
            if regex.search(pattern, text, regex.IGNORECASE):
                return True

        # 检查组合单位模式（多字符单位支持大小写，单字符用 case-SENSITIVE）
        for name, pattern in self.COMPOSITE_PATTERNS.items():
            if name in ("force", "energy", "power", "voltage", "frequency", "resistance", "temperature", "magnetic"):
                # 单字符单位：不用 IGNORECASE
                if regex.search(pattern, text):
                    return True
            else:
                # 多字符单位：支持大小写
                if regex.search(pattern, text, regex.IGNORECASE):
                    return True

        # 检查数值+多字符单位
        has_multi = regex.search(
            rf"\d+([.,]\d+)?\s*(?:Hz|Pa|Wb|lm|lx|Bq|Gy|kat|Ohm|cd)\b",
            text, regex.IGNORECASE)
        # 检查数值+单字符单位（大写 N J W V A F T，case-SENSITIVE）
        # 修复：数值后面必须是空格或紧跟大写单字符单位才匹配
        has_single = regex.search(
            r"\d+([.,]\d+)?\s+[NJWVAFFT](?![a-zA-Z])\b",
            text)
        # Ω 特殊
        has_omega = regex.search(r"\d+[.,]?\d*\s*Ω", text)
        if has_multi or has_single or has_omega:
            return True

        # 检查特殊单位（大写形式）
        for unit in self.SPECIAL_UNITS:
            if regex.search(rf"\d+.*\b{unit}\b", text):
                return True

        return False

    def extract(self, text: str) -> List[str]:
        """提取物理表达式"""
        units = []

        for pattern in self.COMPOSITE_PATTERNS.values():
            matches = regex.findall(pattern, text, regex.IGNORECASE)
            units.extend(matches)

        # 提取数值+单位
        unit_matches = regex.findall(r"\d+([.,]\d+)?\s*(?:[NJWVAHzΩTFkMGP]?(?:[a-z]*/?[a-z]*)?)", text, regex.IGNORECASE)
        for m in unit_matches:
            if m.strip():
                units.append(m.strip())

        return list(set(units))

    def get_info(self, text: str) -> Dict[str, Any]:
        """获取详细检测信息"""
        return {
            "name": "physics",
            "detected": self.detect(text),
            "count": len(self.extract(text)),
            "units": self.extract(text)
        }