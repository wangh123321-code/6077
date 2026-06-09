<template>
  <div class="attendance-page">
    <div class="container">
      <div class="page-header">
        <h1>考勤打卡</h1>
      </div>

      <el-row :gutter="24" class="attendance-content">
        <el-col :span="8">
          <el-card class="check-in-card">
            <div class="current-time">
              <div class="time">{{ currentTime }}</div>
              <div class="date">{{ currentDate }}</div>
            </div>

            <div class="today-schedule" v-if="todaySchedule">
              <div class="schedule-label">今日班次</div>
              <div class="schedule-info">
                <el-tag
                  :style="{ background: todaySchedule.shift?.color }"
                  effect="dark"
                  size="large"
                >
                  {{ todaySchedule.shift?.name }}
                </el-tag>
                <span class="schedule-time">
                  {{ todaySchedule.shift?.startTime }} - {{ todaySchedule.shift?.endTime }}
                </span>
              </div>
            </div>

            <div class="today-attendance" v-if="todayAttendance">
              <div class="attendance-row">
                <span class="label">上班打卡</span>
                <span class="value" :class="getCheckInStatusClass()">
                  {{ todayAttendance.checkInTime || '未打卡' }}
                </span>
              </div>
              <div class="attendance-row">
                <span class="label">下班打卡</span>
                <span class="value" :class="getCheckOutStatusClass()">
                  {{ todayAttendance.checkOutTime || '未打卡' }}
                </span>
              </div>
              <div class="attendance-row">
                <span class="label">考勤状态</span>
                <el-tag :type="getStatusType(todayAttendance.status)" size="small">
                  {{ getStatusLabel(todayAttendance.status) }}
                </el-tag>
              </div>
              <div v-if="todayAttendance.lateMinutes" class="attendance-row">
                <span class="label">迟到</span>
                <span class="value late">{{ todayAttendance.lateMinutes }}分钟</span>
              </div>
              <div v-if="todayAttendance.earlyLeaveMinutes" class="attendance-row">
                <span class="label">早退</span>
                <span class="value early">{{ todayAttendance.earlyLeaveMinutes }}分钟</span>
              </div>
              <div v-if="todayAttendance.overtimeMinutes" class="attendance-row">
                <span class="label">加班</span>
                <span class="value overtime">{{ todayAttendance.overtimeMinutes }}分钟</span>
              </div>
            </div>

            <div class="check-buttons">
              <el-button
                type="primary"
                size="large"
                :disabled="!!todayAttendance?.checkInTime"
                :loading="checkingIn"
                @click="handleCheckIn"
              >
                <el-icon><Watch /></el-icon>
                {{ todayAttendance?.checkInTime ? '已打卡' : '上班打卡' }}
              </el-button>
              <el-button
                type="success"
                size="large"
                :disabled="!todayAttendance?.checkInTime || !!todayAttendance?.checkOutTime"
                :loading="checkingOut"
                @click="handleCheckOut"
              >
                <el-icon><SwitchButton /></el-icon>
                {{ todayAttendance?.checkOutTime ? '已打卡' : '下班打卡' }}
              </el-button>
            </div>
          </el-card>

          <el-card class="stats-card">
            <template #header>
              <span>本月统计</span>
              <el-date-picker
                v-model="statsMonth"
                type="month"
                format="YYYY-MM"
                value-format="YYYY-MM"
                size="small"
                @change="loadMyReport"
              />
            </template>
            <div v-if="myStats" class="stats-grid">
              <div class="stat-item">
                <div class="stat-value">{{ myStats.actualWorkingDays }}</div>
                <div class="stat-label">出勤天数</div>
              </div>
              <div class="stat-item">
                <div class="stat-value late">{{ myStats.lateCount }}</div>
                <div class="stat-label">迟到次数</div>
              </div>
              <div class="stat-item">
                <div class="stat-value early">{{ myStats.earlyLeaveCount }}</div>
                <div class="stat-label">早退次数</div>
              </div>
              <div class="stat-item">
                <div class="stat-value absent">{{ myStats.absentCount }}</div>
                <div class="stat-label">旷工次数</div>
              </div>
              <div class="stat-item">
                <div class="stat-value leave">{{ myStats.leaveCount }}</div>
                <div class="stat-label">请假天数</div>
              </div>
              <div class="stat-item">
                <div class="stat-value overtime">{{ myStats.totalOvertimeHours }}h</div>
                <div class="stat-label">加班时长</div>
              </div>
            </div>
            <div v-else class="no-data">暂无数据</div>
          </el-card>
        </el-col>

        <el-col :span="16">
          <el-card class="calendar-card">
            <template #header>
              <div class="card-header">
                <span>考勤日历</span>
                <div class="date-nav">
                  <el-button-group>
                    <el-button size="small" @click="changeMonth(-1)">
                      <el-icon><ArrowLeft /></el-icon>
                    </el-button>
                    <el-button size="small" @click="goToToday">今天</el-button>
                    <el-button size="small" @click="changeMonth(1)">
                      <el-icon><ArrowRight /></el-icon>
                    </el-button>
                  </el-button-group>
                  <span class="current-month">{{ currentMonthLabel }}</span>
                </div>
              </div>
            </template>

            <div class="attendance-calendar" v-loading="loading.calendar">
              <div class="calendar-weekdays">
                <div v-for="day in weekdayLabels" :key="day" class="weekday-cell">
                  {{ day }}
                </div>
              </div>
              <div class="calendar-days">
                <div
                  v-for="day in calendarDays"
                  :key="day.date"
                  class="day-cell"
                  :class="{
                    'other-month': !day.inMonth,
                    'today': day.isToday,
                    'weekend': day.isWeekend
                  }"
                >
                  <div class="day-number">{{ day.day }}</div>
                  <div v-if="day.attendance" class="day-status">
                    <el-tag
                      :type="getStatusType(day.attendance.status)"
                      size="small"
                      effect="dark"
                    >
                      {{ getStatusShortLabel(day.attendance.status) }}
                    </el-tag>
                  </div>
                  <div v-else-if="day.schedule" class="day-status">
                    <el-tag
                      :style="{ background: day.schedule.shift?.color }"
                      size="small"
                      effect="dark"
                    >
                      班
                    </el-tag>
                  </div>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { ArrowLeft, ArrowRight, Watch, SwitchButton } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import {
  getMyTodayAttendance,
  getMyAttendanceCalendar,
  getMyAttendanceReport,
  checkIn,
  checkOut
} from '@/api/attendance'
import { getMyScheduleCalendar } from '@/api/schedule'
import type {
  Attendance,
  AttendanceCalendarItem,
  AttendanceStats,
  AttendanceStatus
} from '@/types'

