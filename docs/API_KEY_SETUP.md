# API密钥配置指南

## 需要配置的密钥

### 1. DASHSCOPE_API_KEY（必需）⭐

**用途**：通义千问大模型API密钥

**使用场景**：
- LLM对话生成
- 文本Embedding（向量化）
- RAG检索
- 复杂度评估
- 任务分解

**获取方式**：
1. 访问阿里云百炼平台：https://dashscope.aliyun.com/
2. 注册/登录账号
3. 进入控制台 → API-KEY管理
4. 创建新的API-KEY
5. 复制密钥

**免费额度**：
- 新用户有免费额度
- 具体额度查看官网

---

### 2. QWEATHER_API_KEY（可选）

**用途**：和风天气API密钥

**使用场景**：
- 天气查询工具
- 仅在使用天气功能时需要

**获取方式**：
1. 访问和风天气开发平台：https://dev.qweather.com/
2. 注册/登录账号
3. 创建应用
4. 获取API Key

**免费额度**：
- 免费版：1000次/天
- 足够测试使用

---

## 配置步骤

### 方法1：创建.env文件（推荐）

```bash
# 1. 复制示例文件
cp .env.example .env

# 2. 编辑.env文件
notepad .env  # Windows
# 或
vim .env      # Linux/Mac
```

**编辑内容**：
```env
# 通义千问API Key（必需）
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 和风天气API Key（可选）
QWEATHER_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 服务配置
HOST=0.0.0.0
PORT=8000
```

### 方法2：环境变量（临时）

**Windows (PowerShell)**：
```powershell
$env:DASHSCOPE_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
$env:QWEATHER_API_KEY="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

**Windows (CMD)**：
```cmd
set DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
set QWEATHER_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Linux/Mac**：
```bash
export DASHSCOPE_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export QWEATHER_API_KEY="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

---

## 验证配置

### 快速验证脚本

创建 `verify_config.py`：

```python
import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("API密钥配置验证")
print("=" * 60)

# 检查DASHSCOPE_API_KEY
dashscope_key = os.getenv("DASHSCOPE_API_KEY")
if dashscope_key:
    if dashscope_key == "your_api_key_here":
        print("❌ DASHSCOPE_API_KEY: 未配置（使用默认值）")
    else:
        print(f"✅ DASHSCOPE_API_KEY: 已配置 ({dashscope_key[:10]}...)")
else:
    print("❌ DASHSCOPE_API_KEY: 未找到")

# 检查QWEATHER_API_KEY
qweather_key = os.getenv("QWEATHER_API_KEY")
if qweather_key:
    if qweather_key == "your_weather_api_key_here":
        print("⚠️  QWEATHER_API_KEY: 未配置（可选）")
    else:
        print(f"✅ QWEATHER_API_KEY: 已配置 ({qweather_key[:10]}...)")
else:
    print("⚠️  QWEATHER_API_KEY: 未找到（可选）")

print("=" * 60)

# 测试LLM连接
if dashscope_key and dashscope_key != "your_api_key_here":
    print("\n测试LLM连接...")
    try:
        from src.models.llm import get_llm
        llm = get_llm()
        response = llm.invoke("你好")
        print(f"✅ LLM连接成功: {response[:50]}...")
    except Exception as e:
        print(f"❌ LLM连接失败: {e}")
else:
    print("\n⚠️  跳过LLM连接测试（未配置密钥）")
```

运行验证：
```bash
python verify_config.py
```

---

## 哪些功能需要密钥？

### 需要DASHSCOPE_API_KEY的功能

| 功能 | 文件 | 是否必需 |
|------|------|---------|
| LLM对话 | `src/models/llm.py` | ✅ 必需 |
| 文本Embedding | `src/rag/retriever.py` | ✅ 必需 |
| RAG问答 | `src/rag/chain.py` | ✅ 必需 |
| 复杂度评估 | `src/agents/complexity_assessor.py` | ✅ 必需 |
| 任务分解 | `src/agents/task_decomposer.py` | ✅ 必需 |
| 混合检索 | `src/rag/hybrid_retriever.py` | ✅ 必需 |

### 需要QWEATHER_API_KEY的功能

| 功能 | 文件 | 是否必需 |
|------|------|---------|
| 天气查询 | `src/tools/weather.py` | ⚠️ 可选 |

### 不需要密钥的功能

| 功能 | 文件 | 说明 |
|------|------|------|
| 三层记忆系统 | `src/memory/*` | ✅ 无需密钥 |
| 文档加载 | `src/rag/loader.py` | ✅ 无需密钥 |
| 工作流编排 | `src/agents/workflow_orchestrator.py` | ⚠️ 依赖其他模块 |

---

## 测试记忆系统（无需密钥）

记忆系统是完全独立的，不需要任何API密钥：

```bash
# 测试记忆系统
python tests/test_memory_system.py

# 快速验证
python tests/quick_verify_memory.py

# 运行示例
python examples/memory_usage_example.py
```

这些测试都可以在**没有配置API密钥**的情况下运行！

---

## 常见问题

### Q1：没有API密钥可以测试吗？

**A：可以部分测试**

✅ 可以测试：
- 三层记忆系统（完全独立）
- 文档加载
- 数据结构和逻辑

❌ 无法测试：
- LLM对话
- RAG检索
- 复杂度评估
- 任务分解

### Q2：API密钥收费吗？

**A：有免费额度**

- 通义千问：新用户有免费额度
- 和风天气：免费版1000次/天
- 足够开发和测试使用

### Q3：密钥泄露怎么办？

**A：立即重置**

1. 登录对应平台
2. 删除泄露的密钥
3. 创建新密钥
4. 更新.env文件
5. 确保.env在.gitignore中

### Q4：.env文件会被提交到Git吗？

**A：不会**

`.gitignore` 已经包含了 `.env`，不会被提交到Git。

---

## 安全建议

1. ✅ 使用.env文件存储密钥
2. ✅ 确保.env在.gitignore中
3. ✅ 不要在代码中硬编码密钥
4. ✅ 不要在公开场合分享密钥
5. ✅ 定期轮换密钥
6. ✅ 使用不同环境的不同密钥

---

## 快速开始（无密钥）

如果你暂时没有API密钥，可以先测试记忆系统：

```bash
# 1. 测试记忆系统（无需密钥）
python tests/test_memory_system.py

# 2. 运行示例（无需密钥）
python examples/memory_usage_example.py

# 3. 查看文档
cat docs/MEMORY_SYSTEM.md
```

等配置好密钥后，再测试完整功能：

```bash
# 配置密钥后
cp .env.example .env
# 编辑.env，填入密钥

# 测试完整功能
python tests/test_all_features.py
python src/main.py
```

---

## 总结

**必需配置**：
- ✅ DASHSCOPE_API_KEY（通义千问）

**可选配置**：
- ⚠️ QWEATHER_API_KEY（和风天气）

**无需密钥即可测试**：
- ✅ 三层记忆系统
- ✅ 文档加载
- ✅ 数据结构

**配置方法**：
1. 复制 `.env.example` 为 `.env`
2. 填入API密钥
3. 运行 `python verify_config.py` 验证
