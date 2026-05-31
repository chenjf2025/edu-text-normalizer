# EduTextNormalizer 技术文档
## 面向教育场景的多学科智能文本规范化引擎

---

## 1. 服务概述

### 1.1 定位
EduTextNormalizer 是一个将任意学科文本（数学公式、化学式、物理单位等）转换为适合 TTS 自然朗读的中文自然语言的 API 服务。

### 1.2 核心能力
- 数学公式解析（支持 LaTeX、Unicode、OCR 识别文本）
- 化学式识别与规范化
- 物理单位朗读转换
- 生物术语全称
- 希腊字母读音
- 多学科自动路由识别

### 1.3 技术指标
| 指标 | 要求 |
|------|------|
| 单句延迟 | < 100ms |
| 并发能力 | ≥ 100 QPS |
| GPU 依赖 | 无 |
| 运行模式 | 可离线运行 |

---

## 2. 服务地址

```
http://localhost:18005
```

API 文档（Swagger UI）：`http://localhost:18005/docs`

---

## 3. 接口清单

### 3.1 文本规范化

**Endpoint**: `POST /api/normalize`

**请求头**:
```
Content-Type: application/json
```

**请求体**:
```json
{
  "text": "x = (-b ± √(b²-4ac))/2a",
  "subject": "math"  // 可选，强制指定学科
}
```

**字段说明**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| text | string | 是 | 待规范化的文本 |
| subject | string | 否 | 强制学科：math / chemistry / physics / biology / common |

**响应**:
```json
{
  "subject": "math",
  "normalized_text": "x等于负b加减根号下b平方减4ac整体除以2a",
  "fallback": false,
  "original_text": "x = (-b ± √(b²-4ac))/2a",
  "process_time_ms": 0.85,
  "cached": false
}
```

**响应字段说明**:
| 字段 | 类型 | 说明 |
|------|------|------|
| subject | string | 识别出的学科 |
| normalized_text | string | 规范化后的可朗读文本 |
| fallback | boolean | 是否回退（解析失败时为 true） |
| original_text | string | 原始输入文本 |
| process_time_ms | float | 处理耗时（毫秒） |
| cached | boolean | 是否来自缓存 |

**示例**:
```bash
curl -X POST "http://localhost:18005/api/normalize" \
  -H "Content-Type: application/json" \
  -d '{"text": "E = mc^2"}'
```

---

### 3.2 批量规范化

**Endpoint**: `POST /api/normalize/batch`

**请求体**:
```json
{
  "texts": [
    "H2SO4",
    "E = mc^2",
    "DNA"
  ],
  "subjects": ["chemistry", "math", "biology"]  // 可选
}
```

**响应**:
```json
[
  {
    "subject": "chemistry",
    "normalized_text": "硫酸",
    "fallback": false,
    "original_text": "H2SO4",
    "process_time_ms": 0.57,
    "cached": false
  },
  {
    "subject": "math",
    "normalized_text": "E等于mc的平方",
    "fallback": false,
    "original_text": "E = mc^2",
    "process_time_ms": 0.16,
    "cached": false
  },
  {
    "subject": "biology",
    "normalized_text": "脱氧核糖核酸",
    "fallback": false,
    "original_text": "DNA",
    "process_time_ms": 0.12,
    "cached": false
  }
]
```

**示例**:
```bash
curl -X POST "http://localhost:18005/api/normalize/batch" \
  -H "Content-Type: application/json" \
  -d '{"texts": ["H2SO4", "E = mc^2"]}'
```

---

### 3.3 健康检查

**Endpoint**: `GET /api/health`

**响应**:
```json
{
  "status": "healthy",
  "service": "EduTextNormalizer",
  "version": "1.0.0"
}
```

**示例**:
```bash
curl "http://localhost:18005/api/health"
```

---

### 3.4 服务信息

**Endpoint**: `GET /api/info`

**响应**:
```json
{
  "service": "EduTextNormalizer",
  "version": "1.0.0",
  "description": "面向教育场景的多学科智能文本规范化引擎",
  "capabilities": ["math", "chemistry", "physics", "biology", "common"]
}
```

---

## 4. 支持的输入类型

### 4.1 数学公式

