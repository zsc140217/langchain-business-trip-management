# 模块5：监控系统 - 学习检验题

## 📝 基础概念题（必答）

### Q1: 监控系统的三个层次
**问题**: LangSmith、Prometheus、Grafana 分别负责什么？

**答案**:
- LangSmith: 单次LLM调用的详细追踪（Input/Output/Token/延迟）
- Prometheus: 整体趋势的指标采集和存储（QPS/错误率/P95延迟）
- Grafana: 数据可视化展示（Dashboard面板）

---

### Q2: Prometheus指标类型
**问题**: 以下场景应该用什么指标类型？

A. 记录总请求数 → **Counter**（只增不减）
B. 记录当前内存使用率 → **Gauge**（可增可减）
C. 记录每次请求延迟 → **Histogram**（分布统计）

**解释**:
- Counter: 累计值，如总请求数、总成本
- Gauge: 瞬时值，如CPU使用率、缓存命中率
- Histogram: 分布统计，如延迟P50/P95/P99

---

### Q3: PromQL基础
**问题**: 解释以下查询的含义

```promql
rate(travel_agent_requests_total{status="error"}[5m]) 
/ 
rate(travel_agent_requests_total[5m])
```

**答案**:
- 分子: 5分钟内错误请求的增长率
- 分母: 5分钟内总请求的增长率
- 结果: 错误率（百分比）

---

## 🔧 实战操作题

### Q4: 启动监控服务
**任务**: 启动Prometheus + Grafana + Alertmanager

**命令**:
```bash
cd monitoring
docker-compose up -d
docker-compose ps  # 验证
```

**验证**:
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000
- Alertmanager: http://localhost:9093

---

### Q5: 查看Prometheus指标
**任务**: 运行演示脚本，查看生成的指标

**步骤**:
```bash
# 1. 运行FastAPI演示
python examples/monitoring_fastapi_demo.py

# 2. 触发请求
curl "http://localhost:8000/api/query?q=test"

# 3. 查看指标
curl http://localhost:8000/metrics | grep travel_agent
```

**期望看到**:
```
travel_agent_requests_total{status="success"} 1
travel_agent_llm_calls_total{operation="query_rewrite",cached="false"} 1
```

---

### Q6: Grafana Dashboard
**任务**: 在Grafana中查看Dashboard

**步骤**:
1. 访问 http://localhost:3000
2. 登录 admin / admin123
3. 导航到 Dashboards → Browse → Travel Agent Overview
4. 观察8个面板的数据

**问题**: 如果面板显示"No Data"，可能是什么原因？

**答案**:
- FastAPI应用没有运行（没有数据源）
- Prometheus没有成功抓取指标
- 时间范围设置不对（调整右上角时间）

---

### Q7: LangSmith追踪
**任务**: 在LangSmith中查看调用链

**步骤**:
```bash
# 1. 确保.env中配置了API Key
cat .env | grep LANGCHAIN

# 2. 运行演示
python examples/monitoring_complete_demo.py

# 3. 访问LangSmith
# https://smith.langchain.com/
```

**问题**: 你能在LangSmith中看到哪些信息？

**答案**:
- 调用链树状图（query_rewrite → embedding → llm）
- 每一步的Input/Output
- Token消耗和成本
- 延迟（每步耗时）

---

## 🎯 进阶应用题

### Q8: 设计自定义告警
**场景**: 希望当"缓存命中率低于50%"时触发告警

**任务**: 在 `monitoring/alerts.yml` 中添加告警规则

**答案**:
```yaml
- alert: LowCacheHitRate
  expr: travel_agent_cache_hit_rate < 50
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "缓存命中率过低"
    description: "缓存命中率为 {{ $value }}%，低于50%"
```

---

### Q9: 故障排查
**场景**: Grafana显示"P95延迟突然从1秒升到10秒"

**问题**: 你会如何排查？

**答案**:
1. 在Prometheus中确认趋势（排除Dashboard配置问题）
2. 在LangSmith中查看最近的慢请求
3. 找到具体慢在哪一步（embedding? llm?）
4. 检查该步骤的日志和错误
5. 分析是否有外部依赖问题（API限流？网络？）

---

### Q10: 集成到项目
**任务**: 在你的FastAPI项目中集成监控

**步骤**:
```python
from fastapi import FastAPI
from src.monitoring import initialize_langsmith
from src.monitoring.prometheus_exporter import setup_metrics_endpoint, PrometheusMiddleware

app = FastAPI()

@app.on_event("startup")
async def startup():
    initialize_langsmith(project_name="my-project")
    setup_metrics_endpoint(app)

app.add_middleware(PrometheusMiddleware)
```

**验证**: 访问 `/metrics` 应该看到指标

---

## 🏆 综合测试

### 终极挑战: 完整监控流程
**场景**: 你需要监控一个LLM应用的完整请求链路

**要求**:
1. 启动所有监控服务（Prometheus/Grafana/LangSmith）
2. 编写一个FastAPI应用，集成所有监控
3. 模拟100个请求，其中10%失败
4. 在Grafana中观察错误率趋势
5. 在LangSmith中查看失败的trace
6. 设计一个告警规则，当错误率>5%时触发
7. 用curl模拟触发告警

**提示**: 使用 `examples/monitoring_fastapi_demo.py` 作为基础

---

## 📊 评分标准

- **0-3题正确**: 需要重新阅读文档
- **4-6题正确**: 基础理解，需要更多实践
- **7-8题正确**: 良好掌握，可以实战应用
- **9-10题正确**: 精通，可以独立设计监控系统

---

## 🎓 学习建议

### 如果得分<6分:
1. 重新阅读 `docs/MODULE5_QUICKSTART.md`
2. 运行所有演示脚本
3. 在Grafana中点击每个面板，理解查询语句
4. 在LangSmith中查看至少10条trace

### 如果得分6-8分:
1. 尝试修改 `alerts.yml` 添加自定义告警
2. 修改 Grafana Dashboard 添加新面板
3. 在自己的项目中集成监控
4. 分析LangSmith数据优化Prompt

### 如果得分>8分:
1. 恭喜！你已经掌握了监控系统
2. 尝试优化告警阈值（避免误报）
3. 设计更复杂的Grafana Dashboard
4. 探索LangSmith的高级功能（A/B测试、Dataset）

---

**完成所有题目后，请自评得分，并制定下一步学习计划！**
