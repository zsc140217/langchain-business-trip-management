---
name: run-business-trip-system
description: Run, test, and screenshot the business trip management system (差旅管理系统) - start backend API, run automated tests, verify routing logic
---

# Business Trip Management System - Run Skill

**业务出差管理系统 - 启动和测试指南**

这是一个基于 LangChain 的智能差旅管理系统，包含：
- **后端 API**: FastAPI + 通义千问 LLM
- **前端**: React + Vite
- **架构**: 三层路由（快路径 → LLM意图识别 → QA/审批域）
- **发票识别**: 百度千帆 qianfan-ocr（2026-07-23 新增）

本 skill 提供完整的启动、测试和验证流程。

---

## Prerequisites

**系统要求**: Windows/Linux with Python 3.12+, Node.js 18+

**必需的环境变量** (在 `.env` 文件中):
```bash
# 必需
DASHSCOPE_API_KEY=sk-xxxxx        # 通义千问 API 密钥
LANGCHAIN_API_KEY=lsv2_xxxxx      # LangSmith 追踪密钥
LANGCHAIN_TRACING_V2=true

# 发票识别（2026-07-23 新增）
QIANFAN_API_KEY=bce-v3/ALTAK-...  # 百度千帆 API 密钥

# 可选
FEISHU_WEBHOOK_KEY=xxxxx          # 飞书通知（可选）
FLYAI_API_KEY=xxxxx               # 飞猪API（可选，有Mock降级）
```

**Python 依赖**:
```bash
pip install -r requirements.txt
```

**前端依赖**:
```bash
cd frontend && npm install
```

---

## Architecture Overview

**三层路由架构** (2026-07-17 已修复):

```
用户查询
   ↓
【第1层】快路径（规则匹配）
   ├─ 天气 → query_weather (和风天气API)
   ├─ 酒店 → search_hotels (飞猪API/Mock)
   ├─ 航班 → search_flights (飞猪API/Mock)
   ├─ 政策 → search_policy (FAISS向量库)
   └─ 未匹配 ↓
   
【第2层】LLM意图识别
   ├─ approval（审批域）→ ApprovalEngine
   ├─ chat（闲聊）→ 简单回复
   └─ qa（Q&A域）↓
   
【第3层】QAEngine内部路由
   ├─ simple → 单工具调用
   ├─ complex → TaskDecomposer（任务分解+并行）
   ├─ planning → PlanningEngine（Skill驱动）
   └─ open → ReactEngine（ReAct循环）
```

---

## Run (Agent Path) - Automated Testing

**推荐方式**: 使用自动化测试脚本验证所有链路

### Step 1: 启动后端服务

```bash
# 方式1: 前台启动（开发推荐，可见日志）
uvicorn src.api.unified_api:app --host 0.0.0.0 --port 8001 --reload

# 方式2: 后台启动
nohup uvicorn src.api.unified_api:app --host 0.0.0.0 --port 8001 > backend.log 2>&1 &
```

**启动时间**: 约5-8秒（加载向量库、初始化LLM）

**验证服务健康**:
```bash
curl http://localhost:8001/health
```

**预期响应**:
```json
{
  "status": "healthy",
  "components": {
    "orchestrator": true,
    "memory_service": true,
    "feishu_client": true
  }
}
```

### Step 2: 运行完整测试套件

```bash
# 8个测试用例，覆盖所有业务链路
python test_all_routes.py
```

**测试覆盖**:
- A1-A4: 快路径（天气、酒店、航班、政策）
- B1-B3: 审批域（自动审批、人工审批、状态查询）
- C1: 复杂任务（费用估算）

**预期结果** (修复后):
```
✅ 通过: 7/8 (87.5%)
⚠️  部分通过: 1/8 (12.5%)
平均响应时间: 10-15秒
路由准确率: >95%
```

**测试输出示例**:
```
🧪 测试 [A1]: 天气查询
📝 输入: 北京今天天气怎么样？
✅ 请求成功 | 耗时: 3.21秒
📍 路由: fast_path (正确)
💬 响应: 今天北京天气晴朗，气温25°C...
```

### Step 3: 查看测试结果

```bash
# 测试结果保存在
cat test_results_*.json | jq .

# 查看后端日志（如果后台启动）
tail -f backend.log | grep -E "第1层|第2层|第3层"
```

---

