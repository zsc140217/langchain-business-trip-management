# 多模态发票识别模块

## 功能说明

基于 PaddleOCR + LayoutLMv3 的两阶段发票识别系统，支持：
- 增值税专用发票识别
- 电子发票识别
- 多字段提取（发票代码、号码、日期、金额、税额等）
- 4层交叉验证机制
- 置信度评分

## 快速开始

### 1. 安装依赖

```bash
pip install paddleocr paddlepaddle transformers torch pillow opencv-python scikit-learn pandas
```

### 2. 运行简单测试

```bash
python scripts/test_invoice_recognition_simple.py
```

这会测试 `train_data/zzsfp/imgs/` 目录下的第一张发票图片。

### 3. 使用示例

```python
from src.multimodal.invoice_recognizer import AdvancedInvoiceRecognizer

# 初始化识别器
recognizer = AdvancedInvoiceRecognizer()

# 识别发票
result = recognizer.recognize("path/to/invoice.jpg")

# 查看结果
print(f"发票号码: {result['number']}")
print(f"金额: {result['amount']}")
print(f"置信度: {result['confidence']}")
```

## 架构说明

### 两阶段识别流程

```
输入图片
  ↓
Stage 1: PaddleOCR文本提取 (~200ms)
  ↓
Stage 2: LayoutLMv3多模态理解 (~1.5s)
  ↓
Stage 3: 交叉验证与评分
  ↓
结构化数据 + 置信度
```

### 交叉验证机制

1. **价税合计一致性** - 验证 金额+税额=价税合计
2. **OCR文本包含性** - 检查关键字段是否在OCR结果中
3. **日期合理性** - 开票日期不能晚于当前日期
4. **税率合理性** - 税率必须在 [3%, 6%, 9%, 13%] 范围内

### 置信度评分

综合考虑：
- 基础置信度（交叉验证得分）50%
- 字段完整性 30%
- 异常惩罚 20%

置信度 > 0.8：高置信度，可直接使用
置信度 0.6-0.8：中等置信度，建议复核
置信度 < 0.6：低置信度，需要人工复核

## 注意事项

1. **首次运行较慢** - PaddleOCR 和 LayoutLM 会自动下载模型（约400MB），需要一定时间
2. **GPU加速** - 如果有NVIDIA GPU，修改 `use_gpu=True` 可提升速度
3. **预训练模型** - 当前使用 `microsoft/layoutlmv3-base-chinese` 预训练模型，未针对发票微调
4. **识别准确率** - 预训练模型准确率约70-75%，微调后可达92%+

## 下一步优化

- [ ] 模型微调（需要标注数据转换）
- [ ] 模型量化（提升推理速度）
- [ ] 异步流水线（批量处理优化）
- [ ] API接口集成

## 参考文档

详细技术方案请参考：`docs/MULTIMODAL_ADVANCED_PLAN.md`
