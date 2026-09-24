<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { api, ApiError } from '../lib/api'
import type { User } from '../lib/types'

const users = ref<User[]>([])
const loading = ref(true)
const error = ref('')
const showForm = ref(false)
const submitting = ref(false)
const form = reactive({ username: '', display_name: '', password: '', role: 'member' })

async function load() {
  loading.value = true
  try { users.value = await api.get<User[]>('/api/v1/admin/users') } catch (err) { error.value = err instanceof Error ? err.message : '加载失败' } finally { loading.value = false }
}

async function createUser() {
  submitting.value = true
  error.value = ''
  try {
    await api.post('/api/v1/admin/users', form)
    Object.assign(form, { username: '', display_name: '', password: '', role: 'member' })
    showForm.value = false
    await load()
  } catch (err) { error.value = err instanceof ApiError ? err.message : '创建失败' } finally { submitting.value = false }
}

async function toggleUser(user: User) {
  try { await api.patch(`/api/v1/admin/users/${user.id}`, { status: user.status === 'active' ? 'disabled' : 'active' }); await load() } catch (err) { error.value = err instanceof ApiError ? err.message : '更新失败' }
}

async function resetPassword(user: User) {
  const password = window.prompt(`为 ${user.display_name} 设置新密码（至少8位）`)
  if (!password) return
  try { await api.post(`/api/v1/admin/users/${user.id}/reset-password`, { password }); window.alert('密码已重置'); } catch (err) { error.value = err instanceof ApiError ? err.message : '重置失败' }
}

onMounted(load)
</script>

<template>
  <div class="page-head"><div><h2>成员账号</h2><p>管理员创建账号，普通成员的数据彼此隔离。</p></div><button class="button button-primary" @click="showForm = true">＋ 创建成员</button></div>
  <div v-if="error" class="inline-alert">{{ error }}</div>
  <div class="card table-card"><div v-if="loading" class="loading-line">正在加载成员…</div><table v-else class="data-table"><thead><tr><th>成员</th><th>用户名</th><th>角色</th><th>状态</th><th>创建时间</th><th>操作</th></tr></thead><tbody><tr v-for="member in users" :key="member.id"><td class="primary-cell">{{ member.display_name }}</td><td>{{ member.username }}</td><td>{{ member.role === 'admin' ? '管理员' : '成员' }}</td><td><span class="status-pill" :class="member.status === 'active' ? 'teal' : 'red'">{{ member.status === 'active' ? '正常' : '已停用' }}</span></td><td>{{ member.created_at.slice(0, 10) }}</td><td><div class="actions"><button v-if="member.role !== 'admin'" class="button button-small" @click="toggleUser(member)">{{ member.status === 'active' ? '停用' : '启用' }}</button><button v-if="member.role !== 'admin'" class="button button-small" @click="resetPassword(member)">重置密码</button></div></td></tr></tbody></table></div>
  <div v-if="showForm" class="drawer-backdrop" @click.self="showForm = false"><aside class="drawer"><div class="drawer-head"><div><div class="eyebrow">NEW MEMBER</div><h2>创建成员账号</h2></div><button class="close-button" @click="showForm = false">×</button></div><form class="form-grid" @submit.prevent="createUser"><div class="form-field full"><label>显示名称</label><input v-model="form.display_name" class="input" placeholder="例如：张三" /></div><div class="form-field"><label>用户名</label><input v-model="form.username" class="input" autocomplete="off" placeholder="用于登录" /></div><div class="form-field"><label>初始密码</label><input v-model="form.password" class="input" type="password" autocomplete="new-password" placeholder="至少8位" /></div><div class="form-field full"><label>角色</label><select v-model="form.role" class="select"><option value="member">普通成员</option><option value="admin">管理员</option></select></div><div class="form-footer full"><button type="button" class="button" @click="showForm = false">取消</button><button class="button button-primary" :disabled="submitting">{{ submitting ? '创建中…' : '创建账号' }}</button></div></form></aside></div>
</template>
