<template>
  <div class="home-page">
    <section class="hero">
      <div class="hero-content">
        <h1>给您的爱宠一个温馨的家</h1>
        <p>专业猫咪酒店，提供高品质的猫咪寄养服务</p>
        <div class="hero-actions">
          <el-button type="primary" size="large" @click="handleQuickBook">
            <el-icon><Calendar /></el-icon>
            立即预订
          </el-button>
          <el-button size="large" @click="scrollToServices">
            了解更多
          </el-button>
        </div>
        <div class="quick-book">
          <div class="quick-book-card">
            <div class="quick-book-title">快速预订</div>
            <div class="quick-book-form">
              <DatePicker v-model="quickBookDates" class="date-picker" />
              <el-button type="primary" size="large" @click="handleQuickBook">
                查询可用猫屋
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="features">
      <div class="container">
        <div class="features-grid">
          <div class="feature-item">
            <div class="feature-icon">
              <el-icon size="48"><HomeFilled /></el-icon>
            </div>
            <h3>舒适环境</h3>
            <p>独立空调房间，24小时恒温恒湿</p>
          </div>
          <div class="feature-item">
            <div class="feature-icon green">
              <el-icon size="48"><Camera /></el-icon>
            </div>
            <h3>实时监控</h3>
            <p>手机随时查看爱宠状态</p>
          </div>
          <div class="feature-item">
            <div class="feature-icon orange">
              <el-icon size="48"><UserFilled /></el-icon>
            </div>
            <h3>专业护理</h3>
            <p>持证兽医24小时在岗</p>
          </div>
          <div class="feature-item">
            <div class="feature-icon red">
              <el-icon size="48"><Dish /></el-icon>
            </div>
            <h3>定制饮食</h3>
            <p>根据猫咪情况定制营养餐</p>
          </div>
        </div>
      </div>
    </section>

    <section class="rooms-preview">
      <div class="container">
        <div class="section-header">
          <h2>精选猫屋</h2>
          <p>多种房型，满足不同需求</p>
        </div>
        <div v-loading="loadingRooms" class="rooms-grid">
          <CatRoomCard
            v-for="room in featuredRooms"
            :key="room.id"
            :cat-room="room"
          />
        </div>
        <div class="view-more">
          <el-button type="primary" size="large" @click="router.push('/cat-rooms')">
            查看全部猫屋
            <el-icon><ArrowRight /></el-icon>
          </el-button>
        </div>
      </div>
    </section>

    <section ref="servicesRef" class="services-preview">
      <div class="container">
        <div class="section-header">
          <h2>增值服务</h2>
          <p>为您的爱宠提供全方位呵护</p>
        </div>
        <div v-loading="loadingServices" class="services-grid">
          <div
            v-for="service in featuredServices"
            :key="service.id"
            class="service-card"
          >
            <div class="service-image-wrapper">
              <img :src="service.image" :alt="service.name" />
              <div class="service-category">{{ service.category }}</div>
            </div>
            <div class="service-info">
              <h3>{{ service.name }}</h3>
              <p>{{ service.description }}</p>
              <div class="service-footer">
                <span class="price">¥{{ service.price }}</span>
                <span class="duration">{{ service.duration }}分钟</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="stats-section">
      <div class="container">
        <div class="stats-grid">
          <div class="stat-item">
            <div class="stat-number">{{ stats.rooms }}</div>
            <div class="stat-label">舒适猫屋</div>
          </div>
          <div class="stat-item">
            <div class="stat-number">{{ stats.customers }}</div>
            <div class="stat-label">服务客户</div>
          </div>
          <div class="stat-item">
            <div class="stat-number">{{ stats.orders }}</div>
            <div class="stat-label">完成订单</div>
          </div>
          <div class="stat-item">
            <div class="stat-number">{{ stats.rating }}</div>
            <div class="stat-label">用户好评</div>
          </div>
        </div>
      </div>
    </section>

    <section class="cta-section">
      <div class="container">
        <div class="cta-content">
          <h2>准备好为您的爱宠预订温馨小屋了吗？</h2>
          <p>立即注册成为会员，享受专属优惠</p>
          <div class="cta-actions">
            <el-button type="primary" size="large" @click="router.push('/cat-rooms')">
              立即预订
            </el-button>
            <el-button size="large" @click="router.push('/login')">
              注册会员
            </el-button>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { HomeFilled, Camera, UserFilled, Dish, Calendar, ArrowRight } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import CatRoomCard from '@/components/CatRoomCard.vue'
import DatePicker from '@/components/DatePicker.vue'
import { getCatRoomList } from '@/api/catRoom'
import { getServiceList } from '@/api/service'
import { useBookingStore } from '@/stores/booking'
import type { CatRoom, Service } from '@/types'

