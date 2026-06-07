<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-header">
        <h1>猫咪酒店管理系统</h1>
        <p>欢迎回来，请登录您的账户</p>
      </div>
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        class="login-form"
        @keyup.enter="handleLogin"
      >
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            placeholder="请输入用户名"
            size="large"
            :prefix-icon="User"
          />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            size="large"
            :prefix-icon="Lock"
            show-password
          />
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="form.remember">记住我</el-checkbox>
          <span class="forgot-password">忘记密码？</span>
        </el-form-item>
        <el-button
          type="primary"
          size="large"
          class="login-btn"
          :loading="loading"
          @click="handleLogin"
        >
          登录
        </el-button>
        <div class="register-link">
          还没有账户？<router-link to="/login">立即注册</router-link>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const formRef = ref<FormInstance>()
const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
  remember: false
})

const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

async function handleLogin() {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await userStore.handleLogin({
      username: form.username,
      password: form.password
    })
    ElMessage.success('登录成功')
    const redirect = route.query.redirect as string || '/'
    router.push(redirect)
  } catch (error) {
    // 错误已在API拦截器中处理
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 24px;

  .login-container {
    width: 100%;
    max-width: 420px;
    background: #fff;
    border-radius: 16px;
    padding: 48px 40px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  }

  .login-header {
    text-align: center;
    margin-bottom: 40px;

    h1 {
      font-size: 28px;
      margin: 0 0 12px;
      color: #333;
    }

    p {
      font-size: 14px;
      color: #999;
      margin: 0;
    }
  }

  .login-form {
    .forgot-password {
      float: right;
      color: #409eff;
      font-size: 14px;
      cursor: pointer;

      &:hover {
        text-decoration: underline;
      }
    }

    .login-btn {
      width: 100%;
      margin-top: 24px;
    }

    .register-link {
      text-align: center;
      margin-top: 24px;
      font-size: 14px;
      color: #666;

      a {
        color: #409eff;
        text-decoration: none;

        &:hover {
          text-decoration: underline;
        }
      }
    }
  }
}
</style>
