import { get, post, put, del } from './request'
import type { Booking, BookingRequest, PageParams, PageResult, ApiResponse } from '@/types'

export function createBooking(data: BookingRequest): Promise<Booking> {
  return post<Booking>('/bookings', data)
}

export function getBookingList(params: PageParams): Promise<PageResult<Booking>> {
  return get<PageResult<Booking>>('/bookings', params)
}

export function getBookingDetail(id: number): Promise<Booking> {
  return get<Booking>(`/bookings/${id}`)
}

export function cancelBooking(id: number): Promise<ApiResponse<null>> {
  return put<ApiResponse<null>>(`/bookings/${id}/cancel`)
}

export function payBooking(id: number, paymentMethod: string): Promise<{ paymentUrl: string; orderId: string }> {
  return post<{ paymentUrl: string; orderId: string }>(`/bookings/${id}/pay`, { paymentMethod })
}

export function getBookingPrice(data: {
  catRoomId: number
  checkInDate: string
  checkOutDate: string
  serviceIds: number[]
}): Promise<{ totalPrice: number; roomPrice: number; servicePrice: number; discount: number }> {
  return post<{ totalPrice: number; roomPrice: number; servicePrice: number; discount: number }>('/bookings/calculate', data)
}

export function deleteBooking(id: number): Promise<ApiResponse<null>> {
  return del<ApiResponse<null>>(`/bookings/${id}`)
}
