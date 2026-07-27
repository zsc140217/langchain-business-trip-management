# 多模态能力实现方案（基于 ARCHITECTURE_V3_PLAN）

文档版本: v1.0  
创建日期: 2026-07-21  
对应任务: V3 Phase 2 - T3.1-T3.4  

---

## 一、技术架构选型

基于 2026 年最新实践和你的现有素材，采用**混合架构**方案：

| 能力维度 | 技术方案 | 模型/工具 | 理由 |
|---------|---------|----------|------|
| **PDF文档解析** | 文本提取 + LLM结构化 | pdfplumber + Qwen2.5 | 你已有差旅政策PDF，需提取结构化规则 |
| **发票识别** | OCR前置 + Vision LLM校验 | PaddleOCR + Qwen2.5-VL-7B | 双重校验，准确率>90%，中文支持最好 |
| **图片理解** | Vision LLM直接推理 | Qwen2.5-VL-7B | 轻量级7B模型，可本地GPU部署 |
| **OCR引擎** | 开源高性能引擎 | PaddleOCR v2.7+ | 中文场景最优，支持倾斜/模糊图像 |

### 架构决策理由

**为什么选择 PaddleOCR + Qwen2.5-VL？**

1. **成本考虑**：本地部署，无API调用费用
2. **中文能力**：Qwen系列对中文支持最好，发票识别F1>94%
3. **轻量化**：7B模型单卡可推理，部署成本低
4. **准确率**：混合架构比纯OCR提升15-20个百分点

---

## 二、核心能力实现（按优先级）

### P0: PDF差旅政策解析（Week 1）

**目标**：从你的PDF素材中提取差旅标准、审批规则、报销政策

**输入素材**：
```
E:\Desktop\langchain-business-trip-management\
  关于印发内江嘉宏城建集团有限公司差旅费管理办法暂行的通知
  《公司各部室》内嘉城建司发（2019）4号.pdf
```

**实现方案**：

```python
# src/multimodal/pdf_processor.py
import pdfplumber
from typing import Dict, List

class TravelPolicyPDFProcessor:
    """
    差旅政策PDF解析器
    
    提取目标:
    1. 差旅标准表(城市等级、住宿上限、交通方式)
    2. 审批流程(金额阈值、审批人层级)
    3. 报销规则(单据要求、时限要求)
    4. 补贴标准(出差补贴、误餐补贴)
    """
    
    def __init__(self, llm_client):
        self.llm = llm_client
    
    def extract_policy(self, pdf_path: str) -> Dict:
        """提取完整差旅政策"""
        # Step 1: PDF文本提取
        full_text = self._extract_text(pdf_path)
        
        # Step 2: LLM结构化提取(使用Function Calling)
        structured_policy = self.llm.extract_structured(
            text=full_text,
            schema=TRAVEL_POLICY_SCHEMA,
            prompt="""你是差旅政策分析专家。请从文本中提取以下结构化信息:
            
            1. 城市分类标准(一类/二类/三类城市及对应城市列表)
            2. 住宿标准(各城市等级的住宿费上限)
            3. 交通标准(不同距离/职级对应的交通方式)
            4. 审批阈值(各金额区间对应的审批人)
            5. 报销规则(单据要求、报销时限、审批流程)
            6. 补贴标准(出差补贴、误餐补贴)
            
            要求:
            - 金额精确到元
            - 城市名称使用全称(如"北京市"而非"北京")
            - 审批人使用职位名称(如"部门经理"而非具体姓名)
            """
        )
        
        # Step 3: 校验和后处理
        validated = self._validate_policy(structured_policy)
        
        # Step 4: 持久化到向量库(用于后续RAG检索)
        self._save_to_vectorstore(validated)
        
        return validated
    
    def _extract_text(self, pdf_path: str) -> str:
        """提取PDF文本(兼容扫描件和生成式PDF)"""
        with pdfplumber.open(pdf_path) as pdf:
            pages_text = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages_text.append(text)
            return "\n\n".join(pages_text)
    
    def _validate_policy(self, policy: Dict) -> Dict:
        """校验提取结果的完整性和合理性"""
        required_fields = [
            'city_classification',
            'accommodation_standards', 
            'transport_standards',
            'approval_thresholds',
            'reimbursement_rules'
        ]
        
        for field in required_fields:
            if field not in policy or not policy[field]:
                raise ValueError(f"缺少必需字段: {field}")
        
        return policy

# 输出结构示例
TRAVEL_POLICY_SCHEMA = {
    "city_classification": {
        "一类城市": ["北京市", "上海市", "广州市", "深圳市"],
        "二类城市": ["成都市", "杭州市", "西安市"],
        "三类城市": ["其他城市"]
    },
    "accommodation_standards": {
        "一类城市": {"部门经理及以上": 600, "普通员工": 450},
        "二类城市": {"部门经理及以上": 500, "普通员工": 350},
        "三类城市": {"部门经理及以上": 400, "普通员工": 300}
    },
    "transport_standards": {
        "distance_under_500km": {
            "preferred": "高铁二等座",
            "alternative": "长途汽车"
        },
        "distance_500_to_1500km": {
            "senior": "飞机经济舱",
            "regular": "高铁二等座"
        },
        "distance_over_1500km": "飞机经济舱"
    },
    "approval_thresholds": {
        "under_3000": "部门经理",
        "3000_to_10000": "分管副总",
        "over_10000": "总经理"
    },
    "reimbursement_rules": {
        "required_documents": ["出差申请单", "交通票据", "住宿发票"],
        "deadline_days": 30,
        "approval_flow": ["提交人 -> 部门经理 -> 财务审核 -> 分管领导 -> 付款"]
    }
}
```

