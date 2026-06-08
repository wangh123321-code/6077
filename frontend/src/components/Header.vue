<template>
  <header class="app-header">
    <div class="header-container">
      <div class="logo" @click="router.push('/')">
        <el-icon size="32" color="#409eff"><House /></el-icon>
        <span class="logo-text">{{ title }}</span>
      </div>
      <nav class="nav-menu">
        <el-menu
          :default-active="activeMenu"
          mode="horizontal"
          router
          :ellipsis="false"
          background-color="transparent"
          text-color="#333"
          active-text-color="#409eff"
        >
          <el-menu-item index="/">首页</el-menu-item>
          <el-menu-item index="/cat-rooms">猫屋列表</el-menu-item>
          <el-menu-item v-if="userStore.isLoggedIn" index="/orders">订单列表</el-menu-item>
          <el-menu-item v-if="userStore.isLoggedIn" index="/member">会员中心</el-menu-item>
          <el-menu-item v-if="userStore.isAdmin" index="/admin">后台管理</el-menu-item>
        </el-menu>
      </nav>
      <div class="user-actions">
        <template v-if="userStore.isLoggedIn">
          <el-dropdown @command="handleCommand">
            <span class="user-info">
              <el-avatar :size="32" :src="userStore.user?.avatar">
                {{ userStore.user?.nickname?.charAt(0) }}
              </el-avatar>
              <span class="username">{{ userStore.user?.nickname }}</span>
              <el-icon><CaretBottom /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                <el-dropdown-item command="orders">我的订单</el-dropdown-item>
                <el-dropdown-item command="member">会员中心</el-dropdown-item>
                <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>
        <template v-else>
          <el-button type="primary" @click="router.push('/login')">登录</el-button>
          <el-button @click="router.push('/login')">注册</el-button>
        </template>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { House, CaretBottom } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const title = import.meta.env.VITE_APP_TITLE

const activeMenu = computed(() => {
  const path = route.path
  if (path.startsWith('/cat-rooms')) return '/cat-rooms'
  if (path.startsWith('/orders')) return '/orders'
  if (path.startsWith('/member')) return '/member'
  if (path.startsWith('/admin')) return '/admin'
  return path
})

async function handleCommand(command: string) {
  switch (command) {
    case 'profile':
      router.push('/member')
      break
    case 'orders':
      router.push('/orders')
      break
    case 'member':
      router.push('/member')
      break
    case 'logout':
      try {
        await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        await userStore.handleLogout()
        ElMessage.success('退出登录成功')
        router.push('/login')
      } catch {
        // 用户取消
      }
      break
  }
}
</script>

<style scoped lang="scss">
.app-header {
  background: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 0;
  z-index: 1000;

  .header-container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 0 24px;
    height: 64px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .logo {
    display: flex;
    align-items: center;
    gap: 12px;
    cursor: pointer;

    .logo-text {
      font-size: 20px;
      font-weight: 600;
      color: #333;
    }
  }

  .nav-menu {
    flex: 1;
    margin: 0 48px;
    border: none;

    :deep(.el-menu) {
      border: none;
    }

    :deep(.el-menu-item) {
      font-size: 15px;
    }
  }

  .user-actions {
    display: flex;
    align-items: center;
    gap: 12px;

    .user-info {
      display: flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;
      padding: 8px 12px;
      border-radius: 8px;
      transition: background-color 0.3s;

      &:hover {
        background-color: #f5f7fa;
      }

      .username {
        font-size: 14px;
        color: #333;
      }
    }
  }
}
</style>
