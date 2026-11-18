<script setup lang="ts">
import { onMounted, ref } from 'vue'
import AdminShell from '../../components/AdminShell.vue'
import { api } from '../../api'

interface Dashboard {
  mode: string
  frozen: boolean
  stats: { users: number; attempts: number; passed: number; orders: number; spentCents: number }
  warnings: string[]
  pendingConfirmations: string[]
}

const data = ref<Dashboard | null>(null)
const error = ref('')
const actionMessage = ref('')

onMounted(async () => {
  try {
    data.value = await api<Dashboard>('/api/admin/dashboard')
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '读取概览失败'
  }
})

const money = (cents: number) => `¥ ${(cents / 100).toFixed(2)}`

async function reload() {
  data.value = await api<Dashboard>('/api/admin/dashboard')
}

async function resetActivity() {
  const password = window.prompt('输入管理员密码确认重置活动数据')
  if (!password) return
  if (!window.confirm('确定清空用户、答题、抽奖和订单数据？')) return
  try {
    const result = await api<{ counts: Record<string, number> }>('/api/admin/reset', {
      method: 'POST',
      body: JSON.stringify({ confirm: 'RESET', password }),
    })
    actionMessage.value = `已重置：用户 ${result.counts.users || 0}，答题 ${result.counts.attempts || 0}`
    await reload()
  } catch (reason) {
    actionMessage.value = reason instanceof Error ? reason.message : '重置失败'
  }
}

async function unfreeze() {
  try {
    await api('/api/admin/unfreeze', { method: 'POST', body: '{}' })
    actionMessage.value = '已解除封榜'
    await reload()
  } catch (reason) {
    actionMessage.value = reason instanceof Error ? reason.message : '解除失败'
  }
}
</script>

<template>
  <AdminShell active="dashboard" title="运营概览" subtitle="掌握参与情况、预算消耗和发奖状态。">
    <p v-if="error" class="form-error">{{ error }}</p>
    <div v-if="data" class="admin-metrics">
      <div class="admin-metric"><span>参与人数</span><strong>{{ data.stats.users }}</strong></div>
      <div class="admin-metric"><span>答题套次</span><strong>{{ data.stats.attempts }}</strong></div>
      <div class="admin-metric"><span>达标套次</span><strong>{{ data.stats.passed }}</strong></div>
      <div class="admin-metric"><span>中奖订单</span><strong>{{ data.stats.orders }}</strong></div>
      <div class="admin-metric wide"><span>已用红包预算</span><strong>{{ money(data.stats.spentCents) }}</strong></div>
    </div>
    <p v-if="actionMessage" class="notice-bar">{{ actionMessage }}</p>
    <div v-if="data" class="admin-split">
      <section class="card">
        <h2>快捷操作</h2>
        <div class="quick-grid">
          <a href="#/admin/config">活动配置</a>
          <a href="#/admin/questions">题库管理</a>
          <a href="#/admin/prizes">奖品管理</a>
          <a href="#/admin/records">记录与发奖</a>
          <a href="#/admin/config">活动配置</a>
          <a href="#/admin/users">用户管理</a>
        </div>
      </section>
      <section class="card">
        <h2>活动控制</h2>
        <div class="control-row">
          <button class="btn secondary small" type="button" @click="unfreeze" :disabled="!data.frozen">解除封榜</button>
          <button class="btn secondary small danger" type="button" @click="resetActivity">重置活动数据</button>
        </div>
        <p class="help">重置会清空用户、答题、抽奖、订单和榜单，操作不可撤销。</p>
      </section>
      <section class="card">
        <h2>提醒</h2>
        <p v-if="data.frozen" class="notice-bar">活动榜单已封存。</p>
        <p v-for="warn in data.warnings" :key="warn" class="notice-bar">{{ warn }}</p>
        <p v-if="data.pendingConfirmations.length" class="notice-bar">还有 {{ data.pendingConfirmations.length }} 项上线确认未完成。</p>
        <p v-if="!data.warnings.length && !data.frozen && !data.pendingConfirmations.length" class="help">暂无异常提醒。</p>
      </section>
    </div>
  </AdminShell>
</template>