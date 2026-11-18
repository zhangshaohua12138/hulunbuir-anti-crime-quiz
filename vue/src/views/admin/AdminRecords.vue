<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import AdminShell from '../../components/AdminShell.vue'
import { api } from '../../api'

const kind = ref<'orders' | 'attempts' | 'draws'>('orders')
const rows = ref<Array<Record<string, unknown>>>([])
const loading = ref(true)
const message = ref('')
const search = ref('')
const date = ref('')

const columns = computed(() => {
  if (kind.value === 'orders') return ['prize_name', 'status', 'type', 'amountCents', 'nickname', 'recipient', 'createdAt']
  if (kind.value === 'attempts') return ['nickname', 'score', 'passed', 'status', 'totalSeconds', 'createdAt']
  return ['nickname', 'prize_name', 'won', 'message', 'createdAt']
})

onMounted(load)

async function load() {
  loading.value = true
  try {
    const params = new URLSearchParams({ kind: kind.value, q: search.value, date: date.value })
    const data = await api<{ rows: Array<Record<string, unknown>> }>(`/api/admin/records?${params}`)
    rows.value = data.rows
  } catch (reason) {
    message.value = reason instanceof Error ? reason.message : '读取记录失败'
  } finally {
    loading.value = false
  }
}

function switchKind(value: 'orders' | 'attempts' | 'draws') {
  kind.value = value
  load()
}

function display(value: unknown) {
  if (value && typeof value === 'object') return JSON.stringify(value)
  if (value === true) return '是'
  if (value === false) return '否'
  return value ?? '—'
}
</script>

<template>
  <AdminShell active="records" title="记录与发奖" subtitle="查看答题、抽奖和中奖订单，导出对账数据。">
    <p v-if="message" class="notice-bar">{{ message }}</p>
    <section class="card">
      <div class="toolbar">
        <button v-for="item in [{ key: 'orders', label: '中奖订单' }, { key: 'attempts', label: '答题记录' }, { key: 'draws', label: '抽奖记录' }]" :key="item.key" class="btn small" :class="{ secondary: kind !== item.key }" type="button" @click="switchKind(item.key as any)">{{ item.label }}</button>
        <span class="spacer" />
        <input v-model="search" placeholder="单号/昵称/手机号" />
        <input v-model="date" type="date" />
        <button class="btn small secondary" type="button" @click="load">查询</button>
        <a class="btn small secondary" :href="`/api/admin/export?kind=${kind}`">导出 XLSX</a>
      </div>
      <div v-if="loading" class="loading">加载记录…</div>
      <div v-else class="table-scroll">
        <table class="admin-table">
          <thead><tr><th v-for="column in columns" :key="column">{{ column }}</th></tr></thead>
          <tbody>
            <tr v-for="(row, index) in rows" :key="index">
              <td v-for="column in columns" :key="column">{{ display(row[column]) }}</td>
            </tr>
          </tbody>
        </table>
        <p v-if="!rows.length" class="empty-canvas">暂无记录</p>
      </div>
    </section>
  </AdminShell>
</template>