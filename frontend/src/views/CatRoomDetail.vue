<template>
  <div class="cat-room-detail" v-loading="loading">
    <div v-if="catRoom" class="container">
      <el-breadcrumb separator="/" class="breadcrumb">
        <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
        <el-breadcrumb-item :to="{ path: '/cat-rooms' }">猫屋列表</el-breadcrumb-item>
        <el-breadcrumb-item>{{ catRoom.name }}</el-breadcrumb-item>
      </el-breadcrumb>

      <div class="detail-content">
        <div class="room-gallery">
          <el-carousel height="500px" :interval="4000" arrow="hover">
            <el-carousel-item v-for="(img, index) in catRoom.images" :key="index">
              <img :src="img" :alt="catRoom.name" class="gallery-image" @click="previewImage(index)" />
            </el-carousel-item>
          </el-carousel>
          <div class="thumbnail-list">
            <div
              v-for="(img, index) in catRoom.images"
              :key="index"
              class="thumbnail"
              :class="{ active: activeThumbnail === index }"
              @click="activeThumbnail = index"
            >
              <img :src="img" :alt="`缩略图${index + 1}`" />
            </div>
          </div>
        </div>

        <div class="room-info">
          <div class="room-header">
            <div>
              <h1>{{ catRoom.name }}</h1>
              <div class="room-tags">
                <el-tag size="large" type="primary">{{ catRoom.type }}</el-tag>
                <el-tag size="large" type="info">{{ catRoom.size }}</el-tag>
              </div>
            </div>
            <el-tag
              :type="catRoom.status === 'available' ? 'success' : catRoom.status === 'occupied' ? 'danger' : 'info'"
              size="large"
              effect="dark"
            >
              {{ catRoom.status === 'available' ? '可预订' : catRoom.status === 'occupied' ? '已占用' : '维护中' }}
            </el-tag>
          </div>

          <div class="room-price">
            <span class="currency">¥</span>
            <span class="price">{{ catRoom.price }}</span>
            <span class="unit">/晚</span>
          </div>

          <div class="room-description">
            <h3>
              <el-icon><InfoFilled /></el-icon>
              房间介绍
            </h3>
            <p>{{ catRoom.description }}</p>
          </div>

          <div class="room-facilities">
            <h3>
              <el-icon><Tools /></el-icon>
              房间设施
            </h3>
            <div class="facilities-list">
              <div v-for="facility in catRoom.facilities" :key="facility" class="facility-item">
                <el-icon size="20" color="#409eff"><CircleCheckFilled /></el-icon>
                <span>{{ facility }}</span>
              </div>
            </div>
          </div>

          <div class="booking-section">
            <div class="price-summary" v-if="dateRange">
              <div class="price-row">
                <span>房费</span>
                <span>¥{{ catRoom.price }} × {{ nights }}晚</span>
              </div>
              <div v-if="selectedServices.length > 0" class="price-row">
                <span>服务费</span>
                <span>¥{{ servicesTotalPrice }}</span>
              </div>
              <div class="price-row total">
                <span>合计</span>
                <span class="total-price">¥{{ totalPrice }}</span>
              </div>
            </div>

            <div class="booking-form">
              <h3>
                <el-icon><Calendar /></el-icon>
                选择入住日期
              </h3>
              <div class="date-picker-wrapper">
                <el-date-picker
                  v-model="dateRange"
                  type="daterange"
                  start-placeholder="入住日期"
                  end-placeholder="离店日期"
                  range-separator="至"
                  value-format="YYYY-MM-DD"
                  :disabled-date="disabledDate"
                  :shortcuts="shortcuts"
                  size="large"
                  style="width: 100%"
                  @change="handleDateChange"
                />
              </div>
              <div v-if="dateRange" class="date-summary">
                <div class="date-item">
                  <span class="label">入住</span>
                  <span class="value">{{ dateRange[0] }}</span>
                </div>
                <div class="date-arrow">
                  <el-icon><Right /></el-icon>
                </div>
                <div class="date-item">
                  <span class="label">离店</span>
                  <span class="value">{{ dateRange[1] }}</span>
                </div>
                <div class="date-item nights">
                  <span class="highlight">{{ nights }}</span>
                  <span class="label">晚</span>
                </div>
              </div>
              <div v-if="dateUnavailable" class="unavailable-warning">
                <el-icon><WarningFilled /></el-icon>
                <span>所选日期范围内有已被预订的日期，请重新选择</span>
              </div>
            </div>

            <el-button
              type="primary"
              size="large"
              class="book-btn"
              :disabled="!canBook"
              :loading="submitting"
              @click="handleBook"
            >
              <el-icon><ShoppingCart /></el-icon>
              立即预订 · ¥{{ totalPrice }}
            </el-button>
          </div>
        </div>
      </div>

      <div class="services-section">
        <h2>
          <el-icon><Goods /></el-icon>
          可选增值服务
        </h2>
        <ServiceSelector
          v-model="selectedServiceIds"
          :services="services"
          title="选择您需要的服务"
          :show-summary="true"
        />
      </div>

      <div class="cat-info-section">
        <h2>
          <el-icon><Avatar /></el-icon>
          猫咪信息
        </h2>
        <el-form :model="catForm" :rules="catFormRules" ref="catFormRef" label-width="120px" class="cat-form">
          <el-row :gutter="24">
            <el-col :xs="24" :sm="12">
              <el-form-item label="猫咪姓名" prop="name">
                <el-input v-model="catForm.name" placeholder="请输入猫咪姓名" size="large" />
              </el-form-item>
            </el-col>
            <el-col :xs="24" :sm="12">
              <el-form-item label="品种" prop="breed">
                <el-input v-model="catForm.breed" placeholder="请输入猫咪品种" size="large" />
              </el-form-item>
            </el-col>
            <el-col :xs="24" :sm="12">
              <el-form-item label="年龄" prop="age">
                <el-input-number
                  v-model="catForm.age"
                  :min="0"
                  :max="30"
                  :step="0.5"
                  placeholder="请输入年龄"
                  size="large"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
            <el-col :xs="24" :sm="12">
              <el-form-item label="性别">
                <el-radio-group v-model="catForm.gender" size="large">
                  <el-radio value="male">公</el-radio>
                  <el-radio value="female">母</el-radio>
                </el-radio-group>
              </el-form-item>
            </el-col>
            <el-col :span="24">
              <el-form-item label="特殊要求">
                <el-input
                  v-model="catForm.specialRequirements"
                  type="textarea"
                  :rows="4"
                  placeholder="请输入特殊要求，如饮食禁忌、健康状况、性格特点等"
                  maxlength="500"
                  show-word-limit
                />
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>
      </div>
    </div>

    <el-image-viewer
      v-if="previewVisible"
      :url-list="catRoom?.images || []"
      :initial-index="previewIndex"
      @close="previewVisible = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import {
  Check,
  InfoFilled,
  Tools,
  Calendar,
  Right,
  WarningFilled,
  ShoppingCart,
  Goods,
  Avatar,
  CircleCheckFilled
} from '@element-plus/icons-vue'
import DatePicker from '@/components/DatePicker.vue'
import ServiceSelector from '@/components/ServiceSelector.vue'
import { getCatRoomDetail, getCatRoomAvailability } from '@/api/catRoom'
import { getServiceList } from '@/api/service'
import { useBookingStore } from '@/stores/booking'
import { useUserStore } from '@/stores/user'
import { getToday, addDays, formatDate } from '@/utils/date'
import type { CatRoom, Service } from '@/types'

