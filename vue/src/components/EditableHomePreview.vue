<script setup lang="ts">
import { ref } from 'vue'
import BlockRenderer from './BlockRenderer.vue'
import type { Bootstrap, PageLayout } from '../types'

const props = defineProps<{
  boot: Bootstrap
  layout: PageLayout
  selectedIndex: number | null
}>()

const emit = defineEmits<{
  (event: 'select', index: number): void
  (event: 'move', from: number, to: number): void
}>()

const dragIndex = ref<number | null>(null)

function start(index: number, event: DragEvent) {
  dragIndex.value = index
  event.dataTransfer?.setData('text/plain', String(index))
  if (event.dataTransfer) event.dataTransfer.effectAllowed = 'move'
}

function drop(index: number) {
  if (dragIndex.value === null || dragIndex.value === index) return
  emit('move', dragIndex.value, index)
  dragIndex.value = null
}
</script>

<template>
  <div class="editable-preview">
    <div
      v-for="(block, index) in layout.blocks"
      v-show="block.visible"
      :key="block.id"
      class="editor-block"
      :class="{ selected: selectedIndex === index }"
      draggable="true"
      @click="emit('select', index)"
      @dragstart="start(index, $event)"
      @dragover.prevent
      @drop="drop(index)"
    >
      <span class="editor-block-label">{{ block.type.startsWith('custom-') ? '自定义组件' : block.type }}</span>
      <div class="editor-block-content">
        <BlockRenderer
          :block="block"
          :config="boot.config"
          :account="boot.account"
          :user="boot.user"
          :state="boot.state"
        />
      </div>
    </div>
    <p v-if="!layout.blocks.some((item) => item.visible)" class="empty-canvas">从左侧添加组件</p>
  </div>
</template>