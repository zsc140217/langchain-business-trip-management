# Dify 快速开始指南（针对你的配置）

> 根据你的实际配置定制：Windows 11 + Docker Desktop + DeepSeek API + 7897 代理

---

## 🎯 你的配置清单

- ✅ Windows 11 系统
- ✅ Docker Desktop 已安装
- ✅ 16GB RAM
- ✅ E盘 198GB 可用空间
- ✅ 科学上网代理：127.0.0.1:7897
- ✅ DeepSeek API Key

---

## 📝 开始前的准备（5分钟）

### 1. 启动 Docker Desktop

```bash
# 打开"开始菜单"，搜索"Docker Desktop"，点击启动
# 等待 Docker Desktop 启动完成（托盘图标变为绿色）
```

### 2. 配置 Docker 代理

```bash
操作步骤：
1. 打开 Docker Desktop
2. 点击右上角设置图标（齿轮）→ Settings
3. 左侧选择 Resources → Proxies
4. 启用 "Manual proxy configuration"
5. 填入：
   HTTP Proxy: http://127.0.0.1:7897
   HTTPS Proxy: http://127.0.0.1:7897
6. 点击 "Apply & Restart"
7. 等待重启完成（约30秒）
```

### 3. 验证 Docker 状态

打开 Git Bash 或 PowerShell：

```bash
# 检查 Docker 版本
docker --version

# 检查 Docker 是否运行
docker ps

# 如果上面两条命令都正常，说明 Docker 已就绪
```

---

## 🚀 第一步：安装 Dify（20-30分钟）

### 1. 下载 Dify

```bash
# 切换到 E 盘（空间充足）
cd /e

# 创建工作目录
mkdir dify-workspace
cd dify-workspace

# 克隆 Dify 仓库（需要几分钟）
git clone https://github.com/langgenius/dify.git

# 进入 docker 目录
cd dify/docker
```

### 2. 配置环境变量

```bash
# 复制配置模板
cp .env.example .env

# 用记事本打开配置文件
notepad .env
```

在 `.env` 文件中**修改以下内容**：

```bash
# 找到这一行（大约在第10行左右）
SECRET_KEY=

# 改为（随便输入一个长字符串）：
SECRET_KEY=dify-business-travel-2026-secret-key

# 滚动到文件末尾，添加以下内容：
# DeepSeek API 配置
DEEPSEEK_API_KEY=你的DeepSeek API Key
DEEPSEEK_API_BASE=https://api.deepseek.com/v1
```

保存并关闭文件（Ctrl+S，然后关闭）

### 3. 启动 Dify

```bash
# 启动所有服务（首次会下载镜像，需要5-10分钟）
docker-compose up -d

# 查看启动日志（可选）
docker-compose logs -f

# 看到 "Application startup complete" 表示成功
# 按 Ctrl+C 退出日志查看
```

### 4. 检查服务状态

```bash
docker-compose ps

# 应该看到以下服务都是 "Up" 状态：
# - nginx
# - api
# - worker
# - web
# - db
# - redis
# - weaviate
```

### 5. 访问 Dify

```bash
# 打开浏览器，访问：
http://localhost

# 如果 80 端口被占用，改为：
http://localhost:8080

# 第一次访问会进入初始化向导：
# 1. 设置管理员账号（邮箱格式，例如：admin@example.com）
# 2. 设置密码（至少8位）
# 3. 选择语言（中文）
# 4. 点击"完成设置"
```

---

## 🎨 第二步：配置 DeepSeek 模型（10分钟）

### 1. 添加模型供应商

```bash
1. 登录 Dify
2. 点击右上角头像 → "设置"
3. 左侧菜单选择 "模型供应商"
4. 点击 "添加模型供应商"
5. 选择 "自定义模型"（Custom Model）
6. 填写：
   - 供应商名称：DeepSeek
   - 模型类型：Chat
   - API Base URL：https://api.deepseek.com/v1
   - API Key：sk-xxxxx（你的 DeepSeek API Key）
7. 点击 "验证" 测试连接
8. 验证成功后点击 "保存"
```

### 2. 添加具体模型

```bash
1. 在 "自定义模型" 下点击 "添加模型"
2. 填写：
   - 模型名称：deepseek-chat
   - 模型标识：deepseek-chat
   - 上下文长度：32000
   - 最大输出：4000
   - 支持 Function Call：是
3. 点击 "保存"
```

### 3. 配置 Embedding 模型（用于知识库）

```bash
1. 返回 "模型供应商" 页面
2. 找到 "Jina AI"（免费，无需 API Key）
3. 点击启用
4. 选择 "jina-embeddings-v2-base-zh"
5. 保存

注：Jina Embeddings 免费且支持中文，适合快速上手
```

---

## 📚 第三步：创建知识库（15分钟）

### 1. 创建知识库

