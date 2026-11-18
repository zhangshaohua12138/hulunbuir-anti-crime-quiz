<script setup lang="ts">
defineProps<{ active?: string }>()
const items = [
  { key: 'home', to: '#/', label: '首页', icon: '首' },
  { key: 'rules', to: '#/rules', label: '规则', icon: '规' },
  { key: 'ranking', to: '#/ranking', label: '榜单', icon: '榜' },
  { key: 'awards', to: '#/awards', label: '奖品', icon: '礼' },
]
</script>

<template>
  <nav class="mobile-nav" aria-label="移动端导航">
    <a v-for="item in items" :key="item.key" :href="item.to" :class="{ active: active === item.key }">
      <span class="nav-symbol" aria-hidden="true">{{ item.icon }}</span>
      <span>{{ item.label }}</span>
    </a>
  </nav>
</template>