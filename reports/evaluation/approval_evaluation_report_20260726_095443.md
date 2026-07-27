# 审批流程评估报告

**生成时间**: 2026-07-26 09:54:43
**评估器版本**: 1.0.0
**自动审批阈值**: 1000元

## 执行摘要

- **测试总数**: 23
- **通过**: 22
- **失败**: 1
- **通过率**: 95.7%
- **总体覆盖率**: 115.0%

## 测试类别统计

| 类别 | 总数 | 通过 | 失败 | 通过率 |
|------|------|------|------|--------|
| boundary | 8 | 8 | 0 | 100.0% |
| approval_path | 2 | 2 | 0 | 100.0% |
| amount | 7 | 7 | 0 | 100.0% |
| missing_field | 6 | 5 | 1 | 83.3% |

## 覆盖率矩阵

### 1. 金额阈值覆盖

| 金额 | 预期路径 | 实际路径 | 状态 |
|------|----------|----------|------|
| 0元 | auto | auto | PASS |
| 500元 | auto | auto | PASS |
| 999元 | auto | auto | PASS |
| 1000元 | manual | manual | PASS |
| 1001元 | manual | manual | PASS |
| 5000元 | manual | manual | PASS |
| 10000元 | manual | manual | PASS |

### 2. 缺失字段覆盖

| 缺失字段 | 检测状态 |
|----------|----------|
| destination | PASS |
| days | PASS |
| estimated_amount | PASS |
| purpose | FAIL |
| destination, days | PASS |
| destination, days, estimated_amount | PASS |

### 3. 边界条件覆盖

| 测试项 | 状态 |
|--------|------|
| 最小天数: 1天 | PASS |
| 正常天数: 30天 | PASS |
| 异常天数: 0天（无效） | PASS |
| 异常天数: -1天（无效） | PASS |
| 异常金额: 负数（无效） | PASS |
| 超大金额: 999999元 | PASS |
| 空目的地（无效） | PASS |
| 超长目的地: 100字符 | PASS |

### 4. 审批路径覆盖

| 审批路径 | 状态 |
|----------|------|
| 自动审批 | PASS |
| 人工审批 | PASS |

## 失败测试详情

### TC_011: 缺失事由（可选）

- **输入**: `{"destination": "上海", "days": 2, "estimated_amount": 800}`
- **期望**: `{"validation": "fail", "missing_fields": ["purpose"], "error_type": "missing_required_field"}`
- **实际**: `{"validation": "pass", "approval_path": "auto", "status": "approved", "amount": 800, "threshold": 1000}`

## 结论和建议

审批流程稳定性: **优秀** ✅

### 建议

- 修复 1 个失败的测试用例
- 定期执行评估脚本以确保流程稳定性
