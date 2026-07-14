 import { useState, useRef, useEffect, useCallback } from 'react'
 import { motion, AnimatePresence } from 'framer-motion'
 import { Send, Bot, User, Loader2, Sparkles } from 'lucide-react'
 
 const API_BASE = 'http://localhost:8000'
 
 interface Message {
   role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: '你好！我是智旅助手，可以帮你查询天气、航班、酒店信息，也可以解答企业差旅政策问题。请问有什么可以帮到你？',
      timestamp: new Date(),
    },
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

 const handleSend = useCallback(async () => {
   if (!input.trim() || isLoading) return

   const userMessage: Message = {
     role: 'user',
     content: input,
     timestamp: new Date(),
   }

   setMessages((prev) => [...prev, userMessage])
   setInput('')
   setIsLoading(true)

   try {
       const response = await fetch(`${API_BASE}/api/chat/sync`, {
         method: 'POST',
         headers: { 'Content-Type': 'application/json' },
         body: JSON.stringify({ query: input }),
       })
 
       if (!response.ok) {
         throw new Error(`API 请求失败: ${response.status}`)
       }
 
       const data = await response.json()
 
       const assistantMessage: Message = {
         role: 'assistant',
         content: data.answer || '抱歉，暂时无法获取回复。',
         timestamp: new Date(),
       }
       setMessages((prev) => [...prev, assistantMessage])
     } catch (error) {
       const errorMessage: Message = {
         role: 'assistant',
         content: `请求失败：${error instanceof Error ? error.message : '未知错误'}。请检查后端服务是否在运行。`,
         timestamp: new Date(),
       }
       setMessages((prev) => [...prev, errorMessage])
     } finally {
       setIsLoading(false)
     }
   }, [input, isLoading])

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="glass-card p-6 h-[calc(100vh-16rem)] flex flex-col"
    >
      {/* Header */}
      <div className="flex items-center gap-3 mb-6 pb-4 border-b border-white/10">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-glow-md animate-glow">
          <Sparkles className="w-5 h-5 text-white" />
        </div>
        <div>
          <h3 className="text-xl font-bold gradient-text">智能对话</h3>
          <p className="text-sm text-gray-400">支持流式响应 · 多轮对话 · 工具调用</p>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto mb-4 space-y-4 pr-2">
        <AnimatePresence>
          {messages.map((message, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className={`flex gap-3 ${message.role === 'user' ? 'flex-row-reverse' : ''}`}
            >
              {/* Avatar */}
              <div
                className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${
                  message.role === 'user'
                    ? 'bg-gradient-to-br from-purple-500 to-pink-600 shadow-glow-purple'
                    : 'bg-gradient-to-br from-cyan-500 to-blue-600 shadow-glow-md'
                }`}
              >
                {message.role === 'user' ? (
                  <User className="w-5 h-5 text-white" />
                ) : (
                  <Bot className="w-5 h-5 text-white" />
                )}
              </div>

              {/* Message Content */}
              <div className={`flex-1 ${message.role === 'user' ? 'items-end' : 'items-start'} flex flex-col`}>
                <div
                  className={`max-w-[80%] rounded-2xl p-4 ${
                    message.role === 'user'
                      ? 'bg-gradient-to-br from-purple-500/20 to-pink-600/20 border border-purple-500/30'
                      : 'bg-white/5 border border-white/10'
                  }`}
                >
                  <p className="text-white leading-relaxed">{message.content}</p>
                </div>
                <span className="text-xs text-gray-500 mt-1">
                  {message.timestamp.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Loading Indicator */}
        {isLoading && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex gap-3"
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-glow-md">
              <Bot className="w-5 h-5 text-white" />
            </div>
            <div className="bg-white/5 border border-white/10 rounded-2xl p-4">
              <Loader2 className="w-5 h-5 text-cyan-400 animate-spin" />
            </div>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="flex gap-3">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="输入消息... (按 Enter 发送)"
          disabled={isLoading}
          className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500 focus:shadow-glow-sm transition-all disabled:opacity-50"
        />
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={handleSend}
          disabled={!input.trim() || isLoading}
          className="px-6 py-3 bg-gradient-to-r from-cyan-500 to-blue-600 rounded-xl text-white font-medium shadow-glow-md hover:shadow-glow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {isLoading ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <>
              <Send className="w-5 h-5" />
              发送
            </>
          )}
        </motion.button>
      </div>
    </motion.div>
  )
}
