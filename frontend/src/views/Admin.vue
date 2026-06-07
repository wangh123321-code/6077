<template>
  <div class="admin-page">
    <div class="container">
      <div class="page-header">
        <h1>后台管理</h1>
      </div>

      <el-tabs v-model="activeTab">
        <el-tab-pane label="数据概览" name="overview">
          <el-row :gutter="24" class="stats-row">
            <el-col :span="6">
              <el-card class="stat-card">
                <div class="stat-icon" style="background: #409eff">
                  <el-icon size="32" color="#fff"><User /></el-icon>
                </div>
                <div class="stat-content">
                  <div class="stat-value">{{ stats.totalUsers }}</div>
                  <div class="stat-label">总用户数</div>
                </div>
              </el-card>
            </el-col>
            <el-col :span="6">
              <el-card class="stat-card">
                <div class="stat-icon" style="background: #67c23a">
                  <el-icon size="32" color="#fff"><HomeFilled /></el-icon>
                </div>
                <div class="stat-content">
                  <div class="stat-value">{{ stats.totalRooms }}</div>
                  <div class="stat-label">猫屋总数</div>
                </div>
              </el-card>
            </el-col>
            <el-col :span="6">
              <el-card class="stat-card">
                <div class="stat-icon" style="background: #e6a23c">
                  <el-icon size="32" color="#fff"><Document /></el-icon>
                </div>
                <div class="stat-content">
                  <div class="stat-value">{{ stats.totalOrders }}</div>
                  <div class="stat-label">总订单数</div>
                </div>
              </el-card>
            </el-col>
            <el-col :span="6">
              <el-card class="stat-card">
                <div class="stat-icon" style="background: #f56c6c">
                  <el-icon size="32" color="#fff"><Money /></el-icon>
                </div>
                <div class="stat-content">
                  <div class="stat-value">¥{{ stats.totalRevenue }}</div>
                  <div class="stat-label">总收入</div>
                </div>
              </el-card>
            </el-col>
          </el-row>

          <el-row :gutter="24" class="charts-row">
            <el-col :span="12">
              <el-card class="chart-card">
                <template #header>
                  <h3>订单统计</h3>
                </template>
                <v-chart :option="orderChartOption" autoresize />
              </el-card>
            </el-col>
            <el-col :span="12">
              <el-card class="chart-card">
                <template #header>
                  <h3>房型预订占比</h3>
                </template>
                <v-chart :option="roomTypeChartOption" autoresize />
              </el-card>
            </el-col>
          </el-row>
        </el-tab-pane>

        <el-tab-pane label="订单管理" name="orders">
          <el-card>
            <el-table :data="adminOrders" style="width: 100%">
              <el-table-column prop="id" label="订单号" width="100" />
              <el-table-column prop="user" label="用户" width="120">
                <template #default="{ row }">{{ row.user?.username }}</template>
              </el-table-column>
              <el-table-column prop="catRoom" label="猫屋" width="150">
                <template #default="{ row }">{{ row.catRoom?.name }}</template>
              </el-table-column>
              <el-table-column prop="checkInDate" label="入住日期" width="120" />
              <el-table-column prop="checkOutDate" label="离店日期" width="120" />
              <el-table-column prop="totalPrice" label="金额" width="100">
                <template #default="{ row }">¥{{ row.totalPrice }}</template>
              </el-table-column>
              <el-table-column prop="status" label="状态" width="100">
                <template #default="{ row }">
                  <el-tag :type="orderStatusMap[row.status]?.type || 'info'" size="small">
                    {{ getOrderStatusLabel(row.status) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="150">
                <template #default="{ row }">
                  <el-button size="small" @click="handleViewOrder(row)">查看</el-button>
                  <el-button
                    v-if="row.status === 'pending'"
                    type="primary"
                    size="small"
                    @click="handleConfirmOrder(row)"
                  >
                    确认
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-tab-pane>

        <el-tab-pane label="猫屋管理" name="rooms">
          <el-card>
            <div class="table-header">
              <el-button type="primary" @click="handleAddRoom">
                <el-icon><Plus /></el-icon>
                添加猫屋
              </el-button>
            </div>
            <el-table :data="adminRooms" style="width: 100%">
              <el-table-column prop="id" label="ID" width="80" />
              <el-table-column prop="name" label="名称" width="150" />
              <el-table-column prop="type" label="类型" width="100" />
              <el-table-column prop="size" label="面积" width="100" />
              <el-table-column prop="price" label="价格" width="100">
                <template #default="{ row }">¥{{ row.price }}/晚</template>
              </el-table-column>
              <el-table-column prop="status" label="状态" width="100">
                <template #default="{ row }">
                  <el-tag
                    :type="row.status === 'available' ? 'success' : row.status === 'occupied' ? 'danger' : 'info'"
                    size="small"
                  >
                    {{ row.status === 'available' ? '可预订' : row.status === 'occupied' ? '已占用' : '维护中' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="150">
                <template #default="{ row }">
                  <el-button size="small" @click="handleEditRoom(row)">编辑</el-button>
                  <el-button type="danger" size="small" @click="handleDeleteRoom(row)">
                    删除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-tab-pane>

        <el-tab-pane label="用户管理" name="users">
          <el-card>
            <el-table :data="adminUsers" style="width: 100%">
              <el-table-column prop="id" label="ID" width="80" />
              <el-table-column prop="username" label="用户名" width="120" />
              <el-table-column prop="email" label="邮箱" width="200" />
              <el-table-column prop="phone" label="手机号" width="150" />
              <el-table-column prop="role" label="角色" width="100">
                <template #default="{ row }">
                  <el-tag :type="row.role === 'admin' ? 'danger' : 'primary'" size="small">
                    {{ row.role === 'admin' ? '管理员' : '普通用户' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="memberLevel" label="会员等级" width="100">
                <template #default="{ row }">Lv.{{ row.memberLevel }}</template>
              </el-table-column>
              <el-table-column prop="createdAt" label="注册时间" width="180" />
            </el-table>
          </el-card>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { User, HomeFilled, Document, Money, Plus } from '@element-plus/icons-vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, PieChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
} from 'echarts/components'
import { orderStatusMap, getOrderStatusLabel } from '@/utils/payment'
import type { Booking, CatRoom, User } from '@/types'

use([
  CanvasRenderer,
  BarChart,
  PieChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
])

const activeTab = ref('overview')

const stats = reactive({
  totalUsers: 1234,
  totalRooms: 50,
  totalOrders: 856,
  totalRevenue: 128500
})

const adminOrders = ref<Booking[]>([])
const adminRooms = ref<CatRoom[]>([])
const adminUsers = ref<User[]>([])

const orderChartOption = {
  tooltip: { trigger: 'axis' },
  xAxis: {
    type: 'category',
    data: ['1月', '2月', '3月', '4月', '5月', '6月']
  },
  yAxis: { type: 'value' },
  series: [
    {
      name: '订单数',
      type: 'bar',
      data: [120, 200, 150, 80, 70, 110],
      itemStyle: { color: '#409eff' }
    }
  ]
}

const roomTypeChartOption = {
  tooltip: { trigger: 'item' },
  series: [
    {
      name: '房型占比',
      type: 'pie',
      radius: ['40%', '70%'],
      data: [
        { value: 35, name: '标准型' },
        { value: 40, name: '豪华型' },
        { value: 25, name: 'VIP型' }
      ],
      color: ['#67c23a', '#409eff', '#e6a23c']
    }
  ]
}

function handleViewOrder(row: Booking) {
  ElMessage.info(`查看订单 ${row.id}`)
}

function handleConfirmOrder(row: Booking) {
  ElMessage.success(`订单 ${row.id} 已确认`)
}

function handleAddRoom() {
  ElMessage.info('添加猫屋功能开发中')
}

function handleEditRoom(row: CatRoom) {
  ElMessage.info(`编辑猫屋 ${row.name}`)
}

function handleDeleteRoom(row: CatRoom) {
  ElMessage.success(`猫屋 ${row.name} 已删除`)
}

onMounted(() => {
  // 模拟数据加载
})
</script>

<style scoped lang="scss">
.admin-page {
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

  .stats-row {
    margin-bottom: 24px;

    .stat-card {
      display: flex;
      align-items: center;
      gap: 16px;

      .stat-icon {
        width: 64px;
        height: 64px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
      }

      .stat-content {
        .stat-value {
          font-size: 28px;
          font-weight: 700;
          color: #333;
        }

        .stat-label {
          font-size: 14px;
          color: #999;
        }
      }
    }
  }

  .charts-row {
    .chart-card {
      h3 {
        font-size: 16px;
        margin: 0;
      }

      :deep(.v-chart) {
        height: 350px;
      }
    }
  }

  .table-header {
    margin-bottom: 16px;
    text-align: right;
  }
}
</style>
