import { get, post, put, del } from './request'
import type {
  ShiftPreference,
  ShiftPreferenceCreate,
  PageParams,
  PageResult
} from '@/types'

export function getShiftPreferenceList(params: PageParams & { employeeId?: number }): Promise<PageResult<ShiftPreference>> {
  return get<PageResult<ShiftPreference>>('/shift-preferences', params)
}

export function getMyShiftPreferences(params: PageParams): Promise<PageResult<ShiftPreference>> {
  return get<PageResult<ShiftPreference>>('/shift-preferences/my', params)
}

export function getShiftPreferenceDetail(id: number): Promise<ShiftPreference> {
  return get<ShiftPreference>(`/shift-preferences/${id}`)
}

export function createShiftPreference(data: ShiftPreferenceCreate): Promise<ShiftPreference> {
  return post<ShiftPreference>('/shift-preferences', data)
}

export function updateShiftPreference(id: number, data: Partial<ShiftPreferenceCreate>): Promise<ShiftPreference> {
  return put<ShiftPreference>(`/shift-preferences/${id}`, data)
}

export function deleteShiftPreference(id: number): Promise<null> {
  return del<null>(`/shift-preferences/${id}`)
}
