"""物理规范化器"""
import re
from typing import Optional, Dict
from app.normalizers.base_normalizer import BaseNormalizer
from app.config import config
from app.utils.logger import logger


class PhysicsNormalizer(BaseNormalizer):
    """物理单位规范化器"""

    # 基本单位
    BASE_UNITS = {
        "m": "米", "kg": "千克", "s": "秒", "a": "安培",
        "k": "开尔文", "mol": "摩尔", "cd": "坎德拉",
    }

    # 导出单位（小写键）
    DERIVED_UNITS = {
        "hz": "赫兹", "n": "牛顿", "j": "焦耳", "w": "瓦特",
        "v": "伏特", "ohm": "欧姆", "f": "法拉", "pa": "帕斯卡",
        "t": "特斯拉", "h": "亨利", "wb": "韦伯", "s": "西门子",
        "Ω": "欧姆",
    }

    # 组合单位
    COMPOSITE_UNITS = {
        "m/s": "米每秒",
        "m/s²": "米每二次方秒",
        "m/s^2": "米每二次方秒",
        "kg/m³": "千克每立方米",
        "kg/m3": "千克每立方米",
        "N/m": "牛顿每米",
        "J/s": "焦耳每秒",
        "W/m²": "瓦特每平方米",
    }

    # 单位前缀
    # 单位前缀（不在单位前的符号）
    PREFIXES = {
        "k": "千", "M": "兆", "G": "吉", "T": "太", "P": "拍",
        "m": "毫", "μ": "微", "n": "纳", "p": "皮",
        "c": "厘", "d": "分", "h": "百",
    }

    def __init__(self):
        super().__init__()
        self._load_rules()

    def _load_rules(self):
        """加载规则文件"""
        try:
            rules = config.load_rule("physics_units")
            if rules and "physics_units" in rules:
                units = rules["physics_units"]
                if "base_units" in units:
                    self.BASE_UNITS.update(units["base_units"])
                if "derived_units" in units:
                    self.DERIVED_UNITS.update(units["derived_units"])
                if "composite_units" in units:
                    self.COMPOSITE_UNITS.update(units["composite_units"])
        except Exception as e:
            logger.warning(f"加载物理规则失败: {e}")

    def detect(self, text: str) -> bool:
        """检测是否包含物理单位"""
        # 数值+单位（更严格的匹配，避免误匹配普通单词中的字母）
        pattern = r"\d+([.,]\d+)?\s*[kMGTPmc]?(?:m|s|kg|A|K|mol|cd|Hz|N|J|W|V|Ω|F|Pa|T|H|Wb|S)\b"
        if re.search(pattern, text, re.IGNORECASE):
            return True
        # 处理带幂的单位如 m/s², W/m²
        if re.search(r"\d+.*(?:m/s|m²|W/m|N/m|J/s)", text, re.IGNORECASE):
            return True
        return False

    def normalize(self, text: str) -> str:
        """
        规范化物理单位为中文名称

        Args:
            text: 包含物理单位的文本

        Returns:
            规范化后的朗读文本
        """
        try:
            result = text

            # 0. 先转换Unicode上标
            super_map = {"⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4",
                        "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9"}
            for k, v in super_map.items():
                result = result.replace(k, v)

            # 0.5 处理经典物理公式模式
            # E=mc^2, E=mc2
            result = re.sub(r'E\s*=\s*m\s*c\s*\^?\s*2', 'E等于m乘c的2次方', result)
            # F=ma
            result = re.sub(r'F\s*=\s*m\s*a', 'F等于m乘a', result)
            # P=IU
            result = re.sub(r'P\s*=\s*I\s*U', 'P等于I乘U', result)
            # U=IR
            result = re.sub(r'U\s*=\s*I\s*R', 'U等于I乘R', result)
            # v=s/t
            result = re.sub(r'v\s*=\s*s\s*/\s*t', 'v等于s除以t', result)

            # 1. 处理组合单位
            # 先把所有 Unicode 上标转成普通字符
            _super_map = {"⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4",
                         "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9"}
            for k, v in _super_map.items():
                result = result.replace(k, v)

            # 按key长度倒序排列，确保 m/s^2 先于 m/s 被匹配
            sorted_units = sorted(self.COMPOSITE_UNITS.items(), key=lambda x: -len(x[0]))
            for unit, speak in sorted_units:
                escaped_unit = unit
                for sup, num in _super_map.items():
                    escaped_unit = escaped_unit.replace(sup, num)
                # 通配符替换：处理 m/s^2 这类带幂的单位
                # 把 ^2 变成可选部分
                if "^" in escaped_unit:
                    base = escaped_unit.replace("^2", "").replace("^3", "")
                    pattern = rf"((\d+([.,]\d+)?)\s*{re.escape(base)}(?:\^2)?)"
                else:
                    pattern = rf"((\d+([.,]\d+)?)\s*{re.escape(escaped_unit)})"
                m = re.search(pattern, result)
                if m:
                    result = re.sub(pattern, lambda x: f"{x.group(2)} {speak}", result)
                    break # 只匹配一次

            # 2. 处理数值+单位（数字后紧跟单位）
            def _replace_unit(match):
                # 正则: (\d+([.,]\d+)?)\s*([kMGTPmc]?)(m|s|kg|A|K|mol|cd|Hz|N|J|W|V|Ω|F|Pa|T|H|Wb|S)\b
                # group(1)=值, group(2)=小数部分(可选), group(3)=前缀, group(4)=单位
                value = match.group(1)
                prefix = match.group(3) if len(match.groups()) >= 3 else ""
                unit = match.group(4) if len(match.groups()) >= 4 else match.group(1)
                if unit is None or unit == "":
                    return match.group(0)
                full_unit = prefix + unit
                return self._speak_unit(value, full_unit)

            result = re.sub(
                r"(\d+([.,]\d+)?)\s*([kMGTPmc]?)(m|s|kg|A|K|mol|cd|Hz|N|J|W|V|Ω|F|Pa|T|H|Wb|S)\b",
                _replace_unit,
                result,
                flags=re.IGNORECASE
            )

            return result
        except Exception as e:
            logger.error(f"物理规范化失败: {text}, 错误: {e}")
            return text

    def _speak_unit(self, value: str, unit: str) -> str:
        """生成单个单位的朗读"""
        if not unit:
            #纯数值，添加中文小数点转换
            if "." in value:
                parts = value.split(".")
                return parts[0] + "点" + "".join(parts[1])
            return value

        unit_lower = unit.lower()

        # 先尝试完整匹配（小写）
        if unit_lower in self.BASE_UNITS:
            return f"{value} {self.BASE_UNITS[unit_lower]}"

        if unit_lower in self.DERIVED_UNITS:
            return f"{value} {self.DERIVED_UNITS[unit_lower]}"

        # 尝试提取前缀（只对单字符单位有效）
        if len(unit) > 1 and unit[0] in self.PREFIXES:
            prefix = self.PREFIXES[unit[0]]
            base_unit = unit[1:].lower()
            if base_unit in self.BASE_UNITS:
                return f"{value} {prefix}{self.BASE_UNITS[base_unit]}"
            if base_unit in self.DERIVED_UNITS:
                return f"{value} {prefix}{self.DERIVED_UNITS[base_unit]}"

        # 默认
        return f"{value}{unit}"