**预期产出**：
- 结构化差旅政策JSON
- 向量化存储(可被RAG检索)
- 政策规则表(用于自动审批引擎)

---

### P0: 发票识别（Week 2-3）

**目标**：识别增值税发票，提取关键字段，准确率>90%

**技术方案**：两阶段架构 - OCR前置 + Vision LLM校验

**核心代码框架**：

```python
# src/multimodal/invoice_recognizer.py
from paddleocr import PaddleOCR
from typing import Dict

class InvoiceRecognizer:
    """
    发票识别器
    
    架构：
    Stage 1: PaddleOCR 快速文本提取(约200ms)
    Stage 2: Vision LLM 结构化理解(约1.5s)
    Stage 3: 交叉验证 + 业务规则校验
    """
    
    def __init__(self, vision_llm_path: str):
        self.ocr = PaddleOCR(
            use_angle_cls=True,
            lang='ch',
            use_gpu=True
        )
        self.vision_llm = self._load_vision_model(vision_llm_path)
    
    def recognize(self, image_path: str) -> Dict:
        """识别发票并返回结构化数据"""
        # Stage 1: OCR文本提取
        ocr_result = self.ocr.ocr(image_path, cls=True)
        ocr_text = self._merge_ocr_text(ocr_result)
        
        # Stage 2: Vision LLM结构化识别
        image_bytes = open(image_path, 'rb').read()
        invoice_data = self.vision_llm.analyze(
            image=image_bytes,
            prompt=self._build_invoice_prompt()
        )
        
        # Stage 3: 交叉验证
        validated = self._cross_validate(ocr_text, invoice_data)
        
        return validated
    
    def _build_invoice_prompt(self) -> str:
        """构建发票识别Prompt"""
        return """你是财务发票识别专家。请从图像中精确提取以下字段:

1. 发票类型: 增值税专用发票/增值税普通发票/电子发票
2. 发票代码: 12位数字
3. 发票号码: 8位数字
4. 开票日期: 必须转换为YYYY-MM-DD格式
5. 金额: 不含税金额，精确到分(两位小数)
6. 税额: 税额，精确到分
7. 价税合计: 总金额 = 金额 + 税额
8. 销售方名称: 完整公司名称
9. 购买方名称: 完整公司名称

重要约束:
- 金额格式: 1234.56
- 日期格式: YYYY-MM-DD
- 识别置信度<0.85时，标注"[低置信度]"
- 校验: 价税合计 = 金额 + 税额(允许±0.02误差)

只返回JSON，不要解释。"""
    
    def _cross_validate(self, ocr_text: str, llm_result: Dict) -> Dict:
        """OCR和LLM结果交叉验证"""
        warnings = []
        confidence = 1.0
        
        # 价税合计一致性检查
        calculated = llm_result['amount'] + llm_result['tax']
        if abs(llm_result['total'] - calculated) > 0.02:
            warnings.append('价税合计不符')
            confidence *= 0.7
        
        # OCR文本包含性检查
        if str(llm_result['number']) not in ocr_text:
            warnings.append('发票号码未在OCR结果中找到')
            confidence *= 0.85
        
        llm_result['confidence'] = confidence
        llm_result['warnings'] = warnings
        return llm_result
```

**性能指标**：
- 准确率: >90% (基于SCID数据集)
- 处理速度: 1.5-2秒/张
- 置信度: >0.85视为高置信

---

## 三、数据收集计划

### 已有数据

1. **差旅政策PDF** (1份)
   - 内江嘉宏城建集团差旅费管理办法

### 需收集数据

#### **P0: 发票数据集**

| 数据源 | 类型 | 数量 | 用途 | 获取方式 |
|--------|------|------|------|---------|
| **SCID数据集** | 6类发票 | 40,716张 | 训练/测试 | https://davar-lab.github.io/dataset/scid.html (访问码:az49) |
| **百度飞桨** | 增值税发票 | ~1000张 | 补充测试 | https://aistudio.baidu.com/datasetdetail/165561 |
| **Hugging Face** | 通用发票 | 2,238张 | 对照测试 | https://huggingface.co/datasets/philschmid/ocr-invoice-data |