```bash
1. 侧边栏点击 "知识库"
2. 点击 "创建知识库"
3. 填写：
   - 名称：差旅政策库
   - 描述：公司差旅政策、报销规则、城市分级标准
4. 点击 "创建"
```

### 2. 上传政策文档

```bash
1. 进入 "差旅政策库"
2. 点击 "添加文件"
3. 选择你的政策文档（在 data/travel_policies/ 目录下）
4. 批量上传所有 .md 或 .txt 文件
5. 等待文档处理完成（Embedding 向量化）
6. 检查 "段落数" 确认已处理
```

### 3. 配置知识库设置

```bash
1. 点击知识库右上角 "设置"
2. 配置：
   - Embedding 模型：jina-embeddings-v2-base-zh
   - 分块策略：智能分块
   - 最大分块大小：800 tokens
   - 重叠大小：100 tokens
   - 检索模式：混合检索
   - TopK：5
   - Score 阈值：0.7
3. 保存设置
```

---

## 💬 第四步：创建 Chatflow 应用（20分钟）

### 1. 创建应用

```bash
1. 回到首页，点击 "创建应用"
2. 选择 "从空白创建"
3. 应用类型：Chatflow（对话流）
4. 应用名称：差旅审批助手
5. 选择图标
6. 点击 "创建"
```

### 2. 配置 Chatflow

```bash
1. 点击 "编辑" 进入工作区
2. 默认已有 "开始" 节点
3. 添加 "LLM" 节点：
   - 从左侧拖拽 "LLM" 到画布
   - 连接 "开始" → "LLM"
   - 配置：
     * 名称：意图识别
     * 模型：deepseek-chat
     * 提示词：
     
你是差旅审批助手。分析用户输入，识别意图和提取关键信息。

用户输入：{{#start.user_input#}}

请提取以下信息（如果用户提供了）：
- 目的地城市
- 出差时间（开始和结束日期）
- 出差目的
- 预计费用

如果信息不完整，询问缺少的信息。
如果信息完整，返回 JSON 格式。

4. 添加 "知识库检索" 节点：
   - 拖拽 "知识库" 节点
   - 连接 "LLM" → "知识库"
   - 选择知识库：差旅政策库
   - 查询变量：{{#意图识别.output#}}

5. 添加 "回复" 节点：
   - 拖拽 "回复" 节点
   - 连接 "知识库" → "回复"
   - 配置回复内容
```

### 3. 测试 Chatflow

```bash
1. 点击右上角 "运行"
2. 在测试面板输入：
   "我要去上海出差，下周一到周三，拜访客户"
3. 检查输出是否正确
4. 调整提示词直到满意
```

---

## ✅ 完成检查

- [ ] Docker Desktop 正常运行
- [ ] Dify 成功启动（可访问 http://localhost）
- [ ] DeepSeek 模型配置成功
- [ ] Jina Embeddings 配置成功
- [ ] 知识库创建并上传文档
- [ ] Chatflow 创建并测试通过

---

## 🎓 下一步

完成上述步骤后，你可以继续：

1. **创建 Workflow**（详见 `T4_DIFY_STEP_BY_STEP_GUIDE.md` 的 Step 1.4）
   - 添加并行 Agent
   - 配置审批逻辑
   - 集成 HITL 人工审批

2. **性能优化**（详见 Step 2.3）
   - 验证并行执行
   - 配置缓存
   - 优化 LLM 调用

3. **准备面试材料**（详见 Day 3）
   - 对比 LangChain 版本
   - 撰写技术文档
   - 准备演示话术

---

## ❓ 常见问题

### Q1: Docker 拉取镜像失败？
**A:** 检查代理配置是否正确（127.0.0.1:7897），重启 Docker Desktop

### Q2: 端口 80 被占用？
**A:** 修改 `docker-compose.yml`，将 nginx 的端口改为 8080：
```yaml
nginx:
  ports:
    - "8080:80"
```

### Q3: DeepSeek API 调用失败？
**A:** 检查 API Key 是否正确，确认账户余额充足

### Q4: 知识库检索不准确？
**A:** 增加训练数据，调整分块大小，使用混合检索

### Q5: 多模态功能不能用？
**A:** DeepSeek 暂不支持 Vision，需要 GPT-4o 或 Claude Sonnet 4

---

## 🛠️ 常用命令

```bash
# 查看 Dify 服务状态
cd /e/dify-workspace/dify/docker
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose stop

# 重启服务
docker-compose restart

# 完全停止并删除（谨慎使用）
docker-compose down -v
```

---

## 📞 需要帮助？

如果遇到问题：
1. 查看 Docker 日志：`docker-compose logs -f`
2. 检查代理配置
3. 确认 API Key 正确
4. 重启 Docker Desktop

---

**预计完成时间：1-1.5 小时**

祝你顺利完成！🚀
