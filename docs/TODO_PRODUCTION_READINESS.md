 前端开发交接文档

  项目名称: 智旅助手 - 企业差旅管理系统
  交接日期: 2026-07-20
  最后更新: 2026-07-20 (会话管理功能已完成)
  当前状态: 用户认证已完成，基础对话功能可用，会话管理已实现 ✅
  技术栈: React 19 + TypeScript 6 + Vite 8 + TailwindCSS 4

  ---
  📋 目录

  1. 当前系统状态
  2. 立即修复事项
  3. 待开发功能清单
  4. 技术架构说明
  5. API 接口文档
  6. 开发环境配置
  7. 关键文件说明
  8. 常见问题处理

  ---
  🎯 当前系统状态

  ✅ 已完成功能

  1. 用户认证系统

  - 登录页面 ✅
    - 旅行文档风格设计（护照主题）
    - 用户名/密码表单
    - 测试账户提示卡片
    - JWT Token 存储到 localStorage
    - 登录成功后跳转到对话界面
  - 测试账户 ✅
  员工: employee / test123456
  经理: manager / test123456
  高管: executive / test123456
  - 登出功能 ✅
    - 清除 Token 和用户信息
    - 返回登录页
    - Toast 提示

  2. 基础对话功能

  - 消息发送/接收 ✅
    - 用户输入框
    - 发送按钮（支持 Enter 快捷键）
    - 消息列表展示
    - 用户/助手消息区分
  - UI 交互 ✅
    - 消息自动滚动到底部
    - 加载状态显示
    - 错误提示（Toast）
    - 旅行文档风格消息气泡

  3. 设计系统

  - 旅行文档美学 ✅
    - Navy/Amber 配色方案
    - 纸质纹理背景
    - 护照头部、印章、票根撕边等元素
    - 自定义 TailwindCSS 工具类
  - 动画效果 ✅
    - Framer Motion 入场动画
    - 悬停交互
    - 加载动画

  4. 会话管理系统 ✅ (2026-07-20 完成)

  - API 基础设施 ✅
    - API 客户端封装 (src/api/client.ts)
    - 自动 Token 注入
    - 401 错误自动处理
  - 会话 API ✅
    - 获取会话列表（分页支持）
    - 创建新会话
    - 获取会话消息
    - 更新会话标题
    - 删除会话
  - 会话列表侧边栏 ✅
    - 可折叠/展开
    - 会话列表展示
    - 当前会话高亮
    - 友好时间显示（X分钟前/X小时前）
    - 删除会话（带确认）
    - 滚动加载更多
  - 会话管理功能 ✅
    - 新建对话
    - 切换会话并加载历史消息
    - 删除会话自动切换

  ⚠️ 存在的问题

  🔴 严重问题 - 必须立即修复

  问题 1: 对话请求未携带 Token ✅ 已修复 (2026-07-20)

  位置: frontend/src/App.tsx:89-101

  修复内容:
  - ✅ 添加 Authorization header 携带 Token
  - ✅ 使用真实用户ID替代硬编码
  - ✅ 添加 401 错误处理和自动登出

  影响: 已解决
  - ✅ 后端可以正确识别用户身份
  - ✅ 鉴权正常工作
  - ✅ 用户数据正确关联

  修复方案: 已完成，详见 App.tsx 第 89-104 行

  ---
  🚨 立即修复事项

  1. 修复对话请求携带 Token ✅ 已完成 (2026-07-20)

  优先级: 🔴 CRITICAL
  实际耗时: 5 分钟
  文件: frontend/src/App.tsx

  修改内容

  位置: 第 88-104 行 handleSend 函数

  已完成修改:
  - ✅ 从 localStorage 读取 access_token 和 user_info
  - ✅ 在请求头中添加 Authorization: Bearer ${token}
  - ✅ 使用真实用户ID (userInfo?.user_id) 替代硬编码
  - ✅ 添加 401 状态码处理，自动登出
  - ✅ 改进错误处理逻辑

  验证结果 ✅
  - ✅ Token 正确携带到所有对话请求
  - ✅ 后端可以识别用户身份
  - ✅ 401 错误自动登出并跳转登录页
  - ✅ 用户数据正确关联

  ---
  📝 待开发功能清单

  Phase 2: 会话管理 ✅ 已完成 (2026-07-20)【优先级: 🔴 HIGH】

  目标: 实现完整的会话持久化和管理功能 ✅

  功能需求: ✅ 全部完成

  1. 左侧会话列表侧边栏 ✅
    - ✅ 可折叠/展开（默认展开）
    - ✅ 显示会话标题和最后消息时间
    - ✅ 高亮当前活跃会话
    - ✅ 滚动加载更多会话（分页）
  2. 新建会话 ✅
    - ✅ 顶部"新建对话"按钮
    - ✅ 点击清空当前消息
    - ✅ 自动创建新会话ID
    - ✅ 第一条消息发送后调用 POST /api/conversations 创建会话
  3. 会话切换 ✅
    - ✅ 点击侧边栏会话条目
    - ✅ 加载该会话的历史消息
    - ✅ 调用 GET /api/conversations/{id}/messages
  4. 删除会话 ✅
    - ✅ 每个会话条目右侧删除按钮
    - ✅ 弹出确认对话框
    - ✅ 调用 DELETE /api/conversations/{id}
    - ✅ 删除当前会话后自动切换到最新会话
  5. 会话标题生成 🟡 部分完成
    - ✅ 使用第一条用户消息（截取前20字）
    - ⏳ 调用LLM总结会话主题（待实现）
    - ⏳ 支持手动编辑标题（待实现）

  技术实现: ✅ 已完成

  新增文件结构 ✅

  frontend/src/
  ├── api/
  │   ├── client.ts                ✅ API 客户端封装
  │   └── conversations.ts         ✅ 会话 API 调用
  ├── hooks/
  │   └── useConversations.ts      ✅ 会话管理 Hook
  ├── types/
  │   └── conversation.ts          ✅ 会话类型定义
  └── components/
      └── Sidebar.tsx              ✅ 会话列表侧边栏

  实际工作量: 2 小时 (预估: 4-6 小时)

  验收标准: ✅ 全部通过
  - ✅ 侧边栏可正常展开/折叠
  - ✅ 能创建新会话
  - ✅ 能切换会话并加载历史消息
  - ✅ 能删除会话（带确认）
  - ✅ 会话列表支持滚动加载
  - ✅ 当前会话高亮显示
  - ✅ 时间显示友好（几分钟前/几小时前）

  核心代码示例

  1. API 客户端封装 (src/api/client.ts)

  import axios from 'axios'

  const apiClient = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001',
    headers: {
      'Content-Type': 'application/json',
    },
  })

  // 请求拦截器：自动添加 Token
  apiClient.interceptors.request.use((config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  })

  // 响应拦截器：处理 401
  apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.status === 401) {
        localStorage.removeItem('access_token')
        localStorage.removeItem('user_info')
        window.location.href = '/'
      }
      return Promise.reject(error)
    }
  )

  export default apiClient

  2. 会话 API (src/api/conversations.ts)

  import apiClient from './client'

  export interface Conversation {
    conversation_id: string
    user_id: string
    title: string | null
    created_at: string
    updated_at: string
    last_message_at: string | null
  }

  export interface Message {
    message_id: number
    conversation_id: string
    role: 'user' | 'assistant' | 'system'
    content: string
    created_at: string
  }

  export interface ConversationListResponse {
    conversations: Conversation[]
    total: number
    page: number
    page_size: number
  }

  // 获取会话列表
  export const getConversations = async (page = 1, pageSize = 20) => {
    const response = await apiClient.get<ConversationListResponse>('/api/conversations', {
      params: { page, page_size: pageSize },
    })
    return response.data
  }

  // 创建新会话
  export const createConversation = async (title?: string) => {
    const response = await apiClient.post<Conversation>('/api/conversations', {
      title: title || '新对话',
    })
    return response.data
  }

  // 获取会话消息
  export const getConversationMessages = async (conversationId: string, page = 1, pageSize = 50) => {
    const response = await apiClient.get<{ messages: Message[]; total: number }>(
      `/api/conversations/${conversationId}/messages`,
      { params: { page, page_size: pageSize } }
    )
    return response.data
  }

  // 更新会话标题
  export const updateConversationTitle = async (conversationId: string, title: string) => {
    const response = await apiClient.put<Conversation>(
      `/api/conversations/${conversationId}`,
      { title }
    )
    return response.data
  }

  // 删除会话
  export const deleteConversation = async (conversationId: string) => {
    await apiClient.delete(`/api/conversations/${conversationId}`)
  }

  3. 会话管理 Hook (src/hooks/useConversations.ts)

  import { useState, useEffect } from 'react'
  import { getConversations, createConversation, deleteConversation } from '../api/conversations'
  import type { Conversation } from '../api/conversations'
  import toast from 'react-hot-toast'

  export const useConversations = () => {
    const [conversations, setConversations] = useState<Conversation[]>([])
    const [loading, setLoading] = useState(false)
    const [currentPage, setCurrentPage] = useState(1)
    const [hasMore, setHasMore] = useState(true)

    // 加载会话列表
    const loadConversations = async (page = 1) => {
      if (loading) return

      setLoading(true)
      try {
        const data = await getConversations(page, 20)

        if (page === 1) {
          setConversations(data.conversations)
        } else {
          setConversations((prev) => [...prev, ...data.conversations])
        }

        setHasMore(conversations.length < data.total)
        setCurrentPage(page)
      } catch (error) {
        toast.error('加载会话列表失败')
        console.error(error)
      } finally {
        setLoading(false)
      }
    }

    // 创建新会话
    const createNew = async () => {
      try {
        const newConv = await createConversation()
        setConversations((prev) => [newConv, ...prev])
        toast.success('创建新会话')
        return newConv
      } catch (error) {
        toast.error('创建会话失败')
        console.error(error)
        return null
      }
    }

    // 删除会话
    const deleteById = async (conversationId: string) => {
      try {
        await deleteConversation(conversationId)
        setConversations((prev) => prev.filter((c) => c.conversation_id !== conversationId))
        toast.success('会话已删除')
      } catch (error) {
        toast.error('删除会话失败')
        console.error(error)
      }
    }

    // 加载更多
    const loadMore = () => {
      if (hasMore && !loading) {
        loadConversations(currentPage + 1)
      }
    }

    // 初始加载
    useEffect(() => {
      loadConversations(1)
    }, [])

    return {
      conversations,
      loading,
      hasMore,
      loadMore,
      createNew,
      deleteById,
      refresh: () => loadConversations(1),
    }
  }

  4. 侧边栏组件 (src/components/Sidebar.tsx)

  import { useState } from 'react'
  import { motion, AnimatePresence } from 'framer-motion'
  import { Plus, MessageCircle, Trash2, ChevronLeft, ChevronRight } from 'lucide-react'
  import { useConversations } from '../hooks/useConversations'
  import type { Conversation } from '../api/conversations'

  interface SidebarProps {
    currentConversationId: string | null
    onSelectConversation: (conversationId: string) => void
    onNewConversation: () => void
  }

  export default function Sidebar({
    currentConversationId,
    onSelectConversation,
    onNewConversation,
  }: SidebarProps) {
    const [isOpen, setIsOpen] = useState(true)
    const { conversations, loading, hasMore, loadMore, deleteById } = useConversations()

    const handleDelete = async (e: React.MouseEvent, conversationId: string) => {
      e.stopPropagation()

      if (window.confirm('确定要删除这个会话吗？')) {
        await deleteById(conversationId)

        // 如果删除的是当前会话，切换到最新会话
        if (conversationId === currentConversationId && conversations.length > 0) {
          const remaining = conversations.filter((c) => c.conversation_id !== conversationId)
          if (remaining.length > 0) {
            onSelectConversation(remaining[0].conversation_id)
          } else {
            onNewConversation()
          }
        }
      }
    }

    const formatTime = (timestamp: string) => {
      const date = new Date(timestamp)
      const now = new Date()
      const diffMs = now.getTime() - date.getTime()
      const diffMins = Math.floor(diffMs / 60000)
      const diffHours = Math.floor(diffMs / 3600000)
      const diffDays = Math.floor(diffMs / 86400000)

      if (diffMins < 60) return `${diffMins}分钟前`
      if (diffHours < 24) return `${diffHours}小时前`
      if (diffDays < 7) return `${diffDays}天前`
      return date.toLocaleDateString('zh-CN')
    }

    return (
      <>
        {/* 折叠按钮 */}
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="fixed top-20 left-4 z-50 w-10 h-10 bg-[var(--color-navy)] text-[var(--color-amber)]
                     rounded-lg flex items-center justify-center hover:bg-[var(--color-navy-light)]
                     transition-colors shadow-document"
        >
          {isOpen ? <ChevronLeft size={20} /> : <ChevronRight size={20} />}
        </button>

        {/* 侧边栏 */}
        <AnimatePresence>
          {isOpen && (
            <motion.aside
              initial={{ x: -300 }}
              animate={{ x: 0 }}
              exit={{ x: -300 }}
              transition={{ type: 'spring', damping: 20 }}
              className="fixed left-0 top-0 h-screen w-80 bg-[var(--color-paper-dark)]
                         border-r-2 border-[var(--color-navy)] z-40 flex flex-col"
            >
              {/* 头部：新建会话按钮 */}
              <div className="p-4 border-b border-[var(--color-navy)]">
                <button
                  onClick={onNewConversation}
                  className="w-full bg-[var(--color-navy)] text-[var(--color-amber)] py-3 rounded-lg
                             font-medium flex items-center justify-center gap-2
                             hover:bg-[var(--color-navy-light)] transition-colors"
                >
                  <Plus size={20} />
                  新建对话
                </button>
              </div>

              {/* 会话列表 */}
              <div className="flex-1 overflow-y-auto p-2">
                {conversations.map((conversation) => (
                  <motion.div
                    key={conversation.conversation_id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    onClick={() => onSelectConversation(conversation.conversation_id)}
                    className={`p-3 mb-2 rounded-lg cursor-pointer group relative
                              ${
                                conversation.conversation_id === currentConversationId
                                  ? 'bg-[var(--color-navy)] text-[var(--color-paper)]'
                                  : 'bg-white hover:bg-[var(--color-paper)] text-[var(--color-navy)]'
                              }
                              transition-colors border-2 border-transparent
                              ${
                                conversation.conversation_id === currentConversationId
                                  ? 'border-[var(--color-amber)]'
                                  : ''
                              }`}
                  >
                    <div className="flex items-start gap-2">
                      <MessageCircle size={16} className="mt-1 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">
                          {conversation.title || '未命名对话'}
                        </p>
                        <p className="text-xs opacity-70 mt-1">
                          {conversation.last_message_at
                            ? formatTime(conversation.last_message_at)
                            : formatTime(conversation.created_at)}
                        </p>
                      </div>

                      {/* 删除按钮 */}
                      <button
                        onClick={(e) => handleDelete(e, conversation.conversation_id)}
                        className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-500/20
                                   rounded transition-all"
                      >
                        <Trash2 size={16} className="text-red-500" />
                      </button>
                    </div>
                  </motion.div>
                ))}

                {/* 加载更多 */}
                {hasMore && (
                  <button
                    onClick={loadMore}
                    disabled={loading}
                    className="w-full py-2 text-sm text-[var(--color-navy-lighter)]
                               hover:text-[var(--color-navy)] transition-colors"
                  >
                    {loading ? '加载中...' : '加载更多'}
                  </button>
                )}
              </div>
            </motion.aside>
          )}
        </AnimatePresence>
      </>
    )
  }

  5. 集成到 App.tsx

  在 App.tsx 中导入并使用侧边栏：

  import Sidebar from './components/Sidebar'
  import { getConversationMessages } from './api/conversations'

  function App() {
    // ... 现有状态 ...
    const [sidebarOpen, setSidebarOpen] = useState(true)

    // 切换会话
    const handleSelectConversation = async (conversationId: string) => {
      setConversationId(conversationId)
      setMessages([])

      try {
        const data = await getConversationMessages(conversationId)
        const formattedMessages = data.messages.map((msg) => ({
          role: msg.role as 'user' | 'assistant',
          content: msg.content,
          timestamp: msg.created_at,
        }))
        setMessages(formattedMessages)
      } catch (error) {
        toast.error('加载消息失败')
      }
    }

    // 新建会话
    const handleNewConversation = () => {
      setConversationId(null)
      setMessages([])
    }

    return (
      <div className="min-h-screen flex">
        {/* 侧边栏 */}
        <Sidebar
          currentConversationId={conversationId}
          onSelectConversation={handleSelectConversation}
          onNewConversation={handleNewConversation}
        />

        {/* 主内容区（添加左边距） */}
        <main className={`flex-1 ${sidebarOpen ? 'ml-80' : 'ml-0'} transition-all`}>
          {/* ... 现有聊天界面 ... */}
        </main>
      </div>
    )
  }

  预估工作量: 4-6 小时

  验收标准:
  - [ ] 侧边栏可正常展开/折叠
  - [ ] 能创建新会话
  - [ ] 能切换会话并加载历史消息
  - [ ] 能删除会话（带确认）
  - [ ] 会话列表支持滚动加载
  - [ ] 当前会话高亮显示
  - [ ] 时间显示友好（几分钟前/几小时前）

  ---
  Phase 3: 消息增强 【优先级: 🟡 MEDIUM】

  目标: 提升消息展示和交互体验

  3.1 Markdown 渲染

  功能需求:
  - 支持 Markdown 语法（标题、粗体、列表、链接、代码块）
  - 代码语法高亮
  - 表格渲染
  - 支持 LaTeX 数学公式（可选）

  依赖安装:
  npm install react-markdown remark-gfm rehype-highlight
  npm install --save-dev @types/react-syntax-highlighter

  实现示例 (src/components/MessageContent.tsx):

  import ReactMarkdown from 'react-markdown'
  import remarkGfm from 'remark-gfm'
  import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
  import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'

  interface MessageContentProps {
    content: string
  }

  export default function MessageContent({ content }: MessageContentProps) {
    return (
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          code({ node, inline, className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || '')
            return !inline && match ? (
              <SyntaxHighlighter
                style={oneDark}
                language={match[1]}
                PreTag="div"
                {...props}
              >
                {String(children).replace(/\n$/, '')}
              </SyntaxHighlighter>
            ) : (
              <code className="bg-gray-200 px-1 py-0.5 rounded text-sm" {...props}>
                {children}
              </code>
            )
          },
          table({ children }) {
            return (
              <div className="overflow-x-auto my-4">
                <table className="min-w-full border border-gray-300">{children}</table>
              </div>
            )
          },
          th({ children }) {
            return (
              <th className="border border-gray-300 px-4 py-2 bg-gray-100 font-semibold">
                {children}
              </th>
            )
          },
          td({ children }) {
            return <td className="border border-gray-300 px-4 py-2">{children}</td>
          },
        }}
      >
        {content}
      </ReactMarkdown>
    )
  }

  3.2 消息操作

  功能需求:
  - 复制消息内容
  - 重新生成回答（仅 AI 消息）
  - 消息反馈（点赞/点踩）

  实现示例:

  // 复制功能
  const handleCopy = async (content: string) => {
    try {
      await navigator.clipboard.writeText(content)
      toast.success('已复制到剪贴板')
    } catch {
      toast.error('复制失败')
    }
  }

  // 重新生成
  const handleRegenerate = async (messageIndex: number) => {
    const userMessage = messages[messageIndex - 1]
    if (!userMessage || userMessage.role !== 'user') return

    // 删除旧的 AI 回复
    setMessages((prev) => prev.slice(0, messageIndex))

    // 重新发送用户消息
    await sendMessage(userMessage.content)
  }

  // 消息反馈
  const handleFeedback = async (messageId: number, feedback: 'positive' | 'negative') => {
    try {
      await apiClient.post(`/api/messages/${messageId}/feedback`, { feedback })
      toast.success('感谢您的反馈')
    } catch {
      toast.error('提交反馈失败')
    }
  }

  预估工作量: 6-8 小时

  验收标准:
  - [ ] Markdown 正确渲染（标题、列表、链接、代码）
  - [ ] 代码块语法高亮
  - [ ] 表格正确显示
  - [ ] 复制消息功能正常
  - [ ] 重新生成功能正常
  - [ ] 反馈功能正常（如果后端支持）

  ---
  Phase 4: 用户体验优化 【优先级: 🟡 MEDIUM】

  4.1 个人资料页

  功能需求:
  - 显示用户信息（姓名、邮箱、部门、职位）
  - 编辑个人信息
  - 显示统计数据（会话总数、消息总数）
  - 修改密码（可选）

  实现位置: 新增 src/pages/ProfilePage.tsx

  路由配置: 使用 react-router-dom

  npm install react-router-dom

  // App.tsx 改造为路由模式
  import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'

  function App() {
    return (
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LoginPage />} />
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/profile" element={<ProfilePage />} />
        </Routes>
      </BrowserRouter>
    )
  }

  4.2

