import { get, post } from './request'
import type { Member, ApiResponse } from '@/types'

export function getMemberInfo(): Promise<Member> {
  return get<Member>('/member/info')
}

export function getMemberPointsHistory(params: { page: number; pageSize: number }): Promise<{
  items: { id: number; type: string; points: number; description: string; createdAt: string }[]
  total: number
}> {
  return get<{
    items: { id: number; type: string; points: number; description: string; createdAt: string }[]
    total: number
  }>('/member/points/history', params)
}

export function exchangePoints(data: { points: number; giftId: number }): Promise<ApiResponse<null>> {
  return post<ApiResponse<null>>('/member/points/exchange', data)
}

export function getMemberGifts(): Promise<{ id: number; name: string; points: number; image: string; stock: number }[]> {
  return get<{ id: number; name: string; points: number; image: string; stock: number }[]>('/member/gifts')
}

export function upgradeMember(data: { level: number }): Promise<ApiResponse<null>> {
  return post<ApiResponse<null>>('/member/upgrade', data)
}
