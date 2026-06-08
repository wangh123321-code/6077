<template>
  <div class="cat-room-list">
    <div class="container">
      <div class="page-header">
        <h1>猫屋列表</h1>
        <p>选择最适合您爱宠的温馨小屋</p>
      </div>

      <div class="filter-section">
        <div class="filter-header">
          <h3>筛选条件</h3>
          <el-button type="primary" link @click="showMoreFilter = !showMoreFilter">
            {{ showMoreFilter ? '收起筛选' : '更多筛选' }}
            <el-icon><ArrowDown v-if="!showMoreFilter" /><ArrowUp v-else /></el-icon>
          </el-button>
        </div>

        <el-form :model="filterForm" class="filter-form">
          <div class="filter-row">
            <el-form-item label="入住日期">
              <DatePicker v-model="dateRange" @change="handleDateChange" />
            </el-form-item>
            <el-form-item label="房型">
              <el-select v-model="filterForm.type" placeholder="全部房型" clearable style="width: 160px">
                <el-option label="标准型" value="标准型" />
                <el-option label="豪华型" value="豪华型" />
                <el-option label="VIP型" value="VIP型" />
              </el-select>
            </el-form-item>
            <el-form-item label="价格区间">
              <el-slider
                v-model="priceRange"
                range
                :min="0"
                :max="1000"
                :step="50"
                show-input
                style="width: 240px"
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleSearch">
                <el-icon><Search /></el-icon>
                搜索
              </el-button>
              <el-button @click="handleReset">重置</el-button>
            </el-form-item>
          </div>

          <div v-show="showMoreFilter" class="filter-row">
            <el-form-item label="房间设施">
              <el-checkbox-group v-model="selectedFacilities">
                <el-checkbox
                  v-for="facility in facilityOptions"
                  :key="facility"
                  :label="facility"
                >
                  {{ facility }}
                </el-checkbox>
              </el-checkbox-group>
            </el-form-item>
          </div>
        </el-form>

        <div class="active-filters" v-if="activeFilters.length > 0">
          <span class="filter-label">已选条件：</span>
          <el-tag
            v-for="(filter, index) in activeFilters"
            :key="index"
            closable
            @close="removeFilter(filter.key, filter.value)"
          >
            {{ filter.label }}
          </el-tag>
          <el-button type="primary" link @click="handleReset">清除全部</el-button>
        </div>
      </div>

      <div class="list-header">
        <div class="results-count">
          共找到 <span class="highlight">{{ total }}</span> 间可用猫屋
        </div>
        <div class="sort-options">
          <el-radio-group v-model="sortBy" size="small" @change="handleSort">
            <el-radio-button value="default">默认排序</el-radio-button>
            <el-radio-button value="price-asc">价格从低到高</el-radio-button>
            <el-radio-button value="price-desc">价格从高到低</el-radio-button>
          </el-radio-group>
        </div>
      </div>

      <div v-loading="loading" class="rooms-list">
        <el-empty v-if="rooms.length === 0 && !loading" description="暂无符合条件的猫屋">
          <el-button type="primary" @click="handleReset">重置筛选条件</el-button>
        </el-empty>
        <div v-else class="rooms-grid">
          <CatRoomCard
            v-for="room in rooms"
            :key="room.id"
            :cat-room="room"
          />
        </div>
      </div>

      <div v-if="total > 0" class="pagination">
        <el-pagination
          v-model:current-page="filterForm.page"
          v-model:page-size="filterForm.pageSize"
          :page-sizes="[6, 12, 24, 48]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="fetchRooms"
          background
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { Search, ArrowDown, ArrowUp } from '@element-plus/icons-vue'
import CatRoomCard from '@/components/CatRoomCard.vue'
import DatePicker from '@/components/DatePicker.vue'
import { getCatRoomList } from '@/api/catRoom'
import { useBookingStore } from '@/stores/booking'
import type { CatRoom } from '@/types'

const route = useRoute()
const bookingStore = useBookingStore()

