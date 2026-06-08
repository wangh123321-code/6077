import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录', requiresAuth: false }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Register.vue'),
    meta: { title: '注册', requiresAuth: false }
  },
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue'),
    meta: { title: '首页', requiresAuth: false }
  },
  {
    path: '/cat-rooms',
    name: 'CatRoomList',
    component: () => import('@/views/CatRoomList.vue'),
    meta: { title: '猫屋列表', requiresAuth: false }
  },
  {
    path: '/cat-rooms/:id',
    name: 'CatRoomDetail',
    component: () => import('@/views/CatRoomDetail.vue'),
    meta: { title: '猫屋详情', requiresAuth: false }
  },
  {
    path: '/booking/confirm',
    name: 'BookingConfirm',
    component: () => import('@/views/BookingConfirm.vue'),
    meta: { title: '预订确认', requiresAuth: true }
  },
  {
    path: '/orders',
    name: 'OrderList',
    component: () => import('@/views/OrderList.vue'),
    meta: { title: '订单列表', requiresAuth: true }
  },
  {
    path: '/orders/:id',
    name: 'OrderDetail',
    component: () => import('@/views/OrderDetail.vue'),
    meta: { title: '订单详情', requiresAuth: true }
  },
  {
    path: '/member',
    name: 'MemberCenter',
    component: () => import('@/views/MemberCenter.vue'),
    meta: { title: '会员中心', requiresAuth: true }
  },
  {
    path: '/admin',
    name: 'Admin',
    component: () => import('@/views/Admin.vue'),
    meta: { title: '后台管理', requiresAuth: true, requiresAdmin: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 })
})

router.beforeEach((to, _from, next) => {
  const userStore = useUserStore()
  document.title = `${to.meta.title || '猫咪酒店'} - ${import.meta.env.VITE_APP_TITLE}`

  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    next({ path: '/login', query: { redirect: to.fullPath } })
    return
  }

  if (to.meta.requiresAdmin && userStore.user?.role !== 'admin') {
    next({ path: '/' })
    return
  }

  next()
})

export default router
