<script setup lang="ts">
import { onMounted, ref } from 'vue'
import AdminShell from '../../components/AdminShell.vue'
import Pagination from '../../components/Pagination.vue'
import { api } from '../../api'

interface Row { rank: number; nickname: string; points: number; totalSeconds: number }

const rows = ref<Row[]>([])
const frozen = ref(false)
const loading = ref(true)
const message = ref('')
const page = ref(1)
const pageSize = ref(10)
const totalPages = ref(1)
const pagedRows = ref<Row[]>([])

function paginate() {
  totalPages.value = Math.max(1, Math.ceil(rows.value.length / pageSize.value))
  if (page.value > totalPages.value) page.value = totalPages.value
  const start = (page.value - 1) * pageSize.value
  pagedRows.value = rows.value.slice(start, start + pageSize.value)
}

async function load() {
  loading.value = true
  try {
    const data = await api<{ rows: Row[]; frozen: boolean }>('/api/leaderboard')
    rows.value = data.rows || []
    frozen.value = Boolean(data.frozen)
    page.value = 1
    paginate()
  } catch (reason) {
    message.value = reason instanceof Error ? reason.message : '读取排行榜失败'
  } finally {
    loading.value = false
  }
}

function duration(seconds: number) {
  const total = Math.max(0, Math.round(Number(seconds) || 0))
  return `${Math.floor(total / 60)}分${String(total % 60).padStart(2, '0')}秒`
}

function changePage(next: number) {
  page.value = next
  paginate()
}

function changeSize(size: number) {
  pageSize.value = size
  page.value = 1
  paginate()
}

onMounted(load)
</script>

<template>
  <AdminShell active="leaderboard" title="排行榜" subtitle="按累计积分排名，含答题积分与抽奖积分；同分比较总用时。">
    <p v-if="message" class="notice-bar">{{ message }}</p>
    <section class="card">
      <div class="toolbar">
        <span class="help">共 {{ rows.length }} 人上榜</span>
        <span class="chip" :class="frozen ? 'gold' : 'green'">{{ frozen ? '已封榜' : '实时榜单' }}</span>
        <span class="spacer" />
        <button class="btn small secondary" type="button" @click="load">刷新</button>
      </div>
      <div v-if="loading" class="loading">加载排行榜…</div>
      <div v-else class="table-scroll">
        <table class="admin-table leaderboard-table">
          <thead><tr><th>排名</th><th>昵称</th><th>累计积分</th><th>总用时</th></tr></thead>
          <tbody>
            <tr v-for="row in pagedRows" :key="row.rank">
              <td class="rank-cell">{{ row.rank }}</td>
              <td>{{ row.nickname }}</td>
              <td><strong>{{ row.points }}</strong></td>
              <td>{{ duration(row.totalSeconds) }}</td>
            </tr>
          </tbody>
        </table>
        <p v-if="!rows.length" class="empty-canvas">暂无上榜记录</p>
      </div>
      <Pagination :page="page" :pages="totalPages" :total="rows.length" :page-size="pageSize" @update:page="changePage" @update:page-size="changeSize" />
    </section>
  </AdminShell>
</template>
