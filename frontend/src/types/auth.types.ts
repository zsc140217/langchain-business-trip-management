export interface User {
  user_id: string
  username: string
  email: string
  full_name: string
  department: string | null
  position: string | null
  phone: string | null
  is_executive: boolean
  is_active: boolean
  is_admin: boolean
  created_at: string
  updated_at: string
}

export interface UserCreate {
  username: string
  email: string
  password: string
  full_name: string
  department?: string
  position?: string
  phone?: string
  is_executive?: boolean
  is_admin?: boolean
}

export interface UserLogin {
  username: string
  password: string
}

export interface Token {
  access_token: string
  token_type: string
  expires_in: number
  user: User
}
