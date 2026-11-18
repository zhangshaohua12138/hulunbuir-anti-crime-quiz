<script setup lang="ts">
import type { BootConfig, Bootstrap } from '../../types'

defineProps<{
  config: BootConfig
  user: Bootstrap['user']
  state: string
}>()

const emit = defineEmits<{ (event: 'start'): void }>()
</script>

<template>
  <section class="card cta-card">
    <button class="btn full" type="button" :disabled="!user || ['pending', 'paused', 'ended'].includes(state)" @click="emit('start')">
      {{ user ? (config.homeCta || '开始答题，赢取好礼') : '登录参与' }} <span>→</span>
    </button>
    <p class="help center">登录后即可参与 · 每人每天都有答题机会</p>
  </section>
</template>