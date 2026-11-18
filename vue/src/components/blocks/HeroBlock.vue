<script setup lang="ts">
import type { BootConfig } from '../../types'

defineProps<{
  config: BootConfig
  state: string
}>()

const stateName = (value: string) =>
  ({ pending: '即将开始', active: '进行中', paused: '暂停', ended: '已结束' }[value] || value || '进行中')

const shortDate = (value: string) => {
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? '' : `${date.getMonth() + 1}/${date.getDate()}`
}
</script>

<template>
  <section class="hero">
    <div class="eyebrow">{{ config.homeEyebrow || '深化扫黑除恶 · 共建平安家园' }}</div>
    <h1>
      {{ (config.title || '深化扫黑除恶专项斗争有奖答题活动').replace('有奖答题', '') }}
      <span>有奖答题</span>
    </h1>
    <p>{{ config.homeIntro || '让法治精神深入人心，让平安建设与你同行。' }}</p>
    <div class="hero-meta">
      <span>● {{ stateName(state) }}</span>
      <span>{{ shortDate(config.startAt) }} — {{ shortDate(config.endAt) }}</span>
      <span>{{ config.homeMeta || '全民参与 · 共护平安' }}</span>
    </div>
  </section>
</template>