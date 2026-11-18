<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api'
import { useSession } from '../store'
import type { Attempt, LotteryResult } from '../types'
import MobileNav from '../components/MobileNav.vue'

const route = useRoute()
const router = useRouter()
const session = useSession()
const attempt = ref<Attempt | null>(null)
const result = ref<LotteryResult | null>(null)
const loading = ref(true)
const drawing = ref(false)
const error = ref('')

onMounted(async () => {
  await session.loadBoot()
  try {
    attempt.value = await api<Attempt>(`/api/attempts/${route.params.id}`)
    if (attempt.value.lottery) result.value = attempt.value.lottery as LotteryResult
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '读取抽奖信息失败'
  } finally {
    loading.value = false
  }
})

async function draw() {
  if (!attempt.value || drawing.value || result.value) return
  drawing.value = true
  error.value = ''
  try {
    result.value = await api<LotteryResult>('/api/lottery', {
      method: 'POST',
      body: JSON.stringify({ attemptId: attempt.value.id }),
    })
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '抽奖失败'
  } finally {
    drawing.value = false
  }
}
</script>

<template>
  <div class="lottery-page">
    <header class="quiz-header">
      <a href="#/" class="quiz-back">← 返回首页</a>
      <span class="quiz-progress">答题有礼</span>
      <span />
    </header>
    <main class="lottery-card card">
      <div class="eyebrow">答题有礼</div>
      <h1>{{ result?.won ? '恭喜中奖！' : result ? '本次未中奖' : '答题有礼，好运开启' }}</h1>
      <div class="lottery-wheel" :class="{ spinning: drawing }">
        <span>礼</span>
      </div>
      <p v-if="!result" class="help">达到 {{ session.boot?.config.passScore ?? 80 }} 分即可参与一次抽奖。</p>
      <p v-else class="lottery-message">{{ result.message }}</p>
      <p v-if="result?.won && result.prize" class="lottery-prize">{{ result.prize.name }}</p>
      <p v-if="error" class="form-error">{{ error }}</p>
      <div class="result-actions">
        <button v-if="!result" class="btn full" type="button" :disabled="drawing || !attempt?.passed" @click="draw">
          {{ drawing ? '抽取中…' : '开始抽奖' }}
        </button>
        <a class="btn secondary full" href="#awards">查看我的奖品</a>
        <a class="btn secondary full" href="#/">返回首页</a>
      </div>
    </main>
    <div v-if="loading" class="loading">正在读取抽奖信息…</div>
  </div>
  <MobileNav active="awards" />
</template>
