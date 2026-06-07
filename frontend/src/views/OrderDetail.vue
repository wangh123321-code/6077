<template>
  <div class="order-detail" v-loading="loading">
    <div v-if="order" class="container">
      <el-breadcrumb separator="/" class="breadcrumb">
        <el-breadcrumb-item :to="{ path: '/' }">
          <el-icon><House /></el-icon>
          首页
        </el-breadcrumb-item>
        <el-breadcrumb-item :to="{ path: '/orders' }">
          <el-icon><Tickets /></el-icon>
          订单列表
        </el-breadcrumb-item>
        <el-breadcrumb-item>订单详情</el-breadcrumb-item>
      </el-breadcrumb>

      <div class="order-status-banner">
        <div class="status-info">
          <el-icon class="status-icon"><CircleCheckFilled /></el-icon>
          <div>
            <h2>{{ getOrderStatusLabel(order.status) }}</h2>
            <p>{{ getStatusDescription(order.status) }}</p>
          </div>
        </div>
        <div class="order-no">
          订单号：{{ order.id }}
          <el-button type="text" size="small" @click="copyOrderNo">
            <el-icon><CopyDocument /></el-icon>
            复制
          </el-button>
        </div>
      </div>

      <div class="detail-grid">
        <div class="main-content">
          <el-card class="detail-card">
            <template #header>
              <div class="card-header">
                <el-icon><OfficeBuilding /></el-icon>
                <span>猫屋信息</span>
              </div>
            </template>

            <div v-if="order.catRoom" class="room-info">
              <div class="room-gallery">
                <el-carousel height="240px" :interval="4000" arrow="hover">
                  <el-carousel-item v-for="(img, idx) in order.catRoom.images" :key="idx">
                    <img :src="img" :alt="order.catRoom.name" class="room-image" />
                  </el-carousel-item>
                </el-carousel>
              </div>
              <div class="room-details">
                <h4>
                  {{ order.catRoom.name }}
                  <el-tag size="small" type="primary">{{ order.catRoom.type }}</el-tag>
                </h4>
                <p class="room-size">
                  <el-icon><Grid /></el-icon>
                  {{ order.catRoom.size }}
                </p>
                <div class="date-range">
                  <div class="date-item">
                    <span class="date-label">入住日期</span>
                    <span class="date-value">{{ order.checkInDate }}</span>
                  </div>
                  <div class="date-arrow">
                    <el-icon><Right /></el-icon>
                  </div>
                  <div class="date-item">
                    <span class="date-label">离店日期</span>
                    <span class="date-value">{{ order.checkOutDate }}</span>
                  </div>
                  <div class="date-nights">
                    <span class="nights-count">{{ getDaysDiff(order.checkInDate, order.checkOutDate) }}</span>
                    <span class="nights-label">晚</span>
                  </div>
                </div>
                <div class="room-facilities" v-if="order.catRoom.facilities.length > 0">
                  <el-tag
                    v-for="f in order.catRoom.facilities.slice(0, 5)"
                    :key="f"
                    size="small"
                    effect="plain"
                    type="info"
                  >
                    {{ f }}
                  </el-tag>
                </div>
                <p class="room-price">
                  <span class="price-label">房费</span>
                  <span class="price-value">¥{{ order.catRoom.price }}/晚</span>
                </p>
              </div>
            </div>
          </el-card>

          <el-card class="detail-card">
            <template #header>
              <div class="card-header">
                <el-icon><Goods /></el-icon>
                <span>增值服务</span>
              </div>
            </template>

            <el-empty
              v-if="order.services.length === 0"
              description="暂无增值服务"
              :image-size="80"
            />
            <div v-else class="services-list">
              <div
                v-for="service in order.services"
                :key="service.id"
                class="service-item"
              >
                <div class="service-icon" :class="service.category">
                  <el-icon v-if="service.category === '洗护'"><Odometer /></el-icon>
                  <el-icon v-else-if="service.category === '医疗'"><Stethoscope /></el-icon>
                  <el-icon v-else-if="service.category === '美容'"><MagicStick /></el-icon>
                  <el-icon v-else><Goods /></el-icon>
                </div>
                <div class="service-info">
                  <span class="service-name">{{ service.name }}</span>
                  <span class="service-desc">{{ service.description }}</span>
                  <span class="service-duration">
                    <el-icon><Timer /></el-icon>
                    {{ service.duration }}分钟
                  </span>
                </div>
                <span class="service-price">¥{{ service.price }}</span>
              </div>
            </div>
          </el-card>

          <el-card class="detail-card">
            <template #header>
              <div class="card-header">
                <el-icon><Avatar /></el-icon>
                <span>猫咪信息</span>
              </div>
            </template>

            <el-descriptions :column="3" border class="cat-info">
              <el-descriptions-item label="猫咪姓名">
                <span class="cat-field">{{ order.catName || '-' }}</span>
              </el-descriptions-item>
              <el-descriptions-item label="品种">
                <span class="cat-field">{{ order.catBreed || '-' }}</span>
              </el-descriptions-item>
              <el-descriptions-item label="年龄">
                <span class="cat-field">{{ order.catAge ? order.catAge + ' 岁' : '-' }}</span>
              </el-descriptions-item>
              <el-descriptions-item label="特殊要求" :span="3">
                <span class="cat-field">{{ order.specialRequirements || '无' }}</span>
              </el-descriptions-item>
            </el-descriptions>
          </el-card>

          <el-card v-if="order.paymentStatus === 'paid'" class="detail-card">
            <template #header>
              <div class="card-header">
                <el-icon><Service /></el-icon>
                <span>服务记录</span>
              </div>
            </template>

            <el-steps direction="vertical" :active="serviceRecords.length + 1" finish-status="success" class="service-timeline">
              <el-step
                v-for="(record, idx) in serviceRecords"
                :key="idx"
                :title="record.title"
                :description="record.description"
                :icon="record.icon"
              />
              <el-step
                v-if="order.status === 'paid'"
                title="服务进行中"
                description="猫咪正在享受专业服务"
                icon="Loading"
              />
              <el-step
                v-else-if="order.status === 'completed'"
                title="服务完成"
                description="猫咪已被主人接走"
                icon="CircleCheck"
              />
            </el-steps>
          </el-card>

          <el-card class="detail-card">
            <template #header>
              <div class="card-header">
                <el-icon><Wallet /></el-icon>
                <span>支付记录</span>
              </div>
            </template>

            <div class="payment-records">
              <div
                v-for="(record, idx) in paymentRecords"
                :key="idx"
                class="payment-item"
              >
                <div class="payment-icon" :class="record.type">
                  <el-icon><ChatDotRound v-if="record.method === 'wechat'" /></el-icon>
                  <el-icon v-else-if="record.method === 'alipay'"><CreditCard /></el-icon>
                  <el-icon v-else><Wallet /></el-icon>
                </div>
                <div class="payment-info">
                  <span class="payment-title">{{ record.title }}</span>
                  <span class="payment-time">{{ record.time }}</span>
                </div>
                <div class="payment-amount" :class="record.type">
                  {{ record.type === 'refund' ? '+' : '-' }}¥{{ record.amount }}
                </div>
              </div>
            </div>
          </el-card>
        </div>

        <div class="side-content">
          <el-card class="qrcode-card" v-if="order.paymentStatus === 'paid' && (order.status === 'confirmed' || order.status === 'paid')">
            <template #header>
              <div class="card-header">
                <el-icon><QRCode /></el-icon>
                <span>核销码</span>
              </div>
            </template>

            <div class="qrcode-section">
              <div class="qrcode-wrapper">
                <div class="qrcode-placeholder">
                  <el-icon size="64"><QRCode /></el-icon>
                  <p>扫码核销</p>
                </div>
              </div>
              <div class="verification-code">
                <span class="code-label">核销码</span>
                <span class="code-value">{{ verificationCode }}</span>
                <el-button type="text" size="small" @click="copyVerificationCode">
                  <el-icon><CopyDocument /></el-icon>
                  复制
                </el-button>
              </div>
              <el-alert
                title="请在入住时出示此核销码"
                type="info"
                :closable="false"
                show-icon
                class="qrcode-alert"
              />
            </div>
          </el-card>

          <el-card class="price-card">
            <template #header>
              <div class="card-header">
                <el-icon><Money /></el-icon>
                <span>费用明细</span>
              </div>
            </template>

            <div class="price-list">
              <div class="price-item">
                <span>房费 ({{ getDaysDiff(order.checkInDate, order.checkOutDate) }}晚)</span>
                <span>¥{{ roomTotal }}</span>
              </div>
              <div v-if="order.services.length > 0" class="price-item">
                <span>服务费</span>
                <span>¥{{ servicesTotal }}</span>
              </div>
              <div v-if="order.paymentMethod === 'balance'" class="price-item discount">
                <span>会员折扣</span>
                <span>-¥{{ discountAmount }}</span>
              </div>
              <div class="price-item total">
                <span>订单合计</span>
                <span class="amount">¥{{ order.totalPrice }}</span>
              </div>
            </div>

            <el-divider />

            <div class="payment-method-info">
              <div class="method-row">
                <span class="method-label">支付方式</span>
                <el-tag size="small">
                  <el-icon style="margin-right: 4px;">
                    <ChatDotRound v-if="order.paymentMethod === 'wechat'" />
                    <CreditCard v-else-if="order.paymentMethod === 'alipay'" />
                    <Wallet v-else-if="order.paymentMethod === 'balance'" />
                    <QuestionFilled v-else />
                  </el-icon>
                  {{ getPaymentMethodName(order.paymentMethod) }}
                </el-tag>
              </div>
              <div class="method-row">
                <span class="method-label">支付状态</span>
                <el-tag :type="paymentStatusMap[order.paymentStatus]?.type || 'info'" size="small">
                  {{ getPaymentStatusLabel(order.paymentStatus) }}
                </el-tag>
              </div>
              <div class="method-row">
                <span class="method-label">下单时间</span>
                <span class="method-value">{{ formatDateTime(order.createdAt) }}</span>
              </div>
            </div>
          </el-card>

          <div class="sticky-actions">
            <el-button
              v-if="order.paymentStatus === 'unpaid'"
              type="primary"
              size="large"
              class="action-btn"
              @click="handlePay"
            >
              <el-icon><Wallet /></el-icon>
              立即支付 ¥{{ order.totalPrice }}
            </el-button>
            <el-button
              v-if="order.status === 'paid'"
              type="primary"
              size="large"
              class="action-btn"
              @click="handleAddService"
            >
              <el-icon><Plus /></el-icon>
              加购服务
            </el-button>
            <el-button
              v-if="(order.status === 'pending' || order.status === 'confirmed') && order.paymentStatus !== 'paid'"
              type="danger"
              size="large"
              plain
              class="action-btn"
              @click="handleCancel"
            >
              <el-icon><Close /></el-icon>
              取消订单
            </el-button>
            <el-button
              v-if="order.paymentStatus === 'paid' && order.status !== 'completed' && order.status !== 'cancelled'"
              type="warning"
              size="large"
              plain
              class="action-btn"
              @click="handleRefund"
            >
              <el-icon><Refund /></el-icon>
              申请退款
            </el-button>
            <el-button
              v-if="order.status === 'completed'"
              type="success"
              size="large"
              class="action-btn"
              @click="handleReview"
            >
              <el-icon><Star /></el-icon>
              评价服务
            </el-button>
            <el-button
              v-if="order.status === 'completed'"
              size="large"
              plain
              class="action-btn"
              @click="handleReorder"
            >
              <el-icon><RefreshRight /></el-icon>
              再次预订
            </el-button>
            <el-button size="large" plain class="action-btn" @click="router.push('/orders')">
              <el-icon><ArrowLeft /></el-icon>
              返回列表
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, markRaw } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  House,
  Tickets,
  CircleCheckFilled,
  CopyDocument,
  OfficeBuilding,
  Grid,
  Right,
  Goods,
  Odometer,
  Stethoscope,
  MagicStick,
  Timer,
  Avatar,
  Service,
  Wallet,
  ChatDotRound,
  CreditCard,
  QRCode,
  Money,
  QuestionFilled,
  Plus,
  Close,
  Star,
  RefreshRight,
  ArrowLeft,
  CircleCheck,
  Loading,
  Refund
} from '@element-plus/icons-vue'
import { getBookingDetail, cancelBooking, payBooking } from '@/api/booking'
import {
  formatDateTime,
  getOrderStatusLabel,
  getPaymentStatusLabel,
  getPaymentMethodName,
  orderStatusMap,
  paymentStatusMap
} from '@/utils/payment'
import { getDaysDiff } from '@/utils/date'
import { useBookingStore } from '@/stores/booking'
import type { Booking } from '@/types'

