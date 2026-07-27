# 系统测试规划 - 完整链路验证

**测试日期**: 2026-07-17  
**测试环境**: Windows  
**测试目标**: 验证前端到后端所有业务链路畅通

---

## 📋 测试前准备

### 1. 环境检查

```bash
# 1.1 验证Python环境
python --version  # 需要 3.12+

# 1.2 检查环境变量
echo $DASHSCOPE_API_KEY
echo $LANGCHAIN_API_KEY
echo $FEISHU_WEBHOOK_KEY

# 1.3 验证依赖包
pip list | grep -E "fastapi|langchain|dashscope"
```

### 2. 数据库准备

```bash
# 2.1 启动PostgreSQL（如果使用Docker）
docker-compose up -d postgres

# 2.2 验证数据库连接
psql -h localhost -U postgres -d business_trip -c "SELECT version();"
```

### 3. 服务启动顺序

**步骤1: 启动后端**
```bash
cd E:\Desktop\langchain-business-trip-management
uvicorn src.api.unified_api:app --host 0.0.0.0 --port 8001 --reload
```

**预期输出**:
```
INFO:     Uvicorn running on http://0.0.0.0:8001
INFO:     Application startup complete.
```

**步骤2: 验证后端健康**
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

**步骤3: 启动前端**
```bash
cd frontend
npm run dev
```

**预期输出**:
```
VITE ready in 500 ms
Local:   http://localhost:5173/
```

---

## 🧪 测试用例清单

### 测试组 A: 快路径 - 单工具调用

#### A1. 天气查询
**输入**: `北京今天天气怎么样？`

**预期路由**: `qa_domain` → `simple通道` → `search_weather`

**预期响应包含**:
- 北京的天气信息
- 温度、湿度、天气状况
- 数据来源标注

**验证要点**:
- [ ] 响应时间 < 5秒
- [ ] 包含真实天气数据
- [ ] 无报错信息

---

#### A2. 酒店查询
**输入**: `上海有什么酒店推荐？`

**预期路由**: `qa_domain` → `simple通道` → `search_hotel`

**预期响应包含**:
- 上海的酒店列表（至少3家）
- 酒店名称、星级、价格
- 数据来源标注（飞猪数据/模拟数据）

**验证要点**:
- [ ] 响应时间 < 8秒
- [ ] 酒店信息结构完整
- [ ] 包含价格和评分

---

#### A3. 航班查询
**输入**: `查一下北京到上海的航班`

**预期路由**: `qa_domain` → `simple通道` → `search_flight`

**预期响应包含**:
- 航班列表
- 航班号、起降时间、价格
- 数据来源标注

**验证要点**:
- [ ] 响应时间 < 8秒
- [ ] 航班信息结构完整
- [ ] 包含出发和到达时间

---

#### A4. 政策查询
**输入**: `北京的住宿标准是多少？`

**预期路由**: `qa_domain` → `simple通道` → `search_policy`

**预期响应包含**:
- 住宿标准金额
- 员工等级区分
- 相关政策说明

**验证要点**:
- [ ] 响应时间 < 5秒
- [ ] 包含具体金额
- [ ] 引用政策文件

---

### 测试组 B: 审批域

#### B1. 自动审批（金额 < 阈值）
**输入**: `我要报销去北京出差的费用，住了2天，花了800元`

**预期路由**: `approval_domain` → `自动审批`

**预期响应包含**:
- "您的报销申请已自动通过"
- 金额：¥800
- 审批状态：已通过

**验证要点**:
- [ ] 响应时间 < 10秒
- [ ] 明确标注"自动通过"
- [ ] 工作记忆已更新

**后端日志验证**:
```
INFO: ApprovalEngine: amount=800 < threshold=1100 → auto_approve
INFO: WorkingMemory: approval status updated to 'approved'
```

---

#### B2. 人工审批（金额 ≥ 阈值）
**输入**: `我要报销去深圳出差5天的费用，总共花了3500元`

**预期路由**: `approval_domain` → `人工审批`

**预期响应包含**:
- "申请已提交，金额超过XXX元，需要人工审批"
- 审批单号
- "请等待审批人处理"

**验证要点**:
- [ ] 响应时间 < 10秒
- [ ] 明确标注"需要人工审批"
- [ ] 生成审批单号
- [ ] （可选）飞书卡片已发送

**后端日志验证**:
```
INFO: ApprovalEngine: amount=3500 >= threshold=1650 → manual_approval
INFO: FeishuClient: approval card sent successfully
INFO: WorkingMemory: approval status updated to 'pending_approval'
```

---

#### B3. 审批状态查询
**输入**: `我的审批进度怎么样了？`

**预期路由**: `approval_domain` → `check_approval_status`

**预期响应包含**:
- 当前审批状态
- 提交时间
- 审批金额

