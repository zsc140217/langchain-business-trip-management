# Tool Ecosystem P1 Features Implementation Plan

## Overview
实现工具生态系统的P1优先级功能：
1. 动态工具加载（预计3小时）
2. 工具通道管理（预计4小时）

## Task 1: 动态工具加载 (3小时)

### 目标
实现运行时动态加载/卸载工具，无需重启应用

### 当前架构分析
- ToolRegistry在initialize_all()中硬编码导入所有工具
- 工具实例化后无法卸载
- 配置文件支持enabled标志，但未实际使用
- 缺少工具模块的动态发现机制

### 实现方案

#### 1.1 工具插件发现机制
**文件**: `src/tools/plugin_loader.py` (新建)

功能：
- 扫描tools目录下的所有*_tool.py和*_adapter.py
- 通过反射机制动态导入工具类
- 缓存工具类定义（不实例化）
- 支持自定义插件目录

关键API：
```python
class ToolPluginLoader:
    def discover_tools(self, scan_dirs: List[Path]) -> Dict[str, Type[BaseTool]]
    def load_tool_class(self, module_path: str, class_name: str) -> Type[BaseTool]
    def get_tool_metadata(self, tool_class: Type[BaseTool]) -> ToolMetadata
```

#### 1.2 动态注册/卸载机制
**文件**: `src/tools/registry.py` (修改)

新增方法：
```python
def load_tool(self, tool_name: str) -> bool
    """根据配置动态加载工具"""
    
def unload_tool(self, tool_name: str) -> bool
    """卸载工具并清理资源"""
    
def reload_tool(self, tool_name: str) -> bool
    """重新加载工具（先卸载再加载）"""
    
def enable_tool(self, tool_name: str) -> bool
    """启用已禁用的工具"""
    
def disable_tool(self, tool_name: str) -> bool
    """禁用工具（不卸载，仅标记为disabled）"""
```

#### 1.3 配置热重载集成
**文件**: `src/tools/config_loader.py` (修改)

新增功能：
- 配置变更检测（文件监听）
- 配置diff计算（哪些工具需要重载）
- 回调机制通知registry

新增方法：
```python
def watch_config_changes(self, callback: Callable) -> None
    """监听配置文件变化"""
    
def get_config_diff(self, old_config: Dict, new_config: Dict) -> ConfigDiff
    """计算配置差异"""
```

#### 1.4 工具状态管理
**文件**: `src/tools/registry.py` (修改)

工具状态枚举：
- UNKNOWN: 未加载
- LOADING: 加载中
- LOADED: 已加载
- DISABLED: 已禁用
- FAILED: 加载失败
- UNLOADING: 卸载中

状态查询：
```python
def get_tool_state(self, tool_name: str) -> ToolState
def get_all_tool_states(self) -> Dict[str, ToolState]
```

### 文件清单

**新增文件** (2个):
- `src/tools/plugin_loader.py` (约250行) - 插件发现和加载
- `tests/test_plugin_loader.py` (约150行) - 单元测试

**修改文件** (2个):
- `src/tools/registry.py` (新增约200行) - 动态加载API
- `src/tools/config_loader.py` (新增约100行) - 热重载支持

### 实现顺序
1. 创建ToolPluginLoader - 插件发现机制
2. 修改ToolRegistry - 添加load/unload/reload方法
3. 集成ConfigLoader - 配置热重载
4. 添加工具状态管理
5. 编写测试用例

### 测试验证
```python
# 测试1: 工具发现
loader = ToolPluginLoader()
tools = loader.discover_tools()
assert 'query_weather' in tools

# 测试2: 动态加载
registry = get_tool_registry()
registry.load_tool('query_weather')
assert registry.get_tool_state('query_weather') == ToolState.LOADED

# 测试3: 动态卸载
registry.unload_tool('query_weather')
assert registry.get_tool_state('query_weather') == ToolState.UNKNOWN

# 测试4: 配置热重载
# 修改config/tools.yaml，禁用某工具
config_loader.reload()
# 验证工具被自动禁用
```

---

## Task 2: 工具通道管理 (4小时)

### 目标
实现多通道支持（MCP/HTTP/gRPC/Local），自动路由到合适通道

### 当前架构分析
- 配置文件已定义channels配置段
- 工具配置中有channel字段（mcp/local）
- 当前仅实现MCP和Local通道
- 缺少通道抽象和统一路由机制

### 实现方案

#### 2.1 通道抽象层
**文件**: `src/tools/channels/base_channel.py` (新建)

