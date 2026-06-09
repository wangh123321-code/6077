import { get, post, put, del } from './request'
import type {
  ShiftSwap,
  ShiftSwapCreate,
  ShiftSwapApprove,
  PageParams,
  PageResult
} from '@/types'

export function getShiftSwapList(params: PageParams & { status?: string; employeeId?: number }): Promise<PageResult<ShiftSwap>> {
  return get<PageResult<ShiftSwap>>('/shift-swaps', params)
}

export function getMyShiftSwaps(params: PageParams & { status?: string }): Promise<PageResult<ShiftSwap>> {
  return get<PageResult<ShiftSwap>>('/shift-swaps/my', params)
}

export function getShiftSwapDetail(id: number): Promise<ShiftSwap> {
  return get<ShiftSwap>(`/shift-swaps/${id}`)
}

export function createShiftSwap(data: ShiftSwapCreate): Promise<ShiftSwap> {
  return post<ShiftSwap>('/shift-swaps', data)
}

export function approveShiftSwap(id: number, data: ShiftSwapApprove): Promise<ShiftSwap> {
  return put<ShiftSwap>(`/shift-swaps/${id}/approve`, data)
}

export function cancelShiftSwap(id: number): Promise<ShiftSwap> {
  return put<ShiftSwap>(`/shift-swaps/${id}/cancel`)
}

export function deleteShiftSwap(id: number): Promise<null> {
  return del<null>(`/shift-swaps/${id}`)
}
