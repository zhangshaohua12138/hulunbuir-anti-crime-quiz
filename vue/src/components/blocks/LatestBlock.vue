<script setup lang="ts">
defineProps<{ visible: boolean }>()
</script>

<template>
  <section v-if="visible" class="card latest-card">
    <div class="section-title">最近成绩</div>
    <p class="help">查看上一次答题结果，继续积累平安知识。</p>
    <a class="text-link" href="#result">查看最近一次成绩 →</a>
  </section>
</template>