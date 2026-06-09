<template>
  <div class="attendance-report-page">
    <div class="container">
      <div class="page-header">
        <h1>考勤报表</h1>
      </div>

      <el-card class="filter-card">
        <el-form :inline="true" :model="filterForm" class="filter-form">
          <el-form-item label="开始日期">
            <el-date-picker
              v-model="filterForm.startDate"
              type="date"
              value-format="YYYY-MM-DD"
              placeholder="开始日期"
            />
          </el-form-item>
          <el-form-item label="结束日期">
            <el-date-picker
              v-model="filterForm.endDate"
              type="date"
              value-format="YYYY-MM-DD"
              placeholder="结束日期"
            />
          </el-form-item>
          <el-form-item label="员工">
            <el-select
              v-model="filterForm.employeeId"
              placeholder="全部员工"
              clearable
              filterable
            >
              <el-option
                v-for="emp in employeeList"
                :key="emp.id"
                :label="emp.user?.nickname + ' (' + emp.employeeNo + ')'"
                :value="emp.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="部门">
            <el-input
              v-model="filterForm.department"
              placeholder="请输入部门"
              clearable
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="loadReport">
              <el-icon><Search /></el-icon>
              查询
            </el-button>
            <el-button @click="exportReport">
              <el-icon><Download /></el-icon>
              导出
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <el-row :gutter="24" class="summary-row">
        <el-col :span="6">
          <el-card class="summary-card">
            <div class="summary-icon" style="background: #67c23a">
              <el-icon size="28" color="#fff"><User /></el-icon>
            </div>
            <div class="summary-content">
              <div class="summary-value">{{ summary.totalEmployees }}</div>
              <div class="summary-label">员工总数</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="summary-card">
            <div class="summary-icon" style="background: #409eff">
              <el-icon size="28" color="#fff"><Calendar /></el-icon>
            </div>
            <div class="summary-content">
              <div class="summary-value">{{ summary.totalWorkingDays }}</div>
              <div class="summary-label">应出勤天数</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="summary-card">
            <div class="summary-icon" style="background: #e6a23c">
              <el-icon size="28" color="#fff"><Clock /></el-icon>
            </div>
            <div class="summary-content">
              <div class="summary-value">{{ summary.totalOvertimeHours }}h</div>
              <div class="summary-label">总加班时长</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="summary-card">
            <div class="summary-icon" style="background: #f56c6c">
              <el-icon size="28" color="#fff"><Warning /></el-icon>
            </div>
            <div class="summary-content">
              <div class="summary-value">{{ summary.attendanceRate }}%</div>
              <div class="summary-label">平均出勤率</div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <el-card class="report-card">
        <el-table :data="reportData" style="width: 100%" v-loading="loading">
          <el-table-column prop="employeeName" label="员工" width="120" fixed="left" />
          <el-table-column prop="totalWorkingDays" label="应出勤" width="100" align="center" />
          <el-table-column prop="actualWorkingDays" label="实际出勤" width="100" align="center">
            <template #default="{ row }">
              <span class="highlight">{{ row.actualWorkingDays }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="lateCount" label="迟到" width="80" align="center">
            <template #default="{ row }">
              <span v-if="row.lateCount > 0" class="late">{{ row.lateCount }}</span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="earlyLeaveCount" label="早退" width="80" align="center">
            <template #default="{ row }">
              <span v-if="row.earlyLeaveCount > 0" class="early">{{ row.earlyLeaveCount }}</span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="absentCount" label="旷工" width="80" align="center">
            <template #default="{ row }">
              <span v-if="row.absentCount > 0" class="absent">{{ row.absentCount }}</span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="leaveCount" label="请假" width="80" align="center">
            <template #default="{ row }">
              <span v-if="row.leaveCount > 0" class="leave">{{ row.leaveCount }}</span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="totalOvertimeHours" label="加班(h)" width="100" align="center">
            <template #default="{ row }">
              <span v-if="row.totalOvertimeHours > 0" class="overtime">{{ row.totalOvertimeHours }}</span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="totalWorkHours" label="工时(h)" width="100" align="center" />
          <el-table-column prop="attendanceRate" label="出勤率" width="100" align="center" fixed="right">
            <template #default="{ row }">
              <el-tag
                :type="row.attendanceRate >= 95 ? 'success' : row.attendanceRate >= 80 ? 'warning' : 'danger'"
                size="small"
              >
                {{ row.attendanceRate }}%
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Download, User, Calendar, Clock, Warning } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import { getAttendanceReport } from '@/api/attendance'
import { getAllEmployees } from '@/api/employee'
import type { AttendanceStats, AttendanceReportRequest, Employee } from '@/types'