**验证要点**:
- [ ] 响应时间 < 3秒
- [ ] 显示最近的审批记录
- [ ] 状态准确（pending/approved/rejected）

---

### 测试组 C: Q&A域 - 复杂通道

#### C1. 多步骤任务
**输入**: `去杭州出差3天需要多少钱？`

**预期路由**: `qa_domain` → `complex通道` → `TaskDecomposer`

**预期响应包含**:
- 住宿费用估算
- 伙食补助
- 交通费用
- 总计金额

**验证要点**:
- [ ] 响应时间 < 15秒
- [ ] 包含费用明细
- [ ] 调用多个工具（search_policy等）

**后端日志验证**:
```
INFO: ComplexTaskEngine: decomposed into 3 subtasks
INFO: TaskDecomposer: parallel execution started
```

---

#### C2. 关系查询（需要Neo4j）
**输入**: `销售部出差最多的员工是谁？`

**预期路由**: `qa_domain` → `complex通道` → `query_graph`

**预期响应包含**:
- 员工姓名
- 出差次数

**验证要点**:
- [ ] 响应时间 < 10秒
- [ ] 包含具体次数
- [ ] 数据来源Neo4j

**注意**: 如果Neo4j未启动，会降级到RAG检索

---

### 测试组 D: Q&A域 - 规划通道

#### D1. 差旅规划
**输入**: `帮我安排下周去深圳出差3天`

**预期路由**: `qa_domain` → `planning通道` → `PlanningEngine`

**预期响应包含**:
- 住宿推荐
- 天气提醒
- 费用预算
- 注意事项

**验证要点**:
- [ ] 响应时间 < 20秒
- [ ] 包含完整方案
- [ ] 调用Skill步骤

**后端日志验证**:
```
INFO: PlanningEngine: loaded skill 'trip_planning_skill.md'
INFO: PlanningEngine: step 1/7 - extract_info
INFO: PlanningEngine: step 7/7 - generate_plan
```

---

### 测试组 E: Q&A域 - 开放通道

#### E1. 比较推荐
**输入**: `去上海出差，飞机和高铁哪个划算？`

**预期路由**: `qa_domain` → `open通道` → `ReactEngine`

**预期响应包含**:
- 飞机和高铁的对比
- 时间成本分析
- 费用对比
- 推荐建议

**验证要点**:
- [ ] 响应时间 < 15秒
- [ ] 包含多角度分析
- [ ] 给出明确建议

**后端日志验证**:
```
INFO: ReactEngine: iteration 1 - search_policy (交通标准)
INFO: ReactEngine: iteration 2 - search_policy (距离)
INFO: ReactEngine: iteration 3 - synthesize answer
```

---

## 📊 测试结果记录表

| 测试组 | 测试用例 | 预期路由 | 实际路由 | 响应时间 | 结果 | 问题描述 |
|--------|---------|---------|---------|---------|------|---------|
| A1 | 天气查询 | qa_domain/simple | | | ⬜ PASS / ❌ FAIL | |
| A2 | 酒店查询 | qa_domain/simple | | | ⬜ PASS / ❌ FAIL | |
| A3 | 航班查询 | qa_domain/simple | | | ⬜ PASS / ❌ FAIL | |
| A4 | 政策查询 | qa_domain/simple | | | ⬜ PASS / ❌ FAIL | |
| B1 | 自动审批 | approval_domain | | | ⬜ PASS / ❌ FAIL | |
| B2 | 人工审批 | approval_domain | | | ⬜ PASS / ❌ FAIL | |
| B3 | 审批状态 | approval_domain | | | ⬜ PASS / ❌ FAIL | |
| C1 | 多步骤任务 | qa_domain/complex | | | ⬜ PASS / ❌ FAIL | |
| C2 | 关系查询 | qa_domain/complex | | | ⬜ PASS / ❌ FAIL | |
| D1 | 差旅规划 | qa_domain/planning | | | ⬜ PASS / ❌ FAIL | |
| E1 | 比较推荐 | qa_domain/open | | | ⬜ PASS / ❌ FAIL | |

---

## 🔍 故障排查指南

### 问题1: 后端启动失败

**症状**: `ModuleNotFoundError` 或 `ImportError`

**排查步骤**:
```bash
# 1. 验证当前目录
pwd  # 应在 langchain-business-trip-management/

# 2. 重新安装依赖
pip install -r requirements.txt

# 3. 检查Python路径
python -c "import sys; print('\n'.join(sys.path))"
```

---

### 问题2: MCP工具调用失败

**症状**: `RuntimeError: Cannot run the event loop`

**排查步骤**:
```bash
# 1. 检查MCP客户端版本
grep "class MCPClientManager" src/tools/mcp_client.py
# 应包含 "threading.Thread"

# 2. 重启后端清除旧进程
taskkill //F //IM python.exe
```