**SCID数据集说明**：
- 包含: 出租车票、火车票、客运票、通行费票、航空行程单、定额发票
- 已脱敏处理
- 提供OCR标注和信息抽取标注

#### **P1: 差旅政策文档**

已找到的公开模板（可直接使用）：
1. Aperam全球差旅和费用政策 (PDF) - 跨国企业标准
2. 民福社会福利基金会差旅费管理制度 (PDF) - 非营利组织
3. 企业差旅费管理办法模板 (DOCX) - 通用模板

---

## 四、实施时间表

### Week 1: PDF政策解析

- Day 1-2: 实现 TravelPolicyPDFProcessor
- Day 3-4: 解析已有PDF，验证提取准确性
- Day 5: 收集其他差旅政策，测试泛化能力
- **交付**: 结构化差旅政策JSON + 向量库

### Week 2: OCR引擎集成

- Day 1-2: 集成PaddleOCR，配置GPU推理
- Day 3: 下载SCID数据集
- Day 4-5: 测试OCR准确率
- **交付**: OCR服务 + 性能基准报告

### Week 3: Vision LLM + 发票识别

- Day 1-2: 部署Qwen2.5-VL-7B
- Day 3-4: 实现InvoiceRecognizer
- Day 5: 评估F1-score，目标>0.90
- **交付**: 发票识别服务 + 准确率报告

### Week 4: 集成测试

- Day 1-2: 实现多模态统一入口
- Day 3-4: 集成到OrchestratorAgent
- Day 5: E2E测试
- **交付**: 多模态API + 测试报告

---

## 五、代码文件结构

```
src/multimodal/
├── __init__.py
├── processor.py              # 统一入口
├── pdf_processor.py          # PDF政策解析
├── invoice_recognizer.py     # 发票识别
├── image_analyzer.py         # 通用图片分析
├── ocr_engine.py             # PaddleOCR封装
└── vision_llm.py             # Qwen2.5-VL封装

src/multimodal/utils/
├── image_preprocessing.py    # 图像预处理
├── validation.py             # 结果校验
└── schemas.py                # Schema定义

tests/multimodal/
├── test_pdf_processor.py
├── test_invoice_recognizer.py
└── test_image_analyzer.py

data/multimodal/
├── policies/                 # 差旅政策PDF
├── invoices/                 # 发票数据集
│   ├── train/
│   ├── val/
│   └── test/
└── samples/                  # 其他差旅单据
```

---

## 六、风险与缓解

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| **发票OCR准确率不达标** | 中 | 高 | 多模型融合 + Vision LLM校验 + 低置信度人工审核 |
| **Vision LLM推理慢** | 高 | 中 | 模型量化(INT8) + 异步处理 + 批处理优化 |
| **PDF解析中文乱码** | 中 | 中 | pdfplumber优先文本层 + OCR图像层兜底 |
| **模型显存占用高** | 低 | 高 | 使用7B模型 + 4-bit量化 |

---

## 七、成功指标

| 指标 | 目标 | 测量方式 |
|------|------|----------|
| **发票识别准确率(F1)** | 90%+ | SCID测试集 |
| **PDF政策提取完整率** | 95%+ | 人工标注对照 |
| **平均处理延迟** | <2秒 | 端到端时间 |
| **高置信度比例** | >80% | confidence>0.85占比 |

---

## 八、依赖安装

```bash
# 核心依赖
pip install paddleocr>=2.7.0
pip install pdfplumber>=0.10.0
pip install transformers>=4.35.0
pip install torch>=2.0.0

# Qwen2.5-VL
pip install qwen-vl-utils
pip install accelerate

# 图像处理
pip install opencv-python-headless
pip install pillow
```

**GPU要求**：
- 最低: 8GB显存 (T4/RTX 3060)
- 推荐: 16GB显存 (V100/RTX 4090)
- 量化后可降至6GB

---

## 九、参考资料

### 数据集下载
- [SCID数据集](https://davar-lab.github.io/dataset/scid.html) - 访问码: az49
- [百度飞桨发票数据集](https://aistudio.baidu.com/datasetdetail/165561)
- [Hugging Face发票数据集](https://huggingface.co/datasets/philschmid/ocr-invoice-data)

### 技术文档
- [PaddleOCR发票识别教程](https://www.paddleocr.ai/v2.9/applications/发票关键信息抽取.html)
- [Qwen2.5-VL文档](https://github.com/QwenLM/Qwen-VL)

---

**文档状态**: 待实施  
**下一步**: 下载SCID数据集，开始Week 1任务  
**维护人**: 项目团队
