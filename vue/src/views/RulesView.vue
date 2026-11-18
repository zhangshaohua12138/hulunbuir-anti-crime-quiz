<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { useSession } from '../store'
import MobileNav from '../components/MobileNav.vue'

const session = useSession()
const router = useRouter()
const accepted = ref(false)
const busy = ref(false)
const error = ref('')

const config = computed(() => session.boot?.config)
const rulesText = computed(() => config.value?.rulesText || '')

onMounted(async () => {
  await session.loadBoot()
  if (session.boot?.user?.rules) accepted.value = true
})

async function agree() {
  if (busy.value) return
  busy.value = true
  error.value = ''
  try {
    await api('/api/rules/accept', { method: 'POST', body: '{}' })
    await session.loadBoot(true)
    await router.replace('/')
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '操作失败'
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="rules-page">
    <header class="quiz-header">
      <a href="#/" class="quiz-back">← 返回首页</a>
      <span class="quiz-progress">活动规则</span>
      <span />
    </header>
    <main class="rules-card card">
      <div class="eyebrow">参与前请阅读</div>
      <h1>活动规则</h1>
      <p v-if="rulesText" class="rules-copy">{{ rulesText }}</p>
      <template v-else>
        <p>每人每天有 {{ config?.dailyFree ?? 1 }} 次免费答题机会，每套 10 题，单选 5 题、多选 5 题，满分 100 分。</p>
        <p>达到 {{ config?.passScore ?? 80 }} 分可参与抽奖。答题结束后按最高成绩加抽奖积分参与排名，多套不累计。</p>
        <p>现金红包由活动主办方通过微信发放；实物奖品需登记收货信息。活动结束后，排名前 {{ config?.winnerCount ?? 50 }} 名按公示规则发放话费奖励。</p>
        <p>请勿使用外挂、脚本或冒用他人身份参与，违规行为将被取消资格。</p>
        <MobileNav active="rules" />
</template>
      <label class="rules-check">
        <input v-model="accepted" type="checkbox" />
        我已阅读并同意活动规则
      </label>
      <p v-if="error" class="form-error">{{ error }}</p>
      <button class="btn full" type="button" :disabled="!accepted || busy" @click="agree">
        {{ busy ? '提交中…' : '同意规则，返回首页' }}
      </button>
    </main>
  </div>
  <MobileNav active="rules" />
</template>