const currentDate = ref(dayjs())
const statsMonth = ref(dayjs().format('YYYY-MM'))

const currentTime = ref('')
let timeInterval: number | null = null

const todayAttendance = ref<Attendance | null>(null)
const todaySchedule = ref<any>(null)
const myStats = ref<AttendanceStats | null>(null)
const calendarData = ref<AttendanceCalendarItem[]>([])

const checkingIn = ref(false)
const checkingOut = ref(false)

const loading = reactive({
  calendar: false
})

const weekdayLabels = ['日', '一', '二', '三', '四', '五', '六']

const currentMonthLabel = computed(() => {
  return currentDate.value.format('YYYY年MM月')
})

const calendarDays = computed(() => {
  const year = currentDate.value.year()
  const month = currentDate.value.month()
  
  const firstDay = dayjs(new Date(year, month, 1))
  const lastDay = dayjs(new Date(year, month + 1, 0))
  
  const startPadding = firstDay.day()
  const totalDays = lastDay.date()
  
  const days: Array<{
    date: string
    day: number
    inMonth: boolean
    isToday: boolean
    isWeekend: boolean
    attendance?: Attendance
    schedule?: any
  }> = []
  
  const prevMonth = firstDay.subtract(1, 'month')
  for (let i = startPadding - 1; i >= 0; i--) {
    const d = prevMonth.date(prevMonth.daysInMonth() - i)
    days.push({
      date: d.format('YYYY-MM-DD'),
      day: d.date(),
      inMonth: false,
      isToday: false,
      isWeekend: d.day() === 0 || d.day() === 6
    })
  }
  
  for (let i = 1; i <= totalDays; i++) {
    const d = dayjs(new Date(year, month, i))
    const calItem = calendarData.value.find(c => c.date === d.format('YYYY-MM-DD'))
    days.push({
      date: d.format('YYYY-MM-DD'),
      day: i,
      inMonth: true,
      isToday: d.isSame(dayjs(), 'day'),
      isWeekend: d.day() === 0 || d.day() === 6,
      attendance: calItem?.attendance,
      schedule: calItem?.schedule
    })
  }
  
  const remaining = 42 - days.length
  const nextMonth = lastDay.add(1, 'day')
  for (let i = 0; i < remaining; i++) {
    const d = nextMonth.add(i, 'day')
    days.push({
      date: d.format('YYYY-MM-DD'),
      day: d.date(),
      inMonth: false,
      isToday: false,
      isWeekend: d.day() === 0 || d.day() === 6
    })
  }
  
  return days
})

