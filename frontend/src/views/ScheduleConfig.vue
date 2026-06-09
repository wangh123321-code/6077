<template>
  <div class="schedule-config-page">
    <div class="container">
      <div class="page-header">
        <h1>排班配置</h1>
      </div>

      <el-tabs v-model="activeTab" class="config-tabs">
        <el-tab-pane label="班次管理" name="shifts">
          <el-card class="config-card">
            <template #header>
              <div class="card-header">
                <span>班次列表</span>
                <el-button type="primary" @click="showShiftDialog()">
                  <el-icon><Plus /></el-icon>
                  添加班次
                </el-button>
              </div>
            </template>

            <el-table :data="shifts" style="width: 100%" v-loading="loading.shifts">
              <el-table-column prop="name" label="班次名称" width="120" />
              <el-table-column label="班次类型" width="100">
                <template #default="{ row }">
                  <el-tag :type="shiftTypeMap[row.shiftType]?.type || 'info'" size="small">
                    {{ shiftTypeMap[row.shiftType]?.label || row.shiftType }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="时间" width="200">
                <template #default="{ row }">
                  {{ row.startTime }} - {{ row.endTime }}
                </template>
              </el-table-column>
              <el-table-column prop="minStaff" label="最少人数" width="100" />
              <el-table-column prop="maxStaff" label="最大人数" width="100">
                <template #default="{ row }">{{ row.maxStaff || '-' }}</template>
              </el-table-column>
              <el-table-column label="所需技能" min-width="150">
                <template #default="{ row }">
                  <el-tag
                    v-for="skill in row.requiredSkills" :key="skill" size="small" style="margin-right: 4px">
                    {{ skillLabelMap[skill] || skill }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="状态" width="80">
                <template #default="{ row }">
                  <el-tag :type="row.isActive ? 'success' : 'info'" size="small">
                    {{ row.isActive ? '启用' : '禁用' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="颜色" width="80">
                <template #default="{ row }">
                  <div class="color-preview" :style="{ background: row.color }"></div>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="150" fixed="right">
                <template #default="{ row }">
                  <el-button size="small" @click="showShiftDialog(row)">编辑</el-button>
                  <el-button type="danger" size="small" @click="handleDeleteShift(row)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-tab-pane>

        <el-tab-pane label="排班规则" name="rules">
          <el-card class="config-card">
            <template #header>
              <div class="card-header">
              <span>排班规则</span>
              <el-button type="primary" @click="showRuleDialog()">
                <el-icon><Plus /></el-icon>
                添加规则
              </el-button>
            </div>
            </template>

            <el-table :data="rules" style="width: 100%" v-loading="loading.rules">
              <el-table-column prop="name" label="规则名称" width="150" />
              <el-table-column prop="weeklyRestDays" label="每周休息" width="100" />
              <el-table-column prop="maxConsecutiveDays" label="连续上班" width="100" />
              <el-table-column prop="dailyMaxHours" label="日最大工时" width="100" />
              <el-table-column prop="weeklyMaxHours" label="周最大工时" width="100" />
              <el-table-column label="权重配置" min-width="200">
                <template #default="{ row }">
                  <div class="weight-tags">
                    <el-tag size="small" type="primary">偏好{{ row.preferenceWeight }}%</el-tag>
                    <el-tag size="small" type="success">技能{{ row.skillWeight }}%</el-tag>
                    <el-tag size="small" type="warning">工作量{{ row.workloadWeight }}%</el-tag>
                    <el-tag size="small" type="danger">历史{{ row.historyWeight }}%</el-tag>
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="默认" width="80">
                <template #default="{ row }">
                  <el-tag v-if="row.isDefault" type="success" size="small">默认</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="状态" width="80">
                <template #default="{ row }">
                  <el-tag :type="row.isActive ? 'success' : 'info'" size="small">
                    {{ row.isActive ? '启用' : '禁用' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="200" fixed="right">
                <template #default="{ row }">
                  <el-button size="small" @click="showRuleDialog(row)">编辑</el-button>
                  <el-button v-if="!row.isDefault" size="small" type="primary" size="small" @click="handleSetDefault(row)">设为默认</el-button>
                  <el-button type="danger" size="small" @click="handleDeleteRule(row)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-tab-pane>

        <el-tab-pane label="员工管理" name="employees">
          <el-card class="config-card">
            <template #header>
              <div class="card-header">
                <span>员工列表</span>
                <el-button type="primary" @click="showEmployeeDialog()">
                  <el-icon><Plus /></el-icon>
                  添加员工
                </el-button>
              </div>
            </template>

            <el-table :data="employees" style="width: 100%" v-loading="loading.employees">
              <el-table-column prop="employeeNo" label="工号" width="100" />
              <el-table-column label="姓名" width="120">
                <template #default="{ row }">
                  {{ row.user?.nickname || '-' }}
                </template>
              </el-table-column>
              <el-table-column prop="department" label="部门" width="100" />
              <el-table-column prop="position" label="职位" width="100" />
              <el-table-column prop="weeklyRestDays" label="周休天数" width="100" />
              <el-table-column prop="maxConsecutiveDays" label="连续上班" width="100" />
              <el-table-column label="技能" min-width="150">
                <template #default="{ row }">
                  <el-tag
                    v-for="skill in row.skills" :key="skill" size="small" style="margin-right: 4px">
                    {{ skillLabelMap[skill] || skill }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="状态" width="80">
                <template #default="{ row }">
                  <el-tag :type="row.isActive ? 'success' : 'info'" size="small">
                    {{ row.isActive ? '在职' : '离职' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="150" fixed="right">
                <template #default="{ row }">
                  <el-button size="small" @click="showEmployeeDialog(row)">编辑</el-button>
                  <el-button type="danger" size="small" @click="handleDeleteEmployee(row)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-tab-pane>
      </el-tabs>
    </div>

    <el-dialog
      v-model="shiftDialogVisible"
      :title="editingShift ? '编辑班次' : '添加班次'"
      width="600px"
    >
      <el-form :model="shiftForm" label-width="100px">
        <el-form-item label="班次名称" required>
          <el-input v-model="shiftForm.name" placeholder="请输入班次名称" />
        </el-form-item>
        <el-form-item label="班次类型" required>
          <el-select v-model="shiftForm.shiftType">
            <el-option label="早班" value="morning" />
            <el-option label="中班" value="afternoon" />
            <el-option label="晚班" value="night" />
            <el-option label="自定义" value="custom" />
          </el-select>
        </el-form-item>
        <el-form-item label="开始时间" required>
          <el-time-picker v-model="shiftForm.startTime" format="HH:mm" value-format="HH:mm" />
        </el-form-item>
        <el-form-item label="结束时间" required>
          <el-time-picker v-model="shiftForm.endTime" format="HH:mm" value-format="HH:mm" />
        </el-form-item>
        <el-form-item label="最少人数" required>
          <el-input-number v-model="shiftForm.minStaff" :min="1" />
        </el-form-item>
        <el-form-item label="最大人数">
          <el-input-number v-model="shiftForm.maxStaff" :min="1" />
        </el-form-item>
        <el-form-item label="所需技能">
          <el-select v-model="shiftForm.requiredSkills" multiple placeholder="请选择所需技能">
            <el-option
              v-for="(label, value) in skillLabelMap" :key="value" :label="label" :value="value" />
          </el-select>
        </el-form-item>
        <el-form-item label="班次颜色">
          <el-color-picker v-model="shiftForm.color" />
        </el-form-item>
        <el-form-item label="是否启用">
          <el-switch v-model="shiftForm.isActive" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="shiftForm.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="shiftDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveShift">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="ruleDialogVisible"
      :title="editingRule ? '编辑规则' : '添加规则'"
      width="700px"
    >
      <el-form :model="ruleForm" label-width="120px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="规则名称" required>
              <el-input v-model="ruleForm.name" placeholder="请输入规则名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="每周休息天数" required>
              <el-input-number v-model="ruleForm.weeklyRestDays" :min="0" :max="7" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="连续上班最大天数" required>
              <el-input-number v-model="ruleForm.maxConsecutiveDays" :min="1" :max="14" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="每日最大工时" required>
              <el-input-number v-model="ruleForm.dailyMaxHours" :min="1" :max="24" :step="0.5" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="每周最大工时" required>
              <el-input-number v-model="ruleForm.weeklyMaxHours" :min="1" :max="168" :step="0.5" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="班次间最小休息" required>
              <el-input-number v-model="ruleForm.minBreakHoursBetweenShifts" :min="0" :max="24" :step="0.5" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="夜班倍数" required>
              <el-input-number v-model="ruleForm.nightShiftPremium" :min="1" :max="3" :step="0.1" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="周末倍数" required>
              <el-input-number v-model="ruleForm.weekendPremium" :min="1" :max="3" :step="0.1" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="节假日倍数" required>
              <el-input-number v-model="ruleForm.holidayPremium" :min="1" :max="3" :step="0.1" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-divider content-position="left">算法权重（总和建议100）</el-divider>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="偏好权重" required>
              <el-slider v-model="ruleForm.preferenceWeight" :min="0" :max="100" show-input />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="技能权重" required>
              <el-slider v-model="ruleForm.skillWeight" :min="0" :max="100" show-input />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="工作量权重" required>
              <el-slider v-model="ruleForm.workloadWeight" :min="0" :max="100" show-input />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="历史排班权重" required>
              <el-slider v-model="ruleForm.historyWeight" :min="0" :max="100" show-input />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="设为默认">
          <el-switch v-model="ruleForm.isDefault" />
        </el-form-item>
        <el-form-item label="是否启用">
          <el-switch v-model="ruleForm.isActive" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="ruleForm.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="ruleDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveRule">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="employeeDialogVisible"
      :title="editingEmployee ? '编辑员工' : '添加员工'"
      width="600px"
    >
      <el-form :model="employeeForm" label-width="100px">
        <el-form-item label="关联用户" required>
          <el-select v-model="employeeForm.userId" placeholder="请选择用户" filterable>
          </el-select>
        </el-form-item>
        <el-form-item label="员工编号" required>
          <el-input v-model="employeeForm.employeeNo" placeholder="请输入员工编号" />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="部门">
              <el-input v-model="employeeForm.department" placeholder="请输入部门" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="职位">
              <el-input v-model="employeeForm.position" placeholder="请输入职位" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="入职日期">
          <el-date-picker v-model="employeeForm.hireDate" type="date" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="每周休息天数" required>
              <el-input-number v-model="employeeForm.weeklyRestDays" :min="0" :max="7" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="连续上班最大天数" required>
              <el-input-number v-model="employeeForm.maxConsecutiveDays" :min="1" :max="14" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="偏好班次类型">
          <el-select v-model="employeeForm.preferredShiftType" placeholder="请选择偏好班次">
            <el-option label="早班" value="morning" />
            <el-option label="中班" value="afternoon" />
            <el-option label="晚班" value="night" />
          </el-select>
        </el-form-item>
        <el-form-item label="不可用日期">
          <el-checkbox-group v-model="employeeForm.unavailableDays">
            <el-checkbox :label="0">周日</el-checkbox>
            <el-checkbox :label="1">周一</el-checkbox>
            <el-checkbox :label="2">周二</el-checkbox>
            <el-checkbox :label="3">周三</el-checkbox>
            <el-checkbox :label="4">周四</el-checkbox>
            <el-checkbox :label="5">周五</el-checkbox>
            <el-checkbox :label="6">周六</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="技能标签">
          <el-select v-model="employeeForm.skills" multiple placeholder="请选择技能">
            <el-option
              v-for="(label, value) in skillLabelMap" :key="value" :label="label" :value="value" />
          </el-select>
        </el-form-item>
        <el-form-item label="是否在职">
          <el-switch v-model="employeeForm.isActive" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="employeeForm.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="employeeDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveEmployee">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import {
  getShiftList,
  createShift,
  updateShift,
  deleteShift
} from '@/api/shift'
import {
  getSchedulingRuleList,
  createSchedulingRule,
  updateSchedulingRule,
  setDefaultRule,
  deleteSchedulingRule
} from '@/api/schedulingRule'
import {
  getEmployeeList,
  createEmployee,
  updateEmployee,
  deleteEmployee
} from '@/api/employee'
import type { Shift, SchedulingRule, Employee, ShiftCreate, SchedulingRuleCreate, EmployeeCreate, ShiftUpdate, SchedulingRuleUpdate, EmployeeUpdate } from '@/types'

const activeTab = ref('shifts')

const shifts = ref<Shift[]>([])
const rules = ref<SchedulingRule[]>([])
const employees = ref<Employee[]>([])

const loading = reactive({
  shifts: false,
  rules: false,
  employees: false
})

const shiftTypeMap: Record<string, { label: string; type: string } = {
  morning: { label: '早班', type: 'success' },
  afternoon: { label: '中班', type: 'warning' },
  night: { label: '晚班', type: 'danger' },
  custom: { label: '自定义', type: 'info' }
}

const skillLabelMap: Record<string, string> = {
  medication: '喂药',
  emergency: '应急处理',
  cleaning: '清洁',
  reception: '前台接待',
  cat_care: '猫咪护理',
  night_shift: '可值夜班'
}

const shiftDialogVisible = ref(false)
const editingShift = ref<Shift | null>(null)
const shiftForm = reactive<ShiftCreate>({
  name: '',
  shiftType: 'custom',
  startTime: '08:00',
  endTime: '16:00',
  minStaff: 1,
  maxStaff: undefined,
  requiredSkills: [],
  color: '#409EFF',
  isActive: true,
  remark: ''
})

const ruleDialogVisible = ref(false)
const editingRule = ref<SchedulingRule | null>(null)
const ruleForm = reactive<SchedulingRuleCreate>({
  name: '',
  weeklyRestDays: 2,
  maxConsecutiveDays: 5,
  dailyMaxHours: 8,
  weeklyMaxHours: 40,
  minBreakHoursBetweenShifts: 12,
  nightShiftPremium: 1.5,
  weekendPremium: 1.2,
  holidayPremium: 2.0,
  preferenceWeight: 10,
  skillWeight: 20,
  workloadWeight: 30,
  historyWeight: 15,
  isDefault: false,
  isActive: true,
  remark: ''
})

const employeeDialogVisible = ref(false)
const editingEmployee = ref<Employee | null>(null)
const employeeForm = reactive<EmployeeCreate>({
  userId: 0,
  employeeNo: '',
  department: '',
  position: '',
  hireDate: undefined,
  weeklyRestDays: 2,
  maxConsecutiveDays: 5,
  preferredShiftType: undefined,
  unavailableDays: [],
  skills: [],
  isActive: true,
  remark: ''
})

function showShiftDialog(shift?: Shift) {
  editingShift.value = shift || null
  if (shift) {
    Object.assign(shiftForm, shift)
  } else {
    Object.assign(shiftForm, {
      name: '',
      shiftType: 'custom',
      startTime: '08:00',
      endTime: '16:00',
      minStaff: 1,
      maxStaff: undefined,
      requiredSkills: [],
      color: '#409EFF',
      isActive: true,
      remark: ''
    })
  }
  shiftDialogVisible.value = true
}

async function handleSaveShift() {
  try {
    if (editingShift.value) {
      await updateShift(editingShift.value.id, shiftForm as ShiftUpdate)
      ElMessage.success('更新成功')
    } else {
      await createShift(shiftForm)
      ElMessage.success('创建成功')
    }
    shiftDialogVisible.value = false
    loadShifts()
  } catch (e) {
    console.error(e)
  }
}

async function handleDeleteShift(shift: Shift) {
  try {
    await ElMessageBox.confirm('确定要删除这个班次吗？', '确认删除', {
      type: 'warning'
    })
    await deleteShift(shift.id)
    ElMessage.success('删除成功')
    loadShifts()
  } catch (e) {
    if (e !== 'cancel') console.error(e)
  }
}

function showRuleDialog(rule?: SchedulingRule) {
  editingRule.value = rule || null
  if (rule) {
    Object.assign(ruleForm, rule)
  } else {
    Object.assign(ruleForm, {
      name: '',
      weeklyRestDays: 2,
      maxConsecutiveDays: 5,
      dailyMaxHours: 8,
      weeklyMaxHours: 40,
      minBreakHoursBetweenShifts: 12,
      nightShiftPremium: 1.5,
      weekendPremium: 1.2,
      holidayPremium: 2.0,
      preferenceWeight: 10,
      skillWeight: 20,
      workloadWeight: 30,
      historyWeight: 15,
      isDefault: false,
      isActive: true,
      remark: ''
    })
  }
  ruleDialogVisible.value = true
}

async function handleSaveRule() {
  try {
    if (editingRule.value) {
      await updateSchedulingRule(editingRule.value.id, ruleForm as SchedulingRuleUpdate)
      ElMessage.success('更新成功')
    } else {
      await createSchedulingRule(ruleForm)
      ElMessage.success('创建成功')
    }
    ruleDialogVisible.value = false
    loadRules()
  } catch (e) {
    console.error(e)
  }
}

async function handleSetDefault(rule: SchedulingRule) {
  try {
    await setDefaultRule(rule.id)
    ElMessage.success('已设为默认规则')
    loadRules()
  } catch (e) {
    console.error(e)
  }
}

async function handleDeleteRule(rule: SchedulingRule) {
  try {
    await ElMessageBox.confirm('确定要删除这个规则吗？', '确认删除', {
      type: 'warning'
    })
    await deleteSchedulingRule(rule.id)
    ElMessage.success('删除成功')
    loadRules()
  } catch (e) {
    if (e !== 'cancel') console.error(e)
  }
}

function showEmployeeDialog(employee?: Employee) {
  editingEmployee.value = employee || null
  if (employee) {
    Object.assign(employeeForm, employee)
  } else {
    Object.assign(employeeForm, {
      userId: 0,
      employeeNo: '',
      department: '',
      position: '',
      hireDate: undefined,
      weeklyRestDays: 2,
      maxConsecutiveDays: 5,
      preferredShiftType: undefined,
      unavailableDays: [],
      skills: [],
      isActive: true,
      remark: ''
    })
  }
  employeeDialogVisible.value = true
}

async function handleSaveEmployee() {
  try {
    if (editingEmployee.value) {
      await updateEmployee(editingEmployee.value.id, employeeForm as EmployeeUpdate)
      ElMessage.success('更新成功')
    } else {
      await createEmployee(employeeForm)
      ElMessage.success('创建成功')
    }
    employeeDialogVisible.value = false
    loadEmployees()
  } catch (e) {
    console.error(e)
  }
}

async function handleDeleteEmployee(employee: Employee) {
  try {
    await ElMessageBox.confirm('确定要删除这个员工吗？', '确认删除', {
      type: 'warning'
    })
    await deleteEmployee(employee.id)
    ElMessage.success('删除成功')
    loadEmployees()
  } catch (e) {
    if (e !== 'cancel') console.error(e)
  }
}

async function loadShifts() {
  loading.shifts = true
  try {
    const res = await getShiftList({ page: 1, pageSize: 100 })
    shifts.value = res.items
  } catch (e) {
    console.error(e)
  } finally {
    loading.shifts = false
  }
}

async function loadRules() {
  loading.rules = true
  try {
    const res = await getSchedulingRuleList({ page: 1, pageSize: 100 })
    rules.value = res.items
  } catch (e) {
    console.error(e)
  } finally {
    loading.rules = false
  }
}

async function loadEmployees() {
  loading.employees = true
  try {
    const res = await getEmployeeList({ page: 1, pageSize: 100 })
    employees.value = res.items
  } catch (e) {
    console.error(e)
  } finally {
    loading.employees = false
  }
}

onMounted(() => {
  loadShifts()
  loadRules()
  loadEmployees()
})
</script>

<style scoped lang="scss">
.schedule-config-page {
  min-height: 100vh;
  background: #f5f7fa;
  padding: 32px 0;

  .container {
    max-width: 1400px;
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

  .config-tabs {
    :deep(.el-tabs__header) {
      background: #fff;
      padding: 0 16px;
      margin: 0;
    }
  }

  .config-card {
    margin-bottom: 24px;

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .color-preview {
      width: 24px;
      height: 24px;
      border-radius: 4px;
      border: 1px solid #eee;
    }

    .weight-tags {
      display: flex;
      flex-wrap: wrap;
      gap: 4px;
    }
  }
}

@media (max-width: 768px) {
  .schedule-config-page {
    padding: 16px 0;

    .container {
      padding: 0 12px;
    }

    .page-header h1 {
      font-size: 20px;
    }

    .config-card {
      :deep(.el-table) {
        font-size: 12px;
      }
    }
  }
}
</style>
