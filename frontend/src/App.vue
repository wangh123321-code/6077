<template>
  <div class="app">
    <Header v-if="!isLoginPage" />
    <main class="main-content">
      <router-view />
    </main>
    <Footer v-if="!isLoginPage" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import Header from '@/components/Header.vue'
import Footer from '@/components/Footer.vue'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const userStore = useUserStore()

const isLoginPage = computed(() => route.path === '/login')

onMounted(async () => {
  if (userStore.isLoggedIn && !userStore.user) {
    try {
      await userStore.fetchUserInfo()
    } catch (error) {
      userStore.clearUser()
    }
  }
})
</script>

<style lang="scss">
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html,
body,
#app {
  height: 100%;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial,
    'Noto Sans', sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol',
    'Noto Color Emoji';
  font-size: 14px;
  color: #333;
  background-color: #f5f7fa;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

a {
  text-decoration: none;
  color: inherit;
}

.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.main-content {
  flex: 1;
}

img {
  max-width: 100%;
}
</style>
