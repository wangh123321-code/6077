import { post, get, put } from './request'
import type { User, LoginRequest, RegisterRequest } from '@/types'

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

export function updateUserInfo(data: Partial<User>): Promise<User> {
  return put<User>('/auth/me', data)
}

export function changePassword(data: { oldPassword: string; newPassword: string }): Promise<Record<string, any>> {
  return post<Record<string, any>>('/auth/change-password', data)
}