function updateTime() {
  currentTime.value = dayjs().format('HH:mm:ss')
}

function getCheckInStatusClass() {
  if (!todayAttendance.value?.checkInTime) return 'missing'
  if (todayAttendance.value.lateMinutes && todayAttendance.value.lateMinutes > 0) return 'late'
  return 'normal'
}

function getCheckOutStatusClass() {
  if (!todayAttendance.value?.checkOutTime) return 'missing'
  if (todayAttendance.value.earlyLeaveMinutes && todayAttendance.value.earlyLeaveMinutes > 0) return 'early'
  return 'normal'
}

function getStatusType(status: AttendanceStatus) {
  const map: Record<AttendanceStatus, string> = {
    on_time: 'success',
    late: 'warning',
    early_leave: 'warning',
    absent: 'danger',
    leave: 'info',
    day_off: 'info'
  }
  return map[status] || 'info'
}

function getStatusLabel(status: AttendanceStatus) {
  const map: Record<AttendanceStatus, string> = {
    on_time: '准时',
    late: '迟到',
    early_leave: '早退',
    absent: '旷工',
    leave: '请假',
    day_off: '休息'
  }
  return map[status] || status
}

function getStatusShortLabel(status: AttendanceStatus) {
  const map: Record<AttendanceStatus, string> = {
    on_time: '准',
    late: '迟',
    early_leave: '早',
    absent: '旷',
    leave: '假',
    day_off: '休'
  }
  return map[status] || status
}

function changeMonth(delta: number) {
  currentDate.value = currentDate.value.add(delta, 'month')
  loadCalendar()
}

function goToToday() {
  currentDate.value = dayjs()
  loadCalendar()
}

async function handleCheckIn() {
  checkingIn.value = true
  try {
    const res = await checkIn()
    todayAttendance.value = res
    ElMessage.success('打卡成功')
    loadTodayInfo()
  } catch (e) {
    console.error(e)
  } finally {
    checkingIn.value = false
  }
}

async function handleCheckOut() {
  checkingOut.value = true
  try {
    const res = await checkOut()
    todayAttendance.value = res
    ElMessage.success('打卡成功')
    loadTodayInfo()
  } catch (e) {
    console.error(e)
  } finally {
    checkingOut.value = false
  }
}

async function loadTodayInfo() {
  try {
    const [attendance, schedule] = await Promise.all([
      getMyTodayAttendance().catch(() => null),
      getMyScheduleCalendar(dayjs().format('YYYY-MM-DD'), dayjs().format('YYYY-MM-DD')).catch(() => [])
    ])
    
    todayAttendance.value = attendance
    if (schedule.length > 0 && schedule[0].schedules.length > 0) {
      todaySchedule.value = schedule[0].schedules[0]
    }
  } catch (e) {
    console.error(e)
  }
}

async function loadCalendar() {
  loading.calendar = true
  try {
    const startDate = currentDate.value.startOf('month').format('YYYY-MM-DD')
    const endDate = currentDate.value.endOf('month').format('YYYY-MM-DD')
    
    calendarData.value = await getMyAttendanceCalendar(startDate, endDate)
  } catch (e) {
    console.error(e)
  } finally {
    loading.calendar = false
  }
}

async function loadMyReport() {
  try {
    const startDate = dayjs(statsMonth.value).startOf('month').format('YYYY-MM-DD')
    const endDate = dayjs(statsMonth.value).endOf('month').format('YYYY-MM-DD')
    
    myStats.value = await getMyAttendanceReport(startDate, endDate)
  } catch (e) {
    console.error(e)
  }
}

onMounted(() => {
  updateTime()
  timeInterval = window.setInterval(updateTime, 1000)
  loadTodayInfo()
  loadCalendar()
  loadMyReport()
})

onUnmounted(() => {
  if (timeInterval) {
    clearInterval(timeInterval)
  }
})
</script>

