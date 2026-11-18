<script setup lang="ts">
import BlockRenderer from './BlockRenderer.vue'
import type { Bootstrap, PageLayout } from '../types'

defineProps<{
  boot: Bootstrap
  layout: PageLayout
  preview?: boolean
}>()

const emit = defineEmits<{ (event: 'start'): void }>()
</script>

<template>
  <div class="home-preview" :class="{ preview }">
    <BlockRenderer
      v-for="block in layout.blocks.filter((item) => item.visible)"
      :key="block.id"
      :block="block"
      :config="boot.config"
      :account="boot.account"
      :user="boot.user"
      :state="boot.state"
      @start="emit('start')"
    />
  </div>
</template>