## Run (Human Path) - Interactive Testing

**前端启动** (需要后端先运行):

```bash
cd frontend
npm run dev
```

访问: http://localhost:5173

**手动测试指令**:

```
# 快路径测试
北京今天天气怎么样？
上海有什么酒店推荐？
查一下北京到上海的航班
北京的住宿标准是多少？

# 审批域测试
我要报销去北京出差的费用，住了2天，花了800元
我要报销去深圳出差5天的费用，总共花了3500元
我的审批进度怎么样了？

# 复杂任务测试
去杭州出差3天需要多少钱？

# 规划任务测试
帮我安排下周去深圳出差3天

# 对比推荐测试
去上海出差，飞机和高铁哪个划算？
```

---

## Direct Invocation - Component Testing

**测试单个组件** (无需完整启动):

### 测试路由逻辑
```bash
python -c "
from src.agents.orchestrator_agent import OrchestratorAgent
from src.models.llm import get_llm

llm = get_llm()
agent = OrchestratorAgent(llm=llm, tools={})

# 测试意图识别
intent = agent._llm_classify_intent('北京天气')
print(f'Intent: {intent}')  # 预期: qa

intent = agent._llm_classify_intent('我要报销800元')
print(f'Intent: {intent}')  # 预期: approval
"
```

### 测试工具调用
```bash
python -c "
from src.tools.weather_adapter import WeatherTool

tool = WeatherTool()
result = tool._run(city='北京')
print(result[:200])
"
```

### 测试审批引擎
```bash
python -c "
from src.agents.approval_engine import ApprovalEngine
from src.models.llm import get_llm

engine = ApprovalEngine(llm=get_llm())
result = engine.execute(
    query='我要报销800元',
    user_id='test_user',
    conversation_id='test_conv'
)
print(result)
"
```

---

## Gotchas

### 1. 路由问题（已修复 2026-07-17）
**症状**: 所有查询都被路由到 `approval_domain`，天气、酒店查询也显示"需要审批"

**原因**: 旧代码中审批域检查在快路径之前，且使用关键词匹配不精确

**修复**: 重构为三层路由，快路径优先，LLM意图识别保证准确性

**验证**: 查看日志是否包含 `[第1层-快路径] ✅ 命中` 或 `[第2层] LLM判断结果: qa`

### 2. 响应时间慢（20-40秒）
**原因**: 
- LLM调用次数过多（每次查询2-3次）
- 审批域 LangGraph 工作流执行时间长
- 工具 API 调用串行

**缓解**:
- 快路径命中可降至 3-5秒
- 添加缓存（天气10分钟、政策1小时）
- 并行化工具调用

### 3. 飞猪 API 降级到 Mock
**症状**: 酒店/航班返回结果标注"模拟数据"

**原因**: 
- `FLYAI_API_KEY` 未配置
- 飞猪 CLI 未安装：`npm i -g @fly-ai/flyai-cli`
- 免费配额用完（5000次/月）

**处理**: 系统自动降级，不影响功能测试

### 4. Windows 编码问题
**症状**: 测试脚本报错 `'gbk' codec can't encode character`

**修复**: 测试脚本已添加 UTF-8 编码处理
```python
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
```

### 5. PostgreSQL 数据库未启动
**症状**: 审批记录保存失败，日志显示 "未连接数据库，使用内存模式"

**处理**: 
```bash
# 启动 Docker 数据库
docker-compose up -d postgres

# 或使用内存模式（不影响测试）
# 系统会自动降级
```

### 6. Neo4j 图数据库未启动
**症状**: 关系查询（如"销售部出差最多的员工"）返回空结果

**处理**: 系统自动降级到 FAISS 向量检索，不影响其他功能

---

## Troubleshooting

### 错误: "No module named 'src'"
```bash
# 确保在项目根目录
cd E:/Desktop/langchain-business-trip-management

# 检查 PYTHONPATH
export PYTHONPATH=$PWD:$PYTHONPATH
```

### 错误: "port 8001 already in use"
```bash
# Windows
netstat -ano | findstr :8001
taskkill //F //PID <PID>

# Linux
lsof -ti:8001 | xargs kill -9
```

### 错误: "API key not found"
```bash
# 检查 .env 文件
cat .env | grep DASHSCOPE_API_KEY

# 手动设置
export DASHSCOPE_API_KEY=sk-xxxxx
```

