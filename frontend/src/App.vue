<template>
  <router-view v-if="route.path === '/auth'" />
  <div v-else class="app-shell">
    <aside class="sidebar" :class="{ collapsed }">
      <div class="brand">
        <div class="brand-mark">WL</div>
        <div v-if="!collapsed" class="brand-text">
          <div class="brand-title">WellLog</div>
          <div class="brand-subtitle">LSTM 管理系统</div>
        </div>
      </div>

      <el-menu
        :default-active="route.path"
        class="nav-menu"
        :collapse="collapsed"
        router
        background-color="transparent"
        text-color="#334155"
        active-text-color="#2563eb"
      >
        <el-menu-item index="/manage">
          <el-icon><Menu /></el-icon>
          <template #title>钻井管理</template>
        </el-menu-item>
        <el-menu-item index="/predict">
          <el-icon><TrendCharts /></el-icon>
          <template #title>钻井预测</template>
        </el-menu-item>
        <el-menu-item index="/records">
          <el-icon><TrendCharts /></el-icon>
          <template #title>预测记录</template>
        </el-menu-item>
      </el-menu>
    </aside>

    <section class="main-shell">
      <header class="topbar">
        <div class="topbar-left">
          <el-button text class="collapse-btn" @click="collapsed = !collapsed">
            <el-icon><Fold v-if="!collapsed" /><Expand v-else /></el-icon>
          </el-button>
          <div class="page-title">{{ pageTitle }}</div>
        </div>

        <div class="topbar-right">
          <el-tag effect="light" type="info">{{ currentUser?.username || '未登录' }}</el-tag>
          <el-tag effect="light" type="success">API /api</el-tag>
          <el-button text @click="logout">退出</el-button>
        </div>
      </header>

      <main class="content">
        <router-view />
      </main>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Expand, Fold, Menu, TrendCharts } from '@element-plus/icons-vue'
import { clearSession, getSession } from './auth'

const route = useRoute()
const router = useRouter()
const collapsed = ref(false)
const currentUser = ref(getSession())

const pageTitle = computed(() => {
  if (route.path === '/predict') return '钻井预测'
  if (route.path === '/records') return '预测记录'
  return '钻井管理'
})

function logout() {
  clearSession()
  currentUser.value = null
  router.replace('/auth')
}

function syncSession() {
  currentUser.value = getSession()
}

onMounted(() => {
  window.addEventListener('welllog-session-change', syncSession)
})
</script>
