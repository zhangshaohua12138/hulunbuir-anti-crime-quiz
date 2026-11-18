<script setup lang="ts">
import { computed, ref } from 'vue'
import type { LayoutBlock } from '../types'

const props = defineProps<{ block: LayoutBlock }>()
const p = computed(() => props.block.props as Record<string, unknown>)
const query = ref('')

const textStyle = computed(() => ({
  textAlign: String(p.value.align || 'left') as 'left' | 'center' | 'right',
  color: String(p.value.color || ''),
  background: String(p.value.background || ''),
  padding: `${Number(p.value.padding || 20)}px`,
  borderRadius: `${Number(p.value.radius || 12)}px`,
}))
const imageStyle = computed(() => ({
  textAlign: String(p.value.align || 'center') as 'left' | 'center' | 'right',
}))
const imgStyle = computed(() => ({
  width: String(p.value.width || '100%'),
  borderRadius: `${Number(p.value.radius || 12)}px`,
}))
const buttonStyle = computed(() => ({
  background: String(p.value.background || ''),
  color: String(p.value.color || ''),
  borderRadius: `${Number(p.value.radius || 10)}px`,
  width: p.value.full ? '100%' : 'auto',
}))
const buttonWrap = computed(() => ({ textAlign: String(p.value.align || 'center') as 'left' | 'center' | 'right' }))

function search() {
  const action = String(p.value.action || '')
  if (!action) return
  const value = query.value.trim()
  const url = action + (action.includes('?') ? '&' : '?') + 'q=' + encodeURIComponent(value)
  if (action.startsWith('#')) window.location.hash = url.slice(1)
  else window.location.href = url
}
</script>

<template>
  <section v-if="block.type === 'custom-text'" class="custom-text" :style="textStyle">
    <h2 v-if="p.title">{{ p.title }}</h2>
    <p v-if="p.body">{{ p.body }}</p>
  </section>

  <section v-else-if="block.type === 'custom-image'" class="custom-image-card" :style="imageStyle">
    <a v-if="p.link" :href="String(p.link)">
      <img :src="String(p.src || '')" :alt="String(p.alt || '')" :style="imgStyle" />
    </a>
    <img v-else :src="String(p.src || '')" :alt="String(p.alt || '')" :style="imgStyle" />
    <p v-if="p.caption" class="help">{{ p.caption }}</p>
  </section>

  <form v-else-if="block.type === 'custom-search'" class="custom-search" :style="{ background: String(p.background || ''), borderRadius: `${Number(p.radius || 10)}px` }" @submit.prevent="search">
    <input v-model="query" :placeholder="String(p.placeholder || '搜索…')" :style="{ color: String(p.color || '') }" />
    <button type="submit">{{ p.buttonText || '搜索' }}</button>
  </form>

  <section v-else-if="block.type === 'custom-button'" class="custom-button-wrap" :style="buttonWrap">
    <a v-if="p.link" class="custom-button" :href="String(p.link)" :style="buttonStyle">{{ p.label || '了解更多' }}</a>
    <button v-else class="custom-button" type="button" :style="buttonStyle">{{ p.label || '了解更多' }}</button>
  </section>

  <hr v-else-if="block.type === 'custom-divider'" class="custom-divider" :style="{ borderColor: String(p.color || ''), margin: `${Number(p.margin || 18)}px 0` }" />
</template>