const route = useRoute()
const router = useRouter()
const bookingStore = useBookingStore()

const loading = ref(false)
const order = ref<Booking | null>(null)

const mockOrder: Booking = {
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
    images: [
      'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=luxury%20cat%20room%20modern%20interior&image_size=landscape_16_9',
      'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=cozy%20cat%20bedroom%20with%20window&image_size=landscape_16_9',
      'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=cat%20playground%20indoor&image_size=landscape_16_9'
    ],
    facilities: ['空调', '24h监控', '独立卫生间', '自动喂食器', '猫爬架', '落地窗'],
    status: 'available'
  },
  checkInDate: '2024-01-15',
  checkOutDate: '2024-01-20',
  services: [
    { id: 1, name: '专业洗护', description: '包含洗澡、吹干、梳毛、指甲修剪', price: 128, duration: 60, category: '洗护', image: '' },
    { id: 2, name: '健康体检', description: '体温、心率、体重、皮肤、耳朵检查', price: 198, duration: 30, category: '医疗', image: '' }
  ],
  totalPrice: 1821,
  status: 'confirmed',
  paymentMethod: 'wechat',
  paymentStatus: 'paid',
  catName: '咪咪',
  catBreed: '英国短毛猫',
  catAge: 2,
  specialRequirements: '每天需要喂两次罐头，喜欢玩逗猫棒',
  createdAt: '2024-01-10 14:30:00'
}

