<template>
  <div class="booking-confirm">
    <div class="container">
      <el-steps :active="2" finish-status="success" class="booking-steps" simple>
        <el-step title="选择猫屋" icon="OfficeBuilding" />
        <el-step title="选择服务" icon="Goods" />
        <el-step title="确认预订" icon="Check" />
      </el-steps>

      <div class="confirm-content">
        <div class="booking-details">
          <el-card class="detail-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <h2>
                  <el-icon><OfficeBuilding /></el-icon>
                  预订信息
                </h2>
                <el-button type="primary" link @click="router.push('/cat-rooms')">
                  修改预订
                </el-button>
              </div>
            </template>

            <div v-if="bookingStore.selectedCatRoom" class="room-info">
              <div class="room-card">
                <img :src="bookingStore.selectedCatRoom.images[0]" :alt="bookingStore.selectedCatRoom.name" class="room-image" />
                <div class="room-details">
                  <h3>{{ bookingStore.selectedCatRoom.name }}</h3>
                  <p class="room-type">
                    <el-tag v-if="bookingStore.selectedCatRoom.area" size="small" type="primary">{{ bookingStore.selectedCatRoom.area }}㎡</el-tag>
                    <el-tag v-if="bookingStore.selectedCatRoom.floor" size="small" type="info">{{ bookingStore.selectedCatRoom.floor }}楼</el-tag>
                    <el-tag v-if="bookingStore.selectedCatRoom.location" size="small">{{ bookingStore.selectedCatRoom.location }}</el-tag>
                  </p>
                  <p class="room-price">¥{{ bookingStore.selectedCatRoom.price }}/晚</p>
                </div>
              </div>
              <div class="date-info">
                <div class="date-item">
                  <div class="date-icon">
                    <el-icon><Calendar /></el-icon>
                  </div>
                  <div class="date-content">
                    <span class="label">入住日期</span>
                    <span class="value">{{ bookingStore.checkInDate }}</span>
                  </div>
                </div>
                <div class="date-arrow">
                  <el-icon><Right /></el-icon>
                </div>
                <div class="date-item">
                  <div class="date-icon">
                    <el-icon><Calendar /></el-icon>
                  </div>
                  <div class="date-content">
                    <span class="label">离店日期</span>
                    <span class="value">{{ bookingStore.checkOutDate }}</span>
                  </div>
                </div>
                <div class="date-item nights">
                  <div class="date-icon highlight">
                    <el-icon><Clock /></el-icon>
                  </div>
                  <div class="date-content">
                    <span class="label">入住天数</span>
                    <span class="value highlight">{{ bookingStore.nights }} 晚</span>
                  </div>
                </div>
              </div>
            </div>

            <el-divider />

            <div v-if="bookingStore.selectedServices.length > 0" class="services-info">
              <h3>
                <el-icon><Goods /></el-icon>
                已选服务
              </h3>
              <div class="service-list">
                <div
                  v-for="service in bookingStore.selectedServices"
                  :key="service.id"
                  class="service-item"
                >
                  <div class="service-info">
                    <span class="service-name">{{ service.name }}</span>
                    <span class="service-desc">{{ service.description }}</span>
                  </div>
                  <span class="price">¥{{ service.price }}</span>
                </div>
              </div>
            </div>

            <el-divider />

            <div class="cat-info">
              <h3>
                <el-icon><Avatar /></el-icon>
                猫咪信息
              </h3>
              <div class="cat-details">
                <div class="cat-item">
                  <span class="label">姓名</span>
                  <span class="value">{{ bookingStore.catInfo.name }}</span>
                </div>
                <div class="cat-item">
                  <span class="label">品种</span>
                  <span class="value">{{ bookingStore.catInfo.breed }}</span>
                </div>
                <div class="cat-item">
                  <span class="label">年龄</span>
                  <span class="value">{{ bookingStore.catInfo.age }} 岁</span>
                </div>
                <div v-if="bookingStore.catInfo.specialRequirements" class="cat-item full-width">
                  <span class="label">特殊要求</span>
                  <span class="value">{{ bookingStore.catInfo.specialRequirements }}</span>
                </div>
              </div>
            </div>
          </el-card>
        </div>

        <div class="price-summary">
          <el-card class="price-card" shadow="hover">
            <template #header>
              <h2>
                <el-icon><Wallet /></el-icon>
                费用明细
              </h2>
            </template>

            <div class="price-items">
              <div class="price-item">
                <span>房费 ({{ bookingStore.nights }}晚 × ¥{{ bookingStore.selectedCatRoom?.price || 0 }})</span>
                <span>¥{{ bookingStore.priceInfo.roomPrice || bookingStore.calculatedRoomPrice }}</span>
              </div>
              <div v-if="bookingStore.selectedServices.length > 0" class="price-item">
                <span>服务费 ({{ bookingStore.selectedServices.length }}项)</span>
                <span>¥{{ bookingStore.priceInfo.servicePrice || bookingStore.calculatedServicePrice }}</span>
              </div>
              <div v-if="bookingStore.priceInfo.discount > 0" class="price-item discount">
                <span>会员优惠</span>
                <span>-¥{{ bookingStore.priceInfo.discount }}</span>
              </div>
            </div>

            <el-divider />

            <div class="total-price">
              <span>应付金额</span>
              <span class="amount">¥{{ bookingStore.priceInfo.totalPrice || bookingStore.calculatedTotalPrice }}</span>
            </div>

            <div class="payment-method">
              <h3>
                <el-icon><CreditCard /></el-icon>
                选择支付方式
              </h3>
              <el-radio-group v-model="selectedPayment" class="payment-group">
                <el-radio
                  v-for="method in paymentMethods"
                  :key="method.id"
                  :value="method.id"
                  class="payment-option"
                >
                  <div class="payment-card" :class="{ active: selectedPayment === method.id }">
                    <div class="payment-icon" :class="method.id">
                      <el-icon v-if="method.id === 'wechat'"><ChatDotRound /></el-icon>
                      <el-icon v-else-if="method.id === 'alipay'"><CreditCard /></el-icon>
                      <el-icon v-else-if="method.id === 'balance'"><Wallet /></el-icon>
                      <el-icon v-else><Money /></el-icon>
                    </div>
                    <div class="payment-info">
                      <span class="payment-name">{{ method.name }}</span>
                      <span class="payment-desc">{{ method.description }}</span>
                    </div>
                    <div class="payment-check" v-if="selectedPayment === method.id">
                      <el-icon><CircleCheckFilled /></el-icon>
                    </div>
                  </div>
                </el-radio>
              </el-radio-group>
            </div>

            <div class="member-discount" v-if="userStore.isLoggedIn && userStore.memberLevel > 1">
              <el-alert
                :title="`会员等级 Lv.${userStore.memberLevel}，可享受 ${10 - userStore.memberLevel}折 优惠`"
                type="success"
                :closable="false"
                show-icon
              />
            </div>

            <el-button
              type="primary"
              size="large"
              class="confirm-btn"
              :loading="submitting"
              :disabled="!canSubmit"
              @click="handleSubmit"
            >
              <el-icon><ShoppingCart /></el-icon>
              确认支付 ¥{{ bookingStore.priceInfo.totalPrice || bookingStore.calculatedTotalPrice }}
            </el-button>

            <div class="agreement">
              <el-checkbox v-model="agreeTerms">
                我已阅读并同意
                <a href="#" @click.prevent="showAgreement">《预订服务协议》</a>
                和
                <a href="#" @click.prevent="showPrivacy">《隐私政策》</a>
              </el-checkbox>
            </div>

            <div class="secure-info">
              <el-icon><Lock /></el-icon>
              <span>支付安全保障，您的支付信息将被加密处理</span>
            </div>
          </el-card>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  OfficeBuilding,
  Goods,
  Calendar,
  Right,
  Clock,
  Avatar,
  Wallet,
  CreditCard,
  ChatDotRound,
  Money,
  CircleCheckFilled,
  ShoppingCart,
  Lock
} from '@element-plus/icons-vue'
import { useBookingStore } from '@/stores/booking'
import { useUserStore } from '@/stores/user'
import { createBooking, payBooking } from '@/api/booking'
import { paymentMethods } from '@/utils/payment'

