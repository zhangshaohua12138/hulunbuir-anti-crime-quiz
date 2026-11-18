<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api'
import { useSession } from '../store'
import type { Attempt } from '../types'
import ShareReviveOverlay from '../components/ShareReviveOverlay.vue'

const route = useRoute()
const router = useRouter()
const session = useSession()
const attempt = ref<Attempt | null>(null)
const loading = ref(true)
const error = ref('')
const showShare = ref(false)
const reviveNotice = ref('')
const canRevive = computed(() => Boolean(session.account?.canRevive))
const shareMode = computed(() => String(session.boot?.config.shareMode || 'manual'))

onMounted(async () => {
  await session.loadBoot()
  try {
    attempt.value = await api<Attempt>(`/api/attempts/${route.params.id}`)
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '读取成绩失败'
  } finally {
    loading.value = false
  }
  await session.loadBoot(true)
})

async function openRevive() {
  if (shareMode.value === 'disabled') return
  if (shareMode.value === 'free') {
    try {
      await api('/api/revive', { method: 'POST', body: JSON.stringify({ attemptId: attempt.value?.id, channel: 'free' }) })
      reviveNotice.value = '复活机会已到账，返回首页开始新一套答题。'
      await session.loadBoot(true)
    } catch (reason) {
      error.value = reason instanceof Error ? reason.message : '领取失败'
    }
    return
  }
  showShare.value = true
}

async function onRevived() {
  showShare.value = false
  reviveNotice.value = '分享成功，复活机会已到账，返回首页开始新一套答题。'
  await session.loadBoot(true)
}

function lottery() {
  if (!attempt.value) return
  router.push(`/lottery/${attempt.value.id}`)
}
</script>

<template>
  <div class="result-page">
    <header class="quiz-header">
      <a href="#/" class="quiz-back">← 返回首页</a>
      <span class="quiz-progress">本次成绩</span>
      <span />
    </header>

    <main v-if="attempt" class="result-card card">
      <div class="eyebrow">{{ attempt.passed ? '答题达标' : '继续加油' }}</div>
      <h1>{{ attempt.passed ? '答题达标，收获满满！' : '再接再厉，平安知识多一分' }}</h1>
      <div class="score-ring">
        <strong>{{ attempt.score }}</strong>
        <span>/ 100 分</span>
      </div>
      <p class="help">
        {{ attempt.passed ? '已达到抽奖门槛，可以前往抽奖。' : '学习的每一步都有意义，下一次继续加油。' }}
      </p>
      <p v-if="reviveNotice" class="notice-bar">{{ reviveNotice }}</p>
      <div class="result-actions">
        <button v-if="attempt.passed && !attempt.drawn" class="btn full" type="button" @click="lottery">去抽奖</button>
        <button v-else-if="!attempt.passed && canRevive" class="btn full" type="button" @click="openRevive">分享复活，再答一次</button>
        <a class="btn secondary full" href="#/">返回首页</a>
      </div>
    </main>

    <div v-else class="loading">{{ loading ? '正在读取成绩…' : (error || '成绩不存在') }}</div>
    <ShareReviveOverlay v-if="showShare && attempt" :attempt-id="attempt.id" @close="showShare = false" @granted="onRevived" />
  </div>
</template>