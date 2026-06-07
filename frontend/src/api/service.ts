import { get } from './request'
import type { Service, PageParams, PageResult } from '@/types'

export interface ServiceQueryParams extends PageParams {
  category?: string
}

export function getServiceList(params: ServiceQueryParams): Promise<PageResult<Service>> {
  return get<PageResult<Service>>('/services', params)
}

export function getServiceDetail(id: number): Promise<Service> {
  return get<Service>(`/services/${id}`)
}

export function getServiceCategories(): Promise<{ category: string; count: number }[]> {
  return get<{ category: string; count: number }[]>('/services/categories')
}