✻ Churned for 1m 37s

※ recap: You asked me to write a detailed frontend handover document listing all tasks for a new session. I'm outputting
  it to the chat - currently at Phase 4 (user experience optimization). Still need to finish Phase 5 (advanced
  features), technical architecture, API docs, and troubleshooting sections. (disable recaps in /config)

❯ 生成完成了吗

● 还没完成，我继续输出剩余部分：

  ---
  4.2 响应式设计

  功能需求:
  - 移动端适配（< 768px）
    - 侧边栏改为全屏抽屉模式
    - 汉堡菜单按钮
    - 消息气泡适配小屏幕
  - 平板端优化（768px - 1024px）
    - 侧边栏可折叠
    - 消息列表两栏布局

  实现要点:

  // 使用 TailwindCSS 响应式类
  <div className="w-full md:w-80 lg:w-96">  {/* 移动端全宽，中等屏幕固定宽度 */}
    ...
  </div>

  // 移动端汉堡菜单
  <button className="md:hidden" onClick={() => setMobileMenuOpen(true)}>
    <Menu size={24} />
  </button>

  // 侧边栏抽屉模式（移动端）
  <AnimatePresence>
    {mobileMenuOpen && (
      <>
        {/* 遮罩层 */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={() => setMobileMenuOpen(false)}
          className="fixed inset-0 bg-black/50 z-40 md:hidden"
        />

        {/* 侧边栏 */}
        <motion.aside
          initial={{ x: -300 }}
          animate={{ x: 0 }}
          exit={{ x: -300 }}
          className="fixed left-0 top-0 h-full w-80 bg-white z-50 md:hidden"
        >
          {/* 侧边栏内容 */}
        </motion.aside>
      </>
    )}
  </AnimatePresence>

  4.3 暗色模式

  功能需求:
  - 检测系统偏好
  - 手动切换开关
  - 保存到 localStorage
  - 平滑过渡动画

  实现步骤:

  1. 创建主题 Hook (src/hooks/useTheme.ts)

  import { useEffect, useState } from 'react'

  type Theme = 'light' | 'dark'

  export const useTheme = () => {
    const [theme, setTheme] = useState<Theme>(() => {
      // 优先读取 localStorage
      const saved = localStorage.getItem('theme') as Theme | null
      if (saved) return saved

      // 检测系统偏好
      if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
        return 'dark'
      }

      return 'light'
    })

    useEffect(() => {
      const root = document.documentElement

      if (theme === 'dark') {
        root.classList.add('dark')
      } else {
        root.classList.remove('dark')
      }

      localStorage.setItem('theme', theme)
    }, [theme])

    const toggleTheme = () => {
      setTheme((prev) => (prev === 'light' ? 'dark' : 'light'))
    }

    return { theme, toggleTheme }
  }

  2. 配置 Tailwind 暗色模式 (tailwind.config.js)

  export default {
    darkMode: 'class',  // 启用 class 模式
    // ... 其他配置
  }

  3. 暗色主题 CSS 变量 (src/index.css)

  @layer base {
    :root {
      --color-paper: #FFF8F0;
      --color-navy: #1B3A52;
      --color-amber: #D4A574;
      /* ... 其他颜色 */
    }

    .dark {
      --color-paper: #1a1a1a;
      --color-navy: #e8e8e8;
      --color-amber: #d4a574;
      /* ... 暗色主题颜色 */
    }
  }

  4. 切换按钮组件

  import { Sun, Moon } from 'lucide-react'
  import { useTheme } from '../hooks/useTheme'

  export default function ThemeToggle() {
    const { theme, toggleTheme } = useTheme()

    return (
      <button
        onClick={toggleTheme}
        className="p-2 rounded-lg bg-[var(--color-navy)] text-[var(--color-amber)]
                   hover:bg-[var(--color-navy-light)] transition-colors"
        aria-label="切换主题"
      >
        {theme === 'light' ? <Moon size={20} /> : <Sun size={20} />}
      </button>
    )
  }

  预估工作量: 8-10 小时

  验收标准:
  - [ ] 个人资料页正确显示用户信息
  - [ ] 能编辑个人信息
  - [ ] 移动端侧边栏为抽屉模式
  - [ ] 平板端布局合理
  - [ ] 暗色模式正常切换
  - [ ] 主题偏好持久化

  ---
  Phase 5: 高级功能 【优先级: 🟢 LOW】

  5.1 流式响应（SSE）

  功能需求:
  - 使用 Server-Sent Events 接收流式数据
  - 逐字显示 AI 回答
  - 打字机效果动画

  实现示例:

  const handleSendWithStream = async (query: string) => {
    const token = localStorage.getItem('access_token')

    // 创建 EventSource（需要后端支持 SSE）
    const eventSource = new EventSource(
      `${API_BASE}/api/unified/chat/stream?query=${encodeURIComponent(query)}&token=${token}`
    )

    let fullResponse = ''

    eventSource.onmessage = (event) => {
      const chunk = event.data
      fullResponse += chunk

      // 实时更新消息
      setMessages((prev) => {
        const lastMessage = prev[prev.length - 1]
        if (lastMessage && lastMessage.role === 'assistant') {
          return [
            ...prev.slice(0, -1),
            { ...lastMessage, content: fullResponse }
          ]
        } else {
          return [
            ...prev,
            { role: 'assistant', content: fullResponse, timestamp: new Date().toISOString() }
          ]
        }
      })
    }

    eventSource.onerror = () => {
      eventSource.close()
      setIsSending(false)
    }

    eventSource.addEventListener('done', () => {
      eventSource.close()
      setIsSending(false)
    })
  }

  5.2 语音输入

  功能需求:
  - 使用 Web Speech API
  - 麦克风权限管理
  - 语音转文字实时显示

  实现示例:

  import { Mic, MicOff } from 'lucide-react'

  const [isListening, setIsListening] = useState(false)
  const recognition = useRef<SpeechRecognition | null>(null)

  useEffect(() => {
    if ('webkitSpeechRecognition' in window) {
      const SpeechRecognition = window.webkitSpeechRecognition
      recognition.current = new SpeechRecognition()
      recognition.current.continuous = false
      recognition.current.lang = 'zh-CN'

      recognition.current.onresult = (event) => {
        const transcript = event.results[0][0].transcript
        setInput(transcript)
      }

      recognition.current.onend = () => {
        setIsListening(false)
      }
    }
  }, [])

  const toggleListening = () => {
    if (!recognition.current) {
      toast.error('浏览器不支持语音输入')
      return
    }

    if (isListening) {
      recognition.current.stop()
    } else {
      recognition.current.start()
      setIsListening(true)
    }
  }

  // 麦克风按钮
  <button onClick={toggleListening}>
    {isListening ? <MicOff className="text-red-500" /> : <Mic />}
  </button>

  5.3 多语言支持

  依赖安装:
  npm install i18next react-i18next

  配置文件 (src/i18n/config.ts):

  import i18n from 'i18next'
  import { initReactI18next } from 'react-i18next'

  i18n
    .use(initReactI18next)
    .init({
      resources: {
        zh: {
          translation: {
            'login.welcome': '欢迎登机',
            'login.username': '用户名',
            'chat.send': '发送',
            // ... 更多翻译
          }
        },
        en: {
          translation: {
            'login.welcome': 'Welcome Aboard',
            'login.username': 'Username',
            'chat.send': 'Send',
            // ... 更多翻译
          }
        }
      },
      lng: 'zh',
      fallbackLng: 'zh',
      interpolation: {
        escapeValue: false
      }
    })

  export default i18n

  使用翻译:

  import { useTranslation } from 'react-i18next'

  function LoginPage() {
    const { t, i18n } = useTranslation()

    return (
      <div>
        <h1>{t('login.welcome')}</h1>
        <button onClick={() => i18n.changeLanguage('en')}>English</button>
        <button onClick={() => i18n.changeLanguage('zh')}>中文</button>
      </div>
    )
  }

  5.4 PWA 支持

  1. 创建 Service Worker (public/sw.js)

  const CACHE_NAME = 'business-trip-v1'
  const urlsToCache = [
    '/',
    '/index.html',
    '/src/main.tsx',
    '/src/index.css',
  ]

  self.addEventListener('install', (event) => {
    event.waitUntil(
      caches.open(CACHE_NAME).then((cache) => cache.addAll(urlsToCache))
    )
  })

  self.addEventListener('fetch', (event) => {
    event.respondWith(
      caches.match(event.request).then((response) => {
        return response || fetch(event.request)
      })
    )
  })

  2. 注册 Service Worker (src/main.tsx)

  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/sw.js')
        .then(() => console.log('SW registered'))
        .catch(() => console.log('SW registration failed'))
    })
  }

  3. 添加 Web App Manifest (public/manifest.json)

  {
    "name": "智旅助手",
    "short_name": "智旅",
    "description": "企业差旅管理系统",
    "start_url": "/",
    "display": "standalone",
    "background_color": "#FFF8F0",
    "theme_color": "#1B3A52",
    "icons": [
      {
        "src": "/icon-192.png",
        "sizes": "192x192",
        "type": "image/png"
      },
      {
        "src": "/icon-512.png",
        "sizes": "512x512",
        "type": "image/png"
      }
    ]
  }

  4. 在 HTML 中引用 (index.html)

  <link rel="manifest" href="/manifest.json">
  <meta name="theme-color" content="#1B3A52">

  预估工作量: 12-16 小时

  验收标准:
  - [ ] 流式响应逐字显示
  - [ ] 语音输入功能正常
  - [ ] 支持中英文切换
  - [ ] PWA 可安装到桌面
  - [ ] 离线缓存生效

  ---
  🛠️ 技术架构说明

  后端架构

  统一 API 入口 (unified_api.py:8001)
  ├─ 认证路由 (/api/auth)
  │  ├─ POST /login
  │  ├─ POST /register
  │  ├─ GET /me
  │  └─ POST /logout
  ├─ 会话路由 (/api/conversations)
  │  ├─ GET /          (列表)
  │  ├─ POST /         (创建)
  │  ├─ GET /{id}      (详情)
  │  ├─ PUT /{id}      (更新)
  │  ├─ DELETE /{id}   (删除)
  │  └─ GET /{id}/messages (消息)
  └─ 对话路由 (/api/unified)
     ├─ POST /chat     (智能对话)
     └─ GET /stats     (统计)

  核心组件:
  - OrchestratorAgent: 统一路由，识别意图
  - QAEngine: Q&A 域（政策查询）
  - ApprovalEngine: 审批域（报销申请）
  - MemoryService: 三层记忆系统
  - FeishuClient: 飞书集成

  前端架构

  frontend/
  ├── public/
  │   └── favicon.svg
  ├── src/
  │   ├── components/          # 组件
  │   │   ├── Sidebar.tsx
  │   │   ├── MessageContent.tsx
  │   │   └── ThemeToggle.tsx
  │   ├── hooks/              # 自定义 Hooks
  │   │   ├── useConversations.ts
  │   │   ├── useMessages.ts
  │   │   └── useTheme.ts
  │   ├── api/                # API 调用
  │   │   ├── client.ts
  │   │   └── conversations.ts
  │   ├── types/              # 类型定义
  │   │   └── conversation.ts
  │   ├── store/              # 状态管理（可选）
  │   │   └── conversationStore.ts
  │   ├── App.tsx             # 主应用
  │   ├── index.css           # 全局样式
  │   └── main.tsx            # 入口
  ├── .env                    # 环境变量
  ├── tailwind.config.js      # Tailwind 配置
  ├── vite.config.ts          # Vite 配置
  └── package.json

  数据流

  用户输入
    ↓
  前端验证 → localStorage (Token)
    ↓
  Axios 请求 → Authorization Header
    ↓
  后端 unified_api.py
    ↓
  Auth Middleware (验证 Token)
    ↓
  OrchestratorAgent (路由分发)
    ↓
  QAEngine / ApprovalEngine
    ↓
  LLM + Tools + Memory
    ↓
  Response → 前端渲染
    ↓
  保存到 conversations 表

  ---
  🔌 前后端对接说明

  重要提示: 如果后续调整后端通信层、API结构或消息格式，请参考本节确保前后端兼容。

  1. 前端 API 客户端配置

  位置: frontend/src/api/client.ts

  配置项:
  - baseURL: 通过环境变量 VITE_API_BASE_URL 配置（默认 http://localhost:8001）
  - 自动注入 Token: 从 localStorage.getItem('access_token') 读取
  - 自动处理 401: 清除登录信息并跳转到登录页

  如需调整:
  - 修改 .env 文件中的 VITE_API_BASE_URL
  - 如改用其他认证方式（如 Cookie），修改 interceptors.request
  - 如需自定义错误处理，修改 interceptors.response

  2. 前端依赖的 API 端点

  当前已对接的端点:

  【认证】
  - POST /api/auth/login - 登录
    请求: {username, password}
    响应: {access_token, user: {...}}

  【会话管理】
  - GET /api/conversations?page=1&page_size=20 - 获取会话列表
    响应: {conversations: [], total, page, page_size}
  
  - POST /api/conversations - 创建新会话
    请求: {title: "新对话"}
    响应: {conversation_id, user_id, title, created_at, ...}
  
  - GET /api/conversations/{id}/messages?page=1&page_size=50 - 获取会话消息
    响应: {messages: [{message_id, role, content, created_at}], total, ...}
  
  - PUT /api/conversations/{id} - 更新会话标题
    请求: {title: "新标题"}
    响应: {conversation_id, title, ...}
  
  - DELETE /api/conversations/{id} - 删除会话
    响应: 204 No Content

  【对话】
  - POST /api/unified/chat - 发送消息
    请求: {query, user_id, conversation_id}
    响应: {answer, conversation_id, route, user_id}

  3. 前端期望的数据格式

  重要: 后端返回的数据必须符合以下 TypeScript 接口

  位置: frontend/src/types/conversation.ts

  Conversation 对象:
  {
    conversation_id: string       // 会话ID
    user_id: string              // 用户ID
    title: string | null         // 会话标题
    created_at: string           // ISO8601 时间戳
    updated_at: string           // ISO8601 时间戳
    last_message_at: string | null  // ISO8601 时间戳
  }

  Message 对象:
  {
    message_id: number           // 消息ID
    conversation_id: string      // 所属会话ID
    role: 'user' | 'assistant' | 'system'  // 角色（必须是这三个之一）
    content: string              // 消息内容
    created_at: string           // ISO8601 时间戳
  }

  分页响应格式:
  {
    conversations: Conversation[]  // 或 messages: Message[]
    total: number                 // 总数量
    page: number                  // 当前页码
    page_size: number             // 每页数量
  }

  4. 认证 Token 格式

  前端发送:
  - Header: Authorization: Bearer <jwt_token>
  - Token 来源: localStorage.getItem('access_token')

  前端存储:
  - access_token: JWT token 字符串
  - user_info: JSON.stringify(user对象)

  User 对象结构:
  {
    user_id: string
    username: string
    email: string
    full_name: string
    department: string
    position: string
    is_executive: boolean
    is_active: boolean
    is_admin: boolean
    phone: string
  }

  5. 错误处理约定

  后端应返回的 HTTP 状态码:
  - 200: 成功
  - 401: 未授权（Token 无效/过期）→ 前端自动登出
  - 403: 权限不足
  - 404: 资源不存在
  - 422: 参数验证失败
  - 500: 服务器错误

  错误响应格式建议:
  {
    "error": "错误信息",
    "detail": "详细错误描述（可选）",
    "code": "ERROR_CODE（可选）"
  }

  6. 如需修改通信层

  场景A: 修改 API 路径
  - 后端改变路径（如 /api/v2/...）
  - 修改位置: frontend/src/api/conversations.ts 中的所有 URL
  - 或修改 baseURL: frontend/src/api/client.ts

  场景B: 修改请求/响应格式
  - 更新 frontend/src/types/conversation.ts 中的接口定义
  - 修改 frontend/src/api/conversations.ts 中的请求体和响应处理
  - 如需转换数据格式，在 API 函数中添加映射逻辑

  场景C: 改用 WebSocket/SSE 实时通信
  - 当前使用 HTTP 轮询
  - 需新建 frontend/src/api/websocket.ts 或 sse.ts
  - 修改 App.tsx 中的 handleSend 函数使用新的通信方式
  - 参考文档中的"Phase 5: 流式响应（SSE）"章节

  场景D: 改用 GraphQL
  - 需安装: npm install @apollo/client graphql
  - 替换 frontend/src/api/client.ts 为 Apollo Client
  - 重写 frontend/src/api/conversations.ts 为 GraphQL queries
  - 修改 useConversations Hook 使用 useQuery/useMutation

  7. 调试工具

  前端调试:
  - 浏览器 DevTools → Network 查看请求/响应
  - 浏览器 Console 查看错误日志
  - React DevTools 查看组件状态

  后端调试:
  - 确认端口: 后端应运行在 8001 端口
  - 检查 CORS 配置: allow_origins 应包含前端地址
  - Token 验证: 确认后端正确解析 Authorization header

  8. 环境变量配置

  前端 (.env):
  VITE_API_BASE_URL=http://localhost:8001

  生产环境部署时改为:
  VITE_API_BASE_URL=https://your-backend-domain.com

  后端 (.env):
  # 确认 CORS 配置允许前端域名访问
  CORS_ORIGINS=http://localhost:5173,https://your-frontend-domain.com

  ---
  📡 API 接口文档

  认证相关

  POST /api/auth/login

  请求:
  {
    "username": "employee",
    "password": "test123456"
  }

  响应:
  {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "user": {
      "user_id": "user_001",
      "username": "employee",
      "email": "employee@company.com",
      "full_name": "张三",
      "department": "技术部",
      "position": "工程师",
      "is_executive": false,
      "is_active": true,
      "is_admin": false,
      "phone": "13800138001"
    }
  }

  GET /api/auth/me

  Headers:
  Authorization: Bearer <token>

  响应: 同上 user 对象

  PUT /api/auth/me

  Headers:
  Authorization: Bearer <token>

  请求:
  {
    "full_name": "新名字",
    "phone": "13900139000"
  }

  响应: 更新后的 user 对象

  ---
  会话管理

  GET /api/conversations

  Query 参数:
  - page: 页码（默认 1）
  - page_size: 每页数量（默认 20）

  Headers:
  Authorization: Bearer <token>

  响应:
  {
    "conversations": [
      {
        "conversation_id": "conv_abc123",
        "user_id": "user_001",
        "title": "北京差旅咨询",
        "created_at": "2026-07-20T10:30:00",
        "updated_at": "2026-07-20T11:45:00",
        "last_message_at": "2026-07-20T11:45:00"
      }
    ],
    "total": 15,
    "page": 1,
    "page_size": 20
  }

  POST /api/conversations

  Headers:
  Authorization: Bearer <token>

  请求:
  {
    "title": "新对话"
  }

  响应: 单个 conversation 对象

  GET /api/conversations/{conversation_id}

  Headers:
  Authorization: Bearer <token>

  响应:
  {
    "conversation_id": "conv_abc123",
    "user_id": "user_001",
    "title": "北京差旅咨询",
    "created_at": "2026-07-20T10:30:00",
    "updated_at": "2026-07-20T11:45:00",
    "last_message_at": "2026-07-20T11:45:00",
    "messages": [
      {
        "message_id": 1,
        "conversation_id": "conv_abc123",
        "role": "user",
        "content": "北京的住宿标准是多少？",
        "created_at": "2026-07-20T10:30:00"
      },
      {
        "message_id": 2,
        "conversation_id": "conv_abc123",
        "role": "assistant",
        "content": "根据公司政策...",
        "created_at": "2026-07-20T10:30:15"
      }
    ]
  }

  GET /api/conversations/{conversation_id}/messages

  Query 参数:
  - page: 页码（默认 1）
  - page_size: 每页数量（默认 50）

  Headers:
  Authorization: Bearer <token>

  响应:
  {
    "messages": [...],
    "total": 24,
    "page": 1,
    "page_size": 50
  }

  PUT /api/conversations/{conversation_id}

  Headers:
  Authorization: Bearer <token>

  请求:
  {
    "title": "更新后的标题"
  }

  响应: 更新后的 conversation 对象

  DELETE /api/conversations/{conversation_id}

  Headers:
  Authorization: Bearer <token>

  响应:
  {
    "message": "会话已删除"
  }

  ---
  智能对话

  POST /api/unified/chat

  Headers:
  Authorization: Bearer <token>

  请求:
  {
    "query": "北京的住宿标准是多少？",
    "user_id": "user_001",
    "conversation_id": "conv_abc123"
  }

  响应:
  {
    "answer": "根据公司差旅政策，北京地区的住宿标准为...",
    "route": "fast_path",
    "user_id": "user_001",
    "conversation_id": "conv_abc123"
  }

  ---
  ⚙️ 开发环境配置

  前提条件

  - Node.js >= 18
  - Python >= 3.10
  - PostgreSQL >= 14
  - Redis >= 6（可选）

  后端启动

  # 1. 安装依赖
  pip install -r requirements.txt

  # 2. 配置环境变量
  cp .env.example .env
  # 编辑 .env，填入数据库密码和 API Key

  # 3. 初始化数据库
  psql -U postgres -d business_trip -f scripts/init_db.sql

  # 4. 启动服务
  python -m uvicorn src.api.unified_api:app --host 0.0.0.0 --port 8001 --reload

  前端启动

  cd frontend

  # 1. 安装依赖
  npm install

  # 2. 配置环境变量
  cp .env.example .env
  # 确认 VITE_API_BASE_URL=http://localhost:8001

  # 3. 启动开发服务器
  npm run dev

  # 4. 访问
  # http://localhost:5173

  环境变量说明

  后端 .env:
  # LLM API
  DASHSCOPE_API_KEY=sk-xxx            # 必需：通义千问 API Key

  # 数据库
  DB_HOST=localhost
  DB_PORT=5432
  DB_NAME=business_trip
  DB_USER=postgres
  DB_PASSWORD=your_password           # 必需：数据库密码

  # JWT
  JWT_SECRET_KEY=your-secret-key      # 必需：JWT 密钥

  # 飞书（可选）
  FEISHU_WEBHOOK_KEY=xxx              # 可选：飞书通知

  # 监控（可选）
  LANGCHAIN_API_KEY=xxx               # 可选：LangSmith 追踪
  LANGCHAIN_TRACING_V2=true

  前端 .env:
  VITE_API_BASE_URL=http://localhost:8001
  VITE_ENV=development

  ---
  📂 关键文件说明

  后端关键文件

  ┌───────────────────────────────────┬────────────────┬──────────────────────────┐
  │             文件路径              │      说明      │         核心功能         │
  ├───────────────────────────────────┼────────────────┼──────────────────────────┤
  │ src/api/unified_api.py            │ API 主入口     │ 路由注册、启动配置       │
  ├───────────────────────────────────┼────────────────┼──────────────────────────┤
  │ src/api/auth_api.py               │ 认证路由       │ 登录、注册、Token 管理   │
  ├───────────────────────────────────┼────────────────┼──────────────────────────┤
  │ src/api/conversation_api.py       │ 会话路由       │ 会话 CRUD、消息管理      │
  ├───────────────────────────────────┼────────────────┼──────────────────────────┤
  │ src/agents/orchestrator_agent.py  │ 统一路由 Agent │ 意图识别、路径分发       │
  ├───────────────────────────────────┼────────────────┼──────────────────────────┤
  │ src/agents/qa_engine.py           │ Q&A 域引擎     │ 政策查询、RAG 检索       │
  ├───────────────────────────────────┼────────────────┼──────────────────────────┤
  │ src/agents/approval_engine.py     │ 审批域引擎     │ 报销审批、LangGraph 流程 │
  ├───────────────────────────────────┼────────────────┼──────────────────────────┤
  │ src/services/user_service.py      │ 用户服务层     │ 用户业务逻辑             │
  ├───────────────────────────────────┼────────────────┼──────────────────────────┤
  │ src/database/user_repository.py   │ 用户数据访问   │ SQL 查询封装             │
  ├───────────────────────────────────┼────────────────┼──────────────────────────┤
  │ src/auth/jwt_handler.py           │ JWT 处理       │ Token 生成/验证          │
  ├───────────────────────────────────┼────────────────┼──────────────────────────┤
  │ src/middleware/auth_middleware.py │ 认证中间件     │ 请求拦截、Token 验证     │
  ├───────────────────────────────────┼────────────────┼──────────────────────────┤
  │ scripts/init_db.sql               │ 数据库初始化   │ 表结构、测试数据         │
  └───────────────────────────────────┴────────────────┴──────────────────────────┘

  前端关键文件

  ┌────────────────────┬───────────────┬────────────────────────┐
  │      文件路径      │     说明      │        核心功能        │
  ├────────────────────┼───────────────┼────────────────────────┤
  │ src/App.tsx        │ 主应用组件    │ 登录+对话界面          │
  ├────────────────────┼───────────────┼────────────────────────┤
  │ src/main.tsx       │ 应用入口      │ React 挂载、Toast 配置 │
  ├────────────────────┼───────────────┼────────────────────────┤
  │ src/index.css      │ 全局样式      │ 旅行文档设计系统       │
  ├────────────────────┼───────────────┼────────────────────────┤
  │ tailwind.config.js │ Tailwind 配置 │ 主题扩展               │
  ├────────────────────┼───────────────┼────────────────────────┤
  │ vite.config.ts     │ Vite 配置     │ 开发服务器、代理       │
  ├────────────────────┼───────────────┼────────────────────────┤
  │ .env               │ 环境变量      │ API 地址配置           │
  └────────────────────┴───────────────┴────────────────────────┘

  ---
  🐛 常见问题处理

  问题 1: 登录后对话请求返回 401

  原因: 未携带 Authorization 头

  解决: 参考 立即修复事项 #1

  ---
  问题 2: CORS 错误

  症状:
  Access to fetch at 'http://localhost:8001/api/...' from origin 'http://localhost:5173'
  has been blocked by CORS policy

  原因: 后端 CORS 配置问题

  解决:

  检查 src/api/unified_api.py 中的 CORS 配置：
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["*"],  # 开发环境允许所有来源
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )

  生产环境应限制为前端域名：
  allow_origins=["https://your-frontend-domain.com"],

  ---
  问题 3: 数据库连接失败

  症状:
  psycopg2.OperationalError: could not connect to server

  解决:

  1. 确认 PostgreSQL 服务运行：
  # Windows
  net start postgresql-x64-14

  # Linux/Mac
  sudo systemctl start postgresql

  2. 检查 .env 配置：
  DB_HOST=localhost
  DB_PORT=5432
  DB_NAME=business_trip
  DB_USER=postgres
  DB_PASSWORD=正确的密码

  3. 测试连接：
  psql -U postgres -d business_trip -c "SELECT 1"

  ---
  问题 4: Token 过期处理

  症状: 登录后一段时间请求返回 401

  原因: JWT Token 过期（默认 24 小时）

  解决: 前端自动跳转登录页（已在修复方案中实现）

  后端配置 (src/auth/jwt_handler.py):
  # 修改过期时间
  ACCESS_TOKEN_EXPIRE_HOURS = 24  # 改为 48 小时

  ---
  问题 5: 中文乱码

  症状: 数据库查询返回乱码

  解决:

  1. 确认数据库编码：
  SHOW SERVER_ENCODING;  -- 应为 UTF8

  2. 设置客户端编码：
  # src/database/db_config.py
  self.config = {
      'host': os.getenv('DB_HOST', 'localhost'),
      'port': int(os.getenv('DB_PORT', '5432')),
      'database': os.getenv('DB_NAME', 'business_trip'),
      'user': os.getenv('DB_USER', 'postgres'),
      'password': os.getenv('DB_PASSWORD', ''),
      'client_encoding': 'utf8'  # 添加此行
  }

  ---
  问题 6: 前端热重载不生效

  原因: Vite 监听文件变化失败

  解决:

  检查 vite.config.ts：
  export default defineConfig({
    plugins: [react()],
    server: {
      port: 5173,
      watch: {
        usePolling: true,  // 添加此行（Windows 环境）
      },
    },
  })

  ---
  📊 进度追踪表

  ┌──────────┬─────────────────────┬─────────────┬──────────┬───────────┬────────────┐
  │   阶段   │        任务         │   优先级    │ 预估时间 │   状态    │  完成日期  │
  ├──────────┼─────────────────────┼─────────────┼──────────┼───────────┼────────────┤
  │ 立即修复 │ 修复 Token 携带问题 │ 🔴 CRITICAL │ 5 分钟   │ ✅ 已完成 │ 2026-07-20 │
  ├──────────┼─────────────────────┼─────────────┼──────────┼───────────┼────────────┤
  │ Phase 2  │ 会话列表侧边栏      │ 🔴 HIGH     │ 2 小时   │ ✅ 已完成 │ 2026-07-20 │
  ├──────────┼─────────────────────┼─────────────┼──────────┼───────────┼────────────┤
  │ Phase 2  │ 新建/切换会话       │ 🔴 HIGH     │ 1.5 小时 │ ✅ 已完成 │ 2026-07-20 │
  ├──────────┼─────────────────────┼─────────────┼──────────┼───────────┼────────────┤
  │ Phase 2  │ 删除会话功能        │ 🔴 HIGH     │ 1 小时   │ ✅ 已完成 │ 2026-07-20 │
  ├──────────┼─────────────────────┼─────────────┼──────────┼───────────┼────────────┤
  │ Phase 2  │ 会话标题管理        │ 🔴 HIGH     │ 1 小时   │ 🟡 部分   │ 2026-07-20 │
  ├──────────┼─────────────────────┼─────────────┼──────────┼───────────┼────────────┤
  │ Phase 3  │ Markdown 渲染       │ 🟡 MEDIUM   │ 3 小时   │ ❌ 待处理 │ -          │
  ├──────────┼─────────────────────┼─────────────┼──────────┼───────────┼────────────┤
  │ Phase 3  │ 消息操作功能        │ 🟡 MEDIUM   │ 3 小时   │ ❌ 待处理 │ -          │
  ├──────────┼─────────────────────┼─────────────┼──────────┼───────────┼────────────┤
  │ Phase 4  │ 个人资料页          │ 🟡 MEDIUM   │ 4 小时   │ ❌ 待处理 │ -          │
  ├──────────┼─────────────────────┼─────────────┼──────────┼───────────┼────────────┤
  │ Phase 4  │ 响应式设计          │ 🟡 MEDIUM   │ 3 小时   │ ❌ 待处理 │ -          │
  ├──────────┼─────────────────────┼─────────────┼──────────┼───────────┼────────────┤
  │ Phase 4  │ 暗色模式            │ 🟡 MEDIUM   │ 2 小时   │ ❌ 待处理 │ -          │
  ├──────────┼─────────────────────┼─────────────┼──────────┼───────────┼──────────┤
  │ Phase 5  │ 流式响应            │ 🟢 LOW      │ 4 小时   │ ❌ 待处理 │ -        │
  ├──────────┼─────────────────────┼─────────────┼──────────┼───────────┼──────────┤
  │ **       │                     │             │          │           │          │