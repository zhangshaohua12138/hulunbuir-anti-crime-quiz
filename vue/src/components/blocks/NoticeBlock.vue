<script setup lang="ts">
import type { BootConfig } from '../../types'

defineProps<{ config: BootConfig }>()
</script>

<template>
  <section class="card notice-card">
    <div class="notice-line">每一份学习，都是对平安的守护。</div>
    <a class="text-link" href="#rules">了解活动规则 →</a>
    <p class="help">{{ config.footerText || '学法知法 · 守护平安 · 共建美好家园' }}</p>
  </section>
</template>