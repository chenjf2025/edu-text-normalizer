"""化学规范化器"""
import re
from typing import Optional
from app.normalizers.base_normalizer import BaseNormalizer
from app.config import config
from app.utils.logger import logger


class ChemistryNormalizer(BaseNormalizer):
    """化学公式规范化器"""

    # 常见化合物(内置)
    COMPOUNDS = {
        "H2O": "水",
        "H2SO4": "硫酸",
        "HCl": "盐酸",
        "HNO3": "硝酸",
        "H3PO4": "磷酸",
        "NaCl": "氯化钠",
        "NaOH": "氢氧化钠",
        "Na2CO3": "碳酸钠",
        "NaHCO3": "碳酸氢钠",
        "CaCO3": "碳酸钙",
        "CaO": "氧化钙",
        "Ca(OH)2": "氢氧化钙",
        "CO2": "二氧化碳",
        "CO": "一氧化碳",
        "SO2": "二氧化硫",
        "SO3": "三氧化硫",
        "NO": "一氧化氮",
        "NO2": "二氧化氮",
        "NH3": "氨气",
        "NH4Cl": "氯化铵",
        "KOH": "氢氧化钾",
        "KCl": "氯化钾",
        "MgO": "氧化镁",
        "MgCl2": "氯化镁",
        "Fe2O3": "氧化铁",
        "Fe3O4": "四氧化三铁",
        "FeCl2": "氯化亚铁",
        "FeCl3": "氯化铁",
        "CuO": "氧化铜",
        "Cu2O": "氧化亚铜",
        "CuSO4": "硫酸铜",
        "ZnO": "氧化锌",
        "ZnCl2": "氯化锌",
        "Al2O3": "氧化铝",
        "Al(OH)3": "氢氧化铝",
        "SiO2": "二氧化硅",
        "MnO2": "二氧化锰",
        "KMnO4": "高锰酸钾",
        "CH4": "甲烷",
        "C2H5OH": "乙醇",
        "CH3COOH": "乙酸",
        "C6H12O6": "葡萄糖",
        "C12H22O11": "蔗糖",
    }

    # 元素到中文名
    ELEMENTS = {
        "H": "氢", "He": "氦", "Li": "锂", "Be": "铍", "B": "硼",
        "C": "碳", "N": "氮", "O": "氧", "F": "氟", "Ne": "氖",
        "Na": "钠", "Mg": "镁", "Al": "铝", "Si": "硅", "P": "磷",
        "S": "硫", "Cl": "氯", "Ar": "氩", "K": "钾", "Ca": "钙",
        "Fe": "铁", "Cu": "铜", "Zn": "锌", "Ag": "银", "Au": "金",
        "Hg": "汞", "Pb": "铅", "Mn": "锰", "I": "碘",
    }

    def __init__(self):
        super().__init__()
        self._load_rules()

    def _load_rules(self):
        """加载规则文件"""
        try:
            rules = config.load_rule("chemistry_rules")
            if rules and "chemistry_rules" in rules:
                compounds = rules["chemistry_rules"].get("compounds", {})
                self.COMPOUNDS.update(compounds)
        except Exception as e:
            logger.warning(f"加载化学规则失败: {e}")

    def detect(self, text: str) -> bool:
        """检测是否包含化学式"""
        # 转换下划线格式
        normalized = text.strip().replace("_", "")
        
        # 简单化学式
        if re.match(r"^[A-Z][a-z]?\d*$", normalized):
            return True
        # Unicode下标化学式
        if re.match(r"^[A-Z][a-z]?[₀-₉]+$", normalized):
            return True
        # 复杂化学式
        if re.match(r"^[A-Z][a-z]?\d*(?:[A-Z][a-z]?\d*)+$", normalized):
            return True
        return False

    def normalize(self, text: str) -> str:
        """
        规范化化学式为中文名称

        Args:
            text: 化学式

        Returns:
            规范化后的中文名称
        """
        try:
            # 1. 转换下划线格式
            normalized = text.strip().replace("_", "")
            
            # 2. Unicode下标转换
            normalized = self._normalize_subscripts(normalized)

            # 3. 精确匹配
            if normalized in self.COMPOUNDS:
                return self.COMPOUNDS[normalized]

            # 4. 动态解析
            return self._parse_formula(normalized)
        except Exception as e:
            logger.error(f"化学规范化失败: {text}, 错误: {e}")
            return text

    def _normalize_subscripts(self, text: str) -> str:
        """转换Unicode下标为普通数字"""
        sub_map = {
            "₀": "0", "₁": "1", "₂": "2", "₃": "3", "₄": "4",
            "₅": "5", "₆": "6", "₇": "7", "₈": "8", "₉": "9",
        }
        for k, v in sub_map.items():
            text = text.replace(k, v)
        return text

    def _parse_formula(self, formula: str) -> str:
        """动态解析化学式 - 完整重写"""
        # 1. 处理含括号格式如 Ca(OH)2, Fe(OH)3
        # 先提取括号内容和倍数
        bracket_pattern = r'([A-Z][a-z]?)\(([A-Za-z0-9]+)\)(\d*)'
        bracket_match = re.search(bracket_pattern, formula)
        if bracket_match:
            metal = bracket_match.group(1)
            radical = bracket_match.group(2)
            multiplier = int(bracket_match.group(3)) if bracket_match.group(3) else 1
            
            metal_name = self.ELEMENTS.get(metal, metal)
            radical_name = self._parse_radical(radical)
            
            if multiplier == 1:
                return f"{radical_name}{metal_name}"
            else:
                return f"{radical_name}{multiplier}{metal_name}"
        
        # 2. 处理简单酸根格式如 H2SO4, KMnO4
        # 常见酸根及其名称
        acid_roots = {
            "SO4": "硫酸", "SO3": "亚硫酸", "NO3": "硝酸", "NO2": "亚硝酸",
            "CO3": "碳酸", "HCO3": "碳酸氢", "PO4": "磷酸", "OH": "氢氧化",
            "MnO4": "高锰酸", "MnO2": "二氧化锰", "CrO4": "铬酸", "Cr2O7": "重铬酸",
            "ClO3": "氯酸", "ClO": "次氯酸", "SiO3": "硅酸", "NH4": "氨",
        }
        
        # 遍历所有酸根，检查是否包含
        for root, name in acid_roots.items():
            if root in formula:
                # 找到酸根的位置
                idx = formula.index(root)
                before = formula[:idx]
                after = formula[idx + len(root):]
                
                if before:
                    # 酸根在前，如 SO4Ca -> 硫酸钙
                    before_name = self._get_element_name(before)
                    return f"{name}{before_name}"
                elif after:
                    # 金属在前，如 KMnO4 -> 高锰酸钾
                    after_name = self._get_element_name(after)
                    return f"{after_name}{name}"
                else:
                    # 只有酸根本身，如 SO4 -> 硫酸根
                    return name
        
        # 3. 标准解析：提取元素和数量
        elements = re.findall(r"([A-Z][a-z]?)(\d*)", formula)
        
        if not elements:
            return formula
        
        # 过滤空元素
        elements = [(e, c) for e, c in elements if e]
        
        if len(elements) == 1:
            element, count = elements[0]
            element_name = self.ELEMENTS.get(element, element)
            return element_name if not count else f"{element_name}{count}"
        
        # 多元素处理
        parts = []
        for element, count in elements:
            element_name = self.ELEMENTS.get(element, element)
            count = int(count) if count else 1
            
            if count == 1:
                parts.append(element_name)
            else:
                parts.append(f"{element_name}{count}")
        
        # 简单处理：判断氧化物或氯化物模式
        if len(parts) == 2:
            if parts[1] == "氧":
                return f"氧化{parts[0]}"
            elif parts[1] == "氢":
                return f"{parts[0]}化氢"
            else:
                return f"{parts[1]}化{parts[0]}"
        
        return "".join(parts)

    def _get_element_name(self, text: str) -> str:
        """获取元素名称"""
        # 提取数量
        match = re.match(r"^([A-Z][a-z]?)(\d*)$", text)
        if match:
            element = match.group(1)
            count = int(match.group(2)) if match.group(2) else 1
            element_name = self.ELEMENTS.get(element, element)
            return element_name if count == 1 else f"{element_name}{count}"
        return text

    def _parse_radical(self, radical: str) -> str:
        """解析酸根名称"""
        radical_map = {
            "OH": "氢氧化",
            "SO4": "硫酸",
            "SO3": "亚硫酸",
            "CO3": "碳酸",
            "NO3": "硝酸",
            "NO2": "亚硝酸",
            "PO4": "磷酸",
            "HCO3": "碳酸氢",
            "MnO4": "高锰酸",
            "MnO2": "二氧化锰",
        }
        if radical in radical_map:
            return radical_map[radical]
        # 尝试作为元素处理
        return self._get_element_name(radical)