const route = useRoute()
const router = useRouter()
const bookingStore = useBookingStore()
const userStore = useUserStore()

const catFormRef = ref<FormInstance>()
const loading = ref(false)
const submitting = ref(false)
const catRoom = ref<CatRoom | null>(null)
const services = ref<Service[]>([])
const dateRange = ref<[string, string] | null>(null)
const selectedServiceIds = ref<number[]>([])
const activeThumbnail = ref(0)
const previewVisible = ref(false)
const previewIndex = ref(0)
const dateUnavailable = ref(false)

const bookedDates = ref<string[]>([])

const catForm = reactive({
  name: '',
  breed: '',
  age: 0,
  gender: 'male' as 'male' | 'female',
  specialRequirements: ''
})

const catFormRules: FormRules = {
  name: [{ required: true, message: '请输入猫咪姓名', trigger: 'blur' }],
  breed: [{ required: true, message: '请输入猫咪品种', trigger: 'blur' }],
  age: [
    { required: true, message: '请输入猫咪年龄', trigger: 'blur' },
    { type: 'number', min: 0, max: 30, message: '年龄必须在0-30之间', trigger: 'blur' }
  ]
}

const shortcuts = [
  {
    text: '今天入住',
    value: () => {
      const start = getToday()
      const end = addDays(start, 1)
      return [new Date(start), new Date(end)]
    }
  },
  {
    text: '明天入住',
    value: () => {
      const start = addDays(getToday(), 1)
      const end = addDays(start, 1)
      return [new Date(start), new Date(end)]
    }
  },
  {
    text: '周末入住',
    value: () => {
      const now = new Date()
      const day = now.getDay()
      const diffToFriday = day === 0 ? 6 : 5 - day
      const start = addDays(getToday(), Math.max(0, diffToFriday))
      const end = addDays(start, 2)
      return [new Date(start), new Date(end)]
    }
  }
]

