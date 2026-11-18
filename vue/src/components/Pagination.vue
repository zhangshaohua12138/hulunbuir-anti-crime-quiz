<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  page: number
  pages: number
  total?: number
  pageSize?: number
}>()
const emit = defineEmits<{ (event: 'update:page', page: number): void }>()
const safePages = computed(() => Math.max(1, props.pages || 1))

function go(page: number) {
  const next = Math.min(safePages.value, Math.max(1, page))
  if (next !== props.page) emit('update:page', next)
}
</script>

<template>
  <div v-if="safePages > 1 || total" class="pagination">
    <button type="button" :disabled="page <= 1" @click="go(page - 1)">上一页</button>
    <span class="pagination-info">第 {{ page }} / {{ safePages }} 页<span v-if="total"> · 共 {{ total }} 条</span></span>
    <button type="button" :disabled="page >= safePages" @click="go(page + 1)">下一页</button>
  </div>
</template>