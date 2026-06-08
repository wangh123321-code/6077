<template>
  <div class="order-list">
    <div class="container">
      <div class="page-header">
        <h1>
          <el-icon><Tickets /></el-icon>
          我的订单
        </h1>
        <p>查看和管理您的所有预订订单</p>
      </div>

      <div class="filter-tabs">
        <el-tabs v-model="activeTab" @tab-change="handleTabChange" class="order-tabs">
          <el-tab-pane label="全部" name="all">
            <template #label>
              <span class="tab-label">
                全部
                <el-badge v-if="orderCounts.all > 0" :value="orderCounts.all" class="tab-badge" />
              </span>
            </template>
          </el-tab-pane>
          <el-tab-pane label="待支付" name="unpaid">
            <template #label>
              <span class="tab-label">
                待支付
                <el-badge v-if="orderCounts.unpaid > 0" :value="orderCounts.unpaid" class="tab-badge" type="danger" />
              </span>
            </template>
          </el-tab-pane>
          <el-tab-pane label="待入住" name="confirmed">
            <template #label>
              <span class="tab-label">
                待入住
                <el-badge v-if="orderCounts.confirmed > 0" :value="orderCounts.confirmed" class="tab-badge" type="warning" />
              </span>
            </template>
          </el-tab-pane>
          <el-tab-pane label="入住中" name="paid">
            <template #label>
              <span class="tab-label">
                入住中
                <el-badge v-if="orderCounts.paid > 0" :value="orderCounts.paid" class="tab-badge" type="primary" />
              </span>
            </template>
          </el-tab-pane>
          <el-tab-pane label="已完成" name="completed">
            <template #label>
              <span class="tab-label">已完成</span>
            </template>
          </el-tab-pane>
          <el-tab-pane label="已取消" name="cancelled">
            <template #label>
              <span class="tab-label">已取消</span>
            </template>
          </el-tab-pane>
        </el-tabs>
      </div>

      <div v-loading="loading" class="orders-list">
        <el-empty
          v-if="orders.length === 0 && !loading"
          :description="`暂无${activeTab !== 'all' ? getOrderStatusLabel(activeTab) : ''}订单`"
        >
          <el-button type="primary" @click="router.push('/cat-rooms')">去预订</el-button>
        </el-empty>

        <el-card
          v-for="order in filteredOrders"
          :key="order.id"
          class="order-card"
          shadow="hover"
        >
          <div class="order-header">
            <div class="order-info">
              <span class="order-no">
                <el-icon><Document /></el-icon>
                订单号：{{ order.id }}
              </span>
              <span class="order-time">
                <el-icon><Clock /></el-icon>
                {{ formatDateTime(order.createdAt) }}
              </span>
            </div>
            <div class="order-status">
              <el-tag
                :type="orderStatusMap[order.status]?.type || 'info'"
                size="large"
                effect="light"
              >
                {{ getOrderStatusLabel(order.status) }}
              </el-tag>
            </div>
          </div>

          <div class="order-content" @click="goToDetail(order.id)">
            <div class="room-image">
              <img v-if="order.catRoom" :src="order.catRoom.images[0]" :alt="order.catRoom.name" />
              <div v-else class="image-placeholder">
                <el-icon size="48"><Picture /></el-icon>
              </div>
            </div>
            <div class="room-info">
              <h3 v-if="order.catRoom">
                {{ order.catRoom.name }}
                <el-tag size="small" type="primary" style="margin-left: 8px;">{{ order.catRoom.type }}</el-tag>
              </h3>
              <p v-if="order.catRoom" class="room-size">
                {{ order.catRoom.size }}
              </p>
              <p class="date-info">
                <el-icon><Calendar /></el-icon>
                {{ order.checkInDate }} 至 {{ order.checkOutDate }}
                <span class="nights">({{ getNights(order.checkInDate, order.checkOutDate) }}晚)</span>
              </p>
              <p v-if="order.catName" class="cat-info">
                <el-icon><Avatar /></el-icon>
                {{ order.catName }}（{{ order.catBreed }}，{{ order.catAge }}岁）
              </p>
              <div v-if="order.services.length > 0" class="services-info">
                <el-tag
                  v-for="service in order.services.slice(0, 3)"
                  :key="service.id"
                  size="small"
                  type="info"
                  effect="plain"
                >
                  {{ service.name }}
                </el-tag>
                <el-tag
                  v-if="order.services.length > 3"
                  size="small"
                  type="info"
                  effect="plain"
                >
                  +{{ order.services.length - 3 }}项服务
                </el-tag>
              </div>
            </div>
            <div class="order-price">
              <div class="price-label">订单金额</div>
              <div class="total-price">
                <span class="currency">¥</span>
                <span class="price">{{ order.totalPrice }}</span>
              </div>
              <el-tag
                :type="paymentStatusMap[order.paymentStatus]?.type || 'info'"
                size="small"
                effect="light"
                class="payment-status"
              >
                {{ getPaymentStatusLabel(order.paymentStatus) }}
              </el-tag>
            </div>
          </div>

          <div class="order-actions">
            <el-button
              v-if="order.paymentStatus === 'unpaid'"
              type="primary"
              size="small"
              @click.stop="handlePay(order)"
            >
              <el-icon><Wallet /></el-icon>
              立即支付
            </el-button>
            <el-button
              v-if="order.paymentStatus === 'unpaid'"
              size="small"
              @click.stop="handleRemindPay(order)"
            >
              <el-icon><Bell /></el-icon>
              支付提醒
            </el-button>
            <el-button
              v-if="(order.status === 'pending' || order.status === 'confirmed') && order.paymentStatus !== 'paid'"
              type="danger"
              plain
              size="small"
              @click.stop="handleCancel(order)"
            >
              <el-icon><Close /></el-icon>
              取消订单
            </el-button>
            <el-button
              v-if="order.status === 'completed'"
              type="success"
              size="small"
              @click.stop="handleReview(order)"
            >
              <el-icon><Star /></el-icon>
              评价服务
            </el-button>
            <el-button
              v-if="order.status === 'completed'"
              size="small"
              @click.stop="handleReorder(order)"
            >
              <el-icon><RefreshRight /></el-icon>
              再次预订
            </el-button>
            <el-button
              v-if="order.status === 'paid'"
              type="primary"
              plain
              size="small"
              @click.stop="handleAddService(order)"
            >
              <el-icon><Plus /></el-icon>
              加购服务
            </el-button>
            <el-button size="small" @click.stop="goToDetail(order.id)">
              <el-icon><View /></el-icon>
              查看详情
            </el-button>
          </div>
        </el-card>
      </div>

      <div v-if="total > 0" class="pagination">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :page-sizes="[5, 10, 20, 50]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="fetchOrders"
          background
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Tickets,
  Document,
  Clock,
  Picture,
  Calendar,
  Avatar,
  Wallet,
  Bell,
  Close,
  Star,
  RefreshRight,
  Plus,
  View
} from '@element-plus/icons-vue'
import { getBookingList, cancelBooking, payBooking } from '@/api/booking'
import {
  getOrderStatusLabel,
  getPaymentStatusLabel,
  orderStatusMap,
  paymentStatusMap
} from '@/utils/payment'
import { getDaysDiff, formatDateTime } from '@/utils/date'
import type { Booking } from '@/types'