const router = useRouter()
const bookingStore = useBookingStore()
const userStore = useUserStore()

const submitting = ref(false)
const selectedPayment = ref('wechat')
const agreeTerms = ref(false)

const canSubmit = computed(() => {
  return (
    bookingStore.isValid &&
    selectedPayment.value &&
    agreeTerms.value &&
    !submitting.value
  )
})

async function handleSubmit() {
  if (!agreeTerms.value) {
    ElMessage.warning('请先同意服务协议和隐私政策')
    return
  }

  const totalPrice = bookingStore.priceInfo.totalPrice || bookingStore.calculatedTotalPrice

  try {
    await ElMessageBox.confirm(
      `确认支付 ¥${totalPrice} 吗？\n预订成功后将扣除相应款项`,
      '确认支付',
      {
        confirmButtonText: '确认支付',
        cancelButtonText: '取消',
        type: 'info'
      }
    )
  } catch {
    return
  }

  submitting.value = true
  try {
    const bookingData = bookingStore.getBookingData()
    const booking = await createBooking(bookingData)

    try {
      await payBooking(booking.id, selectedPayment.value)
      ElMessage.success('支付成功！')
    } catch {
      ElMessage.info('预订已提交，请在订单详情中完成支付')
    }

    bookingStore.resetBooking()
    router.push(`/orders/${booking.id}`)
  } finally {
    submitting.value = false
  }
}

