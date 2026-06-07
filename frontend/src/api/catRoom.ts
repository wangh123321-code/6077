import { get } from './request'
import type { CatRoom, PageParams, PageResult } from '@/types'

export interface CatRoomQueryParams extends PageParams {
  type?: string
  size?: string
  status?: string
  minPrice?: number
  maxPrice?: number
  checkInDate?: string
  checkOutDate?: string
}

export function getCatRoomList(params: CatRoomQueryParams): Promise<PageResult<CatRoom>> {
  return get<PageResult<CatRoom>>('/cat-rooms', params)
}

export function getCatRoomDetail(id: number): Promise<CatRoom> {
  return get<CatRoom>(`/cat-rooms/${id}`)
}

export function getCatRoomAvailability(id: number, checkInDate: string, checkOutDate: string): Promise<{ available: boolean }> {
  return get<{ available: boolean }>(`/cat-rooms/${id}/availability`, { checkInDate, checkOutDate })
}

export function getCatRoomTypes(): Promise<{ type: string; count: number }[]> {
  return get<{ type: string; count: number }[]>('/cat-rooms/types')
}
