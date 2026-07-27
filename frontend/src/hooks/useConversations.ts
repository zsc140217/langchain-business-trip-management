import { useState, useEffect } from 'react'
import { getConversations, createConversation, deleteConversation } from '../api/conversations'
import type { Conversation } from '../types/conversation'
import toast from 'react-hot-toast'

export const useConversations = () => {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [loading, setLoading] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const [hasMore, setHasMore] = useState(true)

  // Load conversation list
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

      setHasMore(data.conversations.length + (page - 1) * 20 < data.total)
      setCurrentPage(page)
    } catch (error) {
      toast.error('加载会话列表失败')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  // Create new conversation
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

  // Delete conversation
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

  // Load more
  const loadMore = () => {
    if (hasMore && !loading) {
      loadConversations(currentPage + 1)
    }
  }

  // Initial load
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
