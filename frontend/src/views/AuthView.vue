<template>
  <div class="auth-shell">
    <div class="auth-glow auth-glow-a"></div>
    <div class="auth-glow auth-glow-b"></div>

    <div class="auth-panel">
      <section class="auth-card">
        <h2>基于LSTM的CNL预测系统</h2>
        <div class="auth-tabs">
          <button :class="{ active: mode === 'login' }" @click="mode = 'login'">登录</button>
          <button :class="{ active: mode === 'register' }" @click="mode = 'register'">注册</button>
        </div>

        <el-form v-if="mode === 'login'" ref="loginFormRef" :model="loginForm" :rules="loginRules" label-position="top">
          <el-form-item label="用户名" prop="username">
            <el-input v-model="loginForm.username" placeholder="请输入用户名" />
          </el-form-item>
          <el-form-item label="密码" prop="password">
            <el-input v-model="loginForm.password" type="password" show-password placeholder="请输入密码" @keyup.enter="submitLogin" />
          </el-form-item>
          <el-button class="auth-submit" type="primary" :loading="submitting" @click="submitLogin">登录</el-button>
        </el-form>

        <el-form v-else ref="registerFormRef" :model="registerForm" :rules="registerRules" label-position="top">
          <el-form-item label="用户名" prop="username">
            <el-input v-model="registerForm.username" placeholder="请输入用户名" />
          </el-form-item>
          <el-form-item label="姓名" prop="fullName">
            <el-input v-model="registerForm.fullName" placeholder="可选" />
          </el-form-item>
          <el-form-item label="邮箱" prop="email">
            <el-input v-model="registerForm.email" placeholder="可选" />
          </el-form-item>
          <el-form-item label="密码" prop="password">
            <el-input v-model="registerForm.password" type="password" show-password placeholder="至少 6 位" />
          </el-form-item>
          <el-button class="auth-submit" type="primary" :loading="submitting" @click="submitRegister">注册并登录</el-button>
        </el-form>
      </section>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { api } from '../api'
import { setSession } from '../auth'

const router = useRouter()
const mode = ref('login')
const submitting = ref(false)
const loginFormRef = ref()
const registerFormRef = ref()

const loginForm = reactive({ username: '', password: '' })
const registerForm = reactive({ username: '', fullName: '', email: '', password: '' })

const loginRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const registerRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 位', trigger: 'blur' },
  ],
  email: [{ type: 'email', message: '邮箱格式不正确', trigger: 'blur' }],
}

function afterLogin(user) {
  setSession(user)
  ElMessage.success(`欢迎，${user.username}`)
  router.replace('/manage')
}

async function submitLogin() {
  await loginFormRef.value?.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      afterLogin(await api.login(loginForm))
    } catch (error) {
      ElMessage.error(error.message)
    } finally {
      submitting.value = false
    }
  })
}

async function submitRegister() {
  await registerFormRef.value?.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      await api.register({
        username: registerForm.username.trim(),
        password: registerForm.password,
        fullName: registerForm.fullName.trim() || null,
        email: registerForm.email.trim() || null,
        role: 'USER',
      })
      afterLogin(await api.login({ username: registerForm.username, password: registerForm.password }))
    } catch (error) {
      ElMessage.error(error.message)
    } finally {
      submitting.value = false
    }
  })
}
</script>
