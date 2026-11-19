<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import AdminShell from '../../components/AdminShell.vue'
import Pagination from '../../components/Pagination.vue'
import { api } from '../../api'

interface Prize {
  id?: string
  name: string
  type: string
  amountCents: number
  stock: number
  dailyLimit: number
  weight: number
  enabled: boolean
  points: number
  issued?: number
  remaining?: number
}

const prizes = ref<Prize[]>([])
const loading = ref(true)
const message = ref('')
const editing = ref(false)
const page = ref(1)
const pageSize = ref(10)
const totalPages = computed(() => Math.max(1, Math.ceil(prizes.value.length / pageSize.value)))
const pagedPrizes = computed(() => prizes.value.slice((page.value - 1) * pageSize.value, page.value * pageSize.value))
const form = reactive<Prize>({ name: '', type: 'none', amountCents: 0, stock: 1, dailyLimit: 1, weight: 1, enabled: true, points: 0 })

onMounted(load)

async function load() {
  loading.value = true
  try {
    const data = await api<{ prizes: Prize[] }>('/api/admin/prizes')
    prizes.value = data.prizes
    page.value = 1
  } catch (reason) {
    message.value = reason instanceof Error ? reason.message : '读取奖品失败'
  } finally {
    loading.value = false
  }
}

function edit(prize?: Prize) {
  Object.assign(form, prize ? { ...prize, enabled: Boolean(prize.enabled) } : { id: undefined, name: '', type: 'none', amountCents: 0, stock: 1, dailyLimit: 1, weight: 1, enabled: true, points: 0 })
  editing.value = true
}

async function save() {
  try {
    const endpoint = form.id ? `/api/admin/prizes/${form.id}` : '/api/admin/prizes'
    await api(endpoint, { method: 'POST', body: JSON.stringify(form) })
    editing.value = false
    message.value = '奖品已保存'
    await load()
  } catch (reason) {
    message.value = reason instanceof Error ? reason.message : '保存失败'
  }
}

async function toggle(prize: Prize) {
  try {
    await api(`/api/admin/prizes/${prize.id}`, { method: 'POST', body: JSON.stringify({ ...prize, enabled: !prize.enabled }) })
    await load()
  } catch (reason) {
    message.value = reason instanceof Error ? reason.message : '操作失败'
  }
}

async function remove(prize: Prize) {
  if (!window.confirm(`确定删除奖品“${prize.name}”吗？已产生发放记录的奖品不能删除。`)) return
  try {
    await api(`/api/admin/prizes/${prize.id}`, { method: 'DELETE' })
    message.value = '奖品已删除'
    await load()
  } catch (reason) {
    message.value = reason instanceof Error ? reason.message : '删除失败'
  }
}

const typeName = (type: string) => ({ cash: '现金红包', points: '积分', physical: '实物', souvenir: '纪念品', phone: '话费', none: '未中奖' }[type] || type)
const amount = (prize: Prize) => (prize.type === 'cash' ? `¥ ${(prize.amountCents / 100).toFixed(2)}` : prize.type === 'points' ? `${prize.points} 分` : '—')
</script>

<template>
  <AdminShell active="prizes" title="奖品管理" subtitle="现金、积分、实物和未中奖权重统一配置。">
    <p v-if="message" class="notice-bar">{{ message }}</p>
    <section class="card">
      <div class="toolbar"><span class="help">共 {{ prizes.length }} 个奖品</span><span class="spacer" /><button class="btn small" type="button" @click="edit()">新增奖品</button></div>
      <div v-if="loading" class="loading">加载奖品…</div>
      <div v-else class="table-scroll">
        <table class="admin-table">
          <thead><tr><th>奖品</th><th>类型</th><th>面额/积分</th><th>库存</th><th>日限</th><th>权重</th><th>状态</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="prize in pagedPrizes" :key="prize.id">
              <td>{{ prize.name }}</td><td>{{ typeName(prize.type) }}</td><td>{{ amount(prize) }}</td>
              <td>{{ prize.issued || 0 }} / {{ prize.stock }}</td><td>{{ prize.dailyLimit }}</td><td>{{ prize.weight }}</td>
              <td>{{ prize.enabled ? '启用' : '停用' }}</td>
              <td class="row-actions"><button type="button" @click="edit(prize)">编辑</button><button type="button" @click="toggle(prize)">{{ prize.enabled ? '停用' : '启用' }}</button><button type="button" class="danger-link" @click="remove(prize)">删除</button></td>
            </tr>
          </tbody>
        </table>
      </div>
      <Pagination :page="page" :pages="totalPages" :total="prizes.length" :page-size="pageSize" @update:page="page = $event" @update:page-size="pageSize = $event; page = 1" />
    </section>
    <div v-if="editing" class="modal-mask" @click.self="editing = false">
    <form class="card modal-panel admin-form" @submit.prevent="save">
      <div class="modal-head"><h2>{{ form.id ? '编辑奖品' : '新增奖品' }}</h2><button type="button" class="modal-close" @click="editing = false">×</button></div>
      <div class="form-grid">
        <label>名称<input v-model="form.name" required /></label>
        <label>类型<select v-model="form.type"><option value="none">未中奖</option><option value="points">积分</option><option value="cash">现金红包</option></select></label>
        <label>金额（分）<input v-model.number="form.amountCents" type="number" min="0" /></label>
        <label>积分值<input v-model.number="form.points" type="number" min="0" /></label>
        <label>总库存<input v-model.number="form.stock" type="number" min="0" /></label>
        <label>每日投放<input v-model.number="form.dailyLimit" type="number" min="0" /></label>
        <label>权重<input v-model.number="form.weight" type="number" min="0" /></label>
        <label class="check-row"><input v-model="form.enabled" type="checkbox" />启用</label>
      </div>
      <div class="form-actions"><button class="btn secondary" type="button" @click="editing = false">取消</button><button class="btn" type="submit">保存奖品</button></div>
    </form>
    </div>
  </AdminShell>
</template>