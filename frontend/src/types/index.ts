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
  pricePerDay: number
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

export interface PageResult<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
}

export type SkillTag = 'medication' | 'emergency' | 'cleaning' | 'reception' | 'cat_care' | 'night_shift'

export type ShiftType = 'morning' | 'afternoon' | 'night' | 'custom'

export type LeaveType = 'annual' | 'sick' | 'personal' | 'maternity' | 'paternity' | 'other'

export type RequestStatus = 'pending' | 'approved' | 'rejected' | 'cancelled'

export type AttendanceStatus = 'on_time' | 'late' | 'early_leave' | 'absent' | 'leave' | 'day_off'

export type AlertType = 'no_check_in' | 'no_check_out' | 'late_arrival' | 'early_departure'

export interface EmployeeUserInfo {
  id: number
  phone: string
  nickname?: string
  avatar?: string
}

export interface Employee {
  id: number
  userId: number
  employeeNo: string
  department?: string
  position?: string
  hireDate?: string
  weeklyRestDays: number
  maxConsecutiveDays: number
  preferredShiftType?: ShiftType
  unavailableDays: number[]
  skills: string[]
  isActive: boolean
  remark?: string
  user?: EmployeeUserInfo
  createdAt: string
  updatedAt: string
}

export interface EmployeeCreate {
  userId: number
  employeeNo: string
  department?: string
  position?: string
  hireDate?: string
  weeklyRestDays: number
  maxConsecutiveDays: number
  preferredShiftType?: ShiftType
  unavailableDays: number[]
  skills: string[]
  isActive: boolean
  remark?: string
}

export interface EmployeeUpdate {
  department?: string
  position?: string
  hireDate?: string
  weeklyRestDays?: number
  maxConsecutiveDays?: number
  preferredShiftType?: ShiftType
  unavailableDays?: number[]
  skills?: string[]
  isActive?: boolean
  remark?: string
}

export interface Shift {
  id: number
  name: string
  shiftType: ShiftType
  startTime: string
  endTime: string
  minStaff: number
  maxStaff?: number
  requiredSkills: string[]
  color: string
  isActive: boolean
  remark?: string
  createdAt: string
  updatedAt: string
}

export interface ShiftCreate {
  name: string
  shiftType: ShiftType
  startTime: string
  endTime: string
  minStaff: number
  maxStaff?: number
  requiredSkills: string[]
  color: string
  isActive: boolean
  remark?: string
}

export interface ShiftUpdate {
  name?: string
  shiftType?: ShiftType
  startTime?: string
  endTime?: string
  minStaff?: number
  maxStaff?: number
  requiredSkills?: string[]
  color?: string
  isActive?: boolean
  remark?: string
}

export interface SchedulingRule {
  id: number
  name: string
  weeklyRestDays: number
  maxConsecutiveDays: number
  dailyMaxHours: number
  weeklyMaxHours: number
  minBreakHoursBetweenShifts: number
  nightShiftPremium: number
  weekendPremium: number
  holidayPremium: number
  preferenceWeight: number
  skillWeight: number
  workloadWeight: number
  historyWeight: number
  isDefault: boolean
  isActive: boolean
  remark?: string
  createdAt: string
  updatedAt: string
}

export interface SchedulingRuleCreate {
  name: string
  weeklyRestDays: number
  maxConsecutiveDays: number
  dailyMaxHours: number
  weeklyMaxHours: number
  minBreakHoursBetweenShifts: number
  nightShiftPremium: number
  weekendPremium: number
  holidayPremium: number
  preferenceWeight: number
  skillWeight: number
  workloadWeight: number
  historyWeight: number
  isDefault: boolean
  isActive: boolean
  remark?: string
}

export interface SchedulingRuleUpdate {
  name?: string
  weeklyRestDays?: number
  maxConsecutiveDays?: number
  dailyMaxHours?: number
  weeklyMaxHours?: number
  minBreakHoursBetweenShifts?: number
  nightShiftPremium?: number
  weekendPremium?: number
  holidayPremium?: number
  preferenceWeight?: number
  skillWeight?: number
  workloadWeight?: number
  historyWeight?: number
  isDefault?: boolean
  isActive?: boolean
  remark?: string
}

export interface Schedule {
  id: number
  employeeId: number
  shiftId: number
  scheduleDate: string
  isConfirmed: boolean
  isSwapped: boolean
  originalEmployeeId?: number
  remark?: string
  employee?: Employee
  shift?: Shift
  attendance?: Attendance
  createdAt: string
  updatedAt: string
}

