<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import HomePreview from '../components/HomePreview.vue'
import { api } from '../api'
import { useSession } from '../store'
import { applyTheme } from '../theme'

const session = useSession()
const router = useRouter()
const nickname = ref('')
const loggingIn = ref(false)
const message = ref('')

const boot = computed(() => session.boot)
const layout = computed(() => session.layout)
const loggedIn = computed(() => Boolean(session.boot?.user))

onMounted(async () => {
  await session.loadBoot()
  applyTheme(session.config)
})

async function loginDemo() {
  if (loggingIn.value) return
  loggingIn.value = true
  message.value = ''
  try {
    await api('/api/auth/demo', {
      method: 'POST',
      body: JSON.stringify({ nickname: nickname.value || 'Vue 体验用户' }),
    })
    await session.loadBoot(true)
    applyTheme(session.config)
  } catch (error) {
    message.value = error instanceof Error ? error.message : '登录失败'
  } finally {
    loggingIn.value = false
  }
}

async function start() {
  if (!session.boot?.user) {
    void loginDemo()
    return
  }
  if (!session.boot.user.rules) {
    message.value = '请先阅读并同意活动规则，再开始答题。'
    await router.push('/rules')
    return
  }
  try {
    const attempt = await api<{ id: string }>('/api/attempts/start', { method: 'POST', body: '{}' })
    await router.push(`/quiz/${attempt.id}`)
  } catch (reason) {
    message.value = reason instanceof Error ? reason.message : '开始答题失败'
  }
}
</script>

<template>
  <div class="site-shell">
    <header class="site-header">
      <a class="brand" href="#/">
        <span class="brand-mark">法</span>
        <span>
          <strong>呼伦贝尔市 · 有奖答题</strong>
          <small>{{ boot?.config.brandSubtitle || '全民参与 · 共建平安' }}</small>
        </span>
      </a>
      <nav class="site-nav">
        <a href="#/">首页</a>
        <a href="#rules">规则</a>
        <a href="#ranking">榜单</a>
        <a href="#awards">奖品</a>
              </nav>
    </header>

    <main v-if="boot" class="page">
      <HomePreview :boot="boot" :layout="layout" @start="start" />
      <div v-if="message" class="notice-bar">{{ message }}</div>

      <section v-if="!loggedIn" class="card login-card">
        <div class="section-title">体验 Vue 版首页</div>
        <p class="help">当前是演示环境，输入昵称即可体验布局和主题渲染。</p>
        <div class="login-row">
          <input v-model="nickname" maxlength="24" placeholder="输入昵称" @keyup.enter="loginDemo" />
          <button class="btn" type="button" :disabled="loggingIn" @click="loginDemo">
            {{ loggingIn ? '登录中…' : '登录参与' }}
          </button>
        </div>
      </section>

    </main>

    <footer class="site-footer">
      {{ boot?.config.organizer || '主办单位待确认' }} · {{ boot?.config.footerText || '学法知法 · 守护平安 · 共建美好家园' }}
    </footer>
  </div>
</template>