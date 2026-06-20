# Chatflow 与 Workflow 集成指南

> 完成日期：2026-06-17  
> 适用版本：Dify v1.14.2  
> 会话成本：$75.82

---

## 📊 当前两个模块状态

### Chatflow - 差旅审批助手 ✅

**功能**：接收用户对话，提取差旅申请信息

**节点流程**：
```
用户输入 → 意图识别 → 条件分支
  ↓ IF（信息完整）
  构造检索查询 → 意图检索 + 原始问题检索 → 综合回复
  ↓ ELSE（信息不完整）
  直接回复 + 数据收集成功回复
```

**状态**：✅ 独立运行正常

---

### Workflow - 差旅审批引擎 ✅

**功能**：执行审批逻辑

**输入参数**：destination, start_date, end_date, purpose  
**输出变量**：response（审批消息）

**测试结果**：
- ✅ 上海3天 → 自动通过
- ✅ 北京15天 → 人工审批

---

## 🔗 集成步骤

### Step 1：添加代码节点 - 提取申请信息

在 IF 分支添加代码节点：

**代码**：
```python
def main(intent_output: str) -> dict:
    import json
    try:
        start = intent_output.find('{')
        end = intent_output.rfind('}')
        if start != -1 and end != -1:
            json_str = intent_output[start:end+1]
            data = json.loads(json_str)
        else:
            data = {}
    except:
        data = {}
    
    return {
        "destination": data.get("destination", ""),
        "start_date": data.get("start_date", ""),
        "end_date": data.get("end_date", ""),
        "purpose": data.get("purpose", "")
    }
```

**输出变量**：destination, start_date, end_date, purpose

### Step 2：添加 Workflow 节点

删除：意图检索、原始问题检索

**配置**：
- 选择工作流：差旅审批引擎
- 输入映射：4个字段 → 提取申请信息节点

### Step 3：修改综合回复

回复内容改为：`{{#调用审批引擎.response#}}`

---

## 🧪 测试用例

1. "我要去上海出差，6月20-22日，拜访客户" → 自动通过
2. "我要去北京出差，7月1日到15日，长期驻场项目" → 人工审批
3. "我想去北京出差" → 提示补充信息

---

## ⚠️ 常见问题

1. **缺少输入变量**：检查4个变量是否都映射
2. **回复空白**：检查变量引用名称
3. **响应慢(>10秒)**：正常，包含多次LLM调用

---

## ✅ 完成标志

- Chatflow 可调用 Workflow
- 端到端测试通过
- 响应时间 8-12秒

---

## 🚀 下次启动

```bash
# 启动 Docker
docker-compose -f /e/dify-workspace/dify/docker/docker-compose.yml up -d

# 访问
http://localhost
```

**建议**：开新会话继续，提供这份文档！
