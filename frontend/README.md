# 智旅助手 - 前端界面

现代化的商务出差管理系统前端，具有亮眼配色、动画效果和立体感设计。

## 🎨 设计特点

- **亮眼配色**: 青色/蓝色/紫色渐变主题
- **动画效果**: Framer Motion 驱动的流畅动画
- **光效**: 多层次光晕和发光效果
- **立体感**: 3D 阴影、玻璃态效果、景深

## 🚀 快速开始

```bash
# 1. 复制环境变量配置
cp .env.example .env

# 2. 安装依赖
npm install

# 3. 启动开发服务器
npm run dev

# 4. 构建生产版本
npm run build
```

访问: http://localhost:5173

**注意**: 确保后端服务运行在 `http://localhost:8001`

## 📦 技术栈

- **React 19** + TypeScript 6
- **Vite 8** - 超快的构建工具
- **TailwindCSS 4** - 原子化 CSS（使用 @theme 新语法）
- **Framer Motion 12** - 专业动画库
- **Lucide React** - 图标库
- **React Hot Toast** - 通知提示
- **Axios** - HTTP 客户端

## 🎯 核心功能

### 登录页面
- 旅行文档风格设计（护照主题）
- 浮动飞机/指南针装饰
- 印章认证标记
- 票根撕边效果
- 测试账户提示

### 智能对话界面
- 实时消息流
- 用户/助手头像区分
- 旅行文档风格消息气泡
- 加载动画
- JWT 认证集成

## 🔌 后端集成

API 配置在 `.env` 文件中：

```bash
VITE_API_BASE_URL=http://localhost:8001
```

主要 API 端点：
- `POST /api/auth/login` - 用户登录
- `POST /api/unified/chat` - 智能对话

## 🎨 设计系统

### 配色方案（定义在 `src/index.css`）

```css
--color-paper: #FFF8F0       /* 纸质背景 */
--color-navy: #1B3A52        /* 深蓝主色 */
--color-amber: #D4A574       /* 琥珀强调色 */
--color-stamp-red: #A63A2F   /* 印章红 */
```

### 自定义工具类

- `travel-doc` - 文档卡片样式
- `passport-header` - 护照头部
- `ticket-edge-left/right` - 票根边缘
- `stamp` - 印章效果
- `barcode` - 条形码装饰
- `corner-fold` - 折角效果
- `fold-line` - 折叠线
- `diagonal-stripes` - 斜纹背景

### 字体

- **标题**: Playfair Display（衬线）
- **正文**: Commissioner（无衬线）

## 📁 项目结构

```
frontend/
├── src/
│   ├── App.tsx                # 主应用（登录+对话）
│   ├── index.css              # 全局样式+旅行文档设计系统
│   └── main.tsx               # 入口文件+Toast配置
├── public/
│   └── favicon.svg
├── .env.example               # 环境变量模板
├── tailwind.config.js         # TailwindCSS 配置
├── vite.config.ts             # Vite 配置
└── package.json
```

## 🎭 核心设计元素

### 旅行文档美学
- **护照页面**: 头部条纹、国旗配色、官方字体
- **签证印章**: 倾斜、虚线边框、日期戳
- **机票**: 撕边效果、条形码、折叠线
- **纸质纹理**: SVG噪点滤镜背景

### 动画效果
- Framer Motion 入场动画
- 印章盖章效果（scale + rotate）
- 浮动装饰元素
- 悬停交互

## 🔐 认证流程

```
用户登录 → 获取JWT → 存储localStorage → 携带token请求
↓
401状态 → 自动登出 → 清除token → 返回登录页
```

## 📱 响应式设计

- 桌面端: 完整功能，居中卡片布局
- 平板: 自适应宽度
- 移动端: 单列布局，触摸优化

---

**开发者**: Claude Code  
**设计风格**: 旅行文档美学  
**调色板**: Navy × Amber × Paper Texture
