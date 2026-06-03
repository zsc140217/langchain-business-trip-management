# LangChain 差旅管理系统 - 操作指南

## 📋 目录
- [快速开始](#快速开始)
- [API 使用](#api-使用)
- [模块说明](#模块说明)
- [常见问题](#常见问题)
- [面试准备](#面试准备)

---

## 🚀 快速开始

### 1. 环境要求
- Python 3.12.4
- 通义千问 API Key

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 启动 API 服务器

**Windows:**
```cmd
start_api.bat
```

**Linux/Mac:**
```bash
chmod +x run_api.sh
./run_api.sh
```

### 4. 验证启动
访问: http://localhost:8000/docs

### 5. 停止服务器
- 按 Ctrl+C (命令行窗口中)
- 或: taskkill /F /IM python.exe (Windows强制停止)

---

## 🔧 API 使用

### 访问地址
- API 文档: http://localhost:8000/docs
- 根路径: http://localhost:8000/

### 测试示例

#### 方法 1: 浏览器交互式测试
1. 打开 http://localhost:8000/docs
2. 选择 /simple-rag/invoke
3. 点击 "Try it out"
4. 输入: {"input": "去北京出差住宿标准是多少？"}
5. 点击 "Execute"

#### 方法 2: LangServe Playground
- http://localhost:8000/simple-rag/playground/
- http://localhost:8000/advanced-rag/playground/
- http://localhost:8000/react-agent/playground/

#### 方法 3: curl 测试
```bash
curl -X POST "http://localhost:8000/simple-rag/invoke" \
  -H "Content-Type: application/json" \
  -d '{"input": "去北京出差住宿标准是多少？"}'
```

---

## 📦 模块说明

### Module 1: Simple RAG (/simple-rag/)
基础 RAG 检索问答
输入: {"input": "问题"}

### Module 2: Advanced RAG (/advanced-rag/)
高级 RAG - 混合检索 + 重排序
- BM25 + Dense 双路召回
- RRF 融合

### Module 3: ReAct Agent (/react-agent/)
工具调用 Agent
输入: {"input": "任务描述"}

### Module 4: Multi-Agent (/multi-agent/)
多智能体协作（LangGraph）
架构: Supervisor + 3 Workers

### Module 5: Sequential Chain (/sequential-chain/)
顺序执行多步骤
输入: {"input": {"destination": "城市", "days": 天数}}

### Module 6: Parallel Chain (/parallel-chain/)
并行执行多任务
输入: {"input": {"destination": "城市", "days": 天数}}

### Module 7: Memory Chain (/memory-chain/)
带记忆的对话系统
输入: {"input": "你的消息"}

---

## ❓ 常见问题

### Q1: 端口 8000 被占用
```bash
netstat -ano | findstr :8000
taskkill /F /PID <进程ID>
```

### Q2: ModuleNotFoundError
```bash
pip install -r requirements.txt
python verify_environment.py
```

### Q3: 中文显示乱码
这是 Windows GBK 编码问题，不影响功能。

---

## 🎯 面试准备

### 相关文档
1. docs/ARCHITECTURE.md - 架构设计
2. docs/REFACTORING_GUIDE.md - 重构指南
3. docs/INTERVIEW_SCRIPT.md - 面试脚本
4. docs/INTERVIEW_CHEAT_SHEET.md - 速查表
5. docs/SPRING_AI_VS_LANGCHAIN_INTERVIEW_GUIDE.md - 框架对比

### 核心技术点

#### RAG 准确率提升
1. 混合检索（BM25 + Dense）
2. 查询改写
3. 重排序
4. 文档分块优化

#### Agent 工具选择
1. LLM 理解意图
2. 匹配工具描述
3. 构造参数
4. 执行并观察
5. 决定下一步

#### LangGraph 优势
1. 状态持久化
2. 复杂路由
3. 循环控制
4. 可视化

---

## 📁 保留的文档

### 根目录
- README.md - 项目说明
- PROJECT_STATUS.md - 项目状态
- PROJECT_FIX_SUMMARY.md - 修复总结
- QUICK_START.md - 快速开始
- OPERATION_GUIDE.md - 本文件

### docs/ 目录
- API_DOCS.md - API 文档
- ARCHITECTURE.md - 架构设计
- FRAMEWORK_RESEARCH_REPORT.md - 框架研究
- INTERVIEW_CHEAT_SHEET.md - 面试速查
- INTERVIEW_SCRIPT.md - 面试脚本
- REFACTORING_GUIDE.md - 重构指南
- SPRING_AI_ANALYSIS.md - Spring AI 分析
- SPRING_AI_VS_LANGCHAIN.md - 框架对比
- SPRING_AI_VS_LANGCHAIN_INTERVIEW_GUIDE.md - 面试对比指南
- comprehensive-research/ - 综合研究文档

---

## 💡 提示

1. 首次使用建议先访问 /simple-rag/playground/
2. 测试时建议使用 Playground 界面
3. 开发时通过 /docs 查看 API
4. 面试前重点复习 INTERVIEW_SCRIPT.md

---

最后更新: 2026-06-02
