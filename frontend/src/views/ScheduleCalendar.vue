<template>
  <div class="schedule-calendar-page">
    <div class="container">
      <div class="page-header">
        <div class="header-left">
          <h1>排班日历</h1>
          <div class="date-nav">
            <el-button-group>
              <el-button @click="changeMonth(-1)">
                <el-icon><ArrowLeft /></el-icon>
              </el-button>
              <el-button @click="goToToday">今天</el-button>
              <el-button @click="changeMonth(1)">
                <el-icon><ArrowRight /></el-icon>
              </el-button>
            </el-button-group>
            <span class="current-month">{{ currentMonthLabel }}</span>
          </div>
        </div>
        <div class="header-right">
          <el-select v-model="viewMode" style="width: 120px; margin-right: 12px">
            <el-option label="按员工" value="employee" />
            <el-option label="按日期" value="date" />
          </el-select>
          <el-button type="primary" @click="showGenerateDialog">
            <el-icon><MagicStick /></el-icon>
            智能排班
          </el-button>
          <el-button @click="loadCalendar">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>

      <div class="legend-bar">
        <div class="legend-item" v-for="shift in shiftList" :key="shift.id">
          <span class="legend-color" :style="{ background: shift.color }"></span>
          <span class="legend-text">{{ shift.name }} ({{ shift.startTime }}-{{ shift.endTime }})</span>
        </div>
      </div>

      <el-card class="calendar-card" v-loading="loading.calendar">
        <div v-if="viewMode === 'date'" class="calendar-by-date">
          <div class="calendar-header">
            <div class="calendar-cell header-cell">日期</div>
            <div class="calendar-cell header-cell" v-for="shift in shiftList" :key="shift.id">
              {{ shift.name }}
            </div>
          </div>
          <div class="calendar-body">
            <div
              v-for="day in calendarData"
              :key="day.date"
              class="calendar-row"
              :class="{ 'weekend': day.isWeekend, 'holiday': day.isHoliday }"
            >
              <div class="calendar-cell date-cell">
                <div class="date-label">{{ day.date }}</div>
                <div class="weekday-label">{{ weekdayLabels[day.dayOfWeek] }}</div>
              </div>
              <div
                v-for="shift in shiftList"
                :key="shift.id"
                class="calendar-cell shift-cell"
                @dragover.prevent
                @drop="handleDrop($event, day.date, shift.id)"
              >
                <div
                  v-for="schedule in getSchedulesForShift(day, shift.id)"
                  :key="schedule.id"
                  class="schedule-item"
                  :style="{ borderLeftColor: shift.color }"
                  :class="{ 'swapped': schedule.isSwapped, 'confirmed': schedule.isConfirmed }"
                  draggable="true"
                  @dragstart="handleDragStart($event, schedule)"
                  @click="showScheduleDetail(schedule)"
                >
                  <span class="employee-name">
                    {{ schedule.employee?.user?.nickname || schedule.employeeId }}
                  </span>
                  <el-tag v-if="schedule.isSwapped" size="small" type="warning" effect="dark">调</el-tag>
                  <el-tag v-if="!schedule.isConfirmed" size="small" type="info">待确认</el-tag>
                </div>
                <div
                  class="add-schedule-btn"
                  @click="showAddScheduleDialog(day.date, shift.id)"
                >
                  <el-icon><Plus /></el-icon>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-else class="calendar-by-employee">
          <div class="calendar-header">
            <div class="calendar-cell header-cell">员工</div>
            <div class="calendar-cell header-cell" v-for="day in calendarData" :key="day.date">
              <div>{{ day.date.slice(5) }}</div>
              <div class="weekday-small">{{ weekdayLabels[day.dayOfWeek] }}</div>
            </div>
          </div>
          <div class="calendar-body">
            <div v-for="employee in employeeList" :key="employee.id" class="calendar-row">
              <div class="calendar-cell employee-cell">
                <div class="employee-avatar">
                  {{ employee.user?.nickname?.charAt(0) || '员' }}
                </div>
                <div class="employee-info">
                  <div class="employee-name">{{ employee.user?.nickname || '未命名' }}</div>
                  <div class="employee-no">{{ employee.employeeNo }}</div>
                </div>
              </div>
              <div
                v-for="day in calendarData"
                :key="day.date"
                class="calendar-cell day-cell"
                :class="{ 'weekend': day.isWeekend }"
                @dragover.prevent
                @drop="handleDropToEmployee($event, employee.id, day.date)"
              >
                <div
                  v-for="schedule in getEmployeeScheduleForDay(employee.id, day)"
                  :key="schedule.id"
                  class="schedule-item-small"
                  :style="{ background: schedule.shift?.color || '#409EFF' }"
                  draggable="true"
                  @dragstart="handleDragStart($event, schedule)"
                  @click="showScheduleDetail(schedule)"
                >
                  {{ schedule.shift?.name || '班次' }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <el-dialog
      v-model="generateDialogVisible"
      title="智能排班"
      width="500px"
    >
      <el-form :model="generateForm" label-width="100px">
        <el-form-item label="开始日期" required>
          <el-date-picker
            v-model="generateForm.startDate"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="选择开始日期"
          />
        </el-form-item>
        <el-form-item label="结束日期" required>
          <el-date-picker
            v-model="generateForm.endDate"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="选择结束日期"
          />
        </el-form-item>
        <el-form-item label="使用规则">
          <el-select v-model="generateForm.ruleId" placeholder="使用默认规则">
            <el-option
              v-for="rule in ruleList"
              :key="rule.id"
              :label="rule.name + (rule.isDefault ? ' (默认)' : '')"
              :value="rule.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <div class="generate-tips">
        <el-alert
          title="智能排班会考虑以下因素"
          type="info"
          :closable="false"
        >
          <ul>
            <li>员工技能与班次要求的匹配度</li>
            <li>员工班次偏好设置</li>
            <li>员工工作时长和休息时间</li>
            <li>历史排班情况</li>
            <li>已审批的请假申请</li>
          </ul>
        </el-alert>
      </div>
      <template #footer>
        <el-button @click="generateDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleGenerate" :loading="generating">
          生成排班
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="scheduleDetailVisible"
      title="排班详情"
      width="500px"
    >
      <el-descriptions v-if="currentSchedule" :column="1" border>
        <el-descriptions-item label="员工">
          {{ currentSchedule.employee?.user?.nickname || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="班次">
          <el-tag :style="{ background: currentSchedule.shift?.color }" effect="dark">
            {{ currentSchedule.shift?.name }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="时间">
          {{ currentSchedule.shift?.startTime }} - {{ currentSchedule.shift?.endTime }}
        </el-descriptions-item>
        <el-descriptions-item label="日期">
          {{ currentSchedule.scheduleDate }}
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="currentSchedule.isConfirmed ? 'success' : 'warning'">
            {{ currentSchedule.isConfirmed ? '已确认' : '待确认' }}
          </el-tag>
          <el-tag v-if="currentSchedule.isSwapped" type="info" style="margin-left: 8px">
            已调班
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="备注">
          {{ currentSchedule.remark || '-' }}
        </el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="scheduleDetailVisible = false">关闭</el-button>
        <el-button v-if="currentSchedule && !currentSchedule.isConfirmed" type="primary" @click="handleConfirmSchedule">
          确认排班
        </el-button>
        <el-button type="danger" @click="handleDeleteSchedule">
          删除排班
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="addScheduleDialogVisible"
      title="添加排班"
      width="500px"
    >
      <el-form :model="addScheduleForm" label-width="100px">
        <el-form-item label="员工" required>
          <el-select v-model="addScheduleForm.employeeId" placeholder="请选择员工" filterable>
            <el-option
              v-for="emp in employeeList"
              :key="emp.id"
              :label="emp.user?.nickname + ' (' + emp.employeeNo + ')'"
              :value="emp.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="班次" required>
          <el-select v-model="addScheduleForm.shiftId" placeholder="请选择班次">
            <el-option
              v-for="shift in shiftList"
              :key="shift.id"
              :label="shift.name + ' (' + shift.startTime + '-' + shift.endTime + ')'"
              :value="shift.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="日期" required>
          <el-date-picker
            v-model="addScheduleForm.scheduleDate"
            type="date"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="addScheduleForm.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addScheduleDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleAddSchedule">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, ArrowRight, Plus, MagicStick, Refresh } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import {
  getScheduleCalendar,
  generateSchedules,
  createSchedule,
  confirmSchedule,
  deleteSchedule,
  swapSchedule,
  checkScheduleConflict
} from '@/api/schedule'
import { getAllShifts } from '@/api/shift'
import { getAllEmployees } from '@/api/employee'
import { getSchedulingRuleList } from '@/api/schedulingRule'
import type {
  Schedule,
  ScheduleCalendarItem,
  Shift,
  Employee,
  SchedulingRule,
  ScheduleGenerateRequest,
  ScheduleCreate
} from '@/types'

const currentDate = ref(dayjs())
const viewMode = ref<'date' | 'employee'>('date')

const calendarData = ref<ScheduleCalendarItem[]>([])
const shiftList = ref<Shift[]>([])
const employeeList = ref<Employee[]>([])
const ruleList = ref<SchedulingRule[]>([])

const loading = reactive({
  calendar: false
})

const generating = ref(false)
const generateDialogVisible = ref(false)
const generateForm = reactive<ScheduleGenerateRequest>({
  startDate: '',
  endDate: '',
  ruleId: undefined
})

const scheduleDetailVisible = ref(false)
const currentSchedule = ref<Schedule | null>(null)

const addScheduleDialogVisible = ref(false)
const addScheduleForm = reactive<ScheduleCreate>({
  employeeId: 0,
  shiftId: 0,
  scheduleDate: '',
  isConfirmed: false,
  remark: ''
})

const draggedSchedule = ref<Schedule | null>(null)

const weekdayLabels = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']

const currentMonthLabel = computed(() => {
  return currentDate.value.format('YYYY年MM月')
})

function changeMonth(delta: number) {
  currentDate.value = currentDate.value.add(delta, 'month')
  loadCalendar()
}

function goToToday() {
  currentDate.value = dayjs()
  loadCalendar()
}

function getSchedulesForShift(day: ScheduleCalendarItem, shiftId: number) {
  return day.schedules.filter(s => s.shiftId === shiftId)
}

function getEmployeeScheduleForDay(employeeId: number, day: ScheduleCalendarItem) {
  return day.schedules.filter(s => s.employeeId === employeeId)
}

function showGenerateDialog() {
  generateForm.startDate = currentDate.value.startOf('month').format('YYYY-MM-DD')
  generateForm.endDate = currentDate.value.endOf('month').format('YYYY-MM-DD')
  generateDialogVisible.value = true
}

async function handleGenerate() {
  if (!generateForm.startDate || !generateForm.endDate) {
    ElMessage.warning('请选择日期范围')
    return
  }
  generating.value = true
  try {
    await generateSchedules(generateForm)
    ElMessage.success('排班生成成功')
    generateDialogVisible.value = false
    loadCalendar()
  } catch (e) {
    console.error(e)
  } finally {
    generating.value = false
  }
}

function showScheduleDetail(schedule: Schedule) {
  currentSchedule.value = schedule
  scheduleDetailVisible.value = true
}

async function handleConfirmSchedule() {
  if (!currentSchedule.value) return
  try {
    await confirmSchedule(currentSchedule.value.id)
    ElMessage.success('已确认')
    scheduleDetailVisible.value = false
    loadCalendar()
  } catch (e) {
    console.error(e)
  }
}

async function handleDeleteSchedule() {
  if (!currentSchedule.value) return
  try {
    await ElMessageBox.confirm('确定要删除这个排班吗？', '确认删除', {
      type: 'warning'
    })
    await deleteSchedule(currentSchedule.value.id)
    ElMessage.success('删除成功')
    scheduleDetailVisible.value = false
    loadCalendar()
  } catch (e) {
    if (e !== 'cancel') console.error(e)
  }
}

function showAddScheduleDialog(date: string, shiftId: number) {
  addScheduleForm.scheduleDate = date
  addScheduleForm.shiftId = shiftId
  addScheduleForm.employeeId = 0
  addScheduleForm.remark = ''
  addScheduleDialogVisible.value = true
}

async function handleAddSchedule() {
  if (!addScheduleForm.employeeId || !addScheduleForm.shiftId || !addScheduleForm.scheduleDate) {
    ElMessage.warning('请填写完整信息')
    return
  }
  
  try {
    const conflict = await checkScheduleConflict({
      employeeId: addScheduleForm.employeeId,
      shiftId: addScheduleForm.shiftId,
      scheduleDate: addScheduleForm.scheduleDate
    })
    
    if (conflict.hasConflict) {
      await ElMessageBox.confirm(
        `检测到冲突：${conflict.message}，是否仍要添加？`,
        '冲突提醒',
        { type: 'warning' }
      )
    }
    
    await createSchedule(addScheduleForm)
    ElMessage.success('添加成功')
    addScheduleDialogVisible.value = false
    loadCalendar()
  } catch (e) {
    if (e !== 'cancel') console.error(e)
  }
}

function handleDragStart(event: DragEvent, schedule: Schedule) {
  draggedSchedule.value = schedule
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
  }
}

async function handleDrop(event: DragEvent, date: string, shiftId: number) {
  if (!draggedSchedule.value) return
  
  const originalSchedule = draggedSchedule.value
  
  try {
    const conflict = await checkScheduleConflict({
      employeeId: originalSchedule.employeeId,
      shiftId,
      scheduleDate: date,
      excludeScheduleId: originalSchedule.id
    })
    
    if (conflict.hasConflict) {
      ElMessage.warning(conflict.message)
      return
    }
    
    await swapSchedule({
      fromEmployeeId: originalSchedule.employeeId,
      toEmployeeId: originalSchedule.employeeId,
      scheduleDate: date,
      shiftId,
      reason: '拖拽调整'
    })
    
    ElMessage.success('调整成功')
    loadCalendar()
  } catch (e) {
    console.error(e)
  } finally {
    draggedSchedule.value = null
  }
}

async function handleDropToEmployee(event: DragEvent, toEmployeeId: number, date: string) {
  if (!draggedSchedule.value) return
  
  const originalSchedule = draggedSchedule.value
  
  if (originalSchedule.employeeId === toEmployeeId && 
      originalSchedule.scheduleDate === date) {
    return
  }
  
  try {
    const conflict = await checkScheduleConflict({
      employeeId: toEmployeeId,
      shiftId: originalSchedule.shiftId,
      scheduleDate: date
    })
    
    if (conflict.hasConflict) {
      ElMessage.warning(conflict.message)
      return
    }
    
    await swapSchedule({
      fromEmployeeId: originalSchedule.employeeId,
      toEmployeeId,
      scheduleDate: date,
      shiftId: originalSchedule.shiftId,
      reason: '拖拽调班'
    })
    
    ElMessage.success('调班成功')
    loadCalendar()
  } catch (e) {
    console.error(e)
  } finally {
    draggedSchedule.value = null
  }
}

async function loadCalendar() {
  loading.calendar = true
  try {
    const startDate = currentDate.value.startOf('month').format('YYYY-MM-DD')
    const endDate = currentDate.value.endOf('month').format('YYYY-MM-DD')
    
    const [calendar, shifts, employees, rules] = await Promise.all([
      getScheduleCalendar(startDate, endDate),
      getAllShifts(),
      getAllEmployees(),
      getSchedulingRuleList({ page: 1, pageSize: 100 })
    ])
    
    calendarData.value = calendar
    shiftList.value = shifts
    employeeList.value = employees
    ruleList.value = rules.items
  } catch (e) {
    console.error(e)
  } finally {
    loading.calendar = false
  }
}

onMounted(() => {
  loadCalendar()
})
</script>

<style scoped lang="scss">
.schedule-calendar-page {
  min-height: 100vh;
  background: #f5f7fa;
  padding: 32px 0;

  .container {
    max-width: 1600px;
    margin: 0 auto;
    padding: 0 24px;
  }

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 24px;
    flex-wrap: wrap;
    gap: 16px;

    .header-left {
      h1 {
        font-size: 28px;
        margin: 0 0 12px 0;
        color: #333;
      }

      .date-nav {
        display: flex;
        align-items: center;
        gap: 12px;

        .current-month {
          font-size: 18px;
          font-weight: 600;
          color: #333;
        }
      }
    }
  }

  .legend-bar {
    display: flex;
    flex-wrap: wrap;
    gap: 16px;
    margin-bottom: 16px;
    padding: 12px 16px;
    background: #fff;
    border-radius: 8px;

    .legend-item {
      display: flex;
      align-items: center;
      gap: 6px;

      .legend-color {
        width: 16px;
        height: 16px;
        border-radius: 3px;
      }

      .legend-text {
        font-size: 12px;
        color: #666;
      }
    }
  }

  .calendar-card {
    overflow-x: auto;

    .calendar-by-date,
    .calendar-by-employee {
      min-width: 800px;
    }

    .calendar-header {
      display: flex;
      background: #f5f7fa;
      font-weight: 600;

      .header-cell {
        padding: 12px 8px;
        text-align: center;
        border-bottom: 2px solid #e4e7ed;
        font-size: 14px;
        color: #333;
      }
    }

    .calendar-body {
      .calendar-row {
        display: flex;
        border-bottom: 1px solid #e4e7ed;

        &:hover {
          background: #f5f7fa;
        }

        &.weekend {
          background: #fafafa;
        }

        &.holiday {
          background: #fff7f7;
        }
      }

      .calendar-cell {
        flex: 1;
        padding: 8px;
        border-right: 1px solid #e4e7ed;
        min-height: 80px;

        &:last-child {
          border-right: none;
        }

        &.date-cell {
          flex: 0 0 100px;
          background: #fafafa;

          .date-label {
            font-weight: 600;
            font-size: 16px;
          }

          .weekday-label {
            font-size: 12px;
            color: #999;
          }
        }

        &.employee-cell {
          flex: 0 0 150px;
          display: flex;
          align-items: center;
          gap: 8px;
          background: #fafafa;

          .employee-avatar {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background: #409eff;
            color: #fff;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
          }

          .employee-info {
            .employee-name {
              font-weight: 500;
              font-size: 14px;
            }

            .employee-no {
              font-size: 12px;
              color: #999;
            }
          }
        }

        &.day-cell {
          flex: 1;
          min-height: 60px;
        }

        &.shift-cell {
          position: relative;
          min-height: 80px;
        }
      }
    }

    .schedule-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 6px 8px;
      margin-bottom: 4px;
      background: #fff;
      border: 1px solid #e4e7ed;
      border-left: 4px solid #409eff;
      border-radius: 4px;
      cursor: pointer;
      transition: all 0.2s;

      &:hover {
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        transform: translateY(-1px);
      }

      &.swapped {
        border-style: dashed;
      }

      &.confirmed {
        background: #f0f9eb;
      }

      .employee-name {
        font-size: 13px;
        color: #333;
      }
    }

    .schedule-item-small {
      padding: 4px 6px;
      margin-bottom: 2px;
      border-radius: 3px;
      color: #fff;
      font-size: 11px;
      text-align: center;
      cursor: pointer;

      &:hover {
        opacity: 0.8;
      }
    }

    .add-schedule-btn {
      position: absolute;
      bottom: 4px;
      right: 4px;
      width: 24px;
      height: 24px;
      border-radius: 50%;
      background: #f5f7fa;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      opacity: 0;
      transition: opacity 0.2s;
      color: #909399;

      &:hover {
        background: #409eff;
        color: #fff;
      }
    }

    .calendar-row:hover .add-schedule-btn {
      opacity: 1;
    }
  }

  .generate-tips {
    margin-top: 16px;

    ul {
      margin: 8px 0 0 0;
      padding-left: 20px;

      li {
        font-size: 12px;
        color: #666;
        line-height: 1.8;
      }
    }
  }

  .weekday-small {
    font-size: 11px;
    color: #999;
  }
}

@media (max-width: 768px) {
  .schedule-calendar-page {
    padding: 16px 0;

    .container {
      padding: 0 12px;
    }

    .page-header {
      h1 {
        font-size: 20px;
      }
    }

    .legend-bar {
      gap: 8px;

      .legend-item {
        .legend-text {
          font-size: 10px;
        }
      }
    }
  }
}
</style>
