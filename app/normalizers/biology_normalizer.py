"""生物规范化器"""
from app.normalizers.base_normalizer import BaseNormalizer
from app.utils.logger import logger


class BiologyNormalizer(BaseNormalizer):
    """生物术语规范化器"""

    # 常见生物术语
    TERMS = {
        "DNA": "脱氧核糖核酸",
        "RNA": "核糖核酸",
        "ATP": "三磷酸腺苷",
        "ADP": "二磷酸腺苷",
        "AMP": "一磷酸腺苷",
        "NADH": "还原型辅酶一",
        "NADPH": "还原型辅酶二",
        "FADH2": "还原型黄素腺嘌呤二核苷酸",
        "CoA": "辅酶A",
        "GLU": "谷氨酸",
        "ALA": "丙氨酸",
        "GLY": "甘氨酸",
        "VAL": "缬氨酸",
        "LEU": "亮氨酸",
        "ILE": "异亮氨酸",
        "PRO": "脯氨酸",
        "PHE": "苯丙氨酸",
        "TYR": "酪氨酸",
        "TRP": "色氨酸",
        "SER": "丝氨酸",
        "THR": "苏氨酸",
        "CYS": "半胱氨酸",
        "MET": "蛋氨酸",
        "ASN": "天冬酰胺",
        "GLN": "谷氨酰胺",
        "ASP": "天冬氨酸",
        "LYS": "赖氨酸",
        "ARG": "精氨酸",
        "HIS": "组氨酸",
        "mRNA": "信使核糖核酸",
        "tRNA": "转运核糖核酸",
        "rRNA": "核糖体核糖核酸",
        "miRNA": "微小核糖核酸",
        "siRNA": "小干扰核糖核酸",
        "PCR": "聚合酶链式反应",
        "DNAi": "脱氧核糖核酸酶抑制因子",
        "ER": "内质网",
        "Golgi": "高尔基体",
        "Mitochondria": "线粒体",
        "Chloroplast": "叶绿体",
        "Ribosome": "核糖体",
        "Lysosome": "溶酶体",
        "Peroxisome": "过氧化物酶体",
        "Cytoplasm": "细胞质",
        "Nucleus": "细胞核",
        "Cell": "细胞",
        "Protein": "蛋白质",
        "Enzyme": "酶",
        "Hormone": "激素",
        "Vitamin": "维生素",
        "Mineral": "矿物质",
        "Carbohydrate": "碳水化合物",
        "Lipid": "脂质",
        "Fat": "脂肪",
        "Oil": "油脂",
        "Sugar": "糖",
        "Starch": "淀粉",
        "Cellulose": "纤维素",
        "Chitin": "几丁质",
        "Glucose": "葡萄糖",
        "Fructose": "果糖",
        "Sucrose": "蔗糖",
        "Lactose": "乳糖",
        "Maltose": "麦芽糖",
        "Galactose": "半乳糖",
        "RNA": "核糖核酸",
        "Protein": "蛋白质",
        "Amino": "氨基",
        "Acid": "酸",
        "Cell": "细胞",
        "Tissue": "组织",
        "Organ": "器官",
        "System": "系统",
        "Organism": "有机体",
        "Bacteria": "细菌",
        "Virus": "病毒",
        "Fungus": "真菌",
        "Plant": "植物",
        "Animal": "动物",
        "Human": "人类",
        "Gene": "基因",
        "Chromosome": "染色体",
        "Genome": "基因组",
        "Mutation": "突变",
        "Evolution": "进化",
        "Photosynthesis": "光合作用",
        "Respiration": "呼吸作用",
        "Metabolism": "新陈代谢",
        "Homeostasis": "内稳态",
    }

    def detect(self, text: str) -> bool:
        """检测是否包含生物术语"""
        upper_text = text.upper()
        return any(term in upper_text for term in self.TERMS.keys())

    def normalize(self, text: str) -> str:
        """
        规范化生物术语为中文全称

        Args:
            text: 包含生物术语的文本

        Returns:
            规范化后的中文文本
        """
        try:
            result = text
            upper_result = result.upper()

            # 替换术语
            for term, chinese in self.TERMS.items():
                if term in upper_result:
                    # 保持大小写格式
                    idx = upper_result.find(term)
                    if idx >= 0:
                        result = result[:idx] + chinese + result[idx + len(term):]
                        upper_result = result.upper()

            return result
        except Exception as e:
            logger.error(f"生物规范化失败: {text}, 错误: {e}")
            return text