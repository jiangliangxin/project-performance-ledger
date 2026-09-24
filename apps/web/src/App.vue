<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuth } from './lib/auth'
import { ApiError } from './lib/api'

const router = useRouter()
const route = useRoute()
const { user, loading, isAuthenticated, load, logout } = useAuth()
const notice = ref('')

const navItems = computed(() => {
  const items = [
    { path: '/dashboard', label: '总览', icon: '◈' },
    { path: '/records', label: '合作记录', icon: '▤' },
    { path: '/project-types', label: '项目类型', icon: '◇' },
    { path: '/imports', label: '批量导入', icon: '⇩' },
  ]
  if (user.value?.role === 'admin') items.push({ path: '/users', label: '成员账号', icon: '◎' })
  return items
})

const pageTitle = computed(() => {
  const current = navItems.value.find((item) => route.path.startsWith(item.path))
  if (route.name === 'record-detail') return '合作记录详情'
  return current?.label ?? '绩效收益台账'
})

onMounted(load)

watch([isAuthenticated, loading], ([authenticated, isLoading]) => {
  if (!isLoading && !authenticated && route.name !== 'login') router.replace('/login')
  if (!isLoading && authenticated && route.name === 'login') router.replace('/dashboard')
})

async function signOut() {
  await logout()
  router.replace('/login')
}

function handleError(error: unknown) {
  notice.value = error instanceof ApiError ? error.message : '操作失败，请稍后重试'
  window.setTimeout(() => (notice.value = ''), 3200)
}
</script>

<template>
  <div v-if="loading" class="boot-screen">
    <div class="loader"></div>
    <span>正在打开你的绩效账本…</span>
  </div>
  <RouterView v-else-if="!isAuthenticated || route.name === 'login'" @error="handleError" />
  <div v-else class="app-shell">
    <aside class="sidebar">
      <div class="brand-lockup">
        <div class="brand-mark">绩</div>
        <div>
          <strong>绩效账本</strong>
          <span>Personal Ledger</span>
        </div>
      </div>
      <div class="sidebar-label">工作台</div>
      <nav class="nav-list">
        <RouterLink v-for="item in navItems" :key="item.path" :to="item.path" class="nav-item" active-class="is-active">
          <span class="nav-icon">{{ item.icon }}</span>
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>
      <div class="sidebar-footnote">
        <span class="status-dot"></span>
        <span>本地数据已保护</span>
      </div>
    </aside>

    <main class="main-shell">
      <header class="topbar">
        <div>
          <div class="eyebrow">PERSONAL PERFORMANCE LEDGER</div>
          <h1>{{ pageTitle }}</h1>
        </div>
        <div class="user-menu">
          <div class="avatar">{{ user?.display_name.slice(0, 1) }}</div>
          <div class="user-copy">
            <strong>{{ user?.display_name }}</strong>
            <span>{{ user?.role === 'admin' ? '管理员' : '成员' }}</span>
          </div>
          <button class="icon-button" title="退出登录" @click="signOut">↗</button>
        </div>
      </header>
      <div v-if="notice" class="toast toast-error">{{ notice }}</div>
      <section class="content-area">
        <RouterView @error="handleError" />
      </section>
    </main>
  </div>
</template>
