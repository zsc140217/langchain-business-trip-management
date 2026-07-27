# 发票识别技术方案对比

## 背景

当前系统使用 PaddleOCR + LayoutLMv3 遇到兼容性问题，需要评估替代方案。

---

## 方案对比

### 方案 A：PaddleOCR + LayoutLMv3（当前）

**架构**：两阶段
- Stage 1: PaddleOCR 文本提取
- Stage 2: LayoutLMv3 多模态理解
- Stage 3: 交叉验证

**优点**：
- 开源免费，可本地部署
- 数据隐私保护好
- 社区成熟，文档齐全

**缺点**：
- PaddlePaddle 与 OneDNN 兼容性问题（当前阻塞）
- LayoutLMv3 发布于 2022 年，技术相对陈旧
- 预训练模型准确率 70-75%，需微调到 92%+
- 两阶段处理，延迟较高（OCR 200ms + LayoutLM 1.5s）

**当前状态**：
- 运行时错误：`NotImplementedError: ConvertPirAttribute2RuntimeAttribute`
- 需要降级 PaddlePaddle 或更换方案

---

### 方案 B：Qianfan-OCR（推荐）

**架构**：端到端
- 图像 -> 直接输出结构化数据

**核心优势**：

1. **技术前沿性**（2026年3月发布）
   - OmniDocBench v1.5 排名第一：93.12 分
   - OlmOCR Bench 排名第一：79.8 分
   - KIE 平均得分：87.9（超过 Gemini 3-Pro）

2. **Layout-as-Thought 机制**
   - 类似 LLM 的 Chain-of-Thought
   - 复杂布局准确率显著提升
   - 简单文档可禁用思考模式，降低延迟

3. **统一模型**
   - 支持发票、表格、图表、手写识别等多种文档类型
   - 192 种语言支持
   - 4B 参数，能力强但推理速度可接受

4. **部署方式灵活**
   - 云端 API：通过百度千帆平台调用
   - 本地部署：HuggingFace 开源权重，可用 vLLM 部署
   - 量化部署：W8A8 量化后 1.024 页/秒（单 A100）

**缺点**：
- 云端 API 需要付费（但数据会传输到百度）
- 本地部署需要 GPU（A100/V100/4090 等）
- 模型较大（4B 参数）

---

## 技术细节对比

| 维度 | PaddleOCR + LayoutLMv3 | Qianfan-OCR |
|------|------------------------|-------------|
| **发布时间** | 2022 | 2026年3月 |
| **架构** | 两阶段（OCR -> 理解） | 端到端 |
| **模型大小** | 400MB | 4B 参数（约8GB） |
| **准确率** | 70-75%（预训练），92%+（微调） | 93.12（OmniDocBench） |
| **推理速度** | 1.7s（CPU） | 1s（GPU，量化后） |
| **部署复杂度** | 低（pip install） | 中（需 GPU 或调用 API） |
| **成本** | 免费 | API 付费 / GPU 硬件成本 |
| **数据安全** | 本地处理 | API 模式需传输 |

---

## 使用示例

### Qianfan-OCR 云端 API

```python
import requests
import base64
import json

# 1. 获取 Access Token
def get_access_token():
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {
        "grant_type": "client_credentials",
        "client_id": "YOUR_API_KEY",
        "client_secret": "YOUR_SECRET_KEY"
    }
    response = requests.post(url, params=params)
    return response.json()["access_token"]

# 2. 调用 Qianfan-OCR
def recognize_invoice(image_path: str, access_token: str):
    url = f"https://qianfan.baidubce.com/v2/chat/completions?access_token={access_token}"
    
    # 读取图片并转为 base64
    with open(image_path, "rb") as f:
        image_base64 = base64.b64encode(f.read()).decode()
    
    # 构造请求
    payload = {
        "model": "qianfan-ocr",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "从图像中提取以下字段：发票代码、发票号码、开票日期、金额、税额、价税合计、销售方、购买方。使用JSON格式输出。<think>"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    }
                ]
            }
        ]
    }
    
    response = requests.post(url, json=payload)
    result = response.json()
    
    # 解析结果
    content = result["choices"][0]["message"]["content"]
    
    return content

# 使用
access_token = get_access_token()
invoice_data = recognize_invoice("train_data/zzsfp/imgs/b0.jpg", access_token)
print(invoice_data)
```

### Qianfan-OCR 本地部署（HuggingFace）