const serviceRecords = computed(() => [
  { title: '订单创建', description: '2024-01-10 14:30:00', icon: markRaw(Loading) },
  { title: '支付成功', description: '2024-01-10 14:35:20', icon: markRaw(CircleCheck) },
  { title: '确认预订', description: '2024-01-10 15:00:00', icon: markRaw(CircleCheck) }
])

const paymentRecords = computed(() => [
  { title: '微信支付', method: 'wechat', time: '2024-01-10 14:35:20', amount: 1821, type: 'pay' }
])

const verificationCode = computed(() => {
  if (!order.value) return ''
  return 'CR' + String(order.value.id).padStart(6, '0')
})

const roomTotal = computed(() => {
  if (!order.value) return 0
  return (order.value.catRoom?.price || 0) * getDaysDiff(order.value.checkInDate, order.value.checkOutDate)
})

const servicesTotal = computed(() => {
  if (!order.value) return 0
  return order.value.services.reduce((sum, s) => sum + s.price, 0)
})

const discountAmount = computed(() => {
  if (!order.value || order.value.paymentMethod !== 'balance') return 0
  return Math.round((roomTotal.value + servicesTotal.value) * 0.05)
})

function getStatusDescription(status: string): string {
  const descMap: Record<string, string> = {
    pending: '请尽快完成支付以确认预订',
    confirmed: '预订已确认，请按时入住',
    paid: '猫咪正在享受专业服务',
    completed: '服务已完成，期待您的再次光临',
    cancelled: '订单已取消'
  }
  return descMap[status] || ''
}

