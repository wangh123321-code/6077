import { post, get } from './request'
import type { User, LoginRequest, RegisterRequest, ApiResponse } from '@/types'

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export function login(data: LoginRequest): Promise<TokenResponse> {
  return post<TokenResponse>('/auth/login', data)
}

export function register(data: RegisterRequest): Promise<User> {
  return post<User>('/auth/register', data)
}

export function logout(): Promise<Record<string, any>> {
  return post<Record<string, any>>('/auth/logout')
}

export function getUserInfo(): Promise<User> {
  return get<User>('/auth/me')
}