const router = useRouter()

const loading = ref(false)
const orders = ref<Booking[]>([])
const total = ref(0)
const activeTab = ref('all')
const page = ref(1)
const pageSize = ref(10)

const mockOrders: Booking[] = [
  {
    id: 1001,
    userId: 1,
    catRoomId: 1,
    catRoom: {
      id: 1,
      name: '豪华大床房',
      type: '豪华型',
      size: '15㎡',
      price: 299,
      description: '',
      images: ['https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=luxury%20cat%20room%20modern&image_size=landscape_16_9'],
      facilities: [],
      status: 'available'
    },
    checkInDate: '2024-01-15',
    checkOutDate: '2024-01-20',
    services: [
      { id: 1, name: '专业洗护', description: '', price: 128, duration: 60, category: '洗护', image: '' },
      { id: 2, name: '健康体检', description: '', price: 198, duration: 30, category: '医疗', image: '' }
    ],
    totalPrice: 1821,
    status: 'confirmed',
    paymentMethod: 'wechat',
    paymentStatus: 'paid',
    catName: '咪咪',
    catBreed: '英短',
    catAge: 2,
    specialRequirements: '',
    createdAt: '2024-01-10 14:30:00'
  },
  {
    id: 1002,
    userId: 1,
    catRoomId: 2,
    catRoom: {
      id: 2,
      name: '标准双人间',
      type: '标准型',
      size: '10㎡',
      price: 199,
      description: '',
      images: ['https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=cozy%20cat%20room&image_size=landscape_16_9'],
      facilities: [],
      status: 'available'
    },
    checkInDate: '2024-01-05',
    checkOutDate: '2024-01-08',
    services: [],
    totalPrice: 597,
    status: 'pending',
    paymentMethod: '',
    paymentStatus: 'unpaid',
    catName: '豆豆',
    catBreed: '布偶',
    catAge: 1,
    specialRequirements: '',
    createdAt: '2024-01-03 10:20:00'
  },
  {
    id: 1003,
    userId: 1,
    catRoomId: 3,
    catRoom: {
      id: 3,
      name: 'VIP总统套房',
      type: 'VIP型',
      size: '25㎡',
      price: 499,
      description: '',
      images: ['https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=vip%20luxury%20cat%20suite&image_size=landscape_16_9'],
      facilities: [],
      status: 'available'
    },
    checkInDate: '2024-01-01',
    checkOutDate: '2024-01-03',
    services: [
      { id: 4, name: '美容造型', description: '', price: 268, duration: 90, category: '美容', image: '' }
    ],
    totalPrice: 1266,
    status: 'completed',
    paymentMethod: 'alipay',
    paymentStatus: 'paid',
    catName: '胖胖',
    catBreed: '橘猫',
    catAge: 3,
    specialRequirements: '喜欢吃罐头',
    createdAt: '2023-12-28 16:45:00'
  }
]