const loading = ref(false)
const rooms = ref<CatRoom[]>([])
const total = ref(0)
const dateRange = ref<[string, string] | null>(null)
const showMoreFilter = ref(false)
const sortBy = ref('default')
const priceRange = ref<[number, number]>([0, 1000])
const selectedFacilities = ref<string[]>([])

const facilityOptions = ['空调', '摄像头', '猫爬架', '观景窗', '独立卫浴', '跑步机', '24h监控', '玩具', '猫窝']

const filterForm = reactive({
  page: 1,
  pageSize: 6,
  type: '',
  size: '',
  minPrice: 0,
  maxPrice: 1000,
  checkInDate: '',
  checkOutDate: '',
  facilities: [] as string[]
})

const activeFilters = computed(() => {
  const filters: { key: string; value: any; label: string }[] = []

  if (filterForm.type) {
    filters.push({ key: 'type', value: filterForm.type, label: `房型：${filterForm.type}` })
  }
  if (filterForm.checkInDate && filterForm.checkOutDate) {
    filters.push({
      key: 'dates',
      value: [filterForm.checkInDate, filterForm.checkOutDate],
      label: `日期：${filterForm.checkInDate} 至 ${filterForm.checkOutDate}`
    })
  }
  if (priceRange.value[0] > 0 || priceRange.value[1] < 1000) {
    filters.push({
      key: 'price',
      value: priceRange.value,
      label: `价格：¥${priceRange.value[0]}-¥${priceRange.value[1]}`
    })
  }
  if (selectedFacilities.value.length > 0) {
    filters.push({
      key: 'facilities',
      value: selectedFacilities.value,
      label: `设施：${selectedFacilities.value.join('、')}`
    })
  }

  return filters
})

async function fetchRooms() {
  loading.value = true
  try {
    const params = {
      page: filterForm.page,
      page_size: filterForm.pageSize,
      status: filterForm.status,
      min_price: priceRange.value[0],
      max_price: priceRange.value[1],
      check_in_date: filterForm.checkInDate || undefined,
      check_out_date: filterForm.checkOutDate || undefined
    }
    const res = await getCatRoomList(params)
    rooms.value = res.items.map((item: CatRoom) => ({
      ...item,
      price: item.price_per_day
    }))
    total.value = res.total
  } catch (error) {
    rooms.value = [
      {
        id: 1,
        name: '豪华大床房',
        area: 15,
        floor: 2,
        price_per_day: 299,
        price: 299,
        description: '宽敞明亮的独立房间，配备猫爬架和观景窗',
        images: ['https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=luxury%20cat%20room%20modern&image_size=landscape_16_9'],
        facilities: ['空调', '猫爬架', '观景窗', '摄像头'],
        status: 'available'
      },
      {
        id: 2,
        name: '标准双人间',
        area: 10,
        floor: 1,
        price_per_day: 199,
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
      },
      {
        id: 4,
        name: '温馨单人间',
        type: '标准型',
        size: '8㎡',
        price: 129,
        description: '小巧温馨的独立空间，适合单只猫咪',
        images: ['https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=small%20cozy%20cat%20room&image_size=landscape_16_9'],
        facilities: ['空调', '猫窝', '玩具'],
        status: 'available'
      },
      {
        id: 5,
        name: '豪华观景房',
        type: '豪华型',
        size: '18㎡',
        price: 359,
        description: '全景落地窗，阳光充足，视野开阔',
        images: ['https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=cat%20room%20with%20view&image_size=landscape_16_9'],
        facilities: ['空调', '猫爬架', '观景窗', '摄像头', '玩具'],
        status: 'available'
      },
      {
        id: 6,
        name: 'VIP豪华套房',
        type: 'VIP型',
        size: '30㎡',
        price: 599,
        description: '超大面积，独立活动区，专属管家24小时服务',
        images: ['https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=luxury%20vip%20cat%20suite&image_size=landscape_16_9'],
        facilities: ['空调', '猫爬架', '跑步机', '独立卫浴', '24h监控', '玩具'],
        status: 'available'
      }
    ]
    total.value = 12
  } finally {
    loading.value = false
  }
}

