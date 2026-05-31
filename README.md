# EduTextNormalizer

面向教育场景的多学科智能文本规范化引擎

## 项目目标

将任意学科文本中的：
- 数学公式
- 化学公式
- 物理单位
- 希腊字母
- 特殊符号
- LaTeX 表达式
- Unicode 数学表达式

自动转换为：适合 TTS 自然朗读的中文自然语言

## 系统架构

```
输入文本
   ↓
学科识别 Router
   ↓
文本检测器 Detector
   ↓
多学科 Normalizer
   ↓
统一朗读文本生成器
   ↓
输出自然语言
```

## 技术栈

| 模块 | 技术 |
|------|------|
| API | FastAPI |
| 数学解析 | SymPy + 自研AST |
| LaTeX解析 | latex2sympy2 |
| 配置规则 | YAML |
| 正则检测 | regex |
| 缓存 | Redis / 内存 |
| 日志 | loguru |
| 数据模型 | Pydantic |

## 安装

```bash
pip install -r requirements.txt
```

## 运行

```bash
# 开发模式
python -m app.main

# 生产模式
gunicorn app.main:app -w 4 -b 0.0.0.0:8000
```

## API使用

### 规范化单条文本

```bash
curl -X POST http://localhost:8000/api/normalize \
  -H "Content-Type: application/json" \
  -d '{"text": "x = (-b ± √(b²-4ac))/2a"}'
```

响应：
```json
{
  "subject": "math",
  "normalized_text": "x 等于，负 b 加减，根号下 b 平方减 4ac，整体除以 2a",
  "fallback": false,
  "process_time_ms": 12.5
}
```

### 批量规范化

```bash
curl -X POST http://localhost:8000/api/normalize/batch \
  -H "Content-Type: application/json" \
  -d '{"texts": ["H2SO4", "220V", "DNA"]}'
```

### 健康检查

```bash
curl http://localhost:8000/api/health
```

## 支持的输入类型

| 类型 | 支持 |
|------|------|
| 普通中文 | ✓ |
| LaTeX | ✓ |
| Unicode数学符号 | ✓ |
| OCR识别公式 | ✓ |
| Markdown公式 | ✓ |
| 中英混合 | ✓ |

## 数学朗读示例

| 输入 | 输出 |
|------|------|
| `x = \frac{-b}{2a}` | x 等于负 b 除以 2a |
| `y = \sqrt{x^2-5}` | y 等于根号下 x 平方减 5 |
| `α + β = γ` | 阿尔法 加 贝塔 等于 伽马 |

## 化学朗读示例

| 输入 | 输出 |
|------|------|
| `H2SO4` | 硫酸 |
| `NaCl` | 氯化钠 |
| `CO₂` | 二氧化碳 |

## 物理朗读示例

| 输入 | 输出 |
|------|------|
| `9.8m/s²` | 9.8 米每二次方秒 |
| `220V` | 220 伏特 |

## 生物朗读示例

| 输入 | 输出 |
|------|------|
| `DNA` | 脱氧核糖核酸 |
| `ATP` | 三磷酸腺苷 |

## 性能指标

| 项目 | 要求 |
|------|------|
| 单句延迟 | < 100ms |
| 支持并发 | ≥ 100 QPS |
| 缓存命中 | Redis |
| 支持异步 | FastAPI async |
| GPU依赖 | 无 |
| 可离线运行 | 是 |

## 项目结构

```
edu_text_normalizer/
├── app/
│   ├── main.py              # 主入口
│   ├── config.py            # 配置
│   ├── router.py            # 路由
│   ├── api/
│   │   └── normalize_api.py # API端点
│   ├── detectors/           # 检测器
│   │   ├── math_detector.py
│   │   ├── chemistry_detector.py
│   │   ├── physics_detector.py
│   │   └── common_detector.py
│   ├── normalizers/         # 规范化器
│   │   ├── math_normalizer.py
│   │   ├── chemistry_normalizer.py
│   │   ├── physics_normalizer.py
│   │   ├── biology_normalizer.py
│   │   └── chinese_normalizer.py
│   ├── parsers/            # 解析器
│   │   ├── latex_parser.py
│   │   ├── unicode_math_parser.py
│   │   ├── ast_builder.py
│   │   └── expression_tree.py
│   ├── rules/              # 规则文件
│   │   ├── greek_letters.yaml
│   │   ├── math_rules.yaml
│   │   ├── chemistry_rules.yaml
│   │   ├── physics_units.yaml
│   │   └── stop_words.yaml
│   ├── utils/              # 工具
│   │   ├── logger.py
│   │   ├── regex_helper.py
│   │   └── text_helper.py
│   └── services/           # 服务
│       ├── normalize_service.py
│       └── cache_service.py
├── tests/
│   └── test_normalizers.py
├── requirements.txt
└── README.md
```

## Docker部署

```bash
docker build -t edu_text_normalizer .
docker run -p 8000:8000 edu_text_normalizer
```

## 测试

```bash
pytest tests/ -v
```

## License

MIT