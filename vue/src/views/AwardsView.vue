<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { useSession } from '../store'

interface Order {
  id: string
  prize_name?: string
  name?: string
  type?: string
  status?: string
  amountCents?: number
  message?: string
  createdAt?: string
}

const router = useRouter()
const session = useSession()
const orders = ref<Order[]>([])
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  await session.loadBoot()
  if (!session.boot?.user) {
    await router.replace('/')
    return
  }
  try {
    const result = await api<{ orders: Order[] }>('/api/orders')
    orders.value = result.orders || []
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '读取奖品失败'
  } finally {
    loading.value = false
  }
})

const statusName = (status?: string) =>
  ({ pending: '待发放', processing: '发放中', shipped: '已发货', received: '已领取', granted: '已发放', wait_confirm: '待确认收款', paid: '已到账', held: '挂账处理中', failed: '发放失败', returned: '已退回' }[status || ''] || status || '处理中')

const amount = (order: Order) => (order.amountCents ? `${(order.amountCents / 100).toFixed(2)} 元` : '')
</script>

<template>
  <div class="awards-page">
    <header class="quiz-header">
      <a href="#/" class="quiz-back">← 返回首页</a>
      <span class="quiz-progress">我的奖品</span>
      <span />
    </header>
    <main class="awards-card card">
      <div class="eyebrow">我的奖品</div>
      <h1>记录每一份收获</h1>
      <p class="help">中奖后请按提示确认收款或登记收货信息。</p>
      <div v-for="order in orders" :key="order.id" class="award-row">
        <div>
          <strong>{{ order.prize_name || order.name || '奖品' }}</strong>
          <p class="help">{{ amount(order) || order.message || '' }}</p>
        </div>
        <span class="award-status">{{ statusName(order.status) }}</span>
      </div>
      <p v-if="!loading && !orders.length" class="empty-canvas">暂无中奖记录。完成答题并达标后，可参与好礼抽取。</p>
      <div v-if="loading" class="loading">正在读取奖品…</div>
      <p v-if="error" class="form-error">{{ error }}</p>
    </main>
  </div>
</template>