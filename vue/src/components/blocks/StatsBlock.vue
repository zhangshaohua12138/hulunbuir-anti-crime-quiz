<script setup lang="ts">
import type { BootAccount, BootConfig, Bootstrap } from '../../types'

defineProps<{
  account: BootAccount | null
  config: BootConfig
  user: Bootstrap['user']
}>()

const emit = defineEmits<{ (event: 'start'): void }>()
</script>

<template>
  <section class="card action-card">
    <div class="section-title">{{ config.homeCardTitle || '今天，也为平安加一分' }}</div>
    <div class="stats">
      <div class="stat">
        <strong>{{ user ? (user.is_test ? '不限' : Number(account?.freeRemaining || 0) + Number(account?.reviveRemaining || 0)) : '—' }}</strong>
        <span>{{ user?.is_test ? '测试答题' : '今日剩余机会' }}</span>
      </div>
      <div class="stat">
        <strong>{{ account?.points ?? 0 }}</strong>
        <span>我的累计积分</span>
      </div>
      <div class="stat">
        <strong>{{ config.passScore ?? 80 }}</strong>
        <span>抽奖达标分数</span>
      </div>
    </div>
    <button class="btn full" type="button" @click="emit('start')">
      {{ config.homeCta || '开始答题，赢取好礼' }} <span>→</span>
    </button>
    <p class="help center">每套 10 题 · 单选 5 题 + 多选 5 题 · 满分 100 分</p>
  </section>
</template>