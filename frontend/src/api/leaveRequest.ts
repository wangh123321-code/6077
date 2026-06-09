import { get, post, put, del } from './request'
import type {
  LeaveRequest,
  LeaveRequestCreate,
  LeaveRequestApprove,
  PageParams,
  PageResult
} from '@/types'

export function getLeaveRequestList(params: PageParams & { status?: string; employeeId?: number }): Promise<PageResult<LeaveRequest>> {
  return get<PageResult<LeaveRequest>>('/leave-requests', params)
}

export function getMyLeaveRequests(params: PageParams & { status?: string }): Promise<PageResult<LeaveRequest>> {
  return get<PageResult<LeaveRequest>>('/leave-requests/my', params)
}

export function getLeaveRequestDetail(id: number): Promise<LeaveRequest> {
  return get<LeaveRequest>(`/leave-requests/${id}`)
}

export function createLeaveRequest(data: LeaveRequestCreate): Promise<LeaveRequest> {
  return post<LeaveRequest>('/leave-requests', data)
}

export function approveLeaveRequest(id: number, data: LeaveRequestApprove): Promise<LeaveRequest> {
  return put<LeaveRequest>(`/leave-requests/${id}/approve`, data)
}

export function cancelLeaveRequest(id: number): Promise<LeaveRequest> {
  return put<LeaveRequest>(`/leave-requests/${id}/cancel`)
}

export function deleteLeaveRequest(id: number): Promise<null> {
  return del<null>(`/leave-requests/${id}`)
}
