# 生产环境就绪性待办清单

**文档版本**: v1.0  
**创建日期**: 2026-07-14  
**状态**: 待处理  

---

## 📊 当前架构完成度总览

| 模块 | 完成度 | 状态 |
|------|--------|------|
| Phase 1-4 架构实现 | 100% | ✅ 代码完整 |
| 工具系统（真实数据） | 30% | ⚠️ 大部分是Mock |
| 用户认证系统 | 0% | ❌ 完全缺失 |
| 会话管理系统 | 0% | ❌ 完全缺失 |
| 前端集成API | 40% | ⚠️ 缺少关键接口 |
| 数据持久化 | 30% | ⚠️ 部分完成 |
| 生产环境部署 | 0% | ❌ 无部署配置 |

---

## 🚨 核心问题识别

### ❌ 致命问题（P0 - 阻碍基本功能）
1. **没有用户认证系统** - 无法区分不同用户，user_id 都是硬编码
2. **工具数据是Mock** - 酒店、航班查询返回假数据（只有天气可能有真实API）
3. **没有会话管理** - conversation_id 随便传，对话无法持久化恢复

### ⚠️ 严重问题（P1 - 影响可用性）
4. **记忆系统缺少用户管理** - MemoryService 依赖 user_id，但无真实用户
5. **前端API不完整** - 缺少注册、登录、会话列表等接口
6. **数据库设计不完整** - 只有审批表，缺少用户、会话、对话历史表

### 💡 改进问题（P2 - 影响体验）
7. **评估脚本不准确** - 基于Mock数据评估召回率
8. **错误处理不统一** - 缺少标准化错误码和响应格式
9. **日志系统不完善** - 缺少结构化日志和链路追踪

---

## P0 - 核心功能缺失（必须完成）

### 1. 用户认证系统 ❌

**当前问题**：
- user_id 是硬编码（"default_user", "test_user_001"）
- 没有注册、登录、Token验证
- 所有API接口无权限控制

**需要创建的文件**：
```
src/models/user.py              # 用户数据模型（User, UserCreate, UserLogin, Token）
src/services/user_service.py   # 用户服务层（注册、登录、验证Token）
src/database/user_repository.py # 用户数据访问层
src/auth/jwt_handler.py         # JWT Token生成和验证
src/auth/password_hasher.py     # 密码加密（bcrypt）
src/middleware/auth_middleware.py # FastAPI认证中间件
scripts/init_user_tables.sql    # 用户表和会话表创建脚本
tests/services/test_user_service.py # 用户服务单元测试
```

**需要新增的API接口**：
```python
POST /api/auth/register        # 用户注册
POST /api/auth/login           # 用户登录（返回JWT Token）
POST /api/auth/logout          # 用户登出
GET  /api/auth/me              # 获取当前用户信息
PUT  /api/auth/me              # 更新用户信息
POST /api/auth/refresh         # 刷新Token
```

**数据库表设计**：
```sql
users (用户表)
  - user_id (主键)
  - username, email, password_hash
  - full_name, department, position
  - is_active, is_admin
  - created_at, updated_at

user_sessions (会话表)
  - session_id (主键)
  - user_id (外键)
  - token_hash
  - expires_at
  - created_at
```

---

### 2. 会话管理系统 ❌

**当前问题**：
- conversation_id 随便传，无持久化
- 对话历史保存在内存，重启丢失
- 无法查看历史对话列表

**需要创建的文件**：
```
src/models/conversation.py          # 会话模型（Conversation, Message）
src/services/conversation_service.py # 会话服务层
src/database/conversation_repository.py # 会话数据访问层
scripts/init_conversation_tables.sql # 会话表创建脚本
tests/services/test_conversation_service.py # 会话服务测试
```

**需要新增的API接口**：
```python
GET  /api/conversations              # 获取用户的所有会话列表
POST /api/conversations              # 创建新会话
GET  /api/conversations/{id}         # 获取会话详情（包含所有消息）
DELETE /api/conversations/{id}       # 删除会话
GET  /api/conversations/{id}/messages # 获取会话的消息列表（分页）
POST /api/conversations/{id}/messages # 发送消息到会话
```