const orderCounts = computed(() => {
  const counts = { all: orders.value.length, unpaid: 0, confirmed: 0, paid: 0, completed: 0, cancelled: 0 }
  orders.value.forEach((order) => {
    if (order.paymentStatus === 'unpaid') counts.unpaid++
    if (order.status === 'confirmed') counts.confirmed++
    if (order.status === 'paid') counts.paid++
    if (order.status === 'completed') counts.completed++
    if (order.status === 'cancelled') counts.cancelled++
  })
  return counts
})

const filteredOrders = computed(() => {
  if (activeTab.value === 'all') return orders.value
  if (activeTab.value === 'unpaid') {
    return orders.value.filter((o) => o.paymentStatus === 'unpaid')
  }
  return orders.value.filter((o) => o.status === activeTab.value)
})

function getNights(checkIn: string, checkOut: string): number {
  return Math.max(1, getDaysDiff(checkIn, checkOut))
}

async function fetchOrders() {
  loading.value = true
  try {
    const res = await getBookingList({ page: page.value, pageSize: pageSize.value })
    orders.value = res.items.length > 0 ? res.items : mockOrders
    total.value = res.total > 0 ? res.total : mockOrders.length
  } catch {
    orders.value = mockOrders
    total.value = mockOrders.length
  } finally {
    loading.value = false
  }
}

function handleTabChange() {
  page.value = 1
  fetchOrders()
}

function handleSizeChange() {
  page.value = 1
  fetchOrders()
}

function goToDetail(id: number) {
  router.push(`/orders/${id}`)
}

async function handlePay(order: Booking) {
  try {
    const res = await payBooking(order.id, 'wechat')
    ElMessage.success('支付链接已生成，请完成支付')
    console.log('Payment URL:', res.paymentUrl)
  } catch {
    ElMessage.info('正在跳转到支付页面...')
    router.push(`/orders/${order.id}`)
  }
}

function handleRemindPay(_order: Booking) {
  ElMessage.info('支付提醒已发送，请在30分钟内完成支付')
}

async function handleCancel(order: Booking) {
  try {
    await ElMessageBox.confirm(
      '确定要取消该订单吗？取消后将无法恢复。',
      '取消订单',
      {
        confirmButtonText: '确定取消',
        cancelButtonText: '再想想',
        type: 'warning',
        confirmButtonClass: 'el-button--danger'
      }
    )
    await cancelBooking(order.id)
    ElMessage.success('订单已取消')
    fetchOrders()
  } catch {
  }
}

function handleReview(_order: Booking) {
  ElMessage.info('评价功能开发中')
}

function handleReorder(order: Booking) {
  if (order.catRoom) {
    router.push(`/cat-rooms/${order.catRoomId}`)
  } else {
    router.push('/cat-rooms')
  }
}

function handleAddService(_order: Booking) {
  ElMessage.info('加购服务功能开发中')
}

onMounted(() => {
  fetchOrders()
})
</script>

