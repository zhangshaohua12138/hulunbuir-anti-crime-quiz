<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import Pagination from '../components/Pagination.vue'
import { api } from '../api'
import { useSession } from '../store'

interface Row {
  rank: number
  nickname: string
  points: number
  totalSeconds: number
}

const route = useRoute()
const session = useSession()
const rows = ref<Row[]>([])
const me = ref<Row | null>(null)
const frozen = ref(false)
const loading = ref(true)
const error = ref('')
const winners = route.query.winners === '1'
const page = ref(1)
const pageSize = ref(10)
const totalPages = computed(() => Math.max(1, Math.ceil(rows.value.length / pageSize.value)))
const pagedRows = computed(() => rows.value.slice((page.value - 1) * pageSize.value, page.value * pageSize.value))

onMounted(async () => {
  await session.loadBoot()
  try {
    const result = await api<{ rows: Row[]; me: Row | null; frozen: boolean }>(`/api/leaderboard${winners ? '?winners=1' : ''}`)
    rows.value = result.rows
    page.value = 1
    me.value = result.me
    frozen.value = result.frozen
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '读取榜单失败'
  } finally {
    loading.value = false
  }
})

function time(seconds: number) {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}分${String(s).padStart(2, '0')}秒`
}
</script>

<template>
  <div class="ranking-page">
    <header class="quiz-header">
      <a href="#/" class="quiz-back">← 返回首页</a>
      <span class="quiz-progress">{{ winners ? '获奖公示' : '积分榜单' }}</span>
      <span />
    </header>
    <main class="ranking-card card">
      <div class="eyebrow">{{ winners ? '荣誉榜单' : '共同进步' }}</div>
      <h1>{{ winners ? '获奖名单公示' : '每一分努力，都值得被看见' }}</h1>
      <p class="help">{{ frozen ? '榜单已封存，排名以最终公示为准。' : '按最高成绩加抽奖积分排名，多套不累计。' }}</p>
      <div v-if="me" class="my-rank">
        我的排名：<strong>第 {{ me.rank }} 名</strong> · {{ me.points }} 分
      </div>
      <div class="rank-list">
        <div v-for="row in pagedRows" :key="row.rank + row.nickname" class="rank-row" :class="{ mine: me?.nickname === row.nickname }">
          <span class="rank-no">{{ row.rank }}</span>
          <span class="rank-name">{{ row.nickname }}</span>
          <span class="rank-points">{{ row.points }} 分</span>
          <span class="rank-time">{{ time(row.totalSeconds) }}</span>
        </div>
        <p v-if="!loading && !rows.length" class="empty-canvas">还没有上榜记录。</p>
      </div>
      <Pagination :page="page" :pages="totalPages" :total="rows.length" :page-size="pageSize" @update:page="page = $event" @update:page-size="pageSize = $event; page = 1" />
      <div v-if="loading" class="loading">正在读取榜单…</div>
      <p v-if="error" class="form-error">{{ error }}</p>
    </main>
  </div>
</template>