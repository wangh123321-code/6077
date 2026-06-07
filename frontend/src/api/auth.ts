import { post, get, put } from './request'
import type { User, LoginRequest, RegisterRequest, ApiResponse } from '@/types'

export interface LoginResponse {
  token: string
  user: User
}

export function login(data: LoginRequest): Promise<LoginResponse> {
  return post<LoginResponse>('/auth/login', data)
}

export function register(data: RegisterRequest): Promise<ApiResponse<null>> {
  return post<ApiResponse<null>>('/auth/register', data)
}

export function logout(): Promise<ApiResponse<null>> {
  return post<ApiResponse<null>>('/auth/logout')
}

export function getUserInfo(): Promise<User> {
  return get<User>('/auth/info')
}

export function updateUserInfo(data: Partial<User>): Promise<User> {
  return put<User>('/auth/info', data)
}

export function changePassword(data: { oldPassword: string; newPassword: string }): Promise<ApiResponse<null>> {
  return post<ApiResponse<null>>('/auth/password', data)
}
