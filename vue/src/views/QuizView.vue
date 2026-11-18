<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api'
import { useSession } from '../store'
import type { Attempt, QuizQuestion } from '../types'
import MobileNav from '../components/MobileNav.vue'

const route = useRoute()
const router = useRouter()
const session = useSession()
const attempt = ref<Attempt | null>(null)
const current = ref(0)
const answers = reactive<Record<string, string[]>>({})
const remaining = ref(0)
const loading = ref(true)
const submitting = ref(false)
const error = ref('')
let timer: number | undefined
let submitted = false

const question = computed<QuizQuestion | null>(() => attempt.value?.questions[current.value] || null)
const progress = computed(() => (attempt.value ? `${current.value + 1} / ${attempt.value.questions.length}` : ''))
const selected = computed(() => (question.value ? answers[question.value.id] || [] : []))

onMounted(async () => {
  await session.loadBoot()
  if (!session.boot?.user) {
    await router.replace('/')
    return
  }
  await load()
})

onBeforeUnmount(() => window.clearInterval(timer))

async function load() {
  try {
    attempt.value = await api<Attempt>(`/api/attempts/${route.params.id}`)
    Object.assign(answers, attempt.value.answers || {})
    if (attempt.value.status !== 'active') {
      await router.replace(`/result/${attempt.value.id}`)
      return
    }
    tick()
    timer = window.setInterval(tick, 1000)
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '读取题目失败'
  } finally {
    loading.value = false
  }
}

function tick() {
  if (!attempt.value) return
  const deadline = new Date(attempt.value.deadlineAt).getTime()
  remaining.value = Math.max(0, Math.ceil((deadline - Date.now()) / 1000))
  if (remaining.value === 0 && !submitted) void submit(true)
}

function choose(optionId: string) {
  if (!question.value || submitting.value) return
  const q = question.value
  if (q.type === 'single') answers[q.id] = [optionId]
  else {
    const list = new Set(answers[q.id] || [])
    if (list.has(optionId)) list.delete(optionId)
    else list.add(optionId)
    answers[q.id] = [...list]
  }
  void saveAnswers()
}

async function saveAnswers() {
  if (!attempt.value) return
  try {
    await api(`/api/attempts/${attempt.value.id}/answers`, {
      method: 'PUT',
      body: JSON.stringify({ answers }),
    })
  } catch {
    // 自动保存失败不打断答题，交卷时仍以当前答案提交。
  }
}

async function next() {
  if (!attempt.value || submitting.value) return
  if (current.value < attempt.value.questions.length - 1) {
    current.value += 1
    return
  }
  await submit(false)
}

async function submit(auto = false) {
  if (!attempt.value || submitting.value || submitted) return
  submitting.value = true
  submitted = true
  try {
    const result = await api<Attempt>(`/api/attempts/${attempt.value.id}/submit`, {
      method: 'POST',
      body: JSON.stringify({ answers }),
    })
    await router.replace(`/result/${result.id}`)
  } catch (reason) {
    submitted = false
    error.value = reason instanceof Error ? reason.message : '交卷失败'
    if (auto) submitted = false
  } finally {
    submitting.value = false
  }
}

function format(seconds: number) {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}
</script>

<template>
  <div class="quiz-page">
    <header class="quiz-header">
      <a href="#/" class="quiz-back">← 退出</a>
      <span class="quiz-progress">{{ progress }}</span>
      <span class="quiz-timer" :class="{ urgent: remaining <= 60 }">{{ format(remaining) }}</span>
    </header>

    <main v-if="question" class="quiz-main">
      <div class="quiz-type">{{ question.type === 'single' ? '单选题 · 8 分' : '多选题 · 12 分' }}</div>
      <h1>{{ question.stem }}</h1>
      <p class="help">{{ question.type === 'single' ? '只能选 1 项' : '至少选 2 项，全部选对才得分' }}</p>

      <div class="option-list">
        <button
          v-for="option in question.options"
          :key="option.id"
          type="button"
          class="option"
          :class="{ selected: selected.includes(option.id), multiple: question.type === 'multiple' }"
          @click="choose(option.id)"
        >
          <span class="option-mark">{{ option.id }}</span>
          <span>{{ option.text }}</span>
        </button>
      </div>

      <p v-if="error" class="form-error">{{ error }}</p>

      <div class="quiz-actions">
        <button class="btn full" type="button" :disabled="submitting" @click="next">
          {{ current === (attempt?.questions.length || 1) - 1 ? '完成答题，交卷' : '下一题 →' }}
        </button>
      </div>
    </main>

    <div v-else class="loading">{{ loading ? '正在加载题目…' : (error || '题目不存在') }}</div>
  </div>
  <MobileNav active="home" />
</template>
