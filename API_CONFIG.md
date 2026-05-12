# API密钥配置快速指南

## 需要配置的密钥

### 1. DASHSCOPE_API_KEY (必需)

**用途**: 通义千问大模型API
**获取**: https://dashscope.aliyun.com/
**使用场景**:
- LLM对话生成
- 文本Embedding
- RAG检索
- 复杂度评估
- 任务分解

### 2. QWEATHER_API_KEY (可选)

**用途**: 和风天气API
**获取**: https://dev.qweather.com/
**使用场景**:
- 天气查询工具

---

## 配置步骤

### 步骤1: 创建.env文件

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

### 步骤2: 编辑.env文件

```env
# 通义千问API Key (必需)
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 和风天气API Key (可选)
QWEATHER_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 服务配置
HOST=0.0.0.0
PORT=8000
```

### 步骤3: 验证配置

```bash
python verify_config.py
```

---

## 哪些功能需要密钥?

### 需要DASHSCOPE_API_KEY

- [x] LLM对话
- [x] RAG问答
- [x] 复杂度评估
- [x] 任务分解
- [x] 混合检索

### 需要QWEATHER_API_KEY

- [ ] 天气查询 (可选)

### 无需密钥

- [x] 三层记忆系统 (完全独立)
- [x] 文档加载
- [x] 数据结构测试

---

## 无密钥测试

记忆系统可以在没有API密钥的情况下完整测试:

```bash
# 测试记忆系统
python tests/test_memory_system.py

# 快速验证
python tests/quick_verify_memory.py

# 运行示例
python examples/memory_usage_example.py
```

---

## 获取API密钥

### 通义千问 (DASHSCOPE_API_KEY)

1. 访问: https://dashscope.aliyun.com/
2. 注册/登录阿里云账号
3. 进入控制台 -> API-KEY管理
4. 创建新的API-KEY
5. 复制密钥到.env文件

### 和风天气 (QWEATHER_API_KEY)

1. 访问: https://dev.qweather.com/
2. 注册/登录账号
3. 创建应用
4. 获取API Key
5. 复制密钥到.env文件

---

## 常见问题

**Q: 没有API密钥可以测试吗?**
A: 可以! 三层记忆系统完全独立,无需任何API密钥

**Q: API密钥收费吗?**
A: 通义千问和和风天气都有免费额度,足够测试使用

**Q: .env文件会被提交到Git吗?**
A: 不会, .gitignore已经包含了.env

---

## 安全提示

- [x] 使用.env文件存储密钥
- [x] 确保.env在.gitignore中
- [x] 不要在代码中硬编码密钥
- [x] 不要在公开场合分享密钥

---

## 详细文档

查看完整配置指南: docs/API_KEY_SETUP.md