const filterForm = reactive<AttendanceReportRequest>({
  startDate: dayjs().startOf('month').format('YYYY-MM-DD'),
  endDate: dayjs().endOf('month').format('YYYY-MM-DD'),
  employeeId: undefined,
  department: ''
})

const reportData = ref<AttendanceStats[]>([])
const employeeList = ref<Employee[]>([])
const loading = ref(false)

const summary = computed(() => {
  if (reportData.value.length === 0) {
    return {
      totalEmployees: 0,
      totalWorkingDays: 0,
      totalOvertimeHours: 0,
      attendanceRate: 0
    }
  }
  
  const totalEmployees = reportData.value.length
  const totalWorkingDays = reportData.value.reduce((sum, r) => sum + r.totalWorkingDays, 0)
  const totalOvertimeHours = reportData.value.reduce((sum, r) => sum + r.totalOvertimeHours, 0)
  const avgAttendanceRate = reportData.value.reduce((sum, r) => sum + r.attendanceRate, 0) / totalEmployees
  
  return {
    totalEmployees,
    totalWorkingDays,
    totalOvertimeHours: totalOvertimeHours.toFixed(1),
    attendanceRate: avgAttendanceRate.toFixed(1)
  }
})

async function loadReport() {
  if (!filterForm.startDate || !filterForm.endDate) {
    ElMessage.warning('请选择日期范围')
    return
  }
  
  loading.value = true
  try {
    reportData.value = await getAttendanceReport(filterForm)
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

function exportReport() {
  if (reportData.value.length === 0) {
    ElMessage.warning('没有数据可导出')
    return
  }
  
  const headers = ['员工', '应出勤', '实际出勤', '迟到', '早退', '旷工', '请假', '加班(h)', '工时(h)', '出勤率(%)']
  const rows = reportData.value.map(r => [
    r.employeeName || '-',
    r.totalWorkingDays,
    r.actualWorkingDays,
    r.lateCount,
    r.earlyLeaveCount,
    r.absentCount,
    r.leaveCount,
    r.totalOvertimeHours,
    r.totalWorkHours,
    r.attendanceRate
  ])
  
  const csvContent = [
    headers.join(','),
    ...rows.map(row => row.join(','))
  ].join('\n')
  
  const BOM = '\uFEFF'
  const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  link.setAttribute('href', url)
  link.setAttribute('download', `考勤报表_${filterForm.startDate}_${filterForm.endDate}.csv`)
  link.style.visibility = 'hidden'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  
  ElMessage.success('导出成功')
}

async function loadEmployees() {
  try {
    employeeList.value = await getAllEmployees()
  } catch (e) {
    console.error(e)
  }
}

onMounted(() => {
  loadEmployees()
  loadReport()
})
</script>

<style scoped lang="scss">
.attendance-report-page {
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

  .filter-card {
    margin-bottom: 24px;

    .filter-form {
      display: flex;
      flex-wrap: wrap;
      gap: 16px;
    }
  }

  .summary-row {
    margin-bottom: 24px;

    .summary-card {
      display: flex;
      align-items: center;
      gap: 16px;

      .summary-icon {
        width: 56px;
        height: 56px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
      }

      .summary-content {
        .summary-value {
          font-size: 24px;
          font-weight: 700;
          color: #333;
        }

        .summary-label {
          font-size: 13px;
          color: #999;
        }
      }
    }
  }

  .report-card {
    :deep(.el-table) {
      .highlight {
        font-weight: 600;
        color: #67c23a;
      }

      .late,
      .early {
        color: #e6a23c;
        font-weight: 600;
      }

      .absent {
        color: #f56c6c;
        font-weight: 600;
      }

      .leave {
        color: #909399;
        font-weight: 600;
      }

      .overtime {
        color: #409eff;
        font-weight: 600;
      }
    }
  }
}

@media (max-width: 768px) {
  .attendance-report-page {
    padding: 16px 0;

    .container {
      padding: 0 12px;
    }

    .page-header h1 {
      font-size: 20px;
    }

    .filter-card {
      .filter-form {
        .el-form-item {
          margin-right: 0;
          margin-bottom: 12px;
        }
      }
    }
  }
}
</style>
