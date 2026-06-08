import { get } from './request'
import type { CatRoom, PageParams, PageResult } from '@/types'

export interface CatRoomQueryParams extends PageParams {
  status?: string
  min_price?: number
  max_price?: number
  check_in_date?: string
  check_out_date?: string
}

export function getCatRoomList(params: CatRoomQueryParams): Promise<PageResult<CatRoom>> {
  return get<PageResult<CatRoom>>('/cat-rooms', params)
}

export function getAvailableCatRooms(check_in_date: string, check_out_date: string): Promise<CatRoom[]> {
  return get<CatRoom[]>('/cat-rooms/availability', { check_in_date, check_out_date })
}

export function getCatRoomDetail(id: number): Promise<CatRoom> {
  return get<CatRoom>(`/cat-rooms/${id}`)
}
