import { get, post, put, del } from './request'
import type {
  Schedule,
  ScheduleCreate,
  ScheduleUpdate,
  ScheduleSwapRequest,
  ScheduleGenerateRequest,
  ScheduleConflictCheckRequest,
  ScheduleConflict,
  ScheduleCalendarItem,
  PageParams,
  PageResult
} from '@/types'

export function getScheduleList(params: PageParams & { startDate?: string; endDate?: string; employeeId?: number }): Promise<PageResult<Schedule>> {
  return get<PageResult<Schedule>>('/schedules', params)
}

export function getScheduleCalendar(startDate: string, endDate: string, employeeId?: number): Promise<ScheduleCalendarItem[]> {
  const params: Record<string, any> = { startDate, endDate }
  if (employeeId) params.employeeId = employeeId
  return get<ScheduleCalendarItem[]>('/schedules/calendar', params)
}

export function getMyScheduleCalendar(startDate: string, endDate: string): Promise<ScheduleCalendarItem[]> {
  return get<ScheduleCalendarItem[]>('/schedules/my-calendar', { startDate, endDate })
}

export function getScheduleDetail(id: number): Promise<Schedule> {
  return get<Schedule>(`/schedules/${id}`)
}

export function createSchedule(data: ScheduleCreate): Promise<Schedule> {
  return post<Schedule>('/schedules', data)
}

export function updateSchedule(id: number, data: ScheduleUpdate): Promise<Schedule> {
  return put<Schedule>(`/schedules/${id}`, data)
}

export function deleteSchedule(id: number): Promise<null> {
  return del<null>(`/schedules/${id}`)
}

export function generateSchedules(data: ScheduleGenerateRequest): Promise<Schedule[]> {
  return post<Schedule[]>('/schedules/generate', data)
}

export function checkScheduleConflict(data: ScheduleConflictCheckRequest): Promise<ScheduleConflict> {
  return post<ScheduleConflict>('/schedules/check-conflict', data)
}

export function swapSchedule(data: ScheduleSwapRequest): Promise<Schedule> {
  return post<Schedule>('/schedules/swap', data)
}

export function confirmSchedule(id: number): Promise<Schedule> {
  return put<Schedule>(`/schedules/${id}/confirm`)
}

export function batchConfirmSchedules(ids: number[]): Promise<Schedule[]> {
  return put<Schedule[]>('/schedules/batch-confirm', { ids })
}
