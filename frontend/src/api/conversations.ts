import apiClient from './client'
import type {
  Conversation,
  ConversationListResponse,
  MessageListResponse,
} from '../types/conversation'

// Get conversation list
export const getConversations = async (page = 1, pageSize = 20) => {
  const response = await apiClient.get<ConversationListResponse>('/api/conversations', {
    params: { page, page_size: pageSize },
  })
  return response.data
}

// Create new conversation
export const createConversation = async (title?: string) => {
  const response = await apiClient.post<Conversation>('/api/conversations', {
    title: title || '新对话',
  })
  return response.data
}

// Get conversation details
export const getConversation = async (conversationId: string) => {
  const response = await apiClient.get<Conversation>(`/api/conversations/${conversationId}`)
  return response.data
}

// Get conversation messages
export const getConversationMessages = async (
  conversationId: string,
  page = 1,
  pageSize = 50
) => {
  const response = await apiClient.get<MessageListResponse>(
    `/api/conversations/${conversationId}/messages`,
    { params: { page, page_size: pageSize } }
  )
  return response.data
}

// Update conversation title
export const updateConversationTitle = async (conversationId: string, title: string) => {
  const response = await apiClient.put<Conversation>(`/api/conversations/${conversationId}`, {
    title,
  })
  return response.data
}

// Delete conversation
export const deleteConversation = async (conversationId: string) => {
  await apiClient.delete(`/api/conversations/${conversationId}`)
}
