<script setup lang="ts">
import { onMounted, ref } from 'vue'
import AdminShell from '../../components/AdminShell.vue'
import { api } from '../../api'

const config = ref<Record<string, any> | null>(null)
const loading = ref(true)
const saving = ref(false)
const message = ref('')

onMounted(async () => {
  try {
    config.value = await api<Record<string, any>>('/api/admin/config')
  } catch (reason) {
    message.value = reason instanceof Error ? reason.message : '读取配置失败'
  } finally {
    loading.value = false
  }
})

async function save() {
  if (!config.value) return
  saving.value = true
  message.value = ''
  try {
    config.value = await api<Record<string, any>>('/api/admin/config', {
      method: 'PUT',
      body: JSON.stringify(config.value),
    })
    message.value = '活动配置已保存'
  } catch (reason) {
    message.value = reason instanceof Error ? reason.message : '保存失败'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <AdminShell active="config" title="活动配置" subtitle="活动时间、答题规则、预算和分享复活方式。">
    <p v-if="message" class="notice-bar">{{ message }}</p>
    <div v-if="loading" class="loading">读取配置…</div>
    <form v-else-if="config" class="card admin-form" @submit.prevent="save">
      <div class="form-grid">
        <label>活动开始时间<input v-model="config.startAt" placeholder="2026-11-18T00:00:00+08:00" /></label>
        <label>活动结束时间<input v-model="config.endAt" placeholder="2026-11-24T23:59:59+08:00" /></label>
        <label>每日免费次数<input v-model.number="config.dailyFree" type="number" min="1" /></label>
        <label>每日复活上限<input v-model.number="config.reviveLimit" type="number" min="0" /></label>
        <label>抽奖达标分数<input v-model.number="config.passScore" type="number" min="1" max="100" /></label>
        <label>整卷限时（秒）<input v-model.number="config.timeLimitSeconds" type="number" min="60" /></label>
        <label>排行榜展示条数<input v-model.number="config.leaderboardLimit" type="number" min="1" /></label>
        <label>获奖人数<input v-model.number="config.winnerCount" type="number" min="1" /></label>
        <label>总红包预算（分）<input v-model.number="config.budgetCents" type="number" min="0" /></label>
        <label>每日红包预算（分）<input v-model.number="config.dailyBudgetCents" type="number" min="0" /></label>
        <label>分享复活方式<select v-model="config.shareMode"><option value="manual">人工确认</option><option value="sdk">微信分享</option><option value="free">直接领取</option><option value="disabled">关闭</option></select></label>
      </div>
      <label class="check-row"><input v-model="config.budgetAutoDaily" type="checkbox" />每日预算按总预算 / 活动天数自动计算</label>
      <label class="check-row"><input v-model="config.paused" type="checkbox" />暂停活动</label>
      <label>评优说明<textarea v-model="config.awardDescription" rows="4" /></label>
      <div class="form-actions">
        <button class="btn" type="submit" :disabled="saving">{{ saving ? '保存中…' : '保存活动配置' }}</button>
      </div>
    </form>
  </AdminShell>
</template>