import { useState, useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import { Plane, Send, Loader2, User, Bot, MapPin, Stamp, Compass, MessageCircle, LogIn, FileText } from 'lucide-react'
import toast from 'react-hot-toast'
import Sidebar from './components/Sidebar'
import ReimbursementHistory from './components/ReimbursementHistory'
import InvoiceUploadButton from './components/InvoiceUploadButton'
import InvoiceResultCard from './components/InvoiceResultCard'
import ApprovalStatusCard from './components/ApprovalStatusCard'
import { getConversationMessages } from './api/conversations'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'

interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  invoiceData?: any
  approvalStatus?: any
}

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  // Navigation state
  const [currentView, setCurrentView] = useState<'chat' | 'history'>('chat')

  // Chat state
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isSending, setIsSending] = useState(false)
  const [conversationId, setConversationId] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    // Check if already logged in
    const token = localStorage.getItem('access_token')
    if (token) {
      setIsLoggedIn(true)
    }
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)

    try {
      const response = await fetch(`${API_BASE}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      })

      if (response.ok) {
        const data = await response.json()
        localStorage.setItem('access_token', data.access_token)
        localStorage.setItem('user_info', JSON.stringify(data.user))
        setIsLoggedIn(true)
        toast.success(`欢迎回来，${data.user.full_name}！`)
      } else {
        toast.error('用户名或密码错误')
      }
    } catch (error) {
      toast.error('网络连接失败，请检查后端服务')
    } finally {
      setIsLoading(false)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user_info')
    setIsLoggedIn(false)
    setMessages([])
    setConversationId(null)
    setCurrentView('chat')
    toast.success('已安全登出')
  }

  // Switch conversation
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
      console.error(error)
    }
  }

  // New conversation
  const handleNewConversation = () => {
    setConversationId(null)
    setMessages([])
  }

  // 处理发票上传成功
  const handleInvoiceUpload = (result: any) => {
    const invoiceMessage: Message = {
      role: 'assistant',
      content: '✅ 发票识别成功！以下是识别结果：',
      timestamp: new Date().toISOString(),
      invoiceData: {
        data: result.invoice_data,
        warnings: result.warnings || [],
        invoiceId: result.invoice_id
      }
    }
    setMessages((prev) => [...prev, invoiceMessage])

    // 自动填充提示
    const promptMessage: Message = {
      role: 'assistant',
      content: '请告诉我出差目的地和天数，我会帮您提交报销申请。\n例如："我要报销去北京出差3天"',
      timestamp: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, promptMessage])
  }

  const handleSend = async () => {
    if (!input.trim() || isSending) return

    const userMessage: Message = {
      role: 'user',
      content: input,
      timestamp: new Date().toISOString(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setIsSending(true)

    try {
      const token = localStorage.getItem('access_token')
      const userInfoStr = localStorage.getItem('user_info')
      const userInfo = userInfoStr ? JSON.parse(userInfoStr) : null

      const response = await fetch(`${API_BASE}/api/unified/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          query: input,
          user_id: userInfo?.user_id || 'employee',
          conversation_id: conversationId,
        }),
      })

      if (response.ok) {
        const data = await response.json()
        setConversationId(data.conversation_id)

        const assistantMessage: Message = {
          role: 'assistant',
          content: data.answer,
          timestamp: new Date().toISOString(),
        }
        setMessages((prev) => [...prev, assistantMessage])
      } else if (response.status === 401) {
        toast.error('登录已过期，请重新登录')
        handleLogout()
      } else {
        toast.error('发送失败，请重试')
      }
    } catch (error) {
      toast.error('网络连接失败')
    } finally {
      setIsSending(false)
    }
  }

  // Login View - Travel Documents Aesthetic
  if (!isLoggedIn) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden">
        {/* Floating Background Elements */}
        <motion.div
          className="absolute top-20 left-10 text-[var(--color-amber)] opacity-10"
          animate={{ x: [0, 100, 0], y: [0, -50, 0], rotate: [0, 10, 0] }}
          transition={{ duration: 20, repeat: Infinity, ease: 'easeInOut' }}
        >
          <Plane size={120} />
        </motion.div>
        <motion.div
          className="absolute bottom-20 right-10 text-[var(--color-navy)] opacity-5"
          animate={{ x: [0, -80, 0], y: [0, 60, 0], rotate: [0, -15, 0] }}
          transition={{ duration: 25, repeat: Infinity, ease: 'easeInOut' }}
        >
          <Compass size={150} />
        </motion.div>

        {/* Login Card */}
        <motion.div
          initial={{ opacity: 0, y: 50, rotate: -2 }}
          animate={{ opacity: 1, y: 0, rotate: 0 }}
          transition={{ duration: 0.8, type: 'spring' }}
          className="relative max-w-md w-full"
        >
          <div className="travel-doc rounded-lg overflow-hidden ticket-edge-left ticket-edge-right">
            {/* Passport Header */}
            <div className="passport-header text-center">
              <Plane className="inline-block mr-2" size={24} />
              <h1 className="inline-block text-xl">智旅助手 · Travel Assistant</h1>
            </div>

            <div className="barcode" />

            {/* Form Content */}
            <div className="p-8 diagonal-stripes relative">
              {/* Stamp */}
              <motion.div
                initial={{ scale: 0, rotate: -15 }}
                animate={{ scale: 1, rotate: -5 }}
                transition={{ delay: 0.5, type: 'spring' }}
                className="absolute top-6 right-6 stamp bg-white text-[var(--color-stamp-red)] text-xs font-bold z-10"
              >
                AUTHORIZED
                <br />
                <span className="text-[10px]">2026.07.15</span>
              </motion.div>

              <h2 className="font-display text-3xl text-[var(--color-navy)] mb-2">欢迎登机</h2>
              <p className="text-[var(--color-navy-lighter)] mb-8">请登录您的差旅管理账户</p>

              <form onSubmit={handleLogin} className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-[var(--color-navy)] mb-2 uppercase tracking-wide">
                    <MapPin size={14} className="inline mr-1" />
                    用户名 / Username
                  </label>
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="w-full px-4 py-3 bg-white border-2 border-[var(--color-navy)] rounded
                             focus:outline-none focus:border-[var(--color-amber)] transition-colors
                             text-[var(--color-navy)]"
                    placeholder="employee"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-[var(--color-navy)] mb-2 uppercase tracking-wide">
                    <Stamp size={14} className="inline mr-1" />
                    密码 / Password
                  </label>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full px-4 py-3 bg-white border-2 border-[var(--color-navy)] rounded
                             focus:outline-none focus:border-[var(--color-amber)] transition-colors
                             text-[var(--color-navy)]"
                    placeholder="••••••••"
                    required
                  />
                </div>

                <div className="fold-line my-8" />

                <motion.button
                  type="submit"
                  disabled={isLoading}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="w-full bg-[var(--color-navy)] text-[var(--color-amber)] py-4 rounded
                           font-display text-lg font-semibold uppercase tracking-widest
                           hover:bg-[var(--color-navy-light)] transition-all
                           disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="animate-spin" size={20} />
                      验证中...
                    </>
                  ) : (
                    <>
                      <LogIn size={20} />
                      登机 / Board
                    </>
                  )}
                </motion.button>

                <div className="mt-6 p-4 bg-[var(--color-paper-dark)] border border-dashed border-[var(--color-amber-dark)] rounded">
                  <p className="text-xs text-[var(--color-navy)] font-medium mb-2">测试账户:</p>
                  <div className="space-y-1 text-xs text-[var(--color-navy-lighter)]">
                    <p>👤 员工: employee / test123456</p>
                    <p>👔 经理: manager / test123456</p>
                    <p>💼 高管: executive / test123456</p>
                  </div>
                </div>
              </form>
            </div>

            <div className="h-3 bg-gradient-to-r from-[var(--color-navy)] via-[var(--color-amber)] to-[var(--color-navy)]" />
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1 }}
          className="absolute bottom-8 text-center w-full"
        >
          <p className="text-sm text-[var(--color-navy-lighter)]">
            基于 LangChain 构建的智能差旅管理系统
          </p>
          <p className="text-xs text-[var(--color-amber-dark)] mt-1">
            Powered by AI · Secured by Design
          </p>
        </motion.div>
      </div>
    )
  }

  // Chat View - After Login
  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <Sidebar
        currentConversationId={conversationId}
        onSelectConversation={handleSelectConversation}
        onNewConversation={handleNewConversation}
      />

      {/* Main content area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="passport-header flex items-center justify-between">
          <div className="flex items-center gap-6">
            {/* Chat Tab */}
            <button
              onClick={() => setCurrentView('chat')}
              className={`flex items-center gap-2 px-4 py-2 rounded transition-colors ${
                currentView === 'chat'
                  ? 'bg-[var(--color-amber)] text-[var(--color-navy)]'
                  : 'text-[var(--color-paper)] hover:bg-[var(--color-navy-light)]'
              }`}
            >
              <MessageCircle size={20} />
              <span className="font-medium">智能对话</span>
            </button>

            {/* History Tab */}
            <button
              onClick={() => setCurrentView('history')}
              className={`flex items-center gap-2 px-4 py-2 rounded transition-colors ${
                currentView === 'history'
                  ? 'bg-[var(--color-amber)] text-[var(--color-navy)]'
                  : 'text-[var(--color-paper)] hover:bg-[var(--color-navy-light)]'
              }`}
            >
              <FileText size={20} />
              <span className="font-medium">历史报销查询</span>
            </button>
          </div>
          <button
            onClick={handleLogout}
            className="px-4 py-2 bg-[var(--color-amber)] text-[var(--color-navy)] rounded font-medium
                     hover:bg-[var(--color-amber-dark)] transition-colors text-sm"
          >
            登出
          </button>
        </header>

        <div className="barcode" />

        {/* Content Area */}
        {currentView === 'chat' ? (
          // Chat Area
          <main className="flex-1 flex flex-col overflow-hidden bg-[var(--color-paper)]">
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.length === 0 ? (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-center mt-20"
            >
              <div className="inline-block p-8 travel-doc rounded-lg corner-fold max-w-lg">
                <MessageCircle size={64} className="text-[var(--color-amber)] mx-auto mb-4" />
                <h2 className="font-display text-2xl text-[var(--color-navy)] mb-2">
                  开始您的智能对话
                </h2>
                <p className="text-[var(--color-navy-lighter)] mb-4">
                  询问政策、提交报销、查询审批状态
                </p>
                <div className="text-sm text-[var(--color-navy-lighter)] space-y-1 text-left">
                  <p>💡 "北京的住宿标准是多少？"</p>
                  <p>✈️ "我要报销去上海出差2天，花了1500元"</p>
                  <p>📋 "我的报销申请审批了吗？"</p>
                </div>
              </div>
            </motion.div>
          ) : (
            messages.map((message, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: message.role === 'user' ? 20 : -20 }}
                animate={{ opacity: 1, x: 0 }}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div className="flex flex-col gap-3">
                  <div
                    className={`max-w-2xl ${
                      message.role === 'user'
                        ? 'bg-[var(--color-navy)] text-[var(--color-paper)]'
                        : 'bg-white text-[var(--color-navy)] travel-doc'
                    } p-4 rounded-lg shadow-document`}
                  >
                    <div className="flex items-center gap-2 mb-2">
                      {message.role === 'user' ? (
                        <User size={16} className="text-[var(--color-amber)]" />
                      ) : (
                        <Bot size={16} className="text-[var(--color-amber)]" />
                      )}
                      <span className="text-xs font-medium uppercase">
                        {message.role === 'user' ? '您' : 'AI 助手'}
                      </span>
                    </div>
                    <p className="whitespace-pre-wrap">{message.content}</p>
                    <p className="text-xs opacity-60 mt-2">
                      {new Date(message.timestamp).toLocaleTimeString('zh-CN')}
                    </p>
                  </div>

                  {/* 显示发票识别结果卡片 */}
                  {message.invoiceData && (
                    <InvoiceResultCard
                      invoiceData={message.invoiceData.data}
                      warnings={message.invoiceData.warnings}
                    />
                  )}

                  {/* 显示审批状态卡片 */}
                  {message.approvalStatus && (
                    <ApprovalStatusCard
                      status={message.approvalStatus.status}
                      currentApprover={message.approvalStatus.currentApprover}
                      applicationId={message.approvalStatus.applicationId}
                      submittedAt={message.approvalStatus.submittedAt}
                    />
                  )}
                </div>
              </motion.div>
            ))
          )}

          {isSending && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex">
              <div className="bg-white p-4 rounded-lg shadow-document travel-doc">
                <div className="flex items-center gap-3">
                  <Loader2 className="animate-spin text-[var(--color-amber)]" size={20} />
                  <span className="text-sm text-[var(--color-navy)]">AI 正在思考...</span>
                </div>
              </div>
            </motion.div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="border-t-2 border-[var(--color-navy)] bg-white p-6 ticket-tear-top">
          <form
            onSubmit={(e) => {
              e.preventDefault()
              handleSend()
            }}
            className="flex gap-3"
          >
            {/* 发票上传按钮 */}
            <InvoiceUploadButton
              onUploadSuccess={handleInvoiceUpload}
              disabled={isSending}
            />

            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="输入您的消息..."
              className="flex-1 px-4 py-3 border-2 border-[var(--color-navy)] rounded
                       focus:outline-none focus:border-[var(--color-amber)] transition-colors
                       text-[var(--color-navy)]"
              disabled={isSending}
            />
            <motion.button
              type="submit"
              disabled={isSending || !input.trim()}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="px-6 py-3 bg-[var(--color-navy)] text-[var(--color-amber)] rounded font-semibold
                       flex items-center gap-2 hover:bg-[var(--color-navy-light)] transition-colors
                       disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send size={18} />
              发送
            </motion.button>
          </form>
        </div>
      </main>
        ) : (
          // History Area
          <main className="flex-1 overflow-y-auto bg-[var(--color-paper)]">
            <ReimbursementHistory />
          </main>
        )}
      </div>
    </div>
  )
}

export default App