const router = useRouter()
const bookingStore = useBookingStore()
const servicesRef = ref<HTMLElement>()

const loadingRooms = ref(false)
const loadingServices = ref(false)
const quickBookDates = ref<[string, string] | null>(null)

const featuredRooms = ref<CatRoom[]>([])
const featuredServices = ref<Service[]>([])

const stats = reactive({
  rooms: 50,
  customers: 10000,
  orders: 50000,
  rating: '99.8%'
})

async function fetchFeaturedRooms() {
  loadingRooms.value = true
  try {
    const res = await getCatRoomList({ page: 1, pageSize: 6 })
    featuredRooms.value = res.items
  } catch (error) {
    featuredRooms.value = [
      {
        id: 1,
        name: '豪华大床房',
        type: '豪华型',
        size: '15㎡',
        price: 299,
        description: '宽敞明亮的独立房间，配备猫爬架和观景窗',
        images: ['https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=luxury%20cat%20room%20modern&image_size=landscape_16_9'],
        facilities: ['空调', '猫爬架', '观景窗', '摄像头'],
        status: 'available'
      },
      {
        id: 2,
        name: '标准双人间',
        type: '标准型',
        size: '10㎡',
        price: 199,
        description: '温馨舒适的标准房间，适合两只猫咪入住',
        images: ['https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=cozy%20cat%20room&image_size=landscape_16_9'],
        facilities: ['空调', '猫窝', '玩具', '摄像头'],
        status: 'available'
      },
      {
        id: 3,
        name: 'VIP总统套房',
        type: 'VIP型',
        size: '25㎡',
        price: 499,
        description: '顶级奢华套房，专属管家服务，独立休闲区',
        images: ['https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=vip%20luxury%20cat%20suite&image_size=landscape_16_9'],
        facilities: ['空调', '猫爬架', '跑步机', '独立卫浴', '24h监控'],
        status: 'available'
      }
    ]
  } finally {
    loadingRooms.value = false
  }
}

async function fetchFeaturedServices() {
  loadingServices.value = true
  try {
    const res = await getServiceList({ page: 1, pageSize: 8 })
    featuredServices.value = res.items
  } catch (error) {
    featuredServices.value = [
      {
        id: 1,
        name: '专业洗护',
        description: '包含洗澡、吹干、梳理、修剪指甲',
        price: 128,
        duration: 60,
        category: '洗护',
        image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=cat%20grooming%20service&image_size=square'
      },
      {
        id: 2,
        name: '健康体检',
        description: '专业兽医全面检查，包括体温、体重、心肺功能等',
        price: 198,
        duration: 30,
        category: '医疗',
        image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=cat%20health%20check&image_size=square'
      },
      {
        id: 3,
        name: '互动玩耍',
        description: '专人陪伴玩耍，释放猫咪精力',
        price: 68,
        duration: 30,
        category: '娱乐',
        image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=cat%20playing%20with%20toy&image_size=square'
      },
      {
        id: 4,
        name: '美容造型',
        description: '根据猫咪特点设计造型，包含剪毛、造型',
        price: 268,
        duration: 90,
        category: '美容',
        image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=cat%20beauty%20styling&image_size=square'
      }
    ]
  } finally {
    loadingServices.value = false
  }
}

function handleQuickBook() {
  if (quickBookDates.value) {
    bookingStore.setDates(quickBookDates.value[0], quickBookDates.value[1])
    router.push({
      path: '/cat-rooms',
      query: {
        checkIn: quickBookDates.value[0],
        checkOut: quickBookDates.value[1]
      }
    })
  } else {
    router.push('/cat-rooms')
  }
}

function scrollToServices() {
  servicesRef.value?.scrollIntoView({ behavior: 'smooth' })
}

onMounted(() => {
  fetchFeaturedRooms()
  fetchFeaturedServices()
})
</script>

