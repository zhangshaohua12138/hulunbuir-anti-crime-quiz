<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import HomePreview from '../components/HomePreview.vue'
import { api } from '../api'
import { blockDefinitions, normalizeLayout, presets, type PageLayout } from '../layout'
import { useSession } from '../store'
import { applyTheme } from '../theme'
import type { BlockType, LayoutBlock, LayoutTemplate } from '../types'

const router = useRouter()
const session = useSession()
const layout = ref<PageLayout>({ version: 1, blocks: [] })
const loading = ref(true)
const saving = ref(false)
const saved = ref('')
const dragIndex = ref<number | null>(null)
const selectedIndex = ref<number | null>(null)
const templates = ref<LayoutTemplate[]>([])
const templateName = ref('')
const themeFields = [
  { key: 'themeColor', label: '主色' },
  { key: 'pageBackground', label: '页面背景' },
  { key: 'cardBackground', label: '卡片背景' },
  { key: 'headerBackground', label: '顶部栏' },
  { key: 'textColor', label: '正文' },
  { key: 'mutedColor', label: '次要文字' },
  { key: 'borderColor', label: '边框' },
  { key: 'iconColor', label: '图标' },
  { key: 'buttonTextColor', label: '按钮文字' },
]
const theme = reactive<Record<string, string | boolean>>({ buttonTextAuto: true })

const boot = computed(() => session.boot)
const blockLabel = (type: BlockType) => blockDefinitions.find((item) => item.type === type)?.label || type
const blockHint = (type: BlockType) => blockDefinitions.find((item) => item.type === type)?.hint || ''
const availableBlocks = computed(() => blockDefinitions.filter((definition) => !layout.value.blocks.some((block) => block.type === definition.type)))
const selectedBlock = computed(() => (selectedIndex.value === null ? null : layout.value.blocks[selectedIndex.value] || null))

onMounted(async () => {
  try {
    await session.loadAdmin()
    await session.loadBoot()
    applyTheme(session.config)
    themeFields.forEach((field) => { if (session.config?.[field.key]) theme[field.key] = String(session.config[field.key]) })
    theme.buttonTextAuto = session.config?.buttonTextAuto !== false
    const result = await api<{ layout: PageLayout; templates?: LayoutTemplate[] }>('/api/admin/layout')
    layout.value = normalizeLayout(result.layout)
    templates.value = result.templates || []
  } catch (error) {
    if ((error as { status?: number }).status === 401 || (error as { status?: number }).status === 403) {
      await router.replace('/login')
      return
    }
    saved.value = error instanceof Error ? error.message : '加载失败'
  } finally {
    loading.value = false
  }
})

function addBlock(type: BlockType) {
  const block: LayoutBlock = { id: `${type}-${Date.now()}`, type, visible: true, props: {} }
  layout.value.blocks.push(block)
  selectedIndex.value = layout.value.blocks.length - 1
}

function removeBlock(index: number) {
  layout.value.blocks.splice(index, 1)
  selectedIndex.value = null
}

function move(index: number, direction: -1 | 1) {
  const target = index + direction
  if (target < 0 || target >= layout.value.blocks.length) return
  const [block] = layout.value.blocks.splice(index, 1)
  layout.value.blocks.splice(target, 0, block)
  selectedIndex.value = target
}

function toggle(index: number) {
  layout.value.blocks[index].visible = !layout.value.blocks[index].visible
}

function onDragStart(index: number, event: DragEvent) {
  dragIndex.value = index
  event.dataTransfer?.setData('text/plain', String(index))
  if (event.dataTransfer) event.dataTransfer.effectAllowed = 'move'
}

function onDrop(index: number) {
  if (dragIndex.value === null || dragIndex.value === index) return
  const [block] = layout.value.blocks.splice(dragIndex.value, 1)
  layout.value.blocks.splice(index, 0, block)
  dragIndex.value = null
  selectedIndex.value = index
}

function applyPreset(id: string) {
  const preset = presets.find((item) => item.id === id)
  if (!preset) return
  layout.value = normalizeLayout({ version: 1, blocks: preset.blocks.map((block) => ({ ...block, props: { ...block.props } })) })
  selectedIndex.value = null
  saved.value = `已应用预设：${preset.name}`
}

async function createTemplate() {
  const name = templateName.value.trim()
  if (!name) {
    saved.value = '请先填写模板名称'
    return
  }
  try {
    const result = await api<{ template: LayoutTemplate; templates: LayoutTemplate[] }>('/api/admin/layout/templates', {
      method: 'POST',
      body: JSON.stringify({ name, layout: layout.value }),
    })
    templates.value = result.templates || []
    templateName.value = ''
    saved.value = `已保存模板：${result.template.name}`
  } catch (error) {
    saved.value = error instanceof Error ? error.message : '模板保存失败'
  }
}

function applySavedTemplate(template: LayoutTemplate) {
  layout.value = normalizeLayout(template.layout)
  selectedIndex.value = null
  saved.value = `已应用模板：${template.name}`
}

async function deleteTemplate(template: LayoutTemplate) {
  if (!window.confirm(`删除模板“${template.name}”？`)) return
  try {
    const result = await api<{ templates: LayoutTemplate[] }>(`/api/admin/layout/templates/${template.id}`, { method: 'DELETE' })
    templates.value = result.templates || []
    saved.value = '模板已删除'
  } catch (error) {
    saved.value = error instanceof Error ? error.message : '删除失败'
  }
}

