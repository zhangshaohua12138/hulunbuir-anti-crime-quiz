<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useSession } from '../store'

defineProps<{ active: string; title: string; subtitle?: string }>()
const session = useSession()
const router = useRouter()
const isSuper = computed(() => session.admin?.role === 'super')
const nav = computed(() =>
  [
    { key: 'dashboard', to: '/admin', label: '运营概览', icon: '览' },
    { key: 'config', to: '/admin/config', label: '活动配置', icon: '配' },
    { key: 'questions', to: '/admin/questions', label: '题库管理', icon: '题' },
    { key: 'prizes', to: '/admin/prizes', label: '奖品管理', icon: '奖' },
    { key: 'users', to: '/admin/users', label: '用户管理', icon: '用' },
    { key: 'records', to: '/admin/records', label: '记录与发奖', icon: '录' },
    ...(isSuper.value
      ? [
          { key: 'accounts', to: '/admin/accounts', label: '账号管理', icon: '账' },
          { key: 'integrations', to: '/admin/integrations', label: '微信配置', icon: '微' },
          { key: 'designer', to: '/designer', label: '布局设计', icon: '布' },
        ]
      : []),
  ],
)

async function logout() {
  await session.logout()
  await router.replace('/login')
}
</script>

<template>
  <div class="admin-shell">
    <aside class="admin-nav">
      <a class="admin-brand" href="#/">
        <span>法</span>
        <strong>活动管理后台</strong>
      </a>
      <nav>
        <RouterLink v-for="item in nav" :key="item.key" :to="item.to" :class="{ active: active === item.key }">
          <b>{{ item.icon }}</b>{{ item.label }}
        </RouterLink>
      </nav>
      <div class="admin-nav-foot">
        <span>{{ session.admin?.username }} · {{ session.admin?.role === 'super' ? '超级管理员' : '运营账号' }}</span>
        <button type="button" @click="logout">退出</button>
      </div>
    </aside>
    <main class="admin-main">
      <header class="admin-head">
        <div>
          <div class="eyebrow">活动运营工作台</div>
          <h1>{{ title }}</h1>
          <p v-if="subtitle" class="help">{{ subtitle }}</p>
        </div>
        <a class="btn secondary" href="/">返回活动首页</a>
      </header>
      <slot />
    </main>
  </div>
</template>