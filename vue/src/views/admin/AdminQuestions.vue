<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import AdminShell from '../../components/AdminShell.vue'
import Pagination from '../../components/Pagination.vue'
import { api } from '../../api'

interface Question {
  id?: string
  type: 'single' | 'multiple'
  stem: string
  options: Array<{ id: string; text: string }>
  answers: string[]
  explanation?: string
  enabled?: boolean
}

const list = ref<Question[]>([])
const counts = ref<{ single: number; multiple: number }>({ single: 0, multiple: 0 })
const page = ref(1)
const pageSize = ref(10)
const pages = ref(1)
const total = ref(0)
const search = ref('')
const loading = ref(true)
const message = ref('')
const editing = ref(false)
const importing = ref(false)
const form = reactive<Question>({ type: 'single', stem: '', options: [], answers: [], explanation: '', enabled: true })

async function importExcel(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  importing.value = true
  message.value = ''
  try {
    const form = new FormData()
    form.append('file', file)
    const result = await api<{ imported: number }>('/api/admin/questions/import', { method: 'POST', body: form })
    message.value = `已导入 ${result.imported} 道题`
    await load()
  } catch (reason) {
    message.value = reason instanceof Error ? reason.message : '导入失败'
  } finally {
    importing.value = false
    input.value = ''
  }
}

function blank() {
  form.id = undefined
  form.type = 'single'
  form.stem = ''
  form.options = ['A', 'B', 'C', 'D'].map((id) => ({ id, text: '' }))
  form.answers = []
  form.explanation = ''
  form.enabled = true
  editing.value = true
}

async function load() {
  loading.value = true
  try {
    const data = await api<{ questions: Question[]; counts: { single: number; multiple: number }; total: number; page: number; pages: number }>(
      `/api/admin/questions?page=${page.value}&pageSize=${pageSize.value}&q=${encodeURIComponent(search.value)}`,
    )
    list.value = data.questions
    counts.value = data.counts
    total.value = data.total
    pages.value = data.pages
  } catch (reason) {
    message.value = reason instanceof Error ? reason.message : '读取题库失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)

function edit(question: Question) {
  form.id = question.id
  form.type = question.type
  form.stem = question.stem
  form.options = question.options.map((option) => ({ ...option }))
  form.answers = [...(question.answers || [])]
  form.explanation = question.explanation || ''
  form.enabled = question.enabled !== false
  editing.value = true
}

async function save() {
  try {
    await api('/api/admin/questions', {
      method: 'POST',
      body: JSON.stringify({
        ...form,
        options: form.options.filter((option) => option.text.trim()),
        answers: form.answers.filter(Boolean),
      }),
    })
    editing.value = false
    message.value = '题目已保存'
    await load()
  } catch (reason) {
    message.value = reason instanceof Error ? reason.message : '保存失败'
  }
}

async function toggle(question: Question) {
  try {
    await api('/api/admin/questions', {
      method: 'POST',
      body: JSON.stringify({ ...question, enabled: !question.enabled }),
    })
    await load()
  } catch (reason) {
    message.value = reason instanceof Error ? reason.message : '操作失败'
  }
}

function answerToggle(id: string) {
  const index = form.answers.indexOf(id)
  if (form.type === 'single') form.answers = [id]
  else if (index >= 0) form.answers.splice(index, 1)
  else form.answers.push(id)
}
</script>

<template>
  <AdminShell active="questions" title="题库管理" subtitle="维护单选与多选题；题目保存后立即进入组卷池。">
    <p v-if="message" class="notice-bar">{{ message }}</p>
    <section class="card">
      <div class="toolbar">
        <input v-model="search" placeholder="搜索题干" @keyup.enter="page = 1; load()" />
        <button class="btn small secondary" type="button" @click="page = 1; load()">搜索</button>
        <span class="spacer" />
        <span class="help">单选 {{ counts.single }} · 多选 {{ counts.multiple }} · 共 {{ total }} 题</span>
        <a class="btn small secondary" href="/api/admin/questions/template">下载导入模板</a>
        <label class="btn small secondary file-button">{{ importing ? '导入中…' : '导入 Excel' }}<input type="file" accept=".xlsx" :disabled="importing" @change="importExcel" /></label>
        <button class="btn small" type="button" @click="blank">新增题目</button>
      </div>
      <div v-if="loading" class="loading">加载题库…</div>
      <div v-else class="question-list">
        <article v-for="question in list" :key="question.id" class="question-row">
          <span class="q-type">{{ question.type === 'single' ? '单选' : '多选' }}</span>
          <div>
            <strong>{{ question.stem }}</strong>
            <small>{{ question.options.map((option) => option.id + '. ' + option.text).join('　') }}</small>
          </div>
          <span class="q-status">{{ question.enabled ? '启用' : '停用' }}</span>
          <div class="row-actions">
            <button type="button" @click="edit(question)">编辑</button>
            <button type="button" @click="toggle(question)">{{ question.enabled ? '停用' : '启用' }}</button>
          </div>
        </article>
        <p v-if="!list.length" class="empty-canvas">暂无题目</p>
      </div>
      <Pagination :page="page" :pages="pages" :total="total" :page-size="pageSize" @update:page="page = $event; load()" @update:page-size="pageSize = $event; page = 1; load()" />
    </section>

    <div v-if="editing" class="modal-mask" @click.self="editing = false">
    <form class="card modal-panel admin-form question-form" @submit.prevent="save">
      <div class="modal-head"><h2>{{ form.id ? '编辑题目' : '新增题目' }}</h2><button type="button" class="modal-close" @click="editing = false">×</button></div>
      <div class="form-grid">
        <label>题型<select v-model="form.type"><option value="single">单选</option><option value="multiple">多选</option></select></label>
        <label class="check-row"><input v-model="form.enabled" type="checkbox" />启用</label>
      </div>
      <label>题干<textarea v-model="form.stem" rows="3" required /></label>
      <div class="option-edit" v-for="option in form.options" :key="option.id">
        <button type="button" class="option-letter" :class="{ active: form.answers.includes(option.id) }" @click="answerToggle(option.id)">{{ option.id }}</button>
        <input v-model="option.text" :placeholder="`选项 ${option.id}`" />
      </div>
      <p class="help">点击选项字母标记正确答案；多选题可标记多个。</p>
      <label>解析（可选）<textarea v-model="form.explanation" rows="2" /></label>
      <div class="form-actions">
        <button class="btn secondary" type="button" @click="editing = false">取消</button>
        <button class="btn" type="submit">保存题目</button>
      </div>
    </form>
    </div>
  </AdminShell>
</template>