通道基类：
```python
class BaseChannel(ABC):
    """工具调用通道抽象基类"""
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> bool
        """初始化通道"""
    
    @abstractmethod
    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Any
        """调用工具"""
    
    @abstractmethod
    async def health_check(self) -> ChannelHealthStatus
        """健康检查"""
    
    @abstractmethod
    async def close(self) -> None
        """关闭通道"""
```

通道健康状态：
```python
@dataclass
class ChannelHealthStatus:
    status: ChannelStatus  # HEALTHY/DEGRADED/DOWN
    latency_ms: float
    error: Optional[str]
    timestamp: datetime
```

#### 2.2 具体通道实现
**目录**: `src/tools/channels/`

**文件结构**:
```
src/tools/channels/
├── __init__.py
├── base_channel.py       (基类)
├── mcp_channel.py        (MCP通道 - 改造现有mcp_client)
├── http_channel.py       (HTTP通道 - 新建)
├── grpc_channel.py       (gRPC通道 - 新建，可选)
├── local_channel.py      (Local通道 - 直接调用)
└── channel_manager.py    (通道管理器)
```

##### 2.2.1 MCP通道
**文件**: `src/tools/channels/mcp_channel.py`

改造现有`src/tools/mcp_client.py`为通道实现：
- 实现BaseChannel接口
- 保持现有MCP协议通信逻辑
- 添加连接池和重连机制

##### 2.2.2 HTTP通道
**文件**: `src/tools/channels/http_channel.py`

功能：
- 通过HTTP REST API调用远程工具
- 支持超时、重试、熔断
- 使用httpx异步HTTP客户端

示例配置：
```yaml
channels:
  http:
    enabled: true
    base_url: "http://localhost:8000"
    timeout: 30
    max_retries: 3
    headers:
      Authorization: "Bearer ${API_TOKEN}"
```

##### 2.2.3 Local通道
**文件**: `src/tools/channels/local_channel.py`

功能：
- 直接调用本地工具实例
- 无需网络通信
- 最快执行路径

#### 2.3 通道管理器
**文件**: `src/tools/channels/channel_manager.py`

功能：
- 管理所有通道实例
- 根据工具配置路由到正确通道
- 通道健康监控
- 自动故障转移（fallback）

关键API：
```python
class ChannelManager:
    def register_channel(self, name: str, channel: BaseChannel) -> None
    def get_channel(self, name: str) -> Optional[BaseChannel]
    def route_tool_call(self, tool_name: str, params: Dict) -> Any
    def get_channel_for_tool(self, tool_name: str) -> str
    def enable_channel_health_check(self) -> None
    def get_all_channel_health(self) -> Dict[str, ChannelHealthStatus]
```

路由逻辑：
1. 从工具配置读取channel字段
2. 检查通道是否enabled且healthy
3. 如果主通道不可用，尝试fallback通道
4. 通过对应通道调用工具

#### 2.4 集成到BaseTool和Registry

**修改**: `src/tools/base_tool.py`

添加通道支持：
```python
class BaseTool:
    channel: str = "local"  # 默认通道
    
    def _run(self, **kwargs) -> str:
        # 通过通道管理器路由调用
        channel_manager = get_channel_manager()
        return channel_manager.route_tool_call(self.name, kwargs)
```

**修改**: `src/tools/registry.py`

初始化通道：
```python
def initialize_channels(self) -> None:
    """初始化所有启用的通道"""
    from src.tools.channels.channel_manager import get_channel_manager
    manager = get_channel_manager()
    
    config_loader = get_config_loader()
    channels_config = config_loader._config.get('channels', {})
    
    for channel_name, channel_config in channels_config.items():
        if channel_config.get('enabled', False):
            # 根据类型创建通道实例
            channel = self._create_channel(channel_name, channel_config)
            manager.register_channel(channel_name, channel)
```

### 文件清单

**新增文件** (7个):
- `src/tools/channels/__init__.py` (约20行)
- `src/tools/channels/base_channel.py` (约100行) - 通道基类
- `src/tools/channels/mcp_channel.py` (约150行) - MCP通道
- `src/tools/channels/http_channel.py` (约200行) - HTTP通道
- `src/tools/channels/local_channel.py` (约80行) - Local通道
- `src/tools/channels/channel_manager.py` (约250行) - 通道管理器
- `tests/test_channel_manager.py` (约200行) - 测试

**修改文件** (3个):
- `src/tools/base_tool.py` (修改约50行) - 集成通道路由
- `src/tools/registry.py` (新增约100行) - 通道初始化
- `src/tools/mcp_client.py` (重构为mcp_channel.py)

