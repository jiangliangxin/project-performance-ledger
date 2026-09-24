import { computed, ref } from 'vue'
import type { User } from './types'
import { api } from './api'

const user = ref<User | null>(null)
const loading = ref(true)

export function useAuth() {
  const isAuthenticated = computed(() => user.value !== null)

  async function load() {
    try {
      user.value = await api.get<User>('/api/v1/auth/me')
    } catch {
      user.value = null
    } finally {
      loading.value = false
    }
  }

  async function login(username: string, password: string) {
    user.value = await api.post<User>('/api/v1/auth/login', { username, password })
  }

  async function logout() {
    await api.post('/api/v1/auth/logout')
    user.value = null
  }

  return { user, loading, isAuthenticated, load, login, logout }
}