---

### 问题3: 工具返回空结果

**症状**: "未找到相关信息"

**排查步骤**:
```bash
# 1. 检查API密钥
echo $DASHSCOPE_API_KEY
echo $FLYAI_API_KEY

# 2. 测试单个工具
python -c "
from src.tools.weather_adapter import WeatherTool
tool = WeatherTool()
result = tool._run(city='北京')
print(result)
"

# 3. 查看后端日志
tail -f backend.log | grep -E "ERROR|WARNING"
```

---

### 问题4: 前端连接后端失败

**症状**: `Network Error` 或 `CORS Error`

**排查步骤**:
```bash
# 1. 验证后端健康
curl http://localhost:8001/health

# 2. 检查前端配置
cat frontend/src/config.ts
# API_BASE_URL 应为 http://localhost:8001

# 3. 检查CORS配置
grep "CORSMiddleware" src/api/unified_api.py
```

---

### 问题5: 审批流程不触发

**症状**: 审批查询被错误路由到Q&A域

**排查步骤**:
```bash
# 1. 检查关键词列表
grep "approval_keywords" src/agents/orchestrator_agent.py
# 应包含: "报销", "申请", "审批"

# 2. 查看路由日志
tail -f backend.log | grep "OrchestratorAgent"
```

---

## 📝 测试完成检查清单

### 核心功能验证
- [ ] 所有快路径工具（天气/酒店/航班/政策）可正常调用
- [ ] 自动审批流程完整（<阈值）
- [ ] 人工审批流程完整（≥阈值）
- [ ] 审批状态查询准确
- [ ] 复杂任务分解执行
- [ ] 差旅规划Skill运行

### 性能指标
- [ ] 简单查询响应时间 < 5秒
- [ ] 复杂查询响应时间 < 15秒
- [ ] 审批流程响应时间 < 10秒

### 数据准确性
- [ ] 天气数据真实（和风天气API）
- [ ] 酒店/航班数据真实（飞猪API）或明确标注模拟
- [ ] 政策检索准确（匹配FAISS向量库）

### 用户体验
- [ ] 前端界面正常显示
- [ ] 聊天消息流畅发送/接收
- [ ] 错误提示清晰友好
- [ ] 加载状态可见

---

## 🚀 快速测试脚本

### 自动化测试脚本

```python
# test_all_routes.py
import requests
import time

BASE_URL = "http://localhost:8001"

test_cases = [
    {"name": "天气查询", "query": "北京今天天气怎么样？", "expected_route": "qa_domain"},
    {"name": "酒店查询", "query": "上海有什么酒店推荐？", "expected_route": "qa_domain"},
    {"name": "政策查询", "query": "北京的住宿标准是多少？", "expected_route": "qa_domain"},
    {"name": "自动审批", "query": "我要报销去北京出差的费用，花了800元", "expected_route": "approval_domain"},
    {"name": "人工审批", "query": "我要报销去深圳出差5天的费用，总共花了3500元", "expected_route": "approval_domain"},
]

def run_test(test_case):
    print(f"\n{'='*60}")
    print(f"测试: {test_case['name']}")
    print(f"输入: {test_case['query']}")
    
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/unified/chat",
            json={
                "query": test_case['query'],
                "user_id": "test_user",
                "conversation_id": "test_conv"
            },
            timeout=60
        )
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 成功 | 耗时: {elapsed:.2f}s")
            print(f"路由: {result.get('route', 'N/A')}")
            print(f"响应: {result['answer'][:150]}...")
            
            if result.get('route') == test_case['expected_route']:
                print("✅ 路由正确")
            else:
                print(f"⚠️ 路由不符: 期望 {test_case['expected_route']}, 实际 {result.get('route')}")
        else:
            print(f"❌ 失败 | 状态码: {response.status_code}")
            print(f"错误: {response.text}")
            
    except Exception as e:
        print(f"❌ 异常: {str(e)}")

if __name__ == "__main__":
    print("开始系统测试...")
    print(f"后端地址: {BASE_URL}")
    
    # 健康检查
    try:
        health = requests.get(f"{BASE_URL}/health", timeout=5)
        if health.status_code == 200:
            print("✅ 后端健康检查通过")
        else:
            print("❌ 后端健康检查失败")
            exit(1)
    except Exception as e:
        print(f"❌ 无法连接后端: {e}")
        exit(1)
    
    # 运行测试
    for test_case in test_cases:
        run_test(test_case)
        time.sleep(2)  # 避免请求过快
    
    print(f"\n{'='*60}")
    print("测试完成！")
```

运行测试:
```bash
python test_all_routes.py
```

---

**测试人员**: _______________  
**测试日期**: _______________  
**测试结果**: ⬜ 全部通过 / ⬜ 部分通过 / ⬜ 失败  
**备注**: _______________________________________________