**数据库表设计**：
```sql
conversations (会话表)
  - conversation_id (主键)
  - user_id (外键)
  - title (会话标题，自动生成)
  - created_at, updated_at
  - last_message_at

messages (消息表)
  - message_id (主键)
  - conversation_id (外键)
  - role (user/assistant/system)
  - content (消息内容)
  - metadata (JSON，存储工具调用等元信息)
  - created_at
```

---

### 3. 记忆系统用户关联 ⚠️

**当前问题**：
- MemoryService 已实现，但依赖真实的 user_id 和 conversation_id
- LongTermMemory 存在文件系统，需要迁移到数据库

**需要修改的文件**：
```
src/memory/long_term_memory.py      # 修改：从文件系统迁移到数据库
src/memory/memory_service.py        # 修改：添加用户验证
scripts/init_memory_tables.sql      # 新建：用户画像表
```

**数据库表设计**：
```sql
user_profiles (用户画像表)
  - profile_id (主键)
  - user_id (外键)
  - conversation_count
  - top_cities (JSON)
  - top_customers (JSON)
  - preferences (JSON)
  - updated_at
```

---

## P1 - Mock数据替换（影响可用性）

### 4. 替换酒店Mock数据 ❌

**当前状态**：
- `src/mcp/trip_tools_server.py` 中硬编码了 MOCK_HOTELS
- 需要接入真实的酒店API

**需要集成的API**：
- 携程API / 去哪儿API / 飞猪API
- 或者使用公开的酒店数据库

**需要修改的文件**：
```
src/mcp/trip_tools_server.py        # 修改：替换Mock数据为真实API调用
src/clients/hotel_api_client.py     # 新建：酒店API客户端
.env                                 # 新增：酒店API密钥配置
```

---

### 5. 替换航班Mock数据 ❌

**当前状态**：
- `src/mcp/trip_tools_server.py` 中硬编码了 MOCK_FLIGHTS
- 需要接入真实的航班API

**需要集成的API**：
- 航旅纵横API / 飞常准API
- 或者使用第三方航班数据服务

**需要修改的文件**：
```
src/mcp/trip_tools_server.py        # 修改：替换Mock数据为真实API调用
src/clients/flight_api_client.py    # 新建：航班API客户端
.env                                 # 新增：航班API密钥配置
```

---

### 6. 验证天气API集成 ⚠️

**当前状态**：
- 可能已有QWeather API配置，需要验证
- `src/tools/qweather_client.py` 和 `src/mcp/trip_tools_server.py` 需要检查

**需要验证**：
- QWEATHER_API_KEY 是否配置
- API调用是否正常
- 错误处理是否完善

---

## P2 - 前端集成准备（影响开发体验）

### 7. 统一错误响应格式 ⚠️

**当前问题**：
- 不同接口返回的错误格式不一致
- 缺少标准化的错误码

**需要创建的文件**：
```
src/models/response.py              # 统一响应模型（ApiResponse, ErrorResponse）
src/exceptions/api_exceptions.py    # 自定义异常类
src/middleware/error_handler.py     # 全局异常处理中间件
docs/API_ERROR_CODES.md             # 错误码文档
```

**标准响应格式**：
```python
# 成功响应
{
  "success": true,
  "data": {...},
  "message": "操作成功"
}

# 错误响应
{
  "success": false,
  "error": {
    "code": "AUTH_001",
    "message": "Token已过期",
    "details": null
  }
}
```

---

### 8. 补充前端需要的管理接口 ❌

**需要新增的API接口**：
```python
# 用户管理
GET  /api/admin/users               # 获取用户列表（管理员）
PUT  /api/admin/users/{id}          # 更新用户信息（管理员）
DELETE /api/admin/users/{id}        # 删除用户（管理员）

# 统计和分析
GET  /api/stats/user                # 获取当前用户的使用统计
GET  /api/stats/system              # 获取系统统计（管理员）

# 审批管理
GET  /api/approvals                 # 获取用户的所有审批记录
GET  /api/approvals/pending         # 获取待审批列表（审批人）
PUT  /api/approvals/{id}            # 更新审批状态（审批人）

# 记忆管理
GET  /api/memory/profile            # 获取用户画像
DELETE /api/memory/conversations/{id} # 清除会话记忆
```

