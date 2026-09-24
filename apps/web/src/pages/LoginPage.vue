<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ApiError } from '../lib/api'
import { useAuth } from '../lib/auth'

const router = useRouter()
const { login } = useAuth()
const username = ref('')
const password = ref('')
const error = ref('')
const submitting = ref(false)

async function submit() {
  if (!username.value || !password.value) {
    error.value = '请输入用户名和密码'
    return
  }
  submitting.value = true
  error.value = ''
  try {
    await login(username.value, password.value)
    router.replace('/dashboard')
  } catch (err) {
    error.value = err instanceof ApiError ? err.message : '登录失败，请稍后重试'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <main class="login-screen">
    <div class="login-aside">
      <div class="login-mark">绩</div>
      <div class="eyebrow light">PERSONAL PERFORMANCE LEDGER</div>
      <h1>把每一笔<br /><em>应得的收益</em><br />记清楚。</h1>
      <p>项目完成只是开始。把公示、收款和到账串起来，你就不会再遗漏任何一笔绩效。</p>
      <div class="login-aside-line"></div>
      <span class="login-caption">PRIVATE · TRACEABLE · YOURS</span>
    </div>
    <div class="login-panel">
      <div class="login-box">
        <div class="eyebrow">WELCOME BACK</div>
        <h2>登录绩效账本</h2>
        <p class="login-subtitle">登录后查看你的项目和收益状态</p>
        <form @submit.prevent="submit">
          <label class="login-label">用户名</label>
          <input v-model="username" class="input login-input" autocomplete="username" placeholder="输入用户名" />
          <label class="login-label">密码</label>
          <input v-model="password" class="input login-input" type="password" autocomplete="current-password" placeholder="输入密码" />
          <div v-if="error" class="login-error">{{ error }}</div>
          <button class="button button-primary login-submit" :disabled="submitting">
            {{ submitting ? '正在验证…' : '进入账本' }} <span>→</span>
          </button>
        </form>
        <div class="login-foot">成员账号由管理员创建 · 数据按账号隔离</div>
      </div>
    </div>
  </main>
</template>

<style scoped>
.login-screen { min-height: 100vh; display: grid; grid-template-columns: 44% 56%; background: #fff; }
.login-aside { position: relative; display: flex; flex-direction: column; justify-content: center; padding: 12% 15%; overflow: hidden; background: #101a2b; color: #fff; }
.login-aside::after { position: absolute; right: -160px; bottom: -180px; width: 450px; height: 450px; border: 1px solid rgba(130, 208, 193, .15); border-radius: 50%; box-shadow: 0 0 0 30px rgba(130,208,193,.035), 0 0 0 61px rgba(130,208,193,.025); content: ''; }
.login-mark { display: grid; place-items: center; width: 47px; height: 47px; margin-bottom: 42px; border: 1px solid #60bda9; border-radius: 14px 14px 14px 3px; color: #c9f7ea; font-family: Georgia, serif; font-size: 24px; }
.eyebrow { color: #94a1b5; font-size: 10px; font-weight: 800; letter-spacing: .16em; }
.eyebrow.light { color: #76b5ae; }
.login-aside h1 { margin: 18px 0 19px; color: #fff; font-family: Georgia, serif; font-size: clamp(38px, 4vw, 60px); font-weight: 400; line-height: 1.15; letter-spacing: -.045em; }
.login-aside h1 em { color: #75c9b4; font-style: normal; }
.login-aside p { max-width: 360px; margin: 0; color: #9eafc4; font-size: 13px; line-height: 1.9; }
.login-aside-line { width: 45px; height: 1px; margin-top: 55px; background: #438c85; }
.login-caption { margin-top: 15px; color: #5e718a; font-size: 9px; letter-spacing: .18em; }
.login-panel { display: grid; place-items: center; background: #fbfcfe; }
.login-box { width: min(360px, 75%); }
.login-box h2 { margin: 15px 0 7px; color: #172033; font-family: Georgia, serif; font-size: 29px; font-weight: 500; }
.login-subtitle { margin: 0 0 33px; color: #8692a5; font-size: 13px; }
.login-label { display: block; margin: 17px 0 7px; color: #5d6b81; font-size: 12px; font-weight: 700; }
.login-input { height: 45px; }
.login-submit { width: 100%; height: 45px; margin-top: 25px; justify-content: space-between; padding: 0 16px; }
.login-error { margin-top: 12px; color: #b35459; font-size: 12px; }
.login-foot { margin-top: 26px; color: #a0a9b7; font-size: 11px; text-align: center; }
@media (max-width: 760px) {
  .login-screen { grid-template-columns: 1fr; }
  .login-aside { display: none; }
}
</style>