<style scoped lang="scss">
.attendance-page {
  min-height: 100vh;
  background: #f5f7fa;
  padding: 32px 0;

  .container {
    max-width: 1600px;
    margin: 0 auto;
    padding: 0 24px;
  }

  .page-header {
    margin-bottom: 24px;

    h1 {
      font-size: 28px;
      margin: 0;
      color: #333;
    }
  }

  .attendance-content {
    .check-in-card {
      margin-bottom: 24px;

      .current-time {
        text-align: center;
        padding: 24px 0;
        border-bottom: 1px solid #eee;
        margin-bottom: 24px;

        .time {
          font-size: 48px;
          font-weight: 700;
          color: #333;
          font-family: 'Courier New', monospace;
        }

        .date {
          font-size: 16px;
          color: #999;
          margin-top: 8px;
        }
      }

      .today-schedule {
        margin-bottom: 24px;

        .schedule-label {
          font-size: 12px;
          color: #999;
          margin-bottom: 8px;
        }

        .schedule-info {
          display: flex;
          align-items: center;
          gap: 12px;

          .schedule-time {
            font-size: 14px;
            color: #666;
          }
        }
      }

      .today-attendance {
        margin-bottom: 24px;

        .attendance-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 8px 0;
          border-bottom: 1px dashed #eee;

          &:last-child {
            border-bottom: none;
          }

          .label {
            font-size: 14px;
            color: #666;
          }

          .value {
            font-size: 14px;
            font-weight: 500;

            &.normal {
              color: #67c23a;
            }

            &.missing {
              color: #f56c6c;
            }

            &.late,
            &.early {
              color: #e6a23c;
            }

            &.overtime {
              color: #409eff;
            }
          }
        }
      }

      .check-buttons {
        display: flex;
        gap: 12px;

        .el-button {
          flex: 1;
        }
      }
    }

    .stats-card {
      .stats-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 16px;

        .stat-item {
          text-align: center;
          padding: 12px;
          background: #f5f7fa;
          border-radius: 8px;

          .stat-value {
            font-size: 24px;
            font-weight: 700;
            color: #333;

            &.late {
              color: #e6a23c;
            }

            &.early {
              color: #e6a23c;
            }

            &.absent {
              color: #f56c6c;
            }

            &.leave {
              color: #909399;
            }

            &.overtime {
              color: #409eff;
            }
          }

          .stat-label {
            font-size: 12px;
            color: #999;
            margin-top: 4px;
          }
        }
      }

      .no-data {
        text-align: center;
        padding: 40px;
        color: #999;
      }
    }

    .calendar-card {
      .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;

        .date-nav {
          display: flex;
          align-items: center;
          gap: 12px;

          .current-month {
            font-size: 14px;
            font-weight: 500;
          }
        }
      }

      .attendance-calendar {
        .calendar-weekdays {
          display: grid;
          grid-template-columns: repeat(7, 1fr);
          background: #f5f7fa;
          border-radius: 8px 8px 0 0;

          .weekday-cell {
            padding: 12px;
            text-align: center;
            font-weight: 500;
            color: #666;
          }
        }

        .calendar-days {
          display: grid;
          grid-template-columns: repeat(7, 1fr);
          border: 1px solid #e4e7ed;
          border-top: none;
          border-radius: 0 0 8px 8px;

          .day-cell {
            min-height: 80px;
            padding: 8px;
            border-right: 1px solid #e4e7ed;
            border-bottom: 1px solid #e4e7ed;
            position: relative;

            &:nth-child(7n) {
              border-right: none;
            }

            &.other-month {
              background: #fafafa;

              .day-number {
                color: #ccc;
              }
            }

            &.today {
              background: #ecf5ff;

              .day-number {
                background: #409eff;
                color: #fff;
                border-radius: 50%;
                width: 24px;
                height: 24px;
                display: flex;
                align-items: center;
                justify-content: center;
              }
            }

            &.weekend {
              background: #fafafa;
            }

            .day-number {
              font-size: 14px;
              font-weight: 500;
              margin-bottom: 4px;
            }

            .day-status {
              position: absolute;
              bottom: 4px;
              right: 4px;
            }
          }
        }
      }
    }
  }
}

@media (max-width: 768px) {
  .attendance-page {
    padding: 16px 0;

    .container {
      padding: 0 12px;
    }

    .page-header h1 {
      font-size: 20px;
    }

    .attendance-content {
      .check-in-card {
        .current-time {
          .time {
            font-size: 36px;
          }
        }
      }

      .stats-card {
        .stats-grid {
          grid-template-columns: repeat(2, 1fr);
        }
      }
    }
  }
}
</style>