### 测试超时（>60秒）
**症状**: 所有测试用例显示 "TIMEOUT"

**原因**: 后端服务未启动或卡住

**处理**:
```bash
# 检查后端进程
ps aux | grep uvicorn

# 重启后端
pkill -f uvicorn
uvicorn src.api.unified_api:app --host 0.0.0.0 --port 8001 --reload
```

### LLM 意图识别失败
**症状**: 日志显示 "LLM意图识别失败: timeout"

**影响**: 系统自动降级到关键词匹配，不影响基本功能

**优化**: 增加 timeout 或使用更快的模型

### 向量库加载慢（>30秒）
**症状**: 启动时卡在 "加载向量库"

**优化**: 使用预生成的向量存储
```bash
# 生成向量库（只需一次）
python scripts/build_vectorstore.py

# 向量库路径: src/data/vectorstore/
```

---

## Test Data

**测试用户**:
```
employee (员工): 日均550元，审批阈值动态计算
executive (高管): 日均670元，审批阈值动态计算
admin (管理员): 全部权限
```

**测试政策数据**: `data/knowledge_base/01_差旅管理办法.txt`

**向量库**: `src/data/vectorstore/` (FAISS)

---

## Performance Benchmarks

| 场景 | 响应时间 | LLM调用 | 状态 |
|------|---------|---------|------|
| 快路径命中（天气） | 2-5秒 | 0次 | ✅ 优秀 |
| 政策查询（缓存命中） | 0.02秒 | 0次 | ✅ 极快 |
| 审批域（自动审批） | 15-25秒 | 2次 | ✅ 正常 |
| 复杂任务（任务分解） | 25-35秒 | 3-4次 | ⚠️ 可优化 |
| ReAct循环（对比推荐） | 30-45秒 | 4-6次 | ⚠️ 较慢 |

---

## Related Documentation

- **架构设计**: `docs/ARCHITECTURE_V2_PLAN.md`
- **测试报告**: `docs/TEST_REPORT_20260717.md`
- **操作指南**: `docs/AI_SYSTEM_OPERATION_GUIDE.md`
- **路由修复交接**: 见会话记录 2026-07-17

---

## Quick Reference

```bash
# 最小启动（仅后端）
uvicorn src.api.unified_api:app --host 0.0.0.0 --port 8001

# 健康检查
curl http://localhost:8001/health

# 快速测试（单个请求）
curl -X POST http://localhost:8001/api/unified/chat \
  -H "Content-Type: application/json" \
  -d '{"query":"北京天气","user_id":"test"}'

# 完整测试
python test_all_routes.py

# 查看路由日志
tail -f backend.log | grep -E "\[第1层\]|\[第2层\]|\[第3层\]"

# 停止服务
pkill -f uvicorn
```

---

**最后更新**: 2026-07-23  
**系统状态**: ✅ 路由逻辑已修复，可正常使用  
**已知问题**: 响应时间偏慢（平均15-25秒），待优化

---

## Invoice Recognition (2026-07-23 新增)

**多模态发票识别功能** - 基于百度千帆 qianfan-ocr

### 功能概述

零样本发票识别系统，支持电子发票和纸质发票的自动识别与数据提取。

**核心能力**:
- 电子发票准确率: 95%+
- 老版发票核心字段: 100%
- 支持格式: JPG/PNG/PDF
- 响应时间: 1-2秒/张
- 自动质量验证和复核标记

### 启动方式

发票识别已集成到主 API，随后端服务自动启动（无需额外配置）。

```bash
# 使用 main.py (端口 8000)
uvicorn src.api.main:app --host 0.0.0.0 --port 8000

# 或使用 unified_api.py (端口 8001)
uvicorn src.api.unified_api:app --host 0.0.0.0 --port 8001
```

### API 端点

#### 1. 健康检查
```bash
curl http://localhost:8000/invoice/health
```

**响应**:
```json
{
  "status": "healthy",
  "model": "qianfan-ocr",
  "enable_thinking": true,
  "confidence_threshold": 0.8,
  "api_configured": true
}
```

#### 2. 识别单张发票
```bash
curl -X POST "http://localhost:8000/invoice/recognize" \
  -F "file=@发票.jpg"
```

