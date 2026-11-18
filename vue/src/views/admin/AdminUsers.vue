<script setup lang="ts">
import { onMounted, ref } from 'vue'
import AdminShell from '../../components/AdminShell.vue'
import Pagination from '../../components/Pagination.vue'
import { api } from '../../api'

interface UserRow {
  id: string
  nickname: string
  followed: number
  is_test: number
  blocked: number
  attempts: number
  best: number
  orders: number
  createdAt?: string
}

const users = ref<UserRow[]>([])
const page = ref(1)
const pages = ref(1)
const total = ref(0)
const search = ref('')
const loading = ref(true)
const message = ref('')

onMounted(load)

async function load() {
  loading.value = true
  try {
    const data = await api<{ rows: UserRow[]; page: number; pages: number; total: number }>(`/api/admin/users?page=${page.value}&q=${encodeURIComponent(search.value)}`)
    users.value = data.rows
    page.value = data.page
    pages.value = data.pages
    total.value = data.total
  } catch (reason) {
    message.value = reason instanceof Error ? reason.message : '读取用户失败'
  } finally {
    loading.value = false
  }
}

async function toggleTest(user: UserRow) {
  const password = window.prompt('请输入测试账号标记密码')
  if (!password) return
  try {
    await api(`/api/admin/users/${user.id}/test`, {
      method: 'POST',
      body: JSON.stringify({ enabled: !user.is_test, password }),
    })
    message.value = user.is_test ? '已取消测试账号' : '已标记为测试账号'
    await load()
  } catch (reason) {
    message.value = reason instanceof Error ? reason.message : '操作失败'
  }
}
</script>

<template>
  <AdminShell active="users" title="用户管理" subtitle="查看参与用户、关注状态和答题情况。">
    <p v-if="message" class="notice-bar">{{ message }}</p>
    <section class="card">
      <div class="toolbar">
        <input v-model="search" placeholder="搜索昵称" @keyup.enter="page = 1; load()" />
        <button class="btn small secondary" type="button" @click="page = 1; load()">搜索</button>
        <span class="spacer" /><span class="help">共 {{ total }} 人</span>
      </div>
      <div v-if="loading" class="loading">加载用户…</div>
      <div v-else class="table-scroll">
        <table class="admin-table">
          <thead><tr><th>用户</th><th>关注</th><th>答题</th><th>最高分</th><th>订单</th><th>状态</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="user in users" :key="user.id">
              <td>{{ user.nickname }}<small class="help">{{ user.id.slice(0, 8) }}</small></td>
              <td>{{ user.followed ? '已关注' : '未关注' }}</td>
              <td>{{ user.attempts }}</td>
              <td>{{ user.best }}</td>
              <td>{{ user.orders }}</td>
              <td>{{ user.is_test ? '测试账号' : user.blocked ? '已停用' : '普通用户' }}</td>
              <td class="row-actions"><button type="button" @click="toggleTest(user)">{{ user.is_test ? '取消测试' : '标记测试' }}</button></td>
            </tr>
          </tbody>
        </table>
        <p v-if="!users.length" class="empty-canvas">暂无用户</p>
      </div>
      <Pagination :page="page" :pages="pages" :total="total" @update:page="page = $event; load()" />
    </section>
  </AdminShell>
</template>