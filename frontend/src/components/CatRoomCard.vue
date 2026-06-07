<template>
  <el-card class="cat-room-card" shadow="hover" @click="handleClick">
    <div class="card-image">
      <img :src="catRoom.images[0]" :alt="catRoom.name" />
      <el-tag
        v-if="catRoom.status === 'available'"
        type="success"
        size="large"
        class="status-tag"
      >
        可预订
      </el-tag>
      <el-tag
        v-else-if="catRoom.status === 'occupied'"
        type="danger"
        size="large"
        class="status-tag"
      >
        已占用
      </el-tag>
      <el-tag
        v-else
        type="info"
        size="large"
        class="status-tag"
      >
        维护中
      </el-tag>
    </div>
    <div class="card-content">
      <div class="card-header">
        <h3 class="room-name">{{ catRoom.name }}</h3>
        <div class="room-price">
          <span class="price">¥{{ catRoom.price }}</span>
          <span class="unit">/晚</span>
        </div>
      </div>
      <div class="room-tags">
        <el-tag size="small" type="primary">{{ catRoom.type }}</el-tag>
        <el-tag size="small">{{ catRoom.size }}</el-tag>
      </div>
      <p class="room-desc">{{ catRoom.description }}</p>
      <div class="room-facilities">
        <el-tag
          v-for="facility in catRoom.facilities.slice(0, 4)"
          :key="facility"
          size="small"
          type="info"
          effect="plain"
        >
          {{ facility }}
        </el-tag>
        <el-tag
          v-if="catRoom.facilities.length > 4"
          size="small"
          type="info"
          effect="plain"
        >
          +{{ catRoom.facilities.length - 4 }}
        </el-tag>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import type { CatRoom } from '@/types'

const props = defineProps<{
  catRoom: CatRoom
}>()

const router = useRouter()

function handleClick() {
  router.push(`/cat-rooms/${props.catRoom.id}`)
}
</script>

<style scoped lang="scss">
.cat-room-card {
  cursor: pointer;
  transition: transform 0.3s, box-shadow 0.3s;

  &:hover {
    transform: translateY(-4px);
  }

  .card-image {
    position: relative;
    height: 200px;
    overflow: hidden;
    border-radius: 8px 8px 0 0;
    margin: -20px -20px 0;

    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
      transition: transform 0.3s;
    }

    &:hover img {
      transform: scale(1.05);
    }

    .status-tag {
      position: absolute;
      top: 12px;
      right: 12px;
    }
  }

  .card-content {
    padding-top: 16px;

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;

      .room-name {
        font-size: 18px;
        font-weight: 600;
        margin: 0;
        color: #333;
      }

      .room-price {
        .price {
          font-size: 24px;
          font-weight: 700;
          color: #f56c6c;
        }

        .unit {
          font-size: 14px;
          color: #999;
        }
      }
    }

    .room-tags {
      display: flex;
      gap: 8px;
      margin-bottom: 12px;
    }

    .room-desc {
      font-size: 14px;
      color: #666;
      line-height: 1.6;
      margin-bottom: 12px;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }

    .room-facilities {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }
  }
}
</style>
