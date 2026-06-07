<template>
  <div class="member-center">
    <div class="container">
      <div class="page-header">
        <h1>会员中心</h1>
      </div>

      <div class="member-layout">
        <div class="sidebar">
          <el-card class="user-card">
            <div class="user-avatar">
              <el-avatar :size="80" :src="userStore.user?.avatar">
                {{ userStore.user?.username?.charAt(0) }}
              </el-avatar>
            </div>
            <div class="user-info">
              <h3>{{ userStore.user?.username }}</h3>
              <p class="user-role">
                <el-tag size="small" :type="userStore.user?.role === 'admin' ? 'danger' : 'primary'">
                  {{ userStore.user?.role === 'admin' ? '管理员' : '普通用户' }}
                </el-tag>
              </p>
            </div>
            <el-divider />
            <el-menu
              :default-active="activeMenu"
              @select="handleMenuSelect"
              class="member-menu"
            >
              <el-menu-item index="info">
                <el-icon><User /></el-icon>
                <span>个人信息</span>
              </el-menu-item>
              <el-menu-item index="member">
                <el-icon><Medal /></el-icon>
                <span>会员权益</span>
              </el-menu-item>
              <el-menu-item index="points">
                <el-icon><GoldMedal /></el-icon>
                <span>积分明细</span>
              </el-menu-item>
              <el-menu-item index="orders">
                <el-icon><Document /></el-icon>
                <span>我的订单</span>
              </el-menu-item>
            </el-menu>
          </el-card>
        </div>

        <div class="main-content">
          <el-card v-show="activeMenu === 'info'" class="content-card">
            <template #header>
              <h2>个人信息</h2>
            </template>
            <el-form :model="userForm" label-width="100px" class="user-form">
              <el-form-item label="用户名">
                <el-input v-model="userForm.username" disabled />
              </el-form-item>
              <el-form-item label="邮箱">
                <el-input v-model="userForm.email" />
              </el-form-item>
              <el-form-item label="手机号">
                <el-input v-model="userForm.phone" />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="handleUpdateInfo">保存修改</el-button>
              </el-form-item>
            </el-form>
          </el-card>

          <el-card v-show="activeMenu === 'member'" class="content-card">
            <template #header>
              <h2>会员权益</h2>
            </template>
            <div v-if="memberInfo" class="member-info">
              <div class="member-level">
                <el-icon size="64" color="#f56c6c"><Medal /></el-icon>
                <div class="level-info">
                  <h3>{{ memberInfo.levelName }}</h3>
                  <p>当前积分：{{ memberInfo.points }}</p>
                  <p>折扣优惠：{{ memberInfo.discount }}折</p>
                  <p>有效期至：{{ memberInfo.expireDate }}</p>
                </div>
              </div>
              <el-divider />
              <h3>会员特权</h3>
              <div class="privileges-grid">
                <div class="privilege-item">
                  <el-icon size="32" color="#409eff"><PriceTag /></el-icon>
                  <h4>专属折扣</h4>
                  <p>享受{{ memberInfo.discount }}折优惠</p>
                </div>
                <div class="privilege-item">
                  <el-icon size="32" color="#67c23a"><Gift /></el-icon>
                  <h4>生日礼包</h4>
                  <p>生日当月赠送专属礼包</p>
                </div>
                <div class="privilege-item">
                  <el-icon size="32" color="#e6a23c"><Service /></el-icon>
                  <h4>优先服务</h4>
                  <p>优先预订，专属客服</p>
                </div>
                <div class="privilege-item">
                  <el-icon size="32" color="#f56c6c"><Star /></el-icon>
                  <h4>积分加倍</h4>
                  <p>消费积分双倍累计</p>
                </div>
              </div>
              <div class="upgrade-section">
                <el-button type="primary" size="large" @click="handleUpgrade">
                  升级会员
                </el-button>
              </div>
            </div>
          </el-card>

          <el-card v-show="activeMenu === 'points'" class="content-card">
            <template #header>
              <h2>积分明细</h2>
            </template>
            <div class="points-summary">
              <div class="points-item">
                <span class="label">当前积分</span>
                <span class="value highlight">{{ memberInfo?.points || 0 }}</span>
              </div>
              <div class="points-item">
                <span class="label">累计获得</span>
                <span class="value">{{ totalPoints }}</span>
              </div>
              <div class="points-item">
                <span class="label">已使用</span>
                <span class="value">{{ usedPoints }}</span>
              </div>
            </div>
            <el-table :data="pointsHistory" style="width: 100%" class="points-table">
              <el-table-column prop="type" label="类型" width="120">
                <template #default="{ row }">
                  <el-tag :type="row.type === 'earn' ? 'success' : 'info'" size="small">
                    {{ row.type === 'earn' ? '获得' : '使用' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="description" label="说明" />
              <el-table-column prop="points" label="积分" width="120">
                <template #default="{ row }">
                  <span :class="row.type === 'earn' ? 'earn' : 'spend'">
                    {{ row.type === 'earn' ? '+' : '-' }}{{ row.points }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="createdAt" label="时间" width="180" />
            </el-table>
          </el-card>

          <el-card v-show="activeMenu === 'orders'" class="content-card">
            <template #header>
              <h2>我的订单</h2>
            </template>
            <el-button type="primary" @click="router.push('/orders')">
              查看全部订单
            </el-button>
          </el-card>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Medal, GoldMedal, Document, PriceTag, Gift, Service, Star } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { getMemberInfo, getMemberPointsHistory, upgradeMember } from '@/api/member'
import { updateUserInfo } from '@/api/auth'
import type { Member } from '@/types'

const router = useRouter()
const userStore = useUserStore()

const activeMenu = ref('info')
const memberInfo = ref<Member | null>(null)
const pointsHistory = ref<{ id: number; type: string; points: number; description: string; createdAt: string }[]>([])

const userForm = reactive({
  username: userStore.user?.username || '',
  email: userStore.user?.email || '',
  phone: userStore.user?.phone || ''
})

const totalPoints = computed(() =>
  pointsHistory.value.filter((p) => p.type === 'earn').reduce((sum, p) => sum + p.points, 0)
)

const usedPoints = computed(() =>
  pointsHistory.value.filter((p) => p.type !== 'earn').reduce((sum, p) => sum + p.points, 0)
)

async function fetchMemberData() {
  try {
    const [info, history] = await Promise.all([
      getMemberInfo(),
      getMemberPointsHistory({ page: 1, pageSize: 50 })
    ])
    memberInfo.value = info
    pointsHistory.value = history.items
  } catch (error) {
    // 错误已处理
  }
}

function handleMenuSelect(index: string) {
  activeMenu.value = index
}

async function handleUpdateInfo() {
  try {
    await updateUserInfo(userForm)
    ElMessage.success('信息更新成功')
    userStore.fetchUserInfo()
  } catch (error) {
    // 错误已处理
  }
}

async function handleUpgrade() {
  try {
    await upgradeMember({ level: 2 })
    ElMessage.success('会员升级成功')
    fetchMemberData()
  } catch (error) {
    // 错误已处理
  }
}

onMounted(() => {
  if (userStore.isLoggedIn) {
    fetchMemberData()
  }
})
</script>

<style scoped lang="scss">
.member-center {
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

  .member-layout {
    display: grid;
    grid-template-columns: 280px 1fr;
    gap: 24px;

    @media (max-width: 768px) {
      grid-template-columns: 1fr;
    }
  }

  .sidebar {
    .user-card {
      position: sticky;
      top: 88px;

      .user-avatar {
        text-align: center;
        margin-bottom: 16px;
      }

      .user-info {
        text-align: center;

        h3 {
          font-size: 18px;
          margin: 0 0 8px;
          color: #333;
        }

        .user-role {
          margin: 0;
        }
      }

      .member-menu {
        border: none;

        :deep(.el-menu-item) {
          height: 48px;
          line-height: 48px;
          border-radius: 8px;
          margin-bottom: 4px;
        }
      }
    }
  }

  .content-card {
    h2 {
      font-size: 20px;
      margin: 0;
    }

    .user-form {
      max-width: 500px;
    }

    .member-info {
      .member-level {
        display: flex;
        align-items: center;
        gap: 24px;
        padding: 24px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        color: #fff;

        .level-info {
          h3 {
            font-size: 28px;
            margin: 0 0 8px;
            color: #fff;
          }

          p {
            font-size: 14px;
            margin: 4px 0;
            opacity: 0.9;
          }
        }
      }

      h3 {
        font-size: 18px;
        margin: 24px 0 16px;
        color: #333;
      }

      .privileges-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 24px;

        @media (max-width: 768px) {
          grid-template-columns: repeat(2, 1fr);
        }

        .privilege-item {
          text-align: center;
          padding: 24px;
          background: #f5f7fa;
          border-radius: 12px;

          h4 {
            font-size: 16px;
            margin: 12px 0 8px;
            color: #333;
          }

          p {
            font-size: 13px;
            color: #999;
            margin: 0;
          }
        }
      }

      .upgrade-section {
        text-align: center;
        margin-top: 32px;
      }
    }

    .points-summary {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 16px;
      margin-bottom: 24px;

      .points-item {
        padding: 24px;
        background: #f5f7fa;
        border-radius: 12px;
        text-align: center;

        .label {
          display: block;
          font-size: 14px;
          color: #999;
          margin-bottom: 8px;
        }

        .value {
          font-size: 28px;
          font-weight: 700;
          color: #333;

          &.highlight {
            color: #f56c6c;
          }
        }
      }
    }

    .points-table {
      .earn {
        color: #67c23a;
        font-weight: 600;
      }

      .spend {
        color: #f56c6c;
        font-weight: 600;
      }
    }
  }
}
</style>
