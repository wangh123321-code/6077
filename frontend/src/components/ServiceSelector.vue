<template>
  <div class="service-selector">
    <div v-if="title" class="selector-title">
      <h3>{{ title }}</h3>
      <p class="subtitle">已选择 {{ selectedIds.length }} 项服务</p>
    </div>
    <div class="service-grid">
      <div
        v-for="service in services"
        :key="service.id"
        class="service-item"
        :class="{ active: isSelected(service.id) }"
        @click="toggleService(service)"
      >
        <div class="service-image">
          <img :src="service.image" :alt="service.name" />
          <div v-if="isSelected(service.id)" class="selected-mask">
            <el-icon size="32" color="#fff"><Check /></el-icon>
          </div>
        </div>
        <div class="service-info">
          <h4 class="service-name">{{ service.name }}</h4>
          <p class="service-desc">{{ service.description }}</p>
          <div class="service-meta">
            <span class="service-price">¥{{ service.price }}</span>
            <span class="service-duration">{{ service.duration }}分钟</span>
          </div>
        </div>
      </div>
    </div>
    <div v-if="showSummary && selectedIds.length > 0" class="service-summary">
      <div class="summary-content">
        <span>已选服务：</span>
        <el-tag
          v-for="id in selectedIds"
          :key="id"
          closable
          @close="removeService(id)"
        >
          {{ getServiceName(id) }}
        </el-tag>
      </div>
      <div class="summary-total">
        服务总价：<span class="total-price">¥{{ totalPrice }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Check } from '@element-plus/icons-vue'
import type { Service } from '@/types'

const props = withDefaults(
  defineProps<{
    services: Service[]
    modelValue?: number[]
    title?: string
    showSummary?: boolean
  }>(),
  {
    title: '',
    showSummary: true
  }
)

const emit = defineEmits<{
  'update:modelValue': [value: number[]]
  change: [value: number[]]
}>()

const selectedIds = computed(() => props.modelValue || [])

const totalPrice = computed(() => {
  return props.services
    .filter((s) => selectedIds.value.includes(s.id))
    .reduce((sum, s) => sum + s.price, 0)
})

function isSelected(id: number): boolean {
  return selectedIds.value.includes(id)
}

function toggleService(service: Service) {
  let newSelected: number[]
  if (isSelected(service.id)) {
    newSelected = selectedIds.value.filter((id) => id !== service.id)
  } else {
    newSelected = [...selectedIds.value, service.id]
  }
  emit('update:modelValue', newSelected)
  emit('change', newSelected)
}

function removeService(id: number) {
  const newSelected = selectedIds.value.filter((sid) => sid !== id)
  emit('update:modelValue', newSelected)
  emit('change', newSelected)
}

function getServiceName(id: number): string {
  return props.services.find((s) => s.id === id)?.name || ''
}
</script>

<style scoped lang="scss">
.service-selector {
  .selector-title {
    margin-bottom: 24px;

    h3 {
      font-size: 20px;
      margin: 0 0 8px;
      color: #333;
    }

    .subtitle {
      font-size: 14px;
      color: #999;
      margin: 0;
    }
  }

  .service-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    gap: 20px;
  }

  .service-item {
    border: 2px solid #e4e7ed;
    border-radius: 12px;
    overflow: hidden;
    cursor: pointer;
    transition: all 0.3s;

    &:hover {
      border-color: #409eff;
      box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15);
    }

    &.active {
      border-color: #409eff;
      box-shadow: 0 4px 12px rgba(64, 158, 255, 0.2);
    }

    .service-image {
      position: relative;
      height: 140px;

      img {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }

      .selected-mask {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(64, 158, 255, 0.6);
        display: flex;
        align-items: center;
        justify-content: center;
      }
    }

    .service-info {
      padding: 16px;

      .service-name {
        font-size: 16px;
        font-weight: 600;
        margin: 0 0 8px;
        color: #333;
      }

      .service-desc {
        font-size: 13px;
        color: #666;
        margin: 0 0 12px;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        line-height: 1.5;
      }

      .service-meta {
        display: flex;
        justify-content: space-between;
        align-items: center;

        .service-price {
          font-size: 18px;
          font-weight: 700;
          color: #f56c6c;
        }

        .service-duration {
          font-size: 12px;
          color: #999;
        }
      }
    }
  }

  .service-summary {
    margin-top: 24px;
    padding: 20px;
    background: #f5f7fa;
    border-radius: 12px;

    .summary-content {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 8px;
      margin-bottom: 16px;

      > span {
        font-size: 14px;
        color: #666;
      }
    }

    .summary-total {
      text-align: right;
      font-size: 16px;
      color: #666;

      .total-price {
        font-size: 24px;
        font-weight: 700;
        color: #f56c6c;
        margin-left: 8px;
      }
    }
  }
}
</style>
