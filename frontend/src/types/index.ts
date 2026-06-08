export interface User {
  id: number
  phone: string
  nickname: string
  avatar: string
  role: 'user' | 'staff' | 'admin'
  createdAt: string
  updatedAt: string
  memberLevel?: number
  memberPoints?: number
}

export interface CatRoom {
  id: number
  name: string
  description: string
  price_per_day: number
  price: number
  facilities: string[]
  images: string[]
  status: 'available' | 'occupied' | 'maintenance' | 'cleaning'
  area: number
  floor: number
  location: string
  createdAt: string
  updatedAt: string
}

export interface Service {
  id: number
  name: string
  description: string
  price: number
  duration: number
  category: string
  image: string
}

export interface Booking {
  id: number
  userId: number
  catRoomId: number
  catRoom?: CatRoom
  checkInDate: string
  checkOutDate: string
  services: Service[]
  totalPrice: number
  status: 'pending' | 'confirmed' | 'paid' | 'cancelled' | 'completed'
  paymentMethod: string
  paymentStatus: 'unpaid' | 'paid' | 'refunded'
  catName: string
  catBreed: string
  catAge: number
  specialRequirements: string
  createdAt: string
}

export interface Member {
  id: number
  userId: number
  level: number
  levelName: string
  points: number
  discount: number
  expireDate: string
}

export interface ApiResponse<T> {
  code: number
  message: string
  data: T
}

export interface LoginRequest {
  phone: string
  password: string
}

export interface RegisterRequest {
  phone: string
  password: string
  nickname: string
}

export interface BookingRequest {
  catRoomId: number
  checkInDate: string
  checkOutDate: string
  serviceIds: number[]
  catName: string
  catBreed: string
  catAge: number
  specialRequirements: string
}

export interface PageParams {
  page: number
  pageSize: number
}

export interface PageResult<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
}
