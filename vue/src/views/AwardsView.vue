<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import Pagination from '../components/Pagination.vue'
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
  recipient?: { name?: string; phone?: string; address?: string; pickup?: string }
  packageInfo?: string
  mchId?: string
  appId?: string
}

const router = useRouter()
const session = useSession()
const orders = ref<Order[]>([])
const loading = ref(true)
const error = ref('')
const claimOrder = ref<Order | null>(null)
const claimBusy = ref(false)
const page = ref(1)
const pageSize = ref(10)
const totalPages = computed(() => Math.max(1, Math.ceil(orders.value.length / pageSize.value)))
const pagedOrders = computed(() => orders.value.slice((page.value - 1) * pageSize.value, page.value * pageSize.value))
const claimError = ref('')
const claimForm = reactive({ name: '', phone: '', address: '', pickup: '' })

onMounted(async () => {
  await session.loadBoot()
  if (!session.boot?.user) {
    await router.replace('/')
    return
  }
  try {
    const result = await api<{ orders: Order[] }>('/api/orders')
    orders.value = result.orders || []
    page.value = 1
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '读取奖品失败'
  } finally {
    loading.value = false
  }
})

const statusName = (status?: string) =>
  ({ pending: '待发放', processing: '发放中', shipped: '已发货', received: '已领取', granted: '已发放', wait_confirm: '待确认收款', paid: '已到账', held: '挂账处理中', failed: '发放失败', returned: '已退回' }[status || ''] || status || '处理中')

const amount = (order: Order) => (order.amountCents ? `${(order.amountCents / 100).toFixed(2)} 元` : '')
const canClaim = (order: Order) => ['physical', 'souvenir', 'phone'].includes(order.type || '') && ['pending', 'ready', 'returned'].includes(order.status || '')

function openClaim(order: Order) {
  claimOrder.value = order
  claimError.value = ''
  claimForm.name = order.recipient?.name || ''
  claimForm.phone = order.recipient?.phone || ''
  claimForm.address = order.recipient?.address || ''
  claimForm.pickup = order.recipient?.pickup || ''
}

async function confirmTransfer(order: Order) {
  if (!order.packageInfo) {
    error.value = '暂未获取到确认收款凭证'
    return
  }
  const bridge = (window as any).WeixinJSBridge
  if (!bridge) {
    error.value = '请在微信中打开后确认收款'
    return
  }
  try {
    await new Promise<void>((resolve, reject) => {
      bridge.invoke('requestMerchantTransfer', { mchId: order.mchId, appId: order.appId, package: order.packageInfo }, (res: { err_msg?: string }) => {
        const msg = res?.err_msg || ''
        if (msg === 'requestMerchantTransfer:ok') resolve()
        else reject(new Error(msg === 'requestMerchantTransfer:cancel' ? '已取消收款' : '确认收款失败'))
      })
    })
    await api(`/api/orders/${order.id}/transfer/sync`, { method: 'POST', body: '{}' })
    error.value = ''
    const result = await api<{ orders: Order[] }>('/api/orders')
    orders.value = result.orders || []
    page.value = 1
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '确认收款失败'
  }
}

async function submitClaim() {
  if (!claimOrder.value || claimBusy.value) return
  claimBusy.value = true
  claimError.value = ''
  try {
    await api(`/api/orders/${claimOrder.value.id}/claim`, {
      method: 'PUT',
      body: JSON.stringify(claimForm),
    })
    claimOrder.value = null
    const result = await api<{ orders: Order[] }>('/api/orders')
    orders.value = result.orders || []
    page.value = 1
  } catch (reason) {
    claimError.value = reason instanceof Error ? reason.message : '登记失败'
  } finally {
    claimBusy.value = false
  }
}
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
      <div v-for="order in pagedOrders" :key="order.id" class="award-row">
        <div>
          <strong>{{ order.prize_name || order.name || '奖品' }}</strong>
          <p class="help">{{ amount(order) || order.message || '' }}</p>
          <button v-if="canClaim(order)" class="text-link" type="button" @click="openClaim(order)">{{ order.recipient?.phone ? '修改领取信息' : '登记领取信息' }}</button>
          <button v-if="order.type === 'cash' && order.status === 'wait_confirm' && order.packageInfo" class="text-link" type="button" @click="confirmTransfer(order)">确认收款</button>
        </div>
        <span class="award-status">{{ statusName(order.status) }}</span>
      </div>
      <p v-if="!loading && !orders.length" class="empty-canvas">暂无中奖记录。完成答题并达标后，可参与好礼抽取。</p>
      <div v-if="loading" class="loading">正在读取奖品…</div>
      <p v-if="error" class="form-error">{{ error }}</p>
      <Pagination :page="page" :pages="totalPages" :total="orders.length" :page-size="pageSize" @update:page="page = $event" @update:page-size="pageSize = $event; page = 1" />
    </main>

    <div v-if="claimOrder" class="claim-mask" @click.self="claimOrder = null">
      <form class="claim-panel card" @submit.prevent="submitClaim">
        <h2>登记领取信息</h2>
        <p class="help">{{ claimOrder.prize_name || claimOrder.name || '奖品' }}</p>
        <label v-if="claimOrder.type !== 'phone'">姓名<input v-model="claimForm.name" required maxlength="40" /></label>
        <label>手机号<input v-model="claimForm.phone" required pattern="1[3-9]\d{9}" maxlength="11" placeholder="11位手机号" /></label>
        <template v-if="claimOrder.type !== 'phone'">
          <label>收货地址<input v-model="claimForm.address" maxlength="300" placeholder="地址或自提点" /></label>
          <label>自提点（可选）<input v-model="claimForm.pickup" maxlength="300" /></label>
        </template>
        <p v-if="claimError" class="form-error">{{ claimError }}</p>
        <div class="claim-actions">
          <button class="btn secondary" type="button" @click="claimOrder = null">取消</button>
          <button class="btn" type="submit" :disabled="claimBusy">{{ claimBusy ? '提交中…' : '保存' }}</button>
        </div>
      </form>
    </div>
  </div>
</template>