const selectedServices = computed(() => {
  return services.value.filter((s) => selectedServiceIds.value.includes(s.id))
})

const nights = computed(() => {
  if (!dateRange.value) return 0
  const start = new Date(dateRange.value[0])
  const end = new Date(dateRange.value[1])
  const diff = end.getTime() - start.getTime()
  return Math.max(1, Math.ceil(diff / (1000 * 60 * 60 * 24)))
})

const servicesTotalPrice = computed(() => {
  return selectedServices.value.reduce((sum, s) => sum + s.price, 0)
})

const roomTotalPrice = computed(() => {
  if (!catRoom.value) return 0
  return catRoom.value.price * nights.value
})

const totalPrice = computed(() => {
  return roomTotalPrice.value + servicesTotalPrice.value
})

const canBook = computed(() => {
  return (
    catRoom.value?.status === 'available' &&
    dateRange.value &&
    !dateUnavailable.value &&
    catForm.name &&
    catForm.breed &&
    catForm.age > 0
  )
})

function disabledDate(time: Date): boolean {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  if (time < today) return true
  const dateStr = formatDate(time)
  return bookedDates.value.includes(dateStr)
}

function previewImage(index: number) {
  previewIndex.value = index
  previewVisible.value = true
}

async function checkAvailability() {
  if (!dateRange.value || !catRoom.value) return
  try {
    const res = await getCatRoomAvailability(
      catRoom.value.id,
      dateRange.value[0],
      dateRange.value[1]
    )
    dateUnavailable.value = !res.available
  } catch {
    dateUnavailable.value = false
  }
}

function handleDateChange(value: [string, string] | null) {
  dateUnavailable.value = false
  if (value) {
    checkAvailability()
  }
}

async function fetchDetail() {
  const id = Number(route.params.id)
  if (!id) return

  loading.value = true
  try {
    const [roomRes, serviceRes] = await Promise.all([
      getCatRoomDetail(id),
      getServiceList({ page: 1, pageSize: 100 })
    ])
    catRoom.value = roomRes
    services.value = serviceRes.items

    const today = new Date()
    for (let i = 0; i < 30; i++) {
      if (Math.random() > 0.7) {
        bookedDates.value.push(formatDate(addDays(today, i)))
      }
    }

    if (bookingStore.checkInDate && bookingStore.checkOutDate) {
      dateRange.value = [bookingStore.checkInDate, bookingStore.checkOutDate]
    }
    if (bookingStore.selectedServices.length > 0) {
      selectedServiceIds.value = bookingStore.selectedServices.map((s) => s.id)
    }
    if (bookingStore.catInfo.name) {
      catForm.name = bookingStore.catInfo.name
      catForm.breed = bookingStore.catInfo.breed
      catForm.age = bookingStore.catInfo.age
      catForm.specialRequirements = bookingStore.catInfo.specialRequirements
    }
  } finally {
    loading.value = false
  }
}

async function handleBook() {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录')
    router.push('/login')
    return
  }

  if (!catFormRef.value) return
  const valid = await catFormRef.value.validate().catch(() => false)
  if (!valid) return

  if (!catRoom.value || !dateRange.value) return

  if (dateUnavailable.value) {
    ElMessage.warning('所选日期范围内有已被预订的日期，请重新选择')
    return
  }

  submitting.value = true
  try {
    await ElMessageBox.confirm(
      `确认预订 ${catRoom.value.name} 吗？\n入住日期：${dateRange.value[0]} 至 ${dateRange.value[1]}\n共 ${nights.value} 晚，合计 ¥${totalPrice.value}`,
      '确认预订',
      {
        confirmButtonText: '确认预订',
        cancelButtonText: '再想想',
        type: 'info'
      }
    )

    bookingStore.setCatRoom(catRoom.value)
    bookingStore.setDates(dateRange.value[0], dateRange.value[1])
    bookingStore.setCatInfo(catForm)
    bookingStore.clearServices()
    selectedServices.value.forEach((service) => {
      bookingStore.addService(service)
    })

    router.push('/booking/confirm')
  } catch {
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  fetchDetail()
})
</script>

