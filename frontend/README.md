# 智旅助手 - 前端界面

现代化的商务出差管理系统前端，具有亮眼配色、动画效果和立体感设计。

## 🎨 设计特点

- **亮眼配色**: 青色/蓝色/紫色渐变主题
- **动画效果**: Framer Motion 驱动的流畅动画
- **光效**: 多层次光晕和发光效果
- **立体感**: 3D 阴影、玻璃态效果、景深

## 🚀 快速开始

```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build
```

访问: http://localhost:5173

## 📦 技术栈

- **React 19** + TypeScript
- **Vite 8** - 超快的构建工具
- **TailwindCSS 4** - 原子化 CSS
- **Framer Motion** - 动画库
- **Lucide React** - 图标库
- **Zustand** - 状态管理
- **Axios** - HTTP 客户端

## 🎯 核心功能

### 首页
- 动态背景粒子效果
- 性能指标卡片（带悬停动画）
- 功能特性展示
- 渐变文字和光效按钮

### 智能对话
- 实时消息流
- 用户/助手头像
- 打字加载动画
- 流式响应支持（待连接后端）

## 🔌 后端集成

修改 `src/components/ChatInterface.tsx` 中的 API 调用：

```typescript
// 将模拟调用替换为真实 API
const response = await fetch('http://localhost:8000/api/chat/stream', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query: input }),
})
```

## 🎨 自定义样式

配色方案在 `tailwind.config.js` 中定义：
- `primary` - 主色调（青色系）
- `accent` - 强调色（紫色系）
- `glow` - 光效颜色

## 📁 项目结构

```
frontend/
├── src/
│   ├── components/
│   │   ├── ChatInterface.tsx   # 对话界面
│   │   ├── StatsCard.tsx       # 统计卡片
│   │   └── FeatureCard.tsx     # 功能卡片
│   ├── App.tsx                 # 主应用
│   ├── index.css              # 全局样式
│   └── main.tsx               # 入口文件
├── tailwind.config.js         # TailwindCSS 配置
└── package.json
```

## 🌈 动画效果

- `animate-gradient` - 渐变流动
- `animate-float` - 浮动效果
- `animate-glow` - 光晕闪烁
- `animate-shimmer` - 闪光扫过

## 📱 响应式设计

- 桌面端: 完整功能
- 平板: 自适应布局
- 移动端: 单列布局

---

**开发者**: Claude Code  
**设计风格**: 赛博朋克 × 商务现代  
**调色板**: Cyan-Blue-Purple Gradient
