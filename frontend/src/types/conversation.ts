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

export interface MessageListResponse {
  messages: Message[]
  total: number
  page: number
  page_size: number
}
