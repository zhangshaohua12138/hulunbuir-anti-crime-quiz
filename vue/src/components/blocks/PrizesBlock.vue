<script setup lang="ts">
import type { BootConfig } from '../../types'

defineProps<{ config: BootConfig }>()
</script>

<template>
  <section class="card">
    <div class="section-title">{{ config.homeGiftTitle || '知识有力量，参与有惊喜' }}</div>
    <div class="prize-row">
      <div class="prize-icon">礼</div>
      <div>
        <strong>答题达标 · 随机好礼</strong>
        <p>现金红包 / 积分奖励</p>
      </div>
    </div>
    <div class="prize-row">
      <div class="prize-icon">榜</div>
      <div>
        <strong>前 {{ config.winnerCount || 50 }} 名 · 话费奖励</strong>
        <p>{{ config.awardDescription || '实物奖以主办方公布名单为准' }}</p>
      </div>
    </div>
  </section>
</template>