| 类型 | 示例 | 输出 |
|------|------|------|
| LaTeX | `\frac{-b \pm \sqrt{b^2-4ac}}{2a}` | 负b加减根号下b平方减4ac整体除以2a |
| Unicode | √2 + √3 | 根号2加根号3 |
| 幂运算 | x² + y² = r² | x的平方加y的平方等于r的平方 |
| 分数 | a/b | a除以b |
| 根号 | √(x²-1) | 根号下x平方减1 |
| 希腊字母 | α + β | 阿尔法加贝塔 |
| 三角函数 | sin 30° + cos 60° | sin30度加cos60度 |
| 积分 | ∫f(x)dx | f(x)的定积分 |
| 求和 | Σ(i=1,n) | 求和从i等于1到n |

### 4.2 化学式

| 输入 | 输出 |
|------|------|
| H2SO4 | 硫酸 |
| NaCl | 氯化钠 |
| CO2 / CO₂ | 二氧化碳 |
| Ca(OH)2 | 氢氧化钙 |
| Fe2O3 | 氧化铁 |
| C6H12O6 | 葡萄糖 |

### 4.3 物理单位

| 输入 | 输出 |
|------|------|
| 9.8m/s² | 9点8米每二次方秒 |
| 220V | 220伏特 |
| 50Hz | 50赫兹 |
| 100W | 100瓦特 |
| 1.5A | 1点5安培 |
| 1000Pa | 1000帕斯卡 |

### 4.4 生物术语

| 输入 | 输出 |
|------|------|
| DNA | 脱氧核糖核酸 |
| RNA | 核糖核酸 |
| ATP | 三磷酸腺苷 |
|蛋白质 | 蛋白质 |
| 叶绿体 | 叶绿体 |

### 4.5 希腊字母

| 符号 | 读音 |
|------|------|
| α | 阿尔法 |
| β | 贝塔 |
| γ | 伽马 |
| δ | 德尔塔 |
| ε | 艾普西隆 |
| θ | 西塔 |
| π | 派 |
| σ | 西格玛 |
| Ω | 欧米伽 |

---

## 5. Python SDK 示例

### 5.1 使用 requests

```python
import requests

def normalize(text: str) -> dict:
    """规范化文本"""
    response = requests.post(
        "http://localhost:18005/api/normalize",
        json={"text": text}
    )
    return response.json()

# 示例
result = normalize("E = mc^2")
print(result["normalized_text"])  # E等于mc的平方
```

### 5.2 使用 httpx（异步）

```python
import asyncio
import httpx

async def normalize_async(text: str) -> dict:
    """异步规范化"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:18005/api/normalize",
            json={"text": text}
        )
        return response.json()

# 示例
result = await normalize_async("H2SO4")
print(result["normalized_text"])  # 硫酸
```

### 5.3 批量处理

```python
import requests

def batch_normalize(texts: list) -> list:
    """批量规范化"""
    response = requests.post(
        "http://localhost:18005/api/normalize/batch",
        json={"texts": texts}
    )
    return response.json()

# 示例
results = batch_normalize(["E = mc^2", "H2SO4", "DNA"])
for r in results:
    print(f"{r['original_text']} -> {r['normalized_text']}")
```

### 5.4 与 TTS 集成

```python
import requests

def text_to_speech(text: str, tts_api_url: str):
    """
    完整流程：规范化 -> TTS
    """
    # 第一步：规范化
    norm_response = requests.post(
        "http://localhost:18005/api/normalize",
        json={"text": text}
    )
    normalized = norm_response.json()["normalized_text"]

    # 第二步：发送给 TTS
    tts_response = requests.post(
        tts_api_url,
        json={"text": normalized}
    )
    return tts_response.content

# 使用
audio = text_to_speech("已知 E = mc^2", "http://your-tts-api/tts")
```

---

## 6. 错误处理

### 6.1 错误响应格式

```json
{
  "detail": "错误信息"
}
```

### 6.2 错误码

| HTTP 状态码 | 说明 |
|-------------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 500 | 服务器内部错误 |

### 6.3 解析失败处理

当公式无法解析时，系统不会崩溃，而是返回 fallback 文本：

```json
{
  "subject": "common",
  "normalized_text": "原文本保持不变",
  "fallback": true,
  "original_text": "无法解析的内容",
  "process_time_ms": 0.05,
  "cached": false
}
```

### 6.4 重试机制示例

```python
import requests
import time

def normalize_with_retry(text: str, max_retries: int = 3) -> dict:
    """带重试的规范化"""
    for i in range(max_retries):
        try:
            response = requests.post(
                "http://localhost:18005/api/normalize",
                json={"text": text},
                timeout=5
            )
            return response.json()
        except requests.exceptions.RequestException as e:
            if i == max_retries - 1:
                raise
            time.sleep(1)
```