### 实现顺序
1. 创建通道基类BaseChannel
2. 实现Local通道（最简单）
3. 重构MCP通道（改造现有代码）
4. 实现HTTP通道
5. 创建ChannelManager
6. 集成到BaseTool和Registry
7. 编写测试用例

### 测试验证
```python
# 测试1: 通道初始化
registry = get_tool_registry()
registry.initialize_channels()
manager = get_channel_manager()
assert 'mcp' in manager.list_channels()
assert 'local' in manager.list_channels()

# 测试2: 通道路由
result = manager.route_tool_call('query_weather', {'city': '北京'})
assert 'temperature' in result.lower()

# 测试3: 通道健康检查
manager.enable_channel_health_check()
health = manager.get_all_channel_health()
assert health['mcp'].status in [ChannelStatus.HEALTHY, ChannelStatus.DEGRADED]

# 测试4: 故障转移
# 禁用MCP通道
# 配置工具使用HTTP作为fallback
# 验证自动切换到HTTP通道
```

---

## 架构整合

### 依赖关系
```
ToolRegistry
    ├── PluginLoader (发现工具类)
    ├── ConfigLoader (配置管理)
    ├── ChannelManager (通道路由)
    │   ├── MCPChannel
    │   ├── HTTPChannel
    │   └── LocalChannel
    └── HealthChecker (健康监控)
```

### 调用流程
```
用户请求
    ↓
ToolRegistry.get(tool_name)
    ↓
检查工具状态（LOADED/DISABLED）
    ↓
BaseTool.invoke(params)
    ↓
ChannelManager.route_tool_call()
    ↓
根据配置选择通道（MCP/HTTP/Local）
    ↓
Channel.call_tool()
    ↓
返回结果
```

### 配置示例
```yaml
tools:
  query_weather:
    enabled: true
    channel: mcp
    fallback_channel: http  # 主通道失败时的备用通道
    
channels:
  mcp:
    enabled: true
    server_script: "src/mcp/trip_tools_server.py"
  http:
    enabled: true
    base_url: "http://localhost:8000"
  local:
    enabled: true
```

---

## 总体时间估算

| 任务 | 预计时间 | 文件数 | 代码行数 |
|------|---------|--------|---------|
| 动态工具加载 | 3小时 | 4个文件 | ~700行 |
| 工具通道管理 | 4小时 | 10个文件 | ~1200行 |
| **总计** | **7小时** | **14个文件** | **~1900行** |

---

## 风险与注意事项

### 风险点
1. **通道切换延迟** - 故障转移可能导致请求延迟增加
2. **状态同步** - 多通道环境下状态一致性问题
3. **资源泄漏** - 动态加载/卸载可能导致内存泄漏
4. **配置复杂度** - 通道配置增加运维复杂度

### 缓解措施
1. 实现连接池复用，减少通道切换开销
2. 使用分布式锁或版本号保证状态一致性
3. 在unload_tool中确保所有资源正确释放
4. 提供配置验证工具和详细文档

### 向后兼容
- 保持现有工具调用API不变
- 现有工具无需修改即可继续工作
- 通道配置可选，默认使用local通道
- MCP通道保持现有行为

---

## 交付标准

### 功能完整性
- [ ] 所有工具可动态加载/卸载
- [ ] 配置热重载工作正常
- [ ] 至少支持MCP、HTTP、Local三种通道
- [ ] 通道自动路由和故障转移
- [ ] 通道健康监控

### 测试覆盖
- [ ] 单元测试覆盖率 >= 80%
- [ ] 集成测试验证端到端流程
- [ ] 性能测试（通道切换延迟 < 100ms）

### 文档完备
- [ ] API文档（方法签名和用法）
- [ ] 配置示例（各通道配置）
- [ ] 故障排查指南

---

## 实施步骤总结

### Phase 1: 动态工具加载（3小时）
1. 创建PluginLoader - 30分钟
2. 修改Registry添加动态加载API - 60分钟
3. 集成ConfigLoader热重载 - 45分钟
4. 添加工具状态管理 - 30分钟
5. 编写测试 - 45分钟

### Phase 2: 工具通道管理（4小时）
1. 创建通道基类和数据结构 - 30分钟
2. 实现Local通道 - 30分钟
3. 重构MCP通道 - 60分钟
4. 实现HTTP通道 - 60分钟
5. 创建ChannelManager - 60分钟
6. 集成到BaseTool和Registry - 30分钟
7. 编写测试 - 60分钟

### Phase 3: 集成测试和文档（1小时）
1. 端到端集成测试 - 30分钟
2. 更新文档和使用示例 - 30分钟

**总计**: 8小时（包含缓冲时间）
