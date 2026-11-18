<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  page: number
  pages: number
  total?: number
  pageSize?: number
}>()
const emit = defineEmits<{ (event: 'update:page', page: number): void; (event: 'update:pageSize', size: number): void }>()
const safePages = computed(() => Math.max(1, props.pages || 1))

function changeSize(event: Event) {
  const size = Number((event.target as HTMLSelectElement).value)
  emit('update:pageSize', size)
}

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
    <label class="page-size">每页<select :value="pageSize || 10" @change="changeSize"><option :value="10">10 条</option><option :value="20">20 条</option><option :value="50">50 条</option></select></label>
  </div>
</template>