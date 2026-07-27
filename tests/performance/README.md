# 轻量级压测模块使用指南

## 快速开始

### 1. 安装依赖
```bash
pip install httpx
```

### 2. 启动服务
```bash
python -m src.api.main
```

### 3. 运行压测
```bash
python tests/performance/load_test.py
```

## 压测配置

### 默认配置
- **并发数**: 10
- **总请求数**: 100
- **超时时间**: 30秒
- **测试端点**: Simple RAG, Multi-Agent, Chat Sync

### 自定义配置
```python
config = LoadTestConfig(
    base_url="http://localhost:8000",
    concurrency=20,        # 修改并发数
    total_requests=200,    # 修改总请求数
    timeout=60.0,          # 修改超时时间
)
```

## 性能指标说明

### 延迟指标
- **P50 (中位数)**: 50%的请求延迟低于此值
- **P95**: 95%的请求延迟低于此值（常用SLA指标）
- **P99**: 99%的请求延迟低于此值（尾部延迟）

### 吞吐量指标
- **QPS**: 每秒查询数 (Queries Per Second)
- **成功率**: 成功请求数 / 总请求数

### 测试场景

#### 场景1: 简单查询 (Simple RAG)
- **端点**: `/simple-rag/invoke`
- **测试内容**: 基础文档检索
- **预期延迟**: P95 < 2000ms

#### 场景2: 复杂任务 (Multi-Agent)
- **端点**: `/multi-agent/invoke`
- **测试内容**: 多智能体协作
- **预期延迟**: P95 < 5000ms

#### 场景3: 智能路由 (Chat Sync)
- **端点**: `/api/chat/sync`
- **测试内容**: 三层路由系统
- **预期延迟**: P95 < 3000ms

## 报告输出

### 终端输出
```
======================================================================
场景: 简单查询 - Simple RAG
----------------------------------------------------------------------
  总请求数:     100
  成功请求:     98
  失败请求:     2
  成功率:       98.00%
  总耗时:       12.34s
  QPS:          7.94 req/s

  延迟统计:
    最小值:     850.23ms
    平均值:     1203.45ms
    P50 (中位): 1150.67ms
    P95:        1789.12ms
    P99:        2103.45ms
    最大值:     2345.67ms
```

### JSON报告
自动生成 `load_test_report.json`：
```json
{
  "timestamp": "2026-07-25 14:30:00",
  "scenarios": [
    {
      "scenario": "简单查询 - Simple RAG",
      "total_requests": 100,
      "successful_requests": 98,
      "failed_requests": 2,
      "success_rate": "98.00%",
      "duration": "12.34s",
      "qps": "7.94",
      "latency": {
        "min": "850.23ms",
        "avg": "1203.45ms",
        "p50": "1150.67ms",
        "p95": "1789.12ms",
        "p99": "2103.45ms",
        "max": "2345.67ms"
      }
    }
  ]
}
```

## 优化建议

### 如果QPS过低
1. 检查数据库连接池配置
2. 增加服务器工作进程数
3. 优化LLM调用并发数

### 如果P95/P99延迟过高
1. 检查是否有慢查询
2. 优化向量检索性能
3. 添加缓存层

### 如果成功率低
1. 检查服务日志
2. 增加超时时间
3. 降低并发数

## 扩展场景

### 添加新测试场景
```python
scenarios = [
    {
        "name": "自定义场景",
        "endpoint": "/your-endpoint/invoke",
        "payload": {"input": "测试输入"},
    },
]
```

### 压测特定端点
```python
metrics = await tester.run_scenario(
    scenario_name="自定义测试",
    endpoint="/advanced-rag/invoke",
    payload={"input": "测试查询"},
)
```
