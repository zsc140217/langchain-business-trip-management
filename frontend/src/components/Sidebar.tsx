import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Plus, MessageCircle, Trash2, ChevronLeft, ChevronRight } from 'lucide-react'
import { useConversations } from '../hooks/useConversations'

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

      // If deleted current conversation, switch to latest conversation
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
      {/* Toggle button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed top-20 left-4 z-50 w-10 h-10 bg-[var(--color-navy)] text-[var(--color-amber)]
                   rounded-lg flex items-center justify-center hover:bg-[var(--color-navy-light)]
                   transition-colors shadow-document"
      >
        {isOpen ? <ChevronLeft size={20} /> : <ChevronRight size={20} />}
      </button>

      {/* Sidebar */}
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
            {/* Header: New conversation button */}
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

            {/* Conversation list */}
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

                    {/* Delete button */}
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

              {/* Load more */}
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