function showAgreement() {
  ElMessageBox.alert(
    '预订服务协议内容...',
    '预订服务协议',
    {
      confirmButtonText: '我已阅读',
      dangerouslyUseHTMLString: true
    }
  )
}

function showPrivacy() {
  ElMessageBox.alert(
    '隐私政策内容...',
    '隐私政策',
    {
      confirmButtonText: '我已阅读',
      dangerouslyUseHTMLString: true
    }
  )
}

onMounted(async () => {
  if (!bookingStore.selectedCatRoom) {
    ElMessage.warning('请先选择猫屋')
    router.push('/cat-rooms')
    return
  }
  try {
    await bookingStore.calculatePrice()
  } catch {
    bookingStore.updateLocalPrice()
  }
})
</script>

<style scoped lang="scss">
.booking-confirm {
  min-height: 100vh;
  background: #f5f7fa;
  padding: 32px 0;

  .container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 0 24px;
  }

  .booking-steps {
    max-width: 600px;
    margin: 0 auto 40px;
    background: #fff;
    padding: 24px;
    border-radius: 12px;
  }

  .confirm-content {
    display: grid;
    grid-template-columns: 1fr 420px;
    gap: 24px;

    @media (max-width: 1024px) {
      grid-template-columns: 1fr;
    }
  }

  .detail-card,
  .price-card {
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    h2 {
      font-size: 20px;
      margin: 0;
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: 600;
    }

    h3 {
      font-size: 16px;
      margin: 0 0 16px;
      color: #333;
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: 600;
    }
  }

  .room-info {
    .room-card {
      display: flex;
      gap: 16px;
      padding: 16px;
      background: #f5f7fa;
      border-radius: 8px;
      margin-bottom: 20px;

      .room-image {
        width: 120px;
        height: 90px;
        object-fit: cover;
        border-radius: 8px;
      }

      .room-details {
        flex: 1;

        h3 {
          font-size: 18px;
          margin: 0 0 8px;
          color: #333;
          font-weight: 600;
        }

        .room-type {
          margin: 0 0 8px;
          display: flex;
          gap: 8px;
        }

        .room-price {
          font-size: 16px;
          font-weight: 600;
          color: #f56c6c;
          margin: 0;
        }
      }
    }

    .date-info {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 16px;
      background: linear-gradient(135deg, #ecf5ff 0%, #f5f7fa 100%);
      border-radius: 8px;

      .date-item {
        flex: 1;
        display: flex;
        align-items: center;
        gap: 12px;

        .date-icon {
          width: 40px;
          height: 40px;
          background: #fff;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #409eff;

          &.highlight {
            background: #409eff;
            color: #fff;
          }
        }

        .date-content {
          .label {
            display: block;
            font-size: 12px;
            color: #999;
            margin-bottom: 2px;
          }

          .value {
            font-size: 14px;
            color: #333;
            font-weight: 500;

            &.highlight {
              color: #409eff;
              font-size: 18px;
              font-weight: 700;
            }
          }
        }

        &.nights {
          .date-content {
            text-align: center;
          }
        }
      }

      .date-arrow {
        color: #999;
      }
    }
  }

  .service-list {
    .service-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 16px;
      background: #f5f7fa;
      border-radius: 8px;
      margin-bottom: 8px;

      .service-info {
        .service-name {
          display: block;
          font-size: 14px;
          font-weight: 500;
          color: #333;
          margin-bottom: 4px;
        }

        .service-desc {
          font-size: 12px;
          color: #999;
        }
      }

      .price {
        font-size: 16px;
        color: #f56c6c;
        font-weight: 600;
      }
    }
  }

  .cat-details {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;

    .cat-item {
      padding: 12px 16px;
      background: #f5f7fa;
      border-radius: 8px;

      &.full-width {
        grid-column: 1 / -1;
      }

      .label {
        display: block;
        font-size: 12px;
        color: #999;
        margin-bottom: 4px;
      }

      .value {
        font-size: 14px;
        color: #333;
        font-weight: 500;
      }
    }
  }

  .price-items {
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
    }
  }

  .total-price {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 16px;
    color: #333;
    font-weight: 600;

    .amount {
      font-size: 36px;
      font-weight: 700;
      color: #f56c6c;
    }
  }

  .payment-method {
    margin-top: 24px;

    .payment-group {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .payment-option {
      padding: 0;
      border: none;

      :deep(.el-radio__input) {
        display: none;
      }
    }

    .payment-card {
      display: flex;
      align-items: center;
      gap: 16px;
      padding: 16px;
      border: 2px solid #e4e7ed;
      border-radius: 12px;
      cursor: pointer;
      transition: all 0.3s;

      &:hover,
      &.active {
        border-color: #409eff;
        background: #ecf5ff;
      }

      .payment-icon {
        width: 48px;
        height: 48px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #fff;
        font-size: 24px;

        &.wechat {
          background: #07c160;
        }

        &.alipay {
          background: #1677ff;
        }

        &.balance {
          background: #ff6b6b;
        }

        &.card {
          background: #ffa502;
        }
      }

      .payment-info {
        flex: 1;

        .payment-name {
          display: block;
          font-size: 15px;
          color: #333;
          font-weight: 600;
          margin-bottom: 2px;
        }

        .payment-desc {
          font-size: 12px;
          color: #999;
        }
      }

      .payment-check {
        color: #409eff;
        font-size: 24px;
      }
    }
  }

  .member-discount {
    margin-top: 20px;
  }

  .confirm-btn {
    width: 100%;
    height: 52px;
    font-size: 18px;
    margin-top: 24px;
    border-radius: 26px;
  }

  .agreement {
    margin-top: 16px;
    text-align: center;
    font-size: 12px;
    color: #999;

    a {
      color: #409eff;
      text-decoration: none;

      &:hover {
        text-decoration: underline;
      }
    }
  }

  .secure-info {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    margin-top: 12px;
    font-size: 12px;
    color: #999;
  }
}
</style>
