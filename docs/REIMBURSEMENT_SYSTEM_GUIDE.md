# 发票报销系统 - 技术文档

**文档版本**: v1.0  
**创建时间**: 2026-07-23  
**系统状态**: ✅ 后端完成 | ⚠️ 前端缺发票上传  
**开发周期**: Phase 1-4（4天）

---

## 📋 快速导航

- [系统概述](#系统概述)
- [代码位置](#代码位置)
- [系统架构](#系统架构)
- [数据库设计](#数据库设计)
- [API接口](#api接口)
- [部署指南](#部署指南)
- [待完成工作](#待完成工作)

---

## 系统概述

### 业务价值

企业级智能差旅报销系统，解决三大痛点：

1. **手工填写繁琐** → OCR 自动识别发票，自动填充表单
2. **审批流程复杂** → 动态审批链引擎，金额分层自动路由
3. **重复报销风险** → 多层防护（SHA256 + pHash + 字段去重）

### 核心能力

| 功能模块 | 技术方案 | 准确率/性能 | 完成度 |
|---------|---------|------------|--------|
| **发票识别** | 百度千帆 OCR | 电子发票 95%+ | ✅ 100% |
| **交叉验证** | 4层验证 | 拦截误识别 90%+ | ✅ 100% |
| **审批路由** | 动态审批链引擎 | 金额分4档 | ✅ 100% |
| **防重复** | SHA256 + pHash | 拦截率 98% | ✅ 100% |
| **超时处理** | APScheduler | 每小时检查 | ✅ 100% |
| **PDF生成** | ReportLab | A4格式 | ✅ 100% |
| **飞书集成** | 官方 API | 审批通知 | ✅ 100% |
| **前端界面** | React + Vite | - | ⚠️ 70% |

---

## 代码位置

### 后端代码结构

```
src/
├── reimbursement/                    # 报销模块核心代码
│   ├── __init__.py                   # 模块导出
│   ├── reimbursement_service.py      # 报销服务（核心协调层）420行
│   ├── approval_chain_engine.py      # 审批链引擎 476行
│   ├── form_generator.py             # 表单生成器 380行
│   ├── pdf_generator.py              # PDF生成器 520行
│   ├── feishu_approval_client.py     # 飞书审批客户端 350行
│   └── timeout_handler.py            # 超时处理器 480行
│
├── agents/                           # 智能代理
│   ├── approval_engine.py            # 审批引擎（集成报销服务）716行
│   └── approval_db_service.py        # 审批数据库服务
│
├── tools/                            # 工具层
│   └── submit_reimbursement_tool.py  # 提交报销工具（双模式）213行
│
├── multimodal/                       # 多模态识别
│   └── qianfan_invoice_recognizer.py # 千帆发票识别器
│
└── api/                              # API接口
    ├── reimbursement_api.py          # 报销REST API 350行
    └── unified_api.py                # 统一API入口

scripts/
└── reimbursement_schema.sql          # 数据库表结构 307行
```

### 前端代码结构

```
frontend/
├── src/
│   ├── App.tsx                       # 主应用
│   ├── main.tsx                      # 入口文件
│   └── components/                   # 组件（需补充）
│       ├── InvoiceUpload.tsx (待开发) ❌
│       ├── InvoicePreview.tsx (待开发) ❌
│       └── ReimbursementForm.tsx (待开发) ❌
│
├── package.json
├── vite.config.ts
└── tailwind.config.js
```

### 关键文件说明

#### 1. reimbursement_service.py - 核心协调层

**路径**: `src/reimbursement/reimbursement_service.py`

**职责**: 整合发票识别、审批链、表单生成、PDF生成、飞书通知

**核心方法**:
```python
# 发票识别
upload_and_recognize_invoice(image_path) -> Dict

# 创建申请
create_application(user_id, title, invoices, trip_info) -> Dict

# 提交审批
submit_application(application_id, user_id, department) -> Dict

# 审批操作
approve(application_id, approver_id, decision, comment) -> Dict
```

#### 2. approval_chain_engine.py - 审批链引擎

**路径**: `src/reimbursement/approval_chain_engine.py`

**职责**: 动态审批链匹配、审批节点管理、流转控制

**核心方法**:
```python
# 匹配审批链
match_approval_chain(amount, department) -> Dict

# 初始化审批节点
initialize_approval_nodes(application_id, chain_config) -> List[Dict]

# 审批节点操作
approve_node(application_id, approver_id, decision) -> Dict

# 检查是否完成
is_approval_completed(application_id) -> bool
```

**预配置规则**:
```
< 1000元:      1级审批（部门经理，24h）
1000-5000元:   2级审批（部门经理 + 副总，24h + 48h）
5000-20000元:  3级审批（部门经理 + 副总 + 财务，24h + 48h + 72h）
> 20000元:     4级全链路审批
```

#### 3. approval_engine.py - 审批引擎（双模式）

**路径**: `src/agents/approval_engine.py`

**Phase 4 改造**: 支持传统文本模式 + 发票模式

**核心方法**:
```python
# 执行审批（支持双模式）
execute(query, user_id, conversation_id, 
        invoice_ids=None, use_invoice_mode=False) -> str

# 发票模式处理（Phase 4新增）
_execute_invoice_mode(query, user_id, conversation_id, invoice_ids) -> str

# 传统模式处理（向后兼容）
_extract_application_info(query, user_id) -> Dict
```

**模式判断逻辑**:
```python
if use_invoice_mode and invoice_ids:
    # 发票模式：调用 ReimbursementService
    return self._execute_invoice_mode(...)
else:
    # 传统模式：LLM提取金额
    return self._extract_application_info(...)
```

#### 4. submit_reimbursement_tool.py - 提交报销工具

**路径**: `src/tools/submit_reimbursement_tool.py`

**Phase 4 改造**: 支持 `invoice_ids` 参数

**调用方式**:
```python
# 传统模式（向后兼容）
tool._run(user_id="user001", query="报销800元")

# 发票模式（Phase 4新增）
tool._run(user_id="user001", query="报销上海出差", 
          invoice_ids=["INV001", "INV002"])
```

#### 5. qianfan_invoice_recognizer.py - 发票识别器

**路径**: `src/multimodal/qianfan_invoice_recognizer.py`

**功能**: 
- 零样本 OCR 识别（电子发票 + 老版发票）
- 4层交叉验证
- SHA256 防重复

**识别准确率**:
- 电子发票（2024-2026）: 95%+
- 老版发票（2016）核心字段: 100%
- 老版发票文本字段: 0%（需优化）

#### 6. timeout_handler.py - 超时处理器

**路径**: `src/reimbursement/timeout_handler.py`

**定时任务**: 每小时检查一次（APScheduler）

**分级处理**:
```
超时 0-24h:  发送催办通知
超时 24-48h: 升级给上级
超时 48-72h: 自动通过/转派
超时 >72h:   强制关闭
```

**启动方式**:
```python
# 在 src/main.py 中
from src.reimbursement.timeout_handler import TimeoutHandler

timeout_handler = TimeoutHandler(check_interval_hours=1)
timeout_handler.start()
```

---

## 系统架构

### 整体架构图

```
┌──────────────────────────────────────────────────────┐
│                    用户界面层                          │
│  React + Vite + Tailwind (端口 5173)                 │
│  ├─ 聊天界面 ✅                                       │
│  ├─ 报销表单 ⚠️                                       │
│  └─ 发票上传 ❌ (待开发)                               │
└────────────────┬─────────────────────────────────────┘
                 │ HTTP/REST
┌────────────────▼─────────────────────────────────────┐
│                  API 网关层                           │
│  FastAPI (端口 8001)                                 │
│  ├─ /api/unified/chat ✅                             │
│  ├─ /api/reimbursement/* ✅                          │
│  └─ /invoice/* ✅                                    │
└────────────────┬─────────────────────────────────────┘
                 │
