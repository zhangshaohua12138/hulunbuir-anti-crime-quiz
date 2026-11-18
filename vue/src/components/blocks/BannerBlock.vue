<script setup lang="ts">
import { computed } from 'vue'
import type { LayoutBlock } from '../types'

const props = defineProps<{ block: LayoutBlock }>()
const p = computed(() => props.block.props as Record<string, unknown>)

const bannerStyle = computed(() => ({
  backgroundImage: `linear-gradient(rgba(0,0,0,${Number(p.value.overlay ?? 0.45)}), rgba(0,0,0,${Number(p.value.overlay ?? 0.45)})), url(${p.value.image || ''})`,
  height: `${Number(p.value.height || 260)}px`,
  borderRadius: `${Number(p.value.radius || 12)}px`,
}))

const textStyle = computed(() => ({
  left: `${Number(p.value.textX ?? 8)}%`,
  top: `${Number(p.value.textY ?? 28)}%`,
  width: `${Number(p.value.textWidth || 70)}%`,
  textAlign: String(p.value.align || 'left') as 'left' | 'center' | 'right',
  background: String(p.value.textBackground || ''),
  padding: `${Number(p.value.textPadding || 0)}px`,
  borderRadius: `${Number(p.value.textRadius || 0)}px`,
}))

const titleStyle = computed(() => ({
  fontSize: `${Number(p.value.titleSize || 26)}px`,
  color: String(p.value.titleColor || p.value.color || '#ffffff'),
}))

const subtitleStyle = computed(() => ({
  fontSize: `${Number(p.value.subtitleSize || 14)}px`,
  color: String(p.value.subtitleColor || p.value.color || '#ffffff'),
}))

const buttonStyle = computed(() => ({
  background: String(p.value.buttonBackground || '#ffffff17'),
  color: String(p.value.buttonColor || p.value.color || '#ffffff'),
  borderRadius: `${Number(p.value.buttonRadius || 8)}px`,
}))
</script>

<template>
  <section class="banner" :style="bannerStyle">
    <div class="banner-copy" :style="textStyle">
      <h2 v-if="p.title" :style="titleStyle">{{ p.title }}</h2>
      <p v-if="p.subtitle" :style="subtitleStyle">{{ p.subtitle }}</p>
      <a v-if="p.buttonText && p.link" class="banner-button" :style="buttonStyle" :href="String(p.link)">{{ p.buttonText }}</a>
    </div>
  </section>
</template>