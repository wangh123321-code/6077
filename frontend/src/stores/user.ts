import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import type { User, LoginRequest, RegisterRequest } from '@/types'
import { login, logout, getUserInfo, register, updateUserInfo, changePassword } from '@/api/auth'
import { setToken, removeToken, getToken, setUser, getUser, removeUser, clearAuth } from '@/utils/auth'

export const useUserStore = defineStore('user', () => {
  const token = ref<string | null>(getToken())
  const user = ref<User | null>(getUser<User>())
  const loading = ref(false)

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const userAvatar = computed(() => user.value?.avatar || '')
  const userName = computed(() => user.value?.username || '')
  const memberLevel = computed(() => user.value?.memberLevel || 1)
  const memberPoints = computed(() => user.value?.memberPoints || 0)

  watch(
    () => user.value,
    (newUser) => {
      if (newUser) {
        setUser(newUser)
      } else {
        removeUser()
      }
    },
    { deep: true }
  )

  watch(
    () => token.value,
    (newToken) => {
      if (newToken) {
        setToken(newToken)
      } else {
        removeToken()
      }
    }
  )

  async function handleLogin(data: LoginRequest) {
    loading.value = true
    try {
      const res = await login(data)
      token.value = res.token
      user.value = res.user
      return res
    } finally {
      loading.value = false
    }
  }

  async function handleRegister(data: RegisterRequest) {
    loading.value = true
    try {
      const res = await register(data)
      return res
    } finally {
      loading.value = false
    }
  }

  async function handleLogout() {
    loading.value = true
    try {
      await logout()
    } finally {
      token.value = null
      user.value = null
      clearAuth()
      loading.value = false
    }
  }

  async function fetchUserInfo() {
    if (!token.value) return null
    loading.value = true
    try {
      const res = await getUserInfo()
      user.value = res
      return res
    } catch (error) {
      clearAuth()
      token.value = null
      user.value = null
      throw error
    } finally {
      loading.value = false
    }
  }

  async function updateUser(data: Partial<User>) {
    loading.value = true
    try {
      const res = await updateUserInfo(data)
      user.value = res
      return res
    } finally {
      loading.value = false
    }
  }

  async function handleChangePassword(oldPassword: string, newPassword: string) {
    loading.value = true
    try {
      const res = await changePassword({ oldPassword, newPassword })
      return res
    } finally {
      loading.value = false
    }
  }

  function clearUser() {
    token.value = null
    user.value = null
    clearAuth()
  }

  function updateMemberPoints(points: number) {
    if (user.value) {
      user.value.memberPoints = points
    }
  }

  return {
    user,
    token,
    loading,
    isLoggedIn,
    isAdmin,
    userAvatar,
    userName,
    memberLevel,
    memberPoints,
    handleLogin,
    handleRegister,
    handleLogout,
    fetchUserInfo,
    updateUser,
    handleChangePassword,
    clearUser,
    updateMemberPoints
  }
})