<style scoped lang="scss">
.home-page {
  .hero {
    min-height: 600px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
    color: #fff;
    position: relative;
    overflow: hidden;

    &::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: url('https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=cute%20cat%20soft%20bokeh%20background&image_size=landscape_16_9') center/cover;
      opacity: 0.15;
    }

    .hero-content {
      max-width: 900px;
      padding: 0 24px;
      position: relative;
      z-index: 1;

      h1 {
        font-size: 48px;
        margin: 0 0 24px;
        font-weight: 700;
        text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
      }

      p {
        font-size: 20px;
        margin: 0 0 40px;
        opacity: 0.95;
      }

      .hero-actions {
        display: flex;
        gap: 16px;
        justify-content: center;
        margin-bottom: 48px;

        .el-button {
          height: 48px;
          padding: 0 32px;
          font-size: 16px;
          border-radius: 24px;
        }
      }

      .quick-book {
        .quick-book-card {
          background: rgba(255, 255, 255, 0.95);
          backdrop-filter: blur(10px);
          border-radius: 16px;
          padding: 24px;
          box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);

          .quick-book-title {
            font-size: 18px;
            font-weight: 600;
            color: #333;
            margin-bottom: 16px;
          }

          .quick-book-form {
            display: flex;
            gap: 16px;
            align-items: center;
            justify-content: center;
            flex-wrap: wrap;

            .date-picker {
              flex: 1;
              min-width: 280px;
              max-width: 400px;
            }

            .el-button {
              height: 40px;
              border-radius: 20px;
            }
          }
        }
      }
    }
  }

  .container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 0 24px;
  }

  .features {
    padding: 80px 0;
    background: #f5f7fa;

    .features-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 40px;

      @media (max-width: 768px) {
        grid-template-columns: repeat(2, 1fr);
      }
    }

    .feature-item {
      text-align: center;

      .feature-icon {
        width: 80px;
        height: 80px;
        margin: 0 auto 16px;
        background: #ecf5ff;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #409eff;

        &.green {
          background: #f0f9eb;
          color: #67c23a;
        }

        &.orange {
          background: #fdf6ec;
          color: #e6a23c;
        }

        &.red {
          background: #fef0f0;
          color: #f56c6c;
        }
      }

      h3 {
        font-size: 20px;
        margin: 16px 0 12px;
        color: #333;
      }

      p {
        font-size: 14px;
        color: #666;
        margin: 0;
        line-height: 1.6;
      }
    }
  }

  .rooms-preview,
  .services-preview {
    padding: 80px 0;
  }

  .section-header {
    text-align: center;
    margin-bottom: 48px;

    h2 {
      font-size: 32px;
      margin: 0 0 12px;
      color: #333;
      font-weight: 700;
    }

    p {
      font-size: 16px;
      color: #999;
      margin: 0;
    }
  }

  .rooms-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 24px;
    margin-bottom: 48px;

    @media (max-width: 768px) {
      grid-template-columns: 1fr;
    }
  }

  .view-more {
    text-align: center;

    .el-button {
      border-radius: 24px;
      padding: 0 32px;
    }
  }

  .services-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 24px;

    @media (max-width: 768px) {
      grid-template-columns: repeat(2, 1fr);
    }

    .service-card {
      background: #fff;
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
      transition: transform 0.3s, box-shadow 0.3s;

      &:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);

        img {
          transform: scale(1.05);
        }
      }

      .service-image-wrapper {
        position: relative;
        height: 160px;
        overflow: hidden;

        img {
          width: 100%;
          height: 100%;
          object-fit: cover;
          transition: transform 0.3s;
        }

        .service-category {
          position: absolute;
          top: 12px;
          left: 12px;
          background: rgba(64, 158, 255, 0.9);
          color: #fff;
          padding: 4px 12px;
          border-radius: 12px;
          font-size: 12px;
        }
      }

      .service-info {
        padding: 20px;

        h3 {
          font-size: 18px;
          margin: 0 0 8px;
          color: #333;
          font-weight: 600;
        }

        p {
          font-size: 14px;
          color: #666;
          margin: 0 0 12px;
          line-height: 1.6;
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
          overflow: hidden;
        }

        .service-footer {
          display: flex;
          justify-content: space-between;
          align-items: center;

          .price {
            font-size: 20px;
            font-weight: 700;
            color: #f56c6c;
          }

          .duration {
            font-size: 12px;
            color: #999;
          }
        }
      }
    }
  }

  .stats-section {
    padding: 60px 0;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: #fff;

    .stats-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 40px;
      text-align: center;

      @media (max-width: 768px) {
        grid-template-columns: repeat(2, 1fr);
      }

      .stat-item {
        .stat-number {
          font-size: 48px;
          font-weight: 700;
          margin-bottom: 8px;
        }

        .stat-label {
          font-size: 16px;
          opacity: 0.9;
        }
      }
    }
  }

  .cta-section {
    padding: 80px 0;
    background: #f5f7fa;

    .cta-content {
      text-align: center;
      max-width: 600px;
      margin: 0 auto;

      h2 {
        font-size: 32px;
        margin: 0 0 16px;
        color: #333;
        font-weight: 700;
      }

      p {
        font-size: 16px;
        color: #666;
        margin: 0 0 32px;
      }

      .cta-actions {
        display: flex;
        gap: 16px;
        justify-content: center;
        flex-wrap: wrap;

        .el-button {
          height: 48px;
          padding: 0 32px;
          border-radius: 24px;
          font-size: 16px;
        }
      }
    }
  }
}
</style>
