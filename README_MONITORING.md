# 监控系统使用指南

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 启动监控服务
```bash
cd monitoring
docker-compose up -d
```

### 3. 访问监控面板
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin123)
- **Alertmanager**: http://localhost:9093

### 4. 停止服务
```bash
cd monitoring
docker-compose down
```

## 产出文件

- `src/monitoring/` - 监控模块代码
- `monitoring/` - Docker部署配置
- `tests/monitoring/` - 集成测试
- `examples/monitoring_example.py` - 演示脚本
- `docs/MODULE5_COMPLETION_SUMMARY.md` - 完整文档

## 核心功能

✅ LangSmith追踪LLM调用链
✅ Prometheus导出8个核心指标
✅ Grafana实时可视化Dashboard
✅ Alertmanager智能告警推送飞书
✅ Docker一键部署
✅ 低延迟开销（<10ms）

详见：`docs/MODULE5_COMPLETION_SUMMARY.md`
