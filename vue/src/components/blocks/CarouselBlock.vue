<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import type { LayoutBlock } from '../types'

const props = defineProps<{ block: LayoutBlock }>()
const p = computed(() => props.block.props as Record<string, unknown>)
const slides = computed(() => {
  const value = p.value.slides
  return Array.isArray(value) ? value as Array<{ src: string; link?: string; title?: string }> : []
})
const index = ref(0)
let timer: number | undefined

const style = computed(() => ({
  height: `${Number(p.value.height || 240)}px`,
  borderRadius: `${Number(p.value.radius || 12)}px`,
}))

onMounted(() => {
  if (p.value.autoplay !== false && slides.value.length > 1) {
    timer = window.setInterval(() => { index.value = (index.value + 1) % slides.value.length }, 3800)
  }
})
onBeforeUnmount(() => window.clearInterval(timer))
</script>

<template>
  <section class="carousel" :style="style">
    <a v-for="(slide, i) in slides" :key="slide.src + i" v-show="i === index" :href="slide.link || undefined" class="carousel-slide" :style="{ backgroundImage: `url(${slide.src})` }">
      <span v-if="slide.title">{{ slide.title }}</span>
    </a>
    <div v-if="slides.length > 1" class="carousel-dots">
      <button v-for="(_, i) in slides" :key="i" type="button" :class="{ active: i === index }" @click="index = i" />
    </div>
  </section>
</template>