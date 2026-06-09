<template>
  <div class="leave-request-page">
    <div class="container">
      <div class="page-header">
        <h1>请假申请</h1>
        <el-button type="primary" @click="showCreateDialog">
          <el-icon><Plus /></el-icon>
          申请请假
        </el-button>
      </div>

      <el-tabs v-model="activeTab">
        <el-tab-pane label="我的申请" name="my">
          <el-card>
            <el-table :data="myRequests" style="width: 100%" v-loading="loading.my">
              <el-table-column prop="leaveType" label="类型" width="100">
                <template #default="{ row }">
                  <el-tag :type="leaveTypeMap[row.leaveType]?.type || 'info'" size="small">
                    {{ leaveTypeMap[row.leaveType]?.label || row.leaveType }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="日期" width="200">
                <template #default="{ row }">
                  {{ row.startDate }} 至 {{ row.endDate }}
                </template>
              </el-table-column>
              <el-table-column label="时间" width="150">
                <template #default="{ row }">
                  {{ row.startTime }} - {{ row.endTime }}
                </template>
              </el-table-column>
              <el-table-column prop="reason" label="原因" min-width="150" show-overflow-tooltip />
              <el-table-column prop="status" label="状态" width="100">
                <template #default="{ row }">
                  <el-tag :type="statusMap[row.status]?.type || 'info'" size="small">
                    {{ statusMap[row.status]?.label || row.status }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="审批" width="150">
                <template #default="{ row }">
                  <div v-if="row.approverId">
                    <div>{{ row.approvalRemark || '-' }}</div>
                    <div class="approved-at">{{ row.approvedAt || '' }}</div>
                  </div>
                  <span v-else>-</span>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="120" fixed="right">
                <template #default="{ row }">
                  <el-button
                    v-if="row.status === 'pending'"
                    size="small"
                    type="danger"
                    @click="handleCancel(row)"
                  >
                    撤销
                  </el-button>
                  <el-button
                    size="small"
                    @click="showDetail(row)"
                  >
                    详情
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-tab-pane>

        <el-tab-pane label="待审批" name="pending" v-if="isAdmin">
          <el-card>
            <el-table :data="pendingRequests" style="width: 100%" v-loading="loading.pending">
              <el-table-column label="申请人" width="120">
                <template #default="{ row }">
                  {{ row.employee?.user?.nickname || '-' }}
                </template>
              </el-table-column>
              <el-table-column prop="leaveType" label="类型" width="100">
                <template #default="{ row }">
                  <el-tag :type="leaveTypeMap[row.leaveType]?.type || 'info'" size="small">
                    {{ leaveTypeMap[row.leaveType]?.label || row.leaveType }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="日期" width="200">
                <template #default="{ row }">
                  {{ row.startDate }} 至 {{ row.endDate }}
                </template>
              </el-table-column>
              <el-table-column prop="reason" label="原因" min-width="150" show-overflow-tooltip />
              <el-table-column label="申请时间" width="180">
                <template #default="{ row }">
                  {{ row.createdAt }}
                </template>
              </el-table-column>
              <el-table-column label="操作" width="200" fixed="right">
                <template #default="{ row }">
                  <el-button
                    size="small"
                    type="success"
                    @click="handleApprove(row)"
                  >
                    通过
                  </el-button>
                  <el-button
                    size="small"
                    type="danger"
                    @click="handleReject(row)"
                  >
                    拒绝
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-tab-pane>

        <el-tab-pane label="全部申请" name="all" v-if="isAdmin">
          <el-card>
            <el-table :data="allRequests" style="width: 100%" v-loading="loading.all">
              <el-table-column label="申请人" width="120">
                <template #default="{ row }">
                  {{ row.employee?.user?.nickname || '-' }}
                </template>
              </el-table-column>
              <el-table-column prop="leaveType" label="类型" width="100">
                <template #default="{ row }">
                  <el-tag :type="leaveTypeMap[row.leaveType]?.type || 'info'" size="small">
                    {{ leaveTypeMap[row.leaveType]?.label || row.leaveType }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="日期" width="200">
                <template #default="{ row }">
                  {{ row.startDate }} 至 {{ row.endDate }}
                </template>
              </el-table-column>
              <el-table-column prop="status" label="状态" width="100">
                <template #default="{ row }">
                  <el-tag :type="statusMap[row.status]?.type || 'info'" size="small">
                    {{ statusMap[row.status]?.label || row.status }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="120" fixed="right">
                <template #default="{ row }">
                  <el-button size="small" @click="showDetail(row)">详情</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-tab-pane>
      </el-tabs>
    </div>

    <el-dialog
      v-model="createDialogVisible"
      title="申请请假"
      width="500px"
    >
      <el-form :model="leaveForm" label-width="100px">
        <el-form-item label="请假类型" required>
          <el-select v-model="leaveForm.leaveType">
            <el-option
              v-for="(item, key) in leaveTypeMap"
              :key="key"
              :label="item.label"
              :value="key"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="开始日期" required>
          <el-date-picker
            v-model="leaveForm.startDate"
            type="date"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item label="结束日期" required>
          <el-date-picker
            v-model="leaveForm.endDate"
            type="date"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item label="开始时间">
          <el-time-picker
            v-model="leaveForm.startTime"
            format="HH:mm"
            value-format="HH:mm"
          />
        </el-form-item>
        <el-form-item label="结束时间">
          <el-time-picker
            v-model="leaveForm.endTime"
            format="HH:mm"
            value-format="HH:mm"
          />
        </el-form-item>
        <el-form-item label="请假原因" required>
          <el-input
            v-model="leaveForm.reason"
            type="textarea"
            :rows="3"
            placeholder="请输入请假原因"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">提交申请</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="detailDialogVisible"
      title="请假详情"
      width="500px"
    >
      <el-descriptions v-if="currentRequest" :column="1" border>
        <el-descriptions-item label="申请人">
          {{ currentRequest.employee?.user?.nickname || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="请假类型">
          <el-tag :type="leaveTypeMap[currentRequest.leaveType]?.type || 'info'">
            {{ leaveTypeMap[currentRequest.leaveType]?.label || currentRequest.leaveType }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="日期">
          {{ currentRequest.startDate }} 至 {{ currentRequest.endDate }}
        </el-descriptions-item>
        <el-descriptions-item label="时间">
          {{ currentRequest.startTime }} - {{ currentRequest.endTime }}
        </el-descriptions-item>
        <el-descriptions-item label="原因">
          {{ currentRequest.reason }}
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="statusMap[currentRequest.status]?.type || 'info'">
            {{ statusMap[currentRequest.status]?.label || currentRequest.status }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item v-if="currentRequest.approverId" label="审批意见">
          {{ currentRequest.approvalRemark || '-' }}
        </el-descriptions-item>
        <el-descriptions-item v-if="currentRequest.approvedAt" label="审批时间">
          {{ currentRequest.approvedAt }}
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <el-dialog
      v-model="approveDialogVisible"
      title="审批请假"
      width="400px"
    >
      <el-form :model="approveForm" label-width="80px">
        <el-form-item label="审批结果">
          <el-radio-group v-model="approveForm.status">
            <el-radio value="approved">通过</el-radio>
            <el-radio value="rejected">拒绝</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="审批意见">
          <el-input
            v-model="approveForm.approvalRemark"
            type="textarea"
            :rows="2"
            placeholder="请输入审批意见（可选）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="approveDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitApprove">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import {
  getMyLeaveRequests,
  getLeaveRequestList,
  createLeaveRequest,
  approveLeaveRequest,
  cancelLeaveRequest
} from '@/api/leaveRequest'
import type {
  LeaveRequest,
  LeaveRequestCreate,
  LeaveRequestApprove,
  RequestStatus
} from '@/types'

const userStore = useUserStore()
const isAdmin = computed(() => userStore.user?.role === 'admin')

const activeTab = ref('my')

const myRequests = ref<LeaveRequest[]>([])
const pendingRequests = ref<LeaveRequest[]>([])
const allRequests = ref<LeaveRequest[]>([])

const loading = reactive({
  my: false,
  pending: false,
  all: false
})

const leaveTypeMap: Record<string, { label: string; type: string } = {
  annual: { label: '年假', type: 'primary' },
  sick: { label: '病假', type: 'danger' },
  personal: { label: '事假', type: 'warning' },
  maternity: { label: '产假', type: 'success' },
  paternity: { label: '陪产假', type: 'success' },
  other: { label: '其他', type: 'info' }
}

const statusMap: Record<string, { label: string; type: string } = {
  pending: { label: '待审批', type: 'warning' },
  approved: { label: '已通过', type: 'success' },
  rejected: { label: '已拒绝', type: 'danger' },
  cancelled: { label: '已撤销', type: 'info' }
}

const createDialogVisible = ref(false)
const leaveForm = reactive<LeaveRequestCreate>({
  leaveType: 'annual',
  startDate: '',
  endDate: '',
  startTime: '09:00',
  endTime: '18:00',
  reason: ''
})

const detailDialogVisible = ref(false)
const currentRequest = ref<LeaveRequest | null>(null)

const approveDialogVisible = ref(false)
const approvingRequest = ref<LeaveRequest | null>(null)
const approveForm = reactive<LeaveRequestApprove>({
  status: 'approved' as RequestStatus,
  approvalRemark: ''
})

function showCreateDialog() {
  leaveForm.leaveType = 'annual'
  leaveForm.startDate = ''
  leaveForm.endDate = ''
  leaveForm.startTime = '09:00'
  leaveForm.endTime = '18:00'
  leaveForm.reason = ''
  createDialogVisible.value = true
}

async function handleSubmit() {
  if (!leaveForm.startDate || !leaveForm.endDate || !leaveForm.reason) {
    ElMessage.warning('请填写完整信息')
    return
  }
  try {
    await createLeaveRequest(leaveForm)
    ElMessage.success('申请提交成功')
    createDialogVisible.value = false
    loadMyRequests()
  } catch (e) {
    console.error(e)
  }
}

function showDetail(request: LeaveRequest) {
  currentRequest.value = request
  detailDialogVisible.value = true
}

function handleApprove(request: LeaveRequest) {
  approvingRequest.value = request
  approveForm.status = 'approved'
  approveForm.approvalRemark = ''
  approveDialogVisible.value = true
}

function handleReject(request: LeaveRequest) {
  approvingRequest.value = request
  approveForm.status = 'rejected'
  approveForm.approvalRemark = ''
  approveDialogVisible.value = true
}

async function handleSubmitApprove() {
  if (!approvingRequest.value) return
  try {
    await approveLeaveRequest(approvingRequest.value.id, approveForm)
    ElMessage.success('审批完成')
    approveDialogVisible.value = false
    loadPendingRequests()
  } catch (e) {
    console.error(e)
  }
}

async function handleCancel(request: LeaveRequest) {
  try {
    await ElMessageBox.confirm('确定要撤销这个请假申请吗？', '确认撤销', {
      type: 'warning'
    })
    await cancelLeaveRequest(request.id)
    ElMessage.success('已撤销')
    loadMyRequests()
  } catch (e) {
    if (e !== 'cancel') console.error(e)
  }
}

async function loadMyRequests() {
  loading.my = true
  try {
    const res = await getMyLeaveRequests({ page: 1, pageSize: 100 })
    myRequests.value = res.items
  } catch (e) {
    console.error(e)
  } finally {
    loading.my = false
  }
}

async function loadPendingRequests() {
  loading.pending = true
  try {
    const res = await getLeaveRequestList({ page: 1, pageSize: 100, status: 'pending' })
    pendingRequests.value = res.items
  } catch (e) {
    console.error(e)
  } finally {
    loading.pending = false
  }
}

async function loadAllRequests() {
  loading.all = true
  try {
    const res = await getLeaveRequestList({ page: 1, pageSize: 100 })
    allRequests.value = res.items
  } catch (e) {
    console.error(e)
  } finally {
    loading.all = false
  }
}

onMounted(() => {
  loadMyRequests()
  if (isAdmin.value) {
    loadPendingRequests()
    loadAllRequests()
  }
})
</script>

<style scoped lang="scss">
.leave-request-page {
  min-height: 100vh;
  background: #f5f7fa;
  padding: 32px 0;

  .container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 0 24px;
  }

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;

    h1 {
      font-size: 28px;
      margin: 0;
      color: #333;
    }
  }

  .approved-at {
    font-size: 12px;
    color: #999;
  }
}

@media (max-width: 768px) {
  .leave-request-page {
    padding: 16px 0;

    .container {
      padding: 0 12px;
    }

    .page-header h1 {
      font-size: 20px;
    }
  }
}
</style>
