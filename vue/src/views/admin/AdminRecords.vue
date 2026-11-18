<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AdminShell from '../../components/AdminShell.vue'
import Pagination from '../../components/Pagination.vue'
import DataTable from '../../components/DataTable.vue'
import { api } from '../../api'

type Kind = 'orders' | 'attempts' | 'draws'
interface Column { key: string; label: string }

const route = useRoute()
const router = useRouter()
const kind = ref<Kind>((route.query.kind as Kind) || 'orders')
const userId = ref(String(route.query.userId || ''))
const userName = ref(String(route.query.userName || ''))
const rows = ref<Array<Record<string, unknown>>>([])
const loading = ref(true)
const message = ref('')
const search = ref('')
const date = ref('')
const page = ref(1)
const pageSize = ref(10)
const totalPages = computed(() => Math.max(1, Math.ceil(rows.value.length / pageSize.value)))
const pagedRows = computed(() => rows.value.slice((page.value - 1) * pageSize.value, page.value * pageSize.value))

const columns = computed<Column[]>(() => {
  if (kind.value === 'orders') return [
    { key: 'prize_name', label: '奖品' },
    { key: 'status', label: '发放状态' },
    { key: 'type', label: '类型' },
    { key: 'amountCents', label: '金额' },
    { key: 'nickname', label: '用户' },
    { key: 'recipient', label: '领取信息' },
    { key: 'createdAt', label: '创建时间' },
  ]
  if (kind.value === 'attempts') return [
    { key: 'nickname', label: '用户' },
    { key: 'score', label: '得分' },
    { key: 'passed', label: '是否达标' },
    { key: 'status', label: '答题状态' },
    { key: 'totalSeconds', label: '用时' },
    { key: 'createdAt', label: '创建时间' },
  ]
  return [
    { key: 'nickname', label: '用户' },
    { key: 'prize_name', label: '奖品' },
    { key: 'won', label: '是否中奖' },
    { key: 'message', label: '抽奖结果' },
    { key: 'createdAt', label: '创建时间' },
  ]
})

const statusLabels: Record<string, string> = {
  pending: '待发放', processing: '发放中', ready: '待领取', shipped: '已发货',
  received: '已领取', granted: '已发放', wait_confirm: '待确认收款', paid: '已到账',
  held: '挂账处理中', failed: '发放失败', returned: '已退回', retrying: '重试中',
  active: '答题中', submitted: '已交卷', expired: '已过期',
}
const typeLabels: Record<string, string> = {
  cash: '现金红包', points: '积分', physical: '实物', souvenir: '纪念品', phone: '话费', none: '未中奖',
}

onMounted(load)

watch(() => route.query, (query) => {
  if (!query.userId) return
  userId.value = String(query.userId)
  userName.value = String(query.userName || '')
  kind.value = (query.kind as Kind) || 'orders'
  page.value = 1
  load()
})

function clearUser() {
  userId.value = ''
  userName.value = ''
  void router.replace({ path: '/admin/records', query: { kind: kind.value } })
  load()
}

async function load() {
  loading.value = true
  try {
    const params = new URLSearchParams({ kind: kind.value, q: search.value, date: date.value })
    if (userId.value) params.set('userId', userId.value)
    const data = await api<{ rows: Array<Record<string, unknown>> }>(`/api/admin/records?${params}`)
    rows.value = data.rows
    page.value = 1
  } catch (reason) {
    message.value = reason instanceof Error ? reason.message : '读取记录失败'
  } finally {
    loading.value = false
  }
}

function switchKind(value: Kind) {
  kind.value = value
  page.value = 1
  load()
}

function display(key: string, value: unknown) {
  if (value === null || value === undefined || value === '') return '—'
  if (key === 'status') return statusLabels[String(value)] || String(value)
  if (key === 'type') return typeLabels[String(value)] || String(value)
  if (key === 'amountCents') return `¥ ${(Number(value) / 100).toFixed(2)}`
  if (key === 'passed' || key === 'won') return value ? '是' : '否'
  if (key === 'totalSeconds') {
    const seconds = Number(value)
    return `${Math.floor(seconds / 60)}分${String(seconds % 60).padStart(2, '0')}秒`
  }
  if (key === 'recipient' && typeof value === 'object') {
    const recipient = value as Record<string, string>
    return [recipient.name, recipient.phone, recipient.address || recipient.pickup].filter(Boolean).join(' / ') || '—'
  }
  if (key === 'createdAt') {
    const text = String(value).replace('T', ' ')
    return text.slice(0, 16)
  }
  return String(value)
}

async function updateOrder(row: Record<string, unknown>, status: string) {
  const tracking = status === 'shipped' ? window.prompt('填写快递单号/发放备注（可留空）') || '' : ''
  try {
    await api(`/api/admin/orders/${row.id}`, { method: 'PUT', body: JSON.stringify({ status, tracking }) })
    message.value = '订单状态已更新'
    await load()
  } catch (reason) {
    message.value = reason instanceof Error ? reason.message : '更新失败'
  }
}

function orderActions(row: Record<string, unknown>) {
  const type = String(row.type || '')
  const status = String(row.status || '')
  if (type === 'phone' && status !== 'granted') return [{ label: '登记已发放', status: 'granted' }]
  if (['physical', 'souvenir'].includes(type)) {
    if (status === 'pending' || status === 'ready') return [{ label: '登记发货', status: 'shipped' }]
    if (status === 'shipped') return [{ label: '确认收货', status: 'received' }, { label: '退回', status: 'returned' }]
    if (status === 'returned') return [{ label: '重新发货', status: 'shipped' }]
  }
  return []
}
</script>

<template>
  <AdminShell active="records" title="记录与发奖" subtitle="查看答题、抽奖和中奖订单，导出对账数据。">
    <p v-if="message" class="notice-bar">{{ message }}</p>
    <section class="card">
      <div v-if="userId" class="user-filter">当前用户：<strong>{{ userName || userId.slice(0, 12) }}</strong><button type="button" @click="clearUser">清除筛选</button></div>
      <div class="toolbar">
        <button v-for="item in [{ key: 'orders', label: '中奖订单' }, { key: 'attempts', label: '答题记录' }, { key: 'draws', label: '抽奖记录' }]" :key="item.key" class="btn small" :class="{ secondary: kind !== item.key }" type="button" @click="switchKind(item.key as Kind)">{{ item.label }}</button>
        <span class="spacer" />
        <input v-model="search" placeholder="单号 / 昵称 / 手机号" />
        <input v-model="date" type="date" />
        <button class="btn small secondary" type="button" @click="load">查询</button>
        <a class="btn small secondary" :href="`/api/admin/export?kind=${kind}`">导出 XLSX</a>
      </div>
      <div v-if="loading" class="loading">加载记录…</div>
      <DataTable
        v-else-if="kind === 'orders'"
        :columns="columns"
        :rows="pagedRows"
        :format="display"
        table-class="records-table orders-table"
        empty-text="暂无记录"
      >
        <template #actions="{ row }">
          <button v-for="action in orderActions(row)" :key="action.status" type="button" @click="updateOrder(row, action.status)">{{ action.label }}</button>
        </template>
      </DataTable>
      <DataTable
        v-else
        :columns="columns"
        :rows="pagedRows"
        :format="display"
        :table-class="`records-table ${kind}-table`"
        empty-text="暂无记录"
      />
      <Pagination :page="page" :pages="totalPages" :total="rows.length" :page-size="pageSize" @update:page="page = $event" @update:page-size="pageSize = $event; page = 1" />
    </section>
  </AdminShell>
</template>