---

### 9. CORS和请求限流配置 ⚠️

**当前状态**：
- `unified_api.py` 已有基础CORS配置（allow_origins=["*"]）
- 缺少请求限流（Rate Limiting）

**需要添加**：
```
src/middleware/rate_limiter.py      # 请求限流中间件
src/middleware/cors_config.py       # 细粒度CORS配置
```

---

## P3 - 生产环境优化（长期改进）

### 10. 数据库连接池和ORM ⚠️

**当前问题**：
- 当前使用原始SQL，缺少连接池
- 建议使用SQLAlchemy ORM

**需要创建的文件**：
```
src/database/connection.py         # 数据库连接池配置
src/database/models.py              # SQLAlchemy ORM模型
src/database/base.py                # Base模型和会话管理
requirements.txt                    # 新增：sqlalchemy, pymysql/psycopg2
```

---

### 11. 配置管理和环境隔离 ⚠️

**需要完善的配置**：
```
config/development.yaml             # 开发环境配置
config/staging.yaml                 # 预发布环境配置
config/production.yaml              # 生产环境配置
src/config/settings.py              # 配置加载器（支持多环境）
```

---

### 12. Docker化部署 ❌

**需要创建的文件**：
```
Dockerfile                          # 应用镜像
docker-compose.yml                  # 本地开发环境编排
docker-compose.prod.yml             # 生产环境编排
.dockerignore                       # Docker忽略文件
scripts/docker-entrypoint.sh        # 容器启动脚本
```

---

### 13. CI/CD流程 ❌

**需要创建的文件**：
```
.github/workflows/ci.yml            # GitHub Actions CI配置
.github/workflows/deploy.yml        # 自动部署配置
scripts/run_tests.sh                # 测试运行脚本
scripts/deploy.sh                   # 部署脚本
```

---

### 14. 日志和监控增强 ⚠️

**当前问题**：
- 日志格式不统一
- 缺少集中式日志收集

**需要添加**：
```
src/logging/formatter.py            # 结构化日志格式化器
src/logging/handlers.py             # 自定义日志处理器（ELK集成）
config/logging.yaml                 # 日志配置文件
```

---

### 15. 性能优化和缓存 ⚠️

**需要添加**：
- Redis缓存（工具调用结果、用户会话）
- 向量检索结果缓存
- API响应缓存

**需要创建的文件**：
```
src/cache/redis_client.py           # Redis客户端封装
src/cache/cache_decorators.py       # 缓存装饰器
requirements.txt                     # 新增：redis, hiredis
```

---

## 📝 实施优先级建议

### 第一阶段（1-2周）- 基本可用
- ✅ P0-1: 用户认证系统
- ✅ P0-2: 会话管理系统
- ✅ P0-3: 记忆系统用户关联
- ✅ P2-7: 统一错误响应格式

### 第二阶段（2-3周）- 功能完善
- ✅ P1-4: 替换酒店Mock数据
- ✅ P1-5: 替换航班Mock数据
- ✅ P2-8: 补充前端管理接口
- ✅ P3-10: 数据库连接池和ORM

### 第三阶段（2-3周）- 生产就绪
- ✅ P3-11: 配置管理和环境隔离
- ✅ P3-12: Docker化部署
- ✅ P3-13: CI/CD流程
- ✅ P3-14: 日志和监控增强
- ✅ P3-15: 性能优化和缓存

---

## 🎯 关键指标

完成所有任务后的预期指标：

| 指标 | 当前 | 目标 |
|------|------|------|
| 用户认证 | 0% | 100% |
| 工具真实数据率 | 30% | 100% |
| API完整度 | 40% | 100% |
| 数据持久化 | 30% | 100% |
| 生产部署就绪 | 0% | 100% |
| 测试覆盖率 | ~60% | ≥80% |

---

## 📚 参考文档

- [ARCHITECTURE_V2_PLAN.md](./ARCHITECTURE_V2_PLAN.md) - 当前架构实现
- [PRODUCTION_TASK_LIST.md](./PRODUCTION_TASK_LIST.md) - 原有任务清单
- [API_DOCS.md](./API_DOCS.md) - API文档

---

**文档结束**
