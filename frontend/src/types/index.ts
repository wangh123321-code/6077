export interface User {
  id: number
  username: string
  email: string
  phone: string
  avatar: string
  role: 'user' | 'admin'
  memberLevel: number
  memberPoints: number
  createdAt: string
}

export interface CatRoom {
  id: number
  name: string
  type: string
  size: string
  price: number
  description: string
  images: string[]
  facilities: string[]
  status: 'available' | 'occupied' | 'maintenance'
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
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  email: string
  phone: string
  password: string
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
