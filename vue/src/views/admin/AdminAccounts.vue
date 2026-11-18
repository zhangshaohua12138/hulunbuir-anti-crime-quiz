<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import AdminShell from '../../components/AdminShell.vue'
import { api } from '../../api'

interface Account { id: string; username: string; role: string; enabled: number; createdAt?: string }
const accounts = ref<Account[]>([])
const loading = ref(true)
const message = ref('')
const form = reactive({ username: '', password: '', role: 'operator' })

onMounted(load)

async function load() {
  loading.value = true
  try {
    const data = await api<{ accounts: Account[] }>('/api/admin/accounts')
    accounts.value = data.accounts
  } catch (reason) {
    message.value = reason instanceof Error ? reason.message : '读取账号失败'
  } finally {
    loading.value = false
  }
}

async function create() {
  message.value = ''
  try {
    await api('/api/admin/accounts', { method: 'POST', body: JSON.stringify(form) })
    form.username = ''
    form.password = ''
    form.role = 'operator'
    message.value = '账号已创建'
    await load()
  } catch (reason) {
    message.value = reason instanceof Error ? reason.message : '创建失败'
  }
}

async function toggle(account: Account) {
  try {
    await api(`/api/admin/accounts/${account.id}`, { method: 'PUT', body: JSON.stringify({ enabled: !account.enabled }) })
    await load()
  } catch (reason) {
    message.value = reason instanceof Error ? reason.message : '操作失败'
  }
}
</script>

<template>
  <AdminShell active="accounts" title="账号管理" subtitle="超级管理员创建运营账号；运营账号只做活动运营。">
    <p v-if="message" class="notice-bar">{{ message }}</p>
    <div class="admin-split">
      <section class="card">
        <h2>后台账号</h2>
        <div v-if="loading" class="loading">加载账号…</div>
        <div v-else class="table-scroll">
          <table class="admin-table">
            <thead><tr><th>用户名</th><th>角色</th><th>状态</th><th>操作</th></tr></thead>
            <tbody>
              <tr v-for="account in accounts" :key="account.id">
                <td>{{ account.username }}</td><td>{{ account.role === 'super' ? '超级管理员' : '运营账号' }}</td><td>{{ account.enabled ? '启用' : '停用' }}</td>
                <td class="row-actions"><button type="button" @click="toggle(account)">{{ account.enabled ? '停用' : '启用' }}</button></td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
      <section class="card">
        <h2>新增账号</h2>
        <form class="admin-form" @submit.prevent="create">
          <label>用户名<input v-model="form.username" required minlength="3" maxlength="40" /></label>
          <label>初始密码<input v-model="form.password" type="password" required minlength="12" /></label>
          <label>角色<select v-model="form.role"><option value="operator">运营账号</option><option value="super">超级管理员</option></select></label>
          <button class="btn full" type="submit">创建账号</button>
        </form>
      </section>
    </div>
  </AdminShell>
</template>