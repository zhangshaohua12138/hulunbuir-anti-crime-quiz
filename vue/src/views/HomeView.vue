<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import HomePreview from '../components/HomePreview.vue'
import { api } from '../api'
import { useSession } from '../store'
import { applyTheme } from '../theme'
import { configureWechatShare } from '../wechat'

const session = useSession()
const router = useRouter()
const nickname = ref('')
const loggingIn = ref(false)
const message = ref('')
const followOpen = ref(false)
const followBusy = ref(false)
const followError = ref('')
const inWeChat = /MicroMessenger/i.test(navigator.userAgent)
const isDemo = computed(() => session.boot?.mode === 'demo')

const boot = computed(() => session.boot)
const layout = computed(() => session.layout)
const loggedIn = computed(() => Boolean(session.boot?.user))

onMounted(async () => {
  await session.loadBoot()
  applyTheme(session.config)
  void configureWechatShare(session.config)
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

async function wechatLogin() {
  window.location.href = `/api/auth/wechat?next=${encodeURIComponent('/vue/')}`
}

async function checkFollow() {
  followBusy.value = true
  followError.value = ''
  try {
    await api('/api/follow/refresh', { method: 'POST', body: '{}' })
    await session.loadBoot(true)
    if (session.boot?.user?.followed) {
      followOpen.value = false
      await start()
      return
    }
  } catch (reason) {
    followError.value = reason instanceof Error ? reason.message : '请先关注公众号'
  }
  followBusy.value = false
  followOpen.value = true
}

async function demoFollow() {
  try {
    await api('/api/demo/follow', { method: 'POST', body: '{}' })
    await session.loadBoot(true)
    followOpen.value = false
    await start()
  } catch (reason) {
    followError.value = reason instanceof Error ? reason.message : '模拟关注失败'
  }
}

async function start() {
  if (!session.boot?.user) {
    if (isDemo.value) void loginDemo()
    else wechatLogin()
    return
  }
  if (!session.boot.user.followed) {
    await checkFollow()
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
        <div class="section-title">{{ isDemo ? '体验 Vue 版首页' : '微信登录参与' }}</div>
        <p class="help">{{ isDemo ? '当前是演示环境，输入昵称即可体验布局和主题渲染。' : '请在微信中打开，授权后参与活动。' }}</p>
        <div v-if="isDemo" class="login-row">
          <input v-model="nickname" maxlength="24" placeholder="输入昵称" @keyup.enter="loginDemo" />
          <button class="btn" type="button" :disabled="loggingIn" @click="loginDemo">
            {{ loggingIn ? '登录中…' : '登录参与' }}
          </button>
        </div>
        <button v-else class="btn full" type="button" @click="wechatLogin">微信授权登录</button>
      </section>

    </main>

    <div v-if="followOpen" class="follow-mask" @click.self="followOpen = false">
      <div class="follow-panel card">
        <h2>请先关注公众号</h2>
        <p class="help">关注“呼伦贝尔政法”后，刷新状态即可参与。</p>
        <img class="follow-qr" :src="'/static/follow-qr.jpg'" alt="公众号二维码" />
        <p v-if="followError" class="form-error">{{ followError }}</p>
        <button class="btn full" type="button" :disabled="followBusy" @click="checkFollow">{{ followBusy ? '检查中…' : '我已关注，刷新状态' }}</button>
        <button v-if="isDemo && !inWeChat" class="btn secondary full" type="button" @click="demoFollow">模拟已关注（演示）</button>
        <a v-if="boot?.config.followUrl" class="text-link" :href="String(boot.config.followUrl)" target="_blank" rel="noopener">打开公众号文章</a>
        <button class="text-link" type="button" @click="followOpen = false">稍后再说</button>
      </div>
    </div>

    <footer class="site-footer">
      {{ boot?.config.organizer || '主办单位待确认' }} · {{ boot?.config.footerText || '学法知法 · 守护平安 · 共建美好家园' }}
    </footer>
  </div>
</template>