function handleDateChange(value: [string, string] | null) {
  if (value) {
    filterForm.checkInDate = value[0]
    filterForm.checkOutDate = value[1]
    bookingStore.setDates(value[0], value[1])
  } else {
    filterForm.checkInDate = ''
    filterForm.checkOutDate = ''
  }
}

function handleSearch() {
  filterForm.page = 1
  fetchRooms()
}

function handleReset() {
  filterForm.type = ''
  filterForm.size = ''
  filterForm.minPrice = 0
  filterForm.maxPrice = 1000
  filterForm.checkInDate = ''
  filterForm.checkOutDate = ''
  filterForm.page = 1
  priceRange.value = [0, 1000]
  selectedFacilities.value = []
  dateRange.value = null
  sortBy.value = 'default'
  fetchRooms()
}

function handleSort() {
  if (sortBy.value === 'price-asc') {
    rooms.value.sort((a, b) => a.price - b.price)
  } else if (sortBy.value === 'price-desc') {
    rooms.value.sort((a, b) => b.price - a.price)
  } else {
    fetchRooms()
  }
}

function handleSizeChange() {
  filterForm.page = 1
  fetchRooms()
}

function removeFilter(key: string, _value: any) {
  switch (key) {
    case 'type':
      filterForm.type = ''
      break
    case 'dates':
      filterForm.checkInDate = ''
      filterForm.checkOutDate = ''
      dateRange.value = null
      break
    case 'price':
      priceRange.value = [0, 1000]
      break
    case 'facilities':
      selectedFacilities.value = []
      break
  }
  fetchRooms()
}

onMounted(() => {
  const checkIn = route.query.checkIn as string
  const checkOut = route.query.checkOut as string
  if (checkIn && checkOut) {
    dateRange.value = [checkIn, checkOut]
    filterForm.checkInDate = checkIn
    filterForm.checkOutDate = checkOut
  } else if (bookingStore.checkInDate && bookingStore.checkOutDate) {
    dateRange.value = [bookingStore.checkInDate, bookingStore.checkOutDate]
    filterForm.checkInDate = bookingStore.checkInDate
    filterForm.checkOutDate = bookingStore.checkOutDate
  }
  fetchRooms()
})
</script>

<style scoped lang="scss">
.cat-room-list {
  min-height: 100vh;
  background: #f5f7fa;
  padding: 32px 0;

  .container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 0 24px;
  }

  .page-header {
    text-align: center;
    margin-bottom: 40px;

    h1 {
      font-size: 36px;
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

  .filter-section {
    background: #fff;
    padding: 24px;
    border-radius: 12px;
    margin-bottom: 24px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);

    .filter-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;

      h3 {
        font-size: 18px;
        margin: 0;
        color: #333;
        font-weight: 600;
      }
    }

    .filter-form {
      .filter-row {
        display: flex;
        flex-wrap: wrap;
        gap: 16px;
        align-items: flex-end;
        margin-bottom: 16px;

        &:last-child {
          margin-bottom: 0;
        }
      }

      :deep(.el-form-item) {
        margin-bottom: 0;
      }

      :deep(.el-date-editor) {
        width: 280px;
      }
    }

    .active-filters {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 8px;
      padding-top: 16px;
      border-top: 1px solid #ebeef5;
      margin-top: 16px;

      .filter-label {
        font-size: 14px;
        color: #666;
        margin-right: 8px;
      }

      .el-tag {
        margin-right: 8px;
      }
    }
  }

  .list-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;

    .results-count {
      font-size: 14px;
      color: #666;

      .highlight {
        color: #409eff;
        font-weight: 600;
        font-size: 18px;
        margin: 0 4px;
      }
    }
  }

  .rooms-list {
    .rooms-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 24px;

      @media (max-width: 1024px) {
        grid-template-columns: repeat(2, 1fr);
      }

      @media (max-width: 768px) {
        grid-template-columns: 1fr;
      }
    }

    .el-empty {
      padding: 80px 0;
    }
  }

  .pagination {
    margin-top: 40px;
    display: flex;
    justify-content: center;
  }
}
</style>