**响应示例**:
```json
{
  "invoice_code": "25502000000008817662",
  "invoice_number": "25502000000008817662",
  "date": "2025-01-21",
  "amount": 2566198.39,
  "tax": 333605.79,
  "tax_rate": 0.13,
  "total": 2899804.18,
  "seller_name": "遂宁公路工程有限公司",
  "buyer_name": "四川川海工程管理咨询有限公司",
  "confidence": 1.0,
  "warnings": [],
  "need_review": false,
  "model": "qianfan-ocr"
}
```

#### 3. 批量识别
```bash
curl -X POST "http://localhost:8000/invoice/batch" \
  -F "files=@发票1.jpg" \
  -F "files=@发票2.pdf" \
  -F "files=@发票3.png"
```

**响应**:
```json
{
  "total": 3,
  "success": 3,
  "failed": 0,
  "results": [...]
}
```

### 测试验证

#### 核心识别器测试
```bash
# 测试老版和电子发票（5个样本）
python scripts/test_qianfan_invoice.py
```

**预期结果**:
```
测试样本数: 5
识别成功率: 100%
平均置信度: 1.000
核心字段准确率: 100%
综合字段准确率: 75%
```

#### API 端到端测试
```bash
# 测试电子发票
curl -X POST http://localhost:8000/invoice/recognize \
  -F "file=@train_data/dzfp_25502000000008817662_四川川海工程管理咨询有限公司_20250121101327.jpg"

# 测试老版发票
curl -X POST http://localhost:8000/invoice/recognize \
  -F "file=@train_data/zzsfp/imgs/b0.jpg"
```

### 性能指标

| 发票类型 | 准确率 | 响应时间 | 状态 |
|---------|--------|---------|------|
| 电子发票 (2024-2026) | 95%+ | 1-2秒 | ✅ 生产可用 |
| 老版发票 (2016) - 核心字段 | 100% | 1-2秒 | ✅ 可用 |
| 老版发票 (2016) - 文本字段 | 0% | - | ⚠️ 需优化 |

**核心字段**: amount, tax, tax_rate, total, date, invoice_number  
**文本字段**: seller_name, seller_tax_id, buyer_name

### 技术架构

```
上传文件 (JPG/PNG/PDF)
    ↓
FastAPI 接收
    ↓
PDF → JPG 转换 (200 DPI)
    ↓
百度千帆 API (qianfan-ocr)
    ↓
4层交叉验证
  ├─ 数学一致性 (amount+tax=total)
  ├─ 日期合理性 (≤今天)
  ├─ 税率合法性 (3%/6%/9%/13%/17%)
  └─ 字段完整性
    ↓
置信度评分 (0-1)
    ↓
返回结果 + 警告 + 复核标记
```

### 已知问题

#### 1. 老版发票文本字段识别率低
**问题**: seller_name 和 seller_tax_id 识别率 0%  
**影响**: 不影响核心业务字段（金额、税额、日期）  
**解决方案**: 
- 方案A: 优化 Prompt（1小时，预期提升至 85%+）
- 方案B: LoRA 微调（1-2天，预期提升至 95%+）

#### 2. 中文显示编码问题
**问题**: Windows 终端显示中文为乱码  
**影响**: 仅显示问题，数据本身正确  
**解决方案**: 前端接收的是正确 UTF-8，无需处理

### 相关文档

- **技术汇报**: 见 2026-07-23 会话输出
- **核心识别器**: `src/multimodal/qianfan_invoice_recognizer.py`
- **API 路由**: `src/api/invoice_api.py`
- **测试脚本**: `scripts/test_qianfan_invoice.py`

### 环境配置

确保 `.env` 文件包含百度千帆 API 密钥：
```bash
QIANFAN_API_KEY=bce-v3/ALTAK-bb5n0uwwEtylRfFVWBnrz/ac8b75364bcb7016af82a0789335a0c8d4ce594e
```

### 快速参考

```bash
# 健康检查
curl http://localhost:8000/invoice/health

# 识别单张
curl -X POST http://localhost:8000/invoice/recognize -F "file=@发票.jpg"

# 批量识别
curl -X POST http://localhost:8000/invoice/batch -F "files=@发票1.jpg" -F "files=@发票2.pdf"

# 测试脚本
python scripts/test_qianfan_invoice.py

# API 文档
http://localhost:8000/docs
```

---

**发票识别更新**: 2026-07-23  
**集成状态**: ✅ 完成  
**开发成本**: $174.34 (2天)

