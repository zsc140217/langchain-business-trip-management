# API文档

## 基础信息

- **Base URL**: `http://localhost:8000`
- **Content-Type**: `application/json`
- **API文档**: `http://localhost:8000/docs` (Swagger UI)

---

## 接口列表

### 1. 健康检查

检查服务是否正常运行。

**请求**

```http
GET /health
```

**响应**

```json
{
  "status": "ok",
  "rag_initialized": true,
  "llm_initialized": true
}
```

---

### 2. 同步对话

发送消息并等待完整回答。适合简单查询。

**请求**

```http
POST /api/chat/sync
Content-Type: application/json

{
  "message": "去上海出差住宿标准是多少？",
  "chat_id": "user123"
}
```

**参数说明**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| message | string | 是 | 用户消息 |
| chat_id | string | 否 | 会话ID，默认"default" |

**响应**

```json
{
  "answer": "根据企业差旅规章，上海属于一线城市，住宿标准为标准间不超过500元/晚。",
  "sources": [
    "第一章 住宿标准\n1. 一线城市（北京、上海、广州、深圳）：标准间不超过500元/晚...",
    "..."
  ]
}
```

**cURL示例**

```bash
curl -X POST "http://localhost:8000/api/chat/sync" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "去上海出差住宿标准是多少？",
    "chat_id": "user123"
  }'
```

---

### 3. 流式对话

实时返回生成内容，提升用户体验。

**请求**

```http
POST /api/chat/stream
Content-Type: application/json

{
  "message": "帮我规划去杭州的行程",
  "chat_id": "user123"
}
```

**响应格式**

SSE (Server-Sent Events) 格式：

```
data: {"content": "根据"}

data: {"content": "企业"}

data: {"content": "差旅"}

data: {"content": "规章"}

...

data: {"done": true}
```

**JavaScript示例**

```javascript
const eventSource = new EventSource('/api/chat/stream');

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.done) {
    console.log('生成完成');
    eventSource.close();
  } else if (data.content) {
    console.log(data.content);
  } else if (data.error) {
    console.error('错误:', data.error);
  }
};
```

**cURL示例**

```bash
curl -X POST "http://localhost:8000/api/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{"message": "帮我规划去杭州的行程"}' \
  --no-buffer
```

---

### 4. 天气查询

查询指定城市的天气信息。

**请求**

```http
GET /api/weather?city=北京
```

**参数说明**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| city | string | 是 | 城市名称 |

**响应**

```json
{
  "city": "北京",
  "weather": "北京天气：晴天，温度25°C，体感温度23°C，风向东南风，风力3级"
}
```

**cURL示例**

```bash
curl "http://localhost:8000/api/weather?city=北京"
```

---

### 5. 天气对比

对比两个城市的天气。

**请求**

```http
GET /api/weather/compare?city1=北京&city2=上海
```

**参数说明**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| city1 | string | 是 | 第一个城市 |
| city2 | string | 是 | 第二个城市 |

**响应**

```json
{
  "comparison": "天气对比：\n北京天气：晴天，温度25°C，体感温度23°C，风向东南风，风力3级\n上海天气：多云，温度28°C，体感温度30°C，风向南风，风力2级"
}
```

**cURL示例**

```bash
curl "http://localhost:8000/api/weather/compare?city1=北京&city2=上海"
```

---

## 错误处理

### 错误响应格式

```json
{
  "detail": "错误描述信息"
}
```

### 常见错误码

| 状态码 | 说明 |
|--------|------|
| 400 | 请求参数错误 |
| 500 | 服务器内部错误 |
| 503 | 服务未初始化 |

### 错误示例

**未初始化**

```json
{
  "detail": "RAG系统未初始化，请检查配置"
}
```

**处理失败**

```json
{
  "detail": "处理失败：无法连接到LLM服务"
}
```

---

## 使用示例

### Python示例

```python
import requests

# 同步对话
response = requests.post(
    "http://localhost:8000/api/chat/sync",
    json={"message": "去上海出差住宿标准是多少？"}
)
print(response.json())

# 天气查询
response = requests.get(
    "http://localhost:8000/api/weather",
    params={"city": "北京"}
)
print(response.json())
```

### JavaScript示例

```javascript
// 同步对话
fetch('http://localhost:8000/api/chat/sync', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    message: '去上海出差住宿标准是多少？'
  })
})
.then(response => response.json())
.then(data => console.log(data));

// 流式对话
const eventSource = new EventSource(
  'http://localhost:8000/api/chat/stream?' + 
  new URLSearchParams({
    message: '帮我规划去杭州的行程'
  })
);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.content) {
    console.log(data.content);
  }
};
```

---

## 性能建议

### 1. 同步 vs 流式

- **同步接口**：适合简单查询，响应时间<3秒
- **流式接口**：适合复杂查询，提升用户体验

### 2. 缓存策略

对于相同的查询，可以在客户端缓存结果：

```python
import hashlib
import json

def get_cache_key(message):
    return hashlib.md5(message.encode()).hexdigest()

cache = {}

def query_with_cache(message):
    key = get_cache_key(message)
    if key in cache:
        return cache[key]
    
    response = requests.post(
        "http://localhost:8000/api/chat/sync",
        json={"message": message}
    )
    result = response.json()
    cache[key] = result
    return result
```

### 3. 并发控制

建议限制并发请求数，避免过载：

```python
from concurrent.futures import ThreadPoolExecutor

# 最多5个并发请求
executor = ThreadPoolExecutor(max_workers=5)
```

---

## 开发调试

### 查看详细日志

启动服务时添加日志级别：

```bash
python src/main.py --log-level debug
```

### 使用Swagger UI

访问 `http://localhost:8000/docs` 可以：
- 查看所有接口
- 在线测试接口
- 查看请求/响应示例

### 使用ReDoc

访问 `http://localhost:8000/redoc` 查看更友好的文档。

---

## 常见问题

### Q1: 为什么返回"RAG系统未初始化"？

**原因**：
- 未配置DASHSCOPE_API_KEY
- data/travel_policy.txt文件不存在
- 向量存储创建失败

**解决**：
1. 检查.env文件
2. 确认data目录存在
3. 查看启动日志

### Q2: 流式接口没有响应？

**原因**：
- 客户端不支持SSE
- 网络代理拦截了流式响应

**解决**：
- 使用支持SSE的客户端
- 添加`--no-buffer`参数（cURL）

### Q3: 天气查询返回模拟数据？

**原因**：未配置QWEATHER_API_KEY

**解决**：
1. 申请和风天气API Key
2. 在.env中配置QWEATHER_API_KEY

---

**最后更新**：2026年5月11日