```python
from transformers import AutoModelForImageTextToText, AutoProcessor
import torch
from PIL import Image

# 1. 加载模型（首次会下载约8GB权重）
model = AutoModelForImageTextToText.from_pretrained(
    "baidu/Qianfan-OCR",
    torch_dtype=torch.bfloat16,
    device_map="auto"
).eval()

processor = AutoProcessor.from_pretrained("baidu/Qianfan-OCR")

# 2. 识别发票
def recognize_invoice(image_path: str):
    image = Image.open(image_path).convert("RGB")
    
    prompt = "从图像中提取以下字段：发票代码、发票号码、开票日期、金额、税额、价税合计、销售方、购买方。使用JSON格式输出。"
    
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image},
                {"type": "text", "text": prompt}
            ]
        }
    ]
    
    # 启用思考模式（复杂布局）
    inputs = processor.apply_chat_template(
        messages,
        add_generation_prompt=True,
        tokenize=True,
        return_dict=True,
        return_tensors="pt",
        enable_thinking=True
    ).to(model.device)
    
    with torch.no_grad():
        output_ids = model.generate(**inputs, max_new_tokens=2048)
    
    generated_ids = output_ids[:, inputs["input_ids"].shape[1]:]
    response = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
    
    return response

# 使用
result = recognize_invoice("train_data/zzsfp/imgs/b0.jpg")
print(result)
```

---

## 决策建议

### 短期方案（P0 - 立即可用）

**选择 Qianfan-OCR 云端 API**

理由：
1. 无需解决 PaddlePaddle 兼容性问题
2. 开箱即用，快速验证效果
3. 准确率更高（93.12 vs 70-75%）
4. 成本可控（按调用量付费）

实施步骤：
1. 注册百度智能云账号
2. 开通千帆平台 Qianfan-OCR 服务
3. 获取 API Key 和 Secret Key
4. 实现 API 调用封装类
5. 用 42 个样本测试准确率

---

### 中期方案（P1 - 1-2周）

**评估本地部署可行性**

条件：
- 有 GPU 服务器（A100/V100/4090 等）
- 对数据隐私有严格要求
- 调用量大，API 成本高

实施步骤：
1. 申请 GPU 资源（云服务器或本地）
2. 部署 vLLM + Qianfan-OCR
3. 实现量化（W8A8）以提升吞吐
4. 对比 API 成本 vs 硬件成本
5. 压力测试验证性能

---

### 长期方案（P2 - 生产优化）

**混合部署 + 模型微调**

优化点：
1. 简单发票用本地模型（成本低）
2. 复杂发票用 Qianfan-OCR（准确率高）
3. 收集错误样本微调本地模型
4. 逐步降低云端 API 依赖

---

## 面试话术

### 技术选型能力

"我调研了2026年最新的文档理解模型，发现百度的 Qianfan-OCR 采用了端到端架构，比传统的 OCR+LayoutLM 方案更先进。它引入了 'Layout-as-Thought' 机制，让模型先生成布局结构的中间推理过程，再输出最终结果，类似于 LLM 的 Chain-of-Thought。这种方法在复杂布局的发票上准确率提升明显，在 OmniDocBench 上达到了 93.12 分，排名第一。"

### 工程权衡思维

"考虑到当前 PaddleOCR 遇到兼容性问题，以及预训练模型准确率只有 70-75% 需要微调的现状，我建议短期先用 Qianfan-OCR 的云端 API 快速验证效果，中期评估本地部署的可行性，长期可以考虑混合部署——简单发票用本地模型降低成本，复杂发票用云端 API 保证准确率。这样既能快速上线，又为后续优化留有空间。"

### 成本意识

"虽然云端 API 需要付费，但考虑到：1）开发时间成本——无需解决兼容性问题；2）准确率提升——从 70% 到 93%，减少人工复核成本；3）维护成本——无需管理 GPU 服务器。初期调用量不大的情况下，API 成本可能比自建更划算。等调用量上来后，可以评估本地部署的 ROI。"

---

## 参考资料

- Qianfan-OCR 论文：https://arxiv.org/html/2603.13398v1
- HuggingFace 模型：https://huggingface.co/baidu/Qianfan-OCR
- 百度千帆平台：https://console.bce.baidu.com/qianfan/modelcenter/model/buildIn/detail/am-52d29fea1063
- API 文档：https://cloud.baidu.com/doc/qianfan-docs/s/Qmispikeo

---

文档创建时间：2026-07-22
状态：方案调研完成，待决策