export interface ScheduleCreate {
  employeeId: number
  shiftId: number
  scheduleDate: string
  isConfirmed?: boolean
  remark?: string
}

export interface ScheduleUpdate {
  shiftId?: number
  isConfirmed?: boolean
  remark?: string
}

export interface ScheduleSwapRequest {
  fromEmployeeId: number
  toEmployeeId: number
  scheduleDate: string
  shiftId: number
  reason?: string
}

export interface ScheduleGenerateRequest {
  startDate: string
  endDate: string
  ruleId?: number
}

export interface ScheduleConflictCheckRequest {
  employeeId: number
  shiftId: number
  scheduleDate: string
  excludeScheduleId?: number
}

export interface ScheduleConflict {
  hasConflict: boolean
  conflictType?: string
  message?: string
}

export interface LeaveRequest {
  id: number
  employeeId: number
  leaveType: LeaveType
  startDate: string
  endDate: string
  startTime: string
  endTime: string
  reason: string
  status: RequestStatus
  approverId?: number
  approvalRemark?: string
  approvedAt?: string
  employee?: Employee
  createdAt: string
  updatedAt: string
}

export interface LeaveRequestCreate {
  leaveType: LeaveType
  startDate: string
  endDate: string
  startTime?: string
  endTime?: string
  reason: string
}

export interface LeaveRequestApprove {
  status: RequestStatus
  approvalRemark?: string
}

export interface ShiftSwap {
  id: number
  employeeId: number
  targetEmployeeId: number
  scheduleDate: string
  shiftId: number
  reason: string
  status: RequestStatus
  approverId?: number
  approvalRemark?: string
  approvedAt?: string
  employee?: Employee
  targetEmployee?: Employee
  shift?: Shift
  createdAt: string
  updatedAt: string
}

export interface ShiftSwapCreate {
  targetEmployeeId: number
  scheduleDate: string
  shiftId: number
  reason: string
}

export interface ShiftSwapApprove {
  status: RequestStatus
  approvalRemark?: string
}

export interface ShiftPreference {
  id: number
  employeeId: number
  shiftId?: number
  shiftType?: ShiftType
  preferenceType: 'prefer' | 'avoid'
  dayOfWeek?: number
  startDate?: string
  endDate?: string
  isRecurring: boolean
  priority: number
  reason?: string
  employee?: Employee
  shift?: Shift
  createdAt: string
  updatedAt: string
}

export interface ShiftPreferenceCreate {
  shiftId?: number
  shiftType?: ShiftType
  preferenceType: 'prefer' | 'avoid'
  dayOfWeek?: number
  startDate?: string
  endDate?: string
  isRecurring: boolean
  priority: number
  reason?: string
}

export interface Attendance {
  id: number
  employeeId: number
  scheduleId?: number
  attendanceDate: string
  checkInTime?: string
  checkOutTime?: string
  status: AttendanceStatus
  lateMinutes?: number
  earlyLeaveMinutes?: number
  overtimeMinutes?: number
  workHours?: number
  remark?: string
  employee?: Employee
  schedule?: Schedule
  createdAt: string
  updatedAt: string
}

export interface AttendanceCheckIn {
  checkInTime?: string
  location?: string
}

export interface AttendanceCheckOut {
  checkOutTime?: string
  location?: string
}

export interface AttendanceStats {
  employeeId: number
  employeeName?: string
  totalWorkingDays: number
  actualWorkingDays: number
  lateCount: number
  earlyLeaveCount: number
  absentCount: number
  leaveCount: number
  totalOvertimeHours: number
  totalWorkHours: number
  attendanceRate: number
}

export interface AttendanceReportRequest {
  startDate: string
  endDate: string
  employeeId?: number
  department?: string
}

export interface AttendanceAlert {
  id: number
  employeeId: number
  attendanceId?: number
  alertType: AlertType
  alertMessage: string
  alertTime: string
  isRead: boolean
  readAt?: string
  employee?: Employee
  attendance?: Attendance
  createdAt: string
}

export interface ScheduleCalendarItem {
  date: string
  dayOfWeek: number
  isWeekend: boolean
  isHoliday: boolean
  schedules: Schedule[]
}

export interface AttendanceCalendarItem {
  date: string
  dayOfWeek: number
  isWeekend: boolean
  attendance?: Attendance
  schedule?: Schedule
}