<style scoped lang="scss">
.cat-room-detail {
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

  .detail-content {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 40px;
    background: #fff;
    padding: 32px;
    border-radius: 12px;
    margin-bottom: 32px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);

    @media (max-width: 1024px) {
      grid-template-columns: 1fr;
    }

    .room-gallery {
      .gallery-image {
        width: 100%;
        height: 100%;
        object-fit: cover;
        border-radius: 8px;
        cursor: pointer;
        transition: transform 0.3s;

        &:hover {
          transform: scale(1.02);
        }
      }

      .thumbnail-list {
        display: flex;
        gap: 12px;
        margin-top: 16px;

        .thumbnail {
          width: 80px;
          height: 60px;
          border-radius: 6px;
          overflow: hidden;
          cursor: pointer;
          border: 2px solid transparent;
          transition: all 0.3s;

          &:hover,
          &.active {
            border-color: #409eff;
          }

          img {
            width: 100%;
            height: 100%;
            object-fit: cover;
          }
        }
      }
    }

    .room-info {
      .room-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 20px;

        h1 {
          font-size: 32px;
          margin: 0 0 12px;
          color: #333;
          font-weight: 700;
        }

        .room-tags {
          display: flex;
          gap: 12px;
        }
      }

      .room-price {
        margin-bottom: 24px;
        padding: 20px;
        background: linear-gradient(135deg, #fef0f0 0%, #fff 100%);
        border-radius: 8px;

        .currency {
          font-size: 20px;
          color: #f56c6c;
          font-weight: 600;
        }

        .price {
          font-size: 48px;
          font-weight: 700;
          color: #f56c6c;
          margin: 0 4px;
        }

        .unit {
          font-size: 16px;
          color: #999;
        }
      }

      .room-description,
      .room-facilities {
        margin-bottom: 24px;

        h3 {
          font-size: 18px;
          margin: 0 0 16px;
          color: #333;
          font-weight: 600;
          display: flex;
          align-items: center;
          gap: 8px;
        }

        p {
          font-size: 14px;
          color: #666;
          line-height: 1.8;
          margin: 0;
        }

        .facilities-list {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 16px;

          .facility-item {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 14px;
            color: #666;
            padding: 8px 12px;
            background: #f5f7fa;
            border-radius: 6px;
          }
        }
      }

      .booking-section {
        padding: 24px;
        background: #f5f7fa;
        border-radius: 12px;

        .price-summary {
          background: #fff;
          padding: 16px;
          border-radius: 8px;
          margin-bottom: 20px;

          .price-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
            font-size: 14px;
            color: #666;

            &.total {
              border-top: 1px dashed #ebeef5;
              margin-top: 8px;
              padding-top: 16px;
              font-size: 16px;
              font-weight: 600;
              color: #333;

              .total-price {
                font-size: 28px;
                font-weight: 700;
                color: #f56c6c;
              }
            }
          }
        }

        .booking-form {
          h3 {
            font-size: 18px;
            margin: 0 0 16px;
            color: #333;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
          }

          .date-picker-wrapper {
            margin-bottom: 16px;
          }

          .date-summary {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 16px;
            background: #fff;
            border-radius: 8px;
            margin-bottom: 16px;

            .date-item {
              flex: 1;
              text-align: center;

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

              &.nights {
                .highlight {
                  font-size: 32px;
                  font-weight: 700;
                  color: #409eff;
                }

                .label {
                  font-size: 14px;
                  color: #666;
                }
              }
            }

            .date-arrow {
              color: #999;
            }
          }

          .unavailable-warning {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 12px 16px;
            background: #fef0f0;
            border-radius: 6px;
            margin-bottom: 16px;
            color: #f56c6c;
            font-size: 14px;
          }
        }

        .book-btn {
          width: 100%;
          height: 52px;
          font-size: 18px;
          border-radius: 26px;
        }
      }
    }
  }

  .services-section,
  .cat-info-section {
    background: #fff;
    padding: 32px;
    border-radius: 12px;
    margin-bottom: 32px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);

    h2 {
      font-size: 24px;
      margin: 0 0 24px;
      color: #333;
      font-weight: 700;
      display: flex;
      align-items: center;
      gap: 10px;
    }
  }

  .cat-form {
    max-width: 800px;
  }
}
</style>