<style scoped lang="scss">
.order-list {
  min-height: 100vh;
  background: #f5f7fa;
  padding: 32px 0;

  .container {
    max-width: 1100px;
    margin: 0 auto;
    padding: 0 24px;
  }

  .page-header {
    margin-bottom: 24px;

    h1 {
      font-size: 28px;
      margin: 0 0 8px;
      color: #333;
      display: flex;
      align-items: center;
      gap: 12px;
      font-weight: 600;
    }

    p {
      font-size: 14px;
      color: #999;
      margin: 0;
    }
  }

  .filter-tabs {
    background: #fff;
    padding: 0 24px;
    border-radius: 12px;
    margin-bottom: 24px;

    .order-tabs {
      :deep(.el-tabs__nav-wrap::after) {
        background-color: #ebeef5;
      }

      :deep(.el-tabs__item) {
        font-size: 15px;
        font-weight: 500;
        color: #666;
        height: 56px;
        line-height: 56px;
      }

      :deep(.el-tabs__item.is-active) {
        color: #409eff;
      }

      .tab-label {
        display: flex;
        align-items: center;
        gap: 8px;

        .tab-badge {
          :deep(.el-badge__content) {
            font-size: 12px;
            padding: 0 6px;
            height: 18px;
            line-height: 18px;
          }
        }
      }
    }
  }

  .orders-list {
    .order-card {
      margin-bottom: 16px;
      border-radius: 12px;
      border: none;
      transition: all 0.3s;

      &:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
      }

      .order-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
        padding-bottom: 16px;
        border-bottom: 1px solid #f0f2f5;

        .order-info {
          display: flex;
          gap: 24px;
          font-size: 14px;
          color: #999;
          flex-wrap: wrap;

          .order-no,
          .order-time {
            display: flex;
            align-items: center;
            gap: 6px;
          }

          .order-no {
            color: #333;
            font-weight: 500;
          }
        }
      }

      .order-content {
        display: flex;
        gap: 20px;
        cursor: pointer;

        .room-image {
          width: 160px;
          height: 120px;
          border-radius: 8px;
          overflow: hidden;
          flex-shrink: 0;
          background: #f5f7fa;
          display: flex;
          align-items: center;
          justify-content: center;

          img {
            width: 100%;
            height: 100%;
            object-fit: cover;
          }

          .image-placeholder {
            color: #c0c4cc;
          }
        }

        .room-info {
          flex: 1;

          h3 {
            font-size: 18px;
            margin: 0 0 6px;
            color: #333;
            display: flex;
            align-items: center;
          }

          .room-size {
            font-size: 13px;
            color: #999;
            margin: 0 0 8px;
          }

          .date-info,
          .cat-info {
            font-size: 14px;
            color: #666;
            margin: 0 0 6px;
            display: flex;
            align-items: center;
            gap: 6px;

            .nights {
              color: #409eff;
              font-weight: 500;
            }
          }

          .services-info {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-top: 8px;
          }
        }

        .order-price {
          text-align: right;
          flex-shrink: 0;
          min-width: 140px;

          .price-label {
            font-size: 12px;
            color: #999;
            margin-bottom: 4px;
          }

          .total-price {
            margin-bottom: 8px;

            .currency {
              font-size: 14px;
              color: #f56c6c;
              vertical-align: top;
            }

            .price {
              font-size: 26px;
              font-weight: 700;
              color: #f56c6c;
            }
          }

          .payment-status {
            display: inline-block;
          }
        }
      }

      .order-actions {
        display: flex;
        justify-content: flex-end;
        gap: 12px;
        margin-top: 16px;
        padding-top: 16px;
        border-top: 1px solid #f0f2f5;
        flex-wrap: wrap;
      }
    }
  }

  .pagination {
    margin-top: 32px;
    display: flex;
    justify-content: center;
  }
}

@media (max-width: 768px) {
  .order-list {
    .container {
      padding: 0 16px;
    }

    .page-header {
      h1 {
        font-size: 22px;
      }
    }

    .orders-list {
      .order-card {
        .order-header {
          flex-direction: column;
          align-items: flex-start;
          gap: 12px;
        }

        .order-content {
          flex-direction: column;

          .room-image {
            width: 100%;
            height: 180px;
          }

          .order-price {
            text-align: left;
            min-width: auto;
          }
        }

        .order-actions {
          justify-content: flex-start;
        }
      }
    }
  }
}
</style>
