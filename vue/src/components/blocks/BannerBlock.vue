<script setup lang="ts">
import { computed } from 'vue'
import type { LayoutBlock } from '../types'

const props = defineProps<{ block: LayoutBlock }>()
const p = computed(() => props.block.props as Record<string, unknown>)
const style = computed(() => ({
  backgroundImage: `linear-gradient(rgba(0,0,0,${Number(p.value.overlay ?? 0.45)}), rgba(0,0,0,${Number(p.value.overlay ?? 0.45)})), url(${p.value.image || ''})`,
  height: `${Number(p.value.height || 260)}px`,
  borderRadius: `${Number(p.value.radius || 12)}px`,
  textAlign: String(p.value.align || 'left') as 'left' | 'center' | 'right',
  color: String(p.value.color || '#fff'),
}))
</script>

<template>
  <section class="banner" :style="style">
    <div class="banner-copy">
      <h2 v-if="p.title">{{ p.title }}</h2>
      <p v-if="p.subtitle">{{ p.subtitle }}</p>
      <a v-if="p.buttonText && p.link" class="banner-button" :href="String(p.link)">{{ p.buttonText }}</a>
    </div>
  </section>
</template>