---

## 7. Node.js / JavaScript 示例

### 7.1 使用 fetch

```javascript
async function normalize(text) {
  const response = await fetch('http://localhost:18005/api/normalize', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ text })
  });
  return response.json();
}

// 示例
normalize('E = mc^2').then(r => console.log(r.normalized_text));
```

### 7.2 使用 axios

```javascript
const axios = require('axios');

async function normalize(text) {
  const response = await axios.post(
    'http://localhost:18005/api/normalize',
    { text }
  );
  return response.data;
}

// 示例
normalize('H2SO4').then(r => console.log(r.normalized_text));
```

---

## 8. Go 示例

```go
package main

import (
    "bytes"
    "encoding/json"
    "fmt"
    "net/http"
)

type NormalizeRequest struct {
    Text string `json:"text"`
}

type NormalizeResponse struct {
    Subject        string  `json:"subject"`
    NormalizedText string  `json:"normalized_text"`
    Fallback       bool    `json:"fallback"`
    ProcessTimeMs  float64 `json:"process_time_ms"`
}

func normalize(text string) (*NormalizeResponse, error) {
    reqBody, _ := json.Marshal(NormalizeRequest{Text: text})
    resp, err := http.Post(
        "http://localhost:18005/api/normalize",
        "application/json",
        bytes.NewBuffer(reqBody),
    )
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()

    var result NormalizeResponse
    if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
        return nil, err
    }
    return &result, nil
}

func main() {
    result, _ := normalize("E = mc^2")
    fmt.Printf("%s -> %s\n", "E = mc^2", result.NormalizedText)
}
```

---

## 9. Java 示例

```java
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.URI;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

public class TextNormalizer {
    private static final String API_URL = "http://localhost:18005/api/normalize";
    private final HttpClient client = HttpClient.newHttpClient();
    private final ObjectMapper mapper = new ObjectMapper();

    public String normalize(String text) throws Exception {
        String body = String.format("{\"text\": \"%s\"}", text);
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(API_URL))
            .header("Content-Type", "application/json")
            .POST(HttpRequest.BodyPublishers.ofString(body))
            .build();

        HttpResponse<String> response = client.send(request,
            HttpResponse.BodyHandlers.ofString());

        JsonNode json = mapper.readTree(response.body());
        return json.get("normalized_text").asText();
    }

    public static void main(String[] args) throws Exception {
        TextNormalizer normalizer = new TextNormalizer();
        String result = normalizer.normalize("E = mc^2");
        System.out.println(result);  // E等于mc的平方
    }
}
```

---

## 10. 调用流程图

```
客户端
  │
  │ POST /api/normalize
  │ {"text": "E = mc^2"}
  ▼
┌─────────────────────────┐
│   EduTextNormalizer     │
│   ┌─────────────────┐   │
│   │  Router         │   │ 识别学科
│   └────────┬────────┘   │
│            ▼            │
│   ┌─────────────────┐   │
│   │  Detector       │   │ 检测公式类型
│   └────────┬────────┘   │
│            ▼            │
│   ┌─────────────────┐   │
│   │  Normalizer     │   │ 解析+规范化
│   └────────┬────────┘   │
│            ▼            │
│   ┌─────────────────┐   │
│   │  AST Builder    │   │ 构建抽象语法树
│   └────────┬────────┘   │
│            ▼            │
│   ┌─────────────────┐   │
│   │  Speech Output  │   │ 生成朗读文本
│   └─────────────────┘   │
└─────────────────────────┘
  │
  │ {"normalized_text": "E等于mc的平方"}
  ▼
客户端
  │
  ▼
┌─────────────────┐
│   GPT-SoVITS    │  TTS 朗读
│   (已有)         │
└─────────────────┘
```

---

## 11. 性能优化建议

### 11.1 缓存策略
- 相同公式在 24 小时内不重复解析
- 可通过 Redis 扩展缓存

### 11.2 批量处理
- 多条文本建议使用 `/api/normalize/batch` 接口
- 减少网络开销

### 11.3 并发配置
```python
# uvicorn 启动参数
uvicorn app.main:app --host 0.0.0.0 --port 18005 --workers 4
```

---

## 12. 联系方式

- 服务：EduTextNormalizer v1.0.0
- 文档版本：2026-05-27