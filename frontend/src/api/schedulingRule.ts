import { get, post, put, del } from './request'
import type { SchedulingRule, SchedulingRuleCreate, SchedulingRuleUpdate, PageParams, PageResult } from '@/types'

export function getSchedulingRuleList(params: PageParams): Promise<PageResult<SchedulingRule>> {
  return get<PageResult<SchedulingRule>>('/scheduling-rules', params)
}

export function getDefaultRule(): Promise<SchedulingRule> {
  return get<SchedulingRule>('/scheduling-rules/default')
}

export function getSchedulingRuleDetail(id: number): Promise<SchedulingRule> {
  return get<SchedulingRule>(`/scheduling-rules/${id}`)
}

export function createSchedulingRule(data: SchedulingRuleCreate): Promise<SchedulingRule> {
  return post<SchedulingRule>('/scheduling-rules', data)
}

export function updateSchedulingRule(id: number, data: SchedulingRuleUpdate): Promise<SchedulingRule> {
  return put<SchedulingRule>(`/scheduling-rules/${id}`, data)
}

export function setDefaultRule(id: number): Promise<SchedulingRule> {
  return put<SchedulingRule>(`/scheduling-rules/${id}/set-default`)
}

export function deleteSchedulingRule(id: number): Promise<null> {
  return del<null>(`/scheduling-rules/${id}`)
}