function copyOrderNo() {
  if (!order.value) return
  navigator.clipboard.writeText(String(order.value.id))
  ElMessage.success('订单号已复制')
}

function copyVerificationCode() {
  navigator.clipboard.writeText(verificationCode.value)
  ElMessage.success('核销码已复制')
}

async function fetchDetail() {
  const id = Number(route.params.id)
  if (!id) return

  loading.value = true
  try {
    order.value = await getBookingDetail(id)
  } catch {
    order.value = { ...mockOrder, id }
  } finally {
    loading.value = false
  }
}

async function handlePay() {
  if (!order.value) return
  try {
    await ElMessageBox.confirm(
      `确认支付 ¥${order.value.totalPrice} 吗？`,
      '确认支付',
      {
        confirmButtonText: '确认支付',
        cancelButtonText: '取消',
        type: 'info'
      }
    )
    const res = await payBooking(order.value.id, 'wechat')
    ElMessage.success('支付链接已生成，请完成支付')
    console.log('Payment URL:', res.paymentUrl)
    fetchDetail()
  } catch {
  }
}

async function handleCancel() {
  if (!order.value) return
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
    await cancelBooking(order.value.id)
    ElMessage.success('订单已取消')
    fetchDetail()
  } catch {
  }
}

async function handleRefund() {
  if (!order.value) return
  try {
    await ElMessageBox.confirm(
      '确定要申请退款吗？退款将在3-5个工作日内原路返回。',
      '申请退款',
      {
        confirmButtonText: '确认申请',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    ElMessage.success('退款申请已提交，客服将在24小时内处理')
  } catch {
  }
}

function handleReview() {
  ElMessage.info('评价功能开发中')
}

function handleReorder() {
  if (order.value?.catRoom) {
    router.push(`/cat-rooms/${order.value.catRoomId}`)
  } else {
    router.push('/cat-rooms')
  }
}

function handleAddService() {
  ElMessage.info('加购服务功能开发中')
}

onMounted(() => {
  fetchDetail()
})
</script>

<style scoped lang="scss">
.order-detail {
  min-height: 100vh;
  background: #f5f7fa;
  padding: 32px 0;

  .container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 0 24px;
  }

  .breadcrumb {
    margin-bottom: 24px;
  }

  .order-status-banner {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: #fff;
    padding: 32px;
    border-radius: 12px;
    margin-bottom: 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;

    .status-info {
      display: flex;
      align-items: center;
      gap: 20px;

      .status-icon {
        font-size: 48px;
      }

      h2 {
        font-size: 24px;
        margin: 0 0 4px;
        font-weight: 600;
      }

      p {
        font-size: 14px;
        margin: 0;
        opacity: 0.9;
      }
    }

    .order-no {
      font-size: 14px;
      opacity: 0.9;

      .el-button {
        color: #fff;

        &:hover {
          color: #fff;
          opacity: 0.8;
        }
      }
    }
  }

  .detail-grid {
    display: grid;
    grid-template-columns: 1fr 380px;
    gap: 24px;

    @media (max-width: 1024px) {
      grid-template-columns: 1fr;
    }
  }

  .detail-card {
    margin-bottom: 24px;
    border-radius: 12px;
    border: none;

    .card-header {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 16px;
      font-weight: 600;
      color: #333;
    }

    h4 {
      font-size: 20px;
      margin: 0 0 8px;
      color: #333;
      display: flex;
      align-items: center;
      gap: 8px;
    }
  }

  .room-info {
    .room-gallery {
      margin-bottom: 20px;

      .room-image {
        width: 100%;
        height: 100%;
        object-fit: cover;
        border-radius: 8px;
      }
    }

    .room-details {
      .room-size {
        font-size: 14px;
        color: #999;
        margin: 0 0 16px;
        display: flex;
        align-items: center;
        gap: 6px;
      }

      .date-range {
        display: flex;
        align-items: center;
        gap: 16px;
        background: #f5f7fa;
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 16px;

        .date-item {
          flex: 1;

          .date-label {
            display: block;
            font-size: 12px;
            color: #999;
            margin-bottom: 4px;
          }

          .date-value {
            font-size: 16px;
            font-weight: 600;
            color: #333;
          }
        }

        .date-arrow {
          color: #999;
        }

        .date-nights {
          text-align: center;
          padding: 8px 16px;
          background: #409eff;
          color: #fff;
          border-radius: 20px;

          .nights-count {
            font-size: 20px;
            font-weight: 700;
          }

          .nights-label {
            font-size: 12px;
            margin-left: 2px;
          }
        }
      }

      .room-facilities {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        margin-bottom: 16px;
      }

      .room-price {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding-top: 16px;
        border-top: 1px solid #ebeef5;
        margin: 0;

        .price-label {
          font-size: 14px;
          color: #999;
        }

        .price-value {
          font-size: 20px;
          font-weight: 700;
          color: #f56c6c;
        }
      }
    }
  }

  .services-list {
    .service-item {
      display: flex;
      align-items: center;
      gap: 16px;
      padding: 16px;
      background: #f5f7fa;
      border-radius: 8px;
      margin-bottom: 12px;

      .service-icon {
        width: 48px;
        height: 48px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #fff;
        font-size: 24px;
        flex-shrink: 0;

        &.洗护 { background: #409eff; }
        &.医疗 { background: #67c23a; }
        &.美容 { background: #e6a23c; }
        &.other { background: #909399; }
      }

      .service-info {
        flex: 1;
        display: flex;
        flex-direction: column;
        gap: 4px;

        .service-name {
          font-size: 15px;
          font-weight: 600;
          color: #333;
        }

        .service-desc {
          font-size: 13px;
          color: #999;
        }

        .service-duration {
          font-size: 12px;
          color: #666;
          display: flex;
          align-items: center;
          gap: 4px;
        }
      }

      .service-price {
        font-size: 18px;
        font-weight: 700;
        color: #f56c6c;
      }
    }
  }

  .cat-info {
    .cat-field {
      font-size: 14px;
      color: #333;
      font-weight: 500;
    }
  }

  .service-timeline {
    padding: 16px 0;
  }

  .payment-records {
    .payment-item {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 12px 0;
      border-bottom: 1px solid #f0f2f5;

      &:last-child {
        border-bottom: none;
      }

      .payment-icon {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #fff;
        font-size: 20px;

        &.pay { background: #67c23a; }
        &.refund { background: #f56c6c; }
      }

      .payment-info {
        flex: 1;
        display: flex;
        flex-direction: column;
        gap: 2px;

        .payment-title {
          font-size: 14px;
          color: #333;
          font-weight: 500;
        }

        .payment-time {
          font-size: 12px;
          color: #999;
        }
      }

      .payment-amount {
        font-size: 16px;
        font-weight: 600;

        &.pay { color: #67c23a; }
        &.refund { color: #f56c6c; }
      }
    }
  }

  .qrcode-card {
    margin-bottom: 24px;
    border-radius: 12px;
    border: none;

    .qrcode-section {
      text-align: center;

      .qrcode-wrapper {
        display: flex;
        justify-content: center;
        margin-bottom: 20px;

        .qrcode-placeholder {
          width: 180px;
          height: 180px;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          border-radius: 12px;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          color: #fff;
          gap: 8px;

          p {
            font-size: 14px;
            margin: 0;
          }
        }
      }

      .verification-code {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
        margin-bottom: 16px;

        .code-label {
          font-size: 14px;
          color: #999;
        }

        .code-value {
          font-size: 24px;
          font-weight: 700;
          color: #333;
          letter-spacing: 4px;
        }
      }

      .qrcode-alert {
        margin-top: 16px;
      }
    }
  }

  .price-card {
    margin-bottom: 24px;
    border-radius: 12px;
    border: none;

    .price-list {
      .price-item {
        display: flex;
        justify-content: space-between;
        padding: 10px 0;
        font-size: 14px;
        color: #666;

        &.discount {
          color: #67c23a;

          span:last-child {
            color: #67c23a;
          }
        }

        &.total {
          font-size: 16px;
          font-weight: 600;
          color: #333;
          padding-top: 16px;
          margin-top: 8px;
          border-top: 1px solid #ebeef5;

          .amount {
            font-size: 32px;
            font-weight: 700;
            color: #f56c6c;
          }
        }
      }
    }

    .payment-method-info {
      margin-top: 8px;

      .method-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 0;
        font-size: 14px;

        .method-label {
          color: #999;
        }

        .method-value {
          color: #333;
          font-weight: 500;
        }
      }
    }
  }

  .sticky-actions {
    position: sticky;
    top: 24px;

    .action-btn {
      width: 100%;
      margin-bottom: 12px;
      height: 48px;
      font-size: 15px;
      border-radius: 24px;
    }
  }
}

@media (max-width: 768px) {
  .order-detail {
    .container {
      padding: 0 16px;
    }

    .order-status-banner {
      flex-direction: column;
      align-items: flex-start;
      gap: 16px;
      padding: 24px;

      .status-info {
        h2 {
          font-size: 20px;
        }
      }
    }

    .detail-grid {
      grid-template-columns: 1fr;
    }

    .room-info {
      .room-details {
        .date-range {
          flex-direction: column;

          .date-arrow {
            transform: rotate(90deg);
          }

          .date-nights {
            width: 100%;
          }
        }
      }
    }
  }
}
</style>
