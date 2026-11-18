<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useSession } from '../store'

const router = useRouter()
const session = useSession()
const username = ref('admin')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function submit() {
  if (loading.value) return
  loading.value = true
  error.value = ''
  try {
    await session.login(username.value, password.value)
    await router.replace('/admin')
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '登录失败'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="login-page">
    <section class="login-panel">
      <div class="eyebrow">管理后台</div>
      <h1>活动管理后台</h1>
      <p class="help">使用超级管理员或运营账号登录，管理活动、题库、奖品和发奖。</p>
      <form @submit.prevent="submit">
        <label>
          用户名
          <input v-model="username" autocomplete="username" required />
        </label>
        <label>
          密码
          <input v-model="password" type="password" autocomplete="current-password" required />
        </label>
        <p v-if="error" class="form-error">{{ error }}</p>
        <button class="btn full" type="submit" :disabled="loading">
          {{ loading ? '登录中…' : '登录管理后台' }}
        </button>
      </form>
      <a class="text-link" href="/">返回活动首页</a>
    </section>
  </main>
</template>