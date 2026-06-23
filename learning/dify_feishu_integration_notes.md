# Dify + 飞书集成实战笔记

> 时间：2026-06-23  
> 目标：用Dify快速验证飞书接入，学习消息队列、多轮对话机制

---

## 已有资源

**飞书应用凭证**：
- App ID: `cli_aa8759bff078dcbd`
- App Secret: `ralUiiVIL2ryfvDxeR9Bhd67DEiGPyGC`

**Dify环境**：
- 访问地址：http://localhost
- 版本：v1.14.2
- 状态：✅ 12个容器全部运行

---

## Step 1：Dify发布到飞书（10分钟）

### 1.1 打开Dify应用

浏览器访问：http://localhost

### 1.2 配置飞书渠道

1. 点击应用右上角「发布」按钮
2. 选择「频道」→「飞书」
3. 填入凭证：
   - **App ID**: `cli_aa8759bff078dcbd`
   - **App Secret**: `ralUiiVIL2ryfvDxeR9Bhd67DEiGPyGC`

### 1.3 配置飞书开放平台

⚠️ **本地开发需要公网地址**

```bash
# 使用ngrok暴露本地端口
ngrok http 80
# 复制生成的公网URL，如：https://abc123.ngrok.io
```

飞书配置：
1. 访问：https://open.feishu.cn/app/cli_aa8759bff078dcbd
2. 进入「事件订阅」
3. 配置请求地址：`https://abc123.ngrok.io/api/external/feishu/webhook/<app_id>`
4. 添加订阅事件：`im.message.receive_v1`

---

## 测试记录

### 测试用例1：多轮对话

- [ ] 完成测试
- [ ] 会话ID观察：
- [ ] 上下文保持：

### 测试用例2：中断恢复

- [ ] 完成测试
- [ ] 超时时间：
- [ ] 状态保留：

---

## 学习要点总结

### Dify会话管理机制
- 会话ID生成规则：[待填写]
- 上下文存储方式：[待填写]
- 会话过期时间：[待填写]

### 迁移到LangChain的关键点
1. Redis消息队列
2. 飞书API调用
3. 异步处理模式
