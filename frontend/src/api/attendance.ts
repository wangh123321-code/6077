import { get, post, put } from './request'
import type {
  Attendance,
  AttendanceCheckIn,
  AttendanceCheckOut,
  AttendanceStats,
  AttendanceReportRequest,
  AttendanceCalendarItem,
  AttendanceAlert,
  PageParams,
  PageResult
} from '@/types'

export function getAttendanceList(params: PageParams & { startDate?: string; endDate?: string; employeeId?: number; status?: string }): Promise<PageResult<Attendance>> {
  return get<PageResult<Attendance>>('/attendances', params)
}

export function getAttendanceCalendar(startDate: string, endDate: string, employeeId?: number): Promise<AttendanceCalendarItem[]> {
  const params: Record<string, any> = { startDate, endDate }
  if (employeeId) params.employeeId = employeeId
  return get<AttendanceCalendarItem[]>('/attendances/calendar', params)
}

export function getMyAttendanceCalendar(startDate: string, endDate: string): Promise<AttendanceCalendarItem[]> {
  return get<AttendanceCalendarItem[]>('/attendances/my-calendar', { startDate, endDate })
}

export function getTodayAttendance(employeeId?: number): Promise<Attendance> {
  const params = employeeId ? { employeeId } : {}
  return get<Attendance>('/attendances/today', params)
}

export function getMyTodayAttendance(): Promise<Attendance> {
  return get<Attendance>('/attendances/my-today')
}

export function getAttendanceDetail(id: number): Promise<Attendance> {
  return get<Attendance>(`/attendances/${id}`)
}

export function checkIn(data?: AttendanceCheckIn): Promise<Attendance> {
  return post<Attendance>('/attendances/check-in', data)
}

export function checkOut(data?: AttendanceCheckOut): Promise<Attendance> {
  return post<Attendance>('/attendances/check-out', data)
}

export function getAttendanceReport(params: AttendanceReportRequest): Promise<AttendanceStats[]> {
  return get<AttendanceStats[]>('/attendances/report', params)
}

export function getMyAttendanceReport(startDate: string, endDate: string): Promise<AttendanceStats> {
  return get<AttendanceStats>('/attendances/my-report', { startDate, endDate })
}

export function getAttendanceAlerts(params: PageParams & { isRead?: boolean; employeeId?: number }): Promise<PageResult<AttendanceAlert>> {
  return get<PageResult<AttendanceAlert>>('/attendances/alerts', params)
}

export function getMyAttendanceAlerts(params: PageParams & { isRead?: boolean }): Promise<PageResult<AttendanceAlert>> {
  return get<PageResult<AttendanceAlert>>('/attendances/my-alerts', params)
}

export function markAlertAsRead(id: number): Promise<AttendanceAlert> {
  return put<AttendanceAlert>(`/attendances/alerts/${id}/read`)
}

export function markAllAlertsAsRead(): Promise<{ count: number }> {
  return put<{ count: number }>('/attendances/alerts/read-all')
}

export function sendDailyReminders(): Promise<{ sent: number; failed: number }> {
  return post<{ sent: number; failed: number }>('/attendances/send-reminders')
}
