# LangSmith 快速使用指南

## 🎯 已配置完成

你的LangSmith已经配置好了！

**配置信息**：
- ✅ API Key: `your-langsmith-api-key-here`
- ✅ 项目名称: `travel-agent-demo`
- ✅ 自动追踪: 已启用

---

## 🚀 如何使用（3步）

### 步骤1: 运行示例代码（2分钟）

```bash
# 运行LangSmith演示
python examples/langsmith_demo.py
```

这个脚本会：
1. 验证LangSmith配置
2. 运行一个简单的LLM调用
3. 运行一个带记忆的对话
4. **自动追踪到LangSmith**（无需改代码）

---

### 步骤2: 查看Trace（3分钟）

1. **访问LangSmith**
   - 打开: https://smith.langchain.com/
   - 用你的账号登录

2. **找到你的项目**
   - 点击左侧 "Projects"
   - 选择 "travel-agent-demo"

3. **查看调用记录**
   - 看到刚才的2次调用
   - 点击任意一个查看详情

---

### 步骤3: 体验可视化调试（5分钟）

**你会看到什么**：

```
调用链可视化（树状结构）：
├─ ConversationChain (总耗时: 1.5s)
│  ├─ Prompt构建 (0.1s)
│  │  输入: {"question": "北京明天天气怎么样？"}
│  │  输出: "你是一个旅行助手。用户问：北京明天天气怎么样？"
│  ├─ LLM调用 (1.3s)
│  │  输入Token: 50
│  │  输出Token: 30
│  │  成本: $0.0001
│  │  输出: "北京明天预计晴天，气温15-25度..."
│  └─ OutputParser (0.1s)
│     输出: "北京明天预计晴天，气温15-25度..."
```

**可以做什么**：
- ✅ 点击任意节点，查看输入输出
- ✅ 看到每个步骤的耗时
- ✅ 看到Token使用量和成本
- ✅ 对比不同调用的差异

---

## 💡 实战：用LangSmith调试你的项目

### 场景1: 调试记忆系统

```bash
# 运行记忆系统测试（会自动追踪）
python tests/test_memory_system.py
```

**在LangSmith中看到**：
- 每次`process_user_message`的调用
- 实体提取的过程
- 记忆更新的逻辑

---

### 场景2: 调试RAG检索

如果你有RAG相关的代码，运行后在LangSmith中可以看到：
- 检索到的文档内容
- Prompt构建过程
- LLM的输入输出
- 整个链路的耗时分布

---

## 🎤 面试中如何展示

### 话术1: 主动提起

> "我的项目集成了LangSmith。比如运行`python examples/langsmith_demo.py`，就能在LangSmith中看到完整的调用链、每个步骤的输入输出、耗时统计。这让调试效率提升了10倍。"

### 话术2: 展示实战

> "我用LangSmith调试记忆系统。运行测试后，在LangSmith中看到每次实体提取的过程，发现某个正则表达式匹配有问题，5分钟就定位到了。"

### 话术3: 对比Spring AI

> "Spring AI只能靠日志，看不到调用关系。LangSmith能可视化整个链路，点击任意节点就能看到输入输出。这是生产环境必备的功能。"

---

## 📊 LangSmith的核心功能

### 1. 调用链可视化
- 树状结构展示整个调用流程
- 点击节点查看详细信息
- 对比不同调用的差异

### 2. 性能分析
- 自动统计每个组件的耗时
- 生成性能火焰图
- 快速定位瓶颈

### 3. 成本统计
- 自动计算Token使用量
- 自动计算API成本
- 生成成本报表

### 4. 输入输出追踪
- 记录每个步骤的输入输出
- 支持搜索和过滤
- 方便复现问题

---

## 🔧 高级用法

### 自定义项目名称

```python
import os
os.environ["LANGCHAIN_PROJECT"] = "my-custom-project"
```

### 添加元数据

```python
from langsmith import Client

client = Client()
client.create_run(
    name="custom-run",
    inputs={"query": "test"},
    run_type="chain",
    extra={"user_id": "user_123"}  # 自定义元数据
)
```

### 过滤和搜索

在LangSmith网页中：
- 按状态过滤（成功/失败）
- 按耗时过滤（>1s）
- 按元数据搜索（user_id = "user_123"）

---

## ✅ 验证配置

运行这个命令验证LangSmith是否正常工作：

```bash
python examples/langsmith_demo.py
```

如果看到：
```
✓ LangSmith已启用
✓ API Key: your-langsmith-api-key-here
✓ 项目名称: travel-agent-demo
✓ 调用成功！
```

说明配置成功！

---

## 🎯 下一步

1. **立即运行示例**
   ```bash
   python examples/langsmith_demo.py
   ```

2. **访问LangSmith**
   - https://smith.langchain.com/
   - 查看刚才的Trace

3. **体验调试功能**
   - 点击节点查看输入输出
   - 查看性能分析
   - 查看成本统计

4. **准备面试话术**
   - "我用LangSmith调试了项目"
   - "5分钟定位问题，效率提升10倍"
   - "这是Spring AI完全没有的功能"

---

## 💪 面试加分项

**主动展示**：
> "我的项目集成了LangSmith。如果需要，我可以现场演示如何用LangSmith调试和优化AI应用。"

**讲具体案例**：
> "我用LangSmith调试记忆系统，发现实体提取的正则表达式有问题，5分钟就定位到了。这在Spring AI中需要打断点调试半天。"

**展示理解深度**：
> "LangSmith的可观测性是LangChain最大的优势。没有可观测性，AI应用就是黑盒。这是生产环境必备的功能。"

---

祝你面试成功！🚀