async function saveTheme() {
  if (!session.boot?.config || !session.admin) return
  try {
    const next = { ...session.boot.config, ...theme }
    await api('/api/admin/config', { method: 'PUT', body: JSON.stringify(next) })
    await session.loadBoot(true)
    applyTheme(session.config)
    saved.value = '主题配色已保存'
  } catch (error) {
    saved.value = error instanceof Error ? error.message : '配色保存失败'
  }
}

async function save() {
  saving.value = true
  saved.value = ''
  try {
    const result = await api<{ layout: PageLayout; templates?: LayoutTemplate[] }>('/api/admin/layout', {
      method: 'PUT',
      body: JSON.stringify({ layout: layout.value }),
    })
    layout.value = normalizeLayout(result.layout)
    templates.value = result.templates || templates.value
    saved.value = '布局已保存，前台首页会立即使用'
  } catch (error) {
    saved.value = error instanceof Error ? error.message : '保存失败'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="designer-shell">
    <header class="designer-header">
      <div>
        <div class="eyebrow">Vue Layout Studio</div>
        <h1>首页布局设计器</h1>
      </div>
      <div class="designer-actions">
        <span v-if="session.admin" class="role-chip">{{ session.admin.role === 'super' ? '超级管理员' : '运营账号' }}</span>
        <a class="text-link" href="#/">查看首页</a>
        <button class="btn" type="button" :disabled="saving || loading" @click="save">{{ saving ? '保存中…' : '保存布局' }}</button>
      </div>
    </header>

    <div v-if="loading" class="loading">正在读取布局…</div>
    <div v-else class="designer-grid">
      <aside class="designer-panel">
        <section>
          <h2>主题配色</h2>
          <div v-for="field in themeFields" :key="field.key" class="theme-color-row">
            <span>{{ field.label }}</span>
            <input v-model="theme[field.key]" type="color" :aria-label="field.label" />
          </div>
          <label class="check-row">
            <input v-model="theme.buttonTextAuto" type="checkbox" />
            按钮文字自动对比
          </label>
          <button class="btn small" type="button" @click="saveTheme">保存配色</button>
        </section>
        <section>
          <h2>预设模板</h2>
          <button v-for="preset in presets" :key="preset.id" class="preset-button" type="button" @click="applyPreset(preset.id)">
            <strong>{{ preset.name }}</strong>
            <small>{{ preset.description }}</small>
          </button>
        </section>
        <section>
          <h2>我的模板</h2>
          <div class="template-save">
            <input v-model="templateName" maxlength="40" placeholder="模板名称" @keyup.enter="createTemplate" />
            <button type="button" @click="createTemplate">保存当前</button>
          </div>
          <div v-for="template in templates" :key="template.id" class="saved-template">
            <button type="button" class="saved-template-name" @click="applySavedTemplate(template)">{{ template.name }}</button>
            <button type="button" class="saved-template-delete" @click="deleteTemplate(template)">删除</button>
          </div>
          <p v-if="!templates.length" class="help">把当前布局保存为命名模板，下次可直接套用。</p>
        </section>
        <section>
          <h2>添加区块</h2>
          <button v-for="definition in availableBlocks" :key="definition.type" class="palette-button" type="button" @click="addBlock(definition.type)">
            <span>{{ definition.label }}</span>
            <small>{{ definition.hint }}</small>
          </button>
          <p v-if="!availableBlocks.length" class="help">所有区块都已添加</p>
        </section>
        <section v-if="selectedBlock">
          <h2>区块设置</h2>
          <p class="selected-name">{{ blockLabel(selectedBlock.type) }}</p>
          <label class="check-row">
            <input type="checkbox" :checked="selectedBlock.visible" @change="selectedBlock.visible = !selectedBlock.visible" />
            显示此区块
          </label>
          <p class="help">{{ blockHint(selectedBlock.type) }}</p>
        </section>
      </aside>

      <main class="canvas-column">
        <div class="canvas-head">
          <div>
            <h2>页面结构</h2>
            <p class="help">拖动区块排序，或使用箭头微调。隐藏区块仍会保留配置。</p>
          </div>
          <span v-if="saved" class="save-status">{{ saved }}</span>
        </div>
        <div class="block-list">
          <article
            v-for="(block, index) in layout.blocks"
            :key="block.id"
            class="block-row"
            :class="{ selected: selectedIndex === index, hidden: !block.visible }"
            draggable="true"
            @dragstart="onDragStart(index, $event)"
            @dragover.prevent
            @drop="onDrop(index)"
            @click="selectedIndex = index"
          >
            <span class="drag-handle">⋮⋮</span>
            <span class="block-index">{{ index + 1 }}</span>
            <span class="block-copy">
              <strong>{{ blockLabel(block.type) }}</strong>
              <small>{{ blockHint(block.type) }}</small>
            </span>
            <span class="block-actions">
              <button type="button" :title="block.visible ? '隐藏' : '显示'" @click.stop="toggle(index)">{{ block.visible ? '隐藏' : '显示' }}</button>
              <button type="button" title="上移" @click.stop="move(index, -1)">↑</button>
              <button type="button" title="下移" @click.stop="move(index, 1)">↓</button>
              <button type="button" title="删除" @click.stop="removeBlock(index)">删除</button>
            </span>
          </article>
          <p v-if="!layout.blocks.length" class="empty-canvas">从左侧添加区块</p>
        </div>
      </main>

      <aside class="preview-column">
        <div class="preview-head">
          <h2>手机预览</h2>
          <span class="help">实时</span>
        </div>
        <div class="phone-frame">
          <div v-if="boot" class="phone-scroll">
            <HomePreview :boot="boot" :layout="layout" preview />
          </div>
          <div v-else class="loading">读取首页数据…</div>
        </div>
      </aside>
    </div>
  </div>
</template>