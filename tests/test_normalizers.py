"""测试套件"""
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.normalizers.math_normalizer import MathNormalizer
from app.normalizers.chemistry_normalizer import ChemistryNormalizer
from app.normalizers.physics_normalizer import PhysicsNormalizer
from app.normalizers.biology_normalizer import BiologyNormalizer
from app.services.normalize_service import NormalizeService
from app.parsers.ast_builder import ASTBuilder


class TestMathNormalizer:
    """数学规范化器测试"""

    def setup_method(self):
        self.normalizer = MathNormalizer()

    def test_latex_frac(self):
        """测试LaTeX分数"""
        text = r"x = \frac{-b \pm \sqrt{b^2-4ac}}{2a}"
        result = self.normalizer.normalize(text)
        assert "除以" in result or "等于" in result

    def test_unicode_sqrt(self):
        """测试Unicode根号"""
        text = "x = √(b²-4ac)"
        result = self.normalizer.normalize(text)
        assert "根号" in result or "sqrt" in result.lower()

    def test_greek_letters(self):
        """测试希腊字母"""
        text = "α + β = γ"
        result = self.normalizer.normalize(text)
        assert "阿尔法" in result or "伽马" in result


class TestChemistryNormalizer:
    """化学规范化器测试"""

    def setup_method(self):
        self.normalizer = ChemistryNormalizer()

    def test_simple_compounds(self):
        """测试简单化合物"""
        assert self.normalizer.normalize("H2SO4") == "硫酸"
        assert self.normalizer.normalize("NaCl") == "氯化钠"

    def test_co2(self):
        """测试CO2"""
        assert self.normalizer.normalize("CO2") == "二氧化碳"


class TestPhysicsNormalizer:
    """物理规范化器测试"""

    def setup_method(self):
        self.normalizer = PhysicsNormalizer()

    def test_velocity(self):
        """测试速度单位"""
        text = "9.8m/s²"
        result = self.normalizer.normalize(text)
        assert "米" in result

    def test_voltage(self):
        """测试电压单位"""
        text = "220V"
        result = self.normalizer.normalize(text)
        assert "伏特" in result or "V" in result


class TestBiologyNormalizer:
    """生物规范化器测试"""

    def setup_method(self):
        self.normalizer = BiologyNormalizer()

    def test_dna(self):
        """测试DNA"""
        assert self.normalizer.normalize("DNA") == "脱氧核糖核酸"

    def test_atp(self):
        """测试ATP"""
        assert self.normalizer.normalize("ATP") == "三磷酸腺苷"


class TestNormalizeService:
    """规范化服务测试"""

    def setup_method(self):
        self.service = NormalizeService()

    def test_math_detection(self):
        """测试数学检测"""
        result = self.service.normalize(r"x = \frac{-b}{2a}")
        assert result["subject"] == "math"

    def test_chemistry_detection(self):
        """测试化学检测"""
        result = self.service.normalize("H2SO4")
        assert result["subject"] == "chemistry"

    def test_fallback(self):
        """测试回退机制"""
        result = self.service.normalize("这是一段普通中文文本")
        assert "normalized_text" in result
        assert not result.get("fallback", True)


class TestASTBuilder:
    """AST构建器测试"""

    def setup_method(self):
        self.builder = ASTBuilder()

    def test_latex_parsing(self):
        """测试LaTeX解析"""
        result = self.builder.build_and_speak(r"\frac{a}{b}")
        assert result and len(result) > 0

    def test_power_node(self):
        """测试幂节点"""
        result = self.builder.build_and_speak("x^2")
        assert "次方" in result or "平方" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])