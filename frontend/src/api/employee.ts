import { get, post, put, del } from './request'
import type { Employee, EmployeeCreate, EmployeeUpdate, PageParams, PageResult } from '@/types'

export function getEmployeeList(params: PageParams): Promise<PageResult<Employee>> {
  return get<PageResult<Employee>>('/employees', params)
}

export function getAllEmployees(): Promise<Employee[]> {
  return get<Employee[]>('/employees/all')
}

export function getEmployeeDetail(id: number): Promise<Employee> {
  return get<Employee>(`/employees/${id}`)
}

export function getMyEmployeeInfo(): Promise<Employee> {
  return get<Employee>('/employees/me')
}

export function createEmployee(data: EmployeeCreate): Promise<Employee> {
  return post<Employee>('/employees', data)
}

export function updateEmployee(id: number, data: EmployeeUpdate): Promise<Employee> {
  return put<Employee>(`/employees/${id}`, data)
}

export function deleteEmployee(id: number): Promise<null> {
  return del<null>(`/employees/${id}`)
}
