<script setup lang="ts">
interface Column { key: string; label: string }

withDefaults(defineProps<{
  columns: Column[]
  rows: Array<Record<string, unknown>>
  format?: (key: string, value: unknown) => string
  tableClass?: string
  emptyText?: string
}>(), { tableClass: '', emptyText: '暂无数据' })
</script>

<template>
  <div class="table-scroll">
    <table class="admin-table" :class="tableClass">
      <thead>
        <tr>
          <th v-for="column in columns" :key="column.key">{{ column.label }}</th>
          <th v-if="$slots.actions">操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(row, index) in rows" :key="index">
          <td v-for="column in columns" :key="column.key">
            <slot name="cell" :row="row" :column="column" :value="row[column.key]">
              {{ format ? format(column.key, row[column.key]) : (row[column.key] ?? '—') }}
            </slot>
          </td>
          <td v-if="$slots.actions" class="row-actions">
            <slot name="actions" :row="row" />
          </td>
        </tr>
      </tbody>
    </table>
    <p v-if="!rows.length" class="empty-canvas">{{ emptyText }}</p>
  </div>
</template>