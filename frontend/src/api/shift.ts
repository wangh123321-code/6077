import { get, post, put, del } from './request'
import type { Shift, ShiftCreate, ShiftUpdate, PageParams, PageResult } from '@/types'

export function getShiftList(params: PageParams): Promise<PageResult<Shift>> {
  return get<PageResult<Shift>>('/shifts', params)
}

export function getAllShifts(): Promise<Shift[]> {
  return get<Shift[]>('/shifts/all')
}

export function getShiftDetail(id: number): Promise<Shift> {
  return get<Shift>(`/shifts/${id}`)
}

export function createShift(data: ShiftCreate): Promise<Shift> {
  return post<Shift>('/shifts', data)
}

export function updateShift(id: number, data: ShiftUpdate): Promise<Shift> {
  return put<Shift>(`/shifts/${id}`, data)
}

export function deleteShift(id: number): Promise<null> {
  return del<null>(`/shifts/${id}`)
}
