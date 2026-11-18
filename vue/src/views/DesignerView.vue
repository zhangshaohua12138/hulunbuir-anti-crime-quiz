<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import EditableHomePreview from '../components/EditableHomePreview.vue'
import { api } from '../api'
import { allBlockDefinitions, blockDefinitions, customBlockDefinitions, customDefaults, normalizeLayout, presets } from '../layout'
import { useSession } from '../store'
import { applyTheme } from '../theme'
import type { BlockType, LayoutBlock, LayoutTemplate, PageLayout } from '../types'

const router = useRouter()
const session = useSession()
const layout = ref<PageLayout>({ version: 1, blocks: [] })
const templates = ref<LayoutTemplate[]>([])
const templateName = ref('')
const selectedIndex = ref<number | null>(null)
const loading = ref(true)
const saving = ref(false)
const saved = ref('')
const themeFields = [
  { key: 'themeColor', label: '主色' }, { key: 'pageBackground', label: '页面背景' },
  { key: 'cardBackground', label: '卡片背景' }, { key: 'headerBackground', label: '顶部栏' },
  { key: 'textColor', label: '正文' }, { key: 'mutedColor', label: '次要文字' },
  { key: 'borderColor', label: '边框' }, { key: 'iconColor', label: '图标' },
  { key: 'buttonTextColor', label: '按钮文字' },
] as const
const theme = reactive<Record<string, string | boolean>>({ buttonTextAuto: true })

const boot = computed(() => session.boot)
const selectedBlock = computed(() => (selectedIndex.value === null ? null : layout.value.blocks[selectedIndex.value] || null))
const hiddenBlocks = computed(() => layout.value.blocks.map((block, index) => ({ block, index })).filter((item) => !item.block.visible))
const availableBlocks = computed(() => blockDefinitions.filter((definition) => !layout.value.blocks.some((block) => block.type === definition.type)))
const blockLabel = (type: BlockType) => allBlockDefinitions.find((item) => item.type === type)?.label || type
const blockHint = (type: BlockType) => allBlockDefinitions.find((item) => item.type === type)?.hint || ''

const customFields = computed(() => {
  const type = selectedBlock.value?.type
  if (!type || !type.startsWith('custom-')) return []
  const fields: Record<string, Array<{ key: string; label: string; kind?: string; options?: string[] }>> = {
    'custom-text': [{ key: 'title', label: '标题' }, { key: 'body', label: '正文', kind: 'textarea' }, { key: 'align', label: '对齐', kind: 'select', options: ['left', 'center', 'right'] }, { key: 'color', label: '文字颜色（#RRGGBB）' }, { key: 'background', label: '背景颜色（#RRGGBB）' }, { key: 'padding', label: '内边距 px' }, { key: 'radius', label: '圆角 px' }],
    'custom-image': [{ key: 'src', label: '图片地址（/static/ 或 https://）' }, { key: 'alt', label: '替代文字' }, { key: 'link', label: '点击跳转（#/ 或 https://）' }, { key: 'caption', label: '图片说明' }, { key: 'align', label: '对齐', kind: 'select', options: ['left', 'center', 'right'] }, { key: 'width', label: '宽度（例如 100%）' }, { key: 'radius', label: '圆角 px' }],
    'custom-search': [{ key: 'placeholder', label: '占位文字' }, { key: 'buttonText', label: '按钮文字' }, { key: 'action', label: '跳转地址（#/ranking 或 https://）' }, { key: 'background', label: '背景颜色（#RRGGBB）' }, { key: 'color', label: '文字颜色（#RRGGBB）' }, { key: 'radius', label: '圆角 px' }],
    'custom-button': [{ key: 'label', label: '按钮文字' }, { key: 'link', label: '跳转地址（#/rules 或 https://）' }, { key: 'align', label: '对齐', kind: 'select', options: ['left', 'center', 'right'] }, { key: 'background', label: '背景颜色（#RRGGBB）' }, { key: 'color', label: '文字颜色（#RRGGBB）' }, { key: 'radius', label: '圆角 px' }, { key: 'full', label: '占满一行', kind: 'checkbox' }],
    'custom-divider': [{ key: 'color', label: '颜色（#RRGGBB）' }, { key: 'margin', label: '上下间距 px' }],
  }
  return fields[type] || []
})

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
  } catch (reason) {
    if ((reason as { status?: number }).status === 401 || (reason as { status?: number }).status === 403) {
      await router.replace('/login')
      return
    }
    saved.value = reason instanceof Error ? reason.message : '加载布局失败'
  } finally {
    loading.value = false
  }
})

function addBlock(type: BlockType, custom = false) {
  layout.value.blocks.push({ id: `${type}-${Date.now()}`, type, visible: true, props: custom ? { ...(customDefaults[type] || {}) } : {} })
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

function onMove(from: number, to: number) {
  const [block] = layout.value.blocks.splice(from, 1)
  layout.value.blocks.splice(to, 0, block)
  selectedIndex.value = to
}

function toggleSelected() {
  if (selectedIndex.value !== null) toggle(selectedIndex.value)
}

function moveSelected(direction: -1 | 1) {
  if (selectedIndex.value !== null) move(selectedIndex.value, direction)
}

function removeSelected() {
  if (selectedIndex.value !== null) removeBlock(selectedIndex.value)
}

function choose(index: number) {
  selectedIndex.value = index
}

function applyPreset(id: string) {
  const preset = presets.find((item) => item.id === id)
  if (!preset) return
  layout.value = normalizeLayout({ version: 1, blocks: preset.blocks.map((block) => ({ ...block, props: { ...block.props } })) })
  selectedIndex.value = null
  saved.value = `已应用预设：${preset.name}`
}

async function saveLayout() {
  saving.value = true
  saved.value = ''
  try {
    const result = await api<{ layout: PageLayout; templates?: LayoutTemplate[] }>('/api/admin/layout', {
      method: 'PUT',
      body: JSON.stringify({ layout: layout.value }),
    })
    layout.value = normalizeLayout(result.layout)
    templates.value = result.templates || templates.value
    saved.value = '布局已保存，前台首页立即生效'
  } catch (reason) {
    saved.value = reason instanceof Error ? reason.message : '保存失败'
  } finally {
    saving.value = false
  }
}

async function createTemplate() {
  const name = templateName.value.trim()
  if (!name) { saved.value = '请填写模板名称'; return }
  try {
    const result = await api<{ template: LayoutTemplate; templates: LayoutTemplate[] }>('/api/admin/layout/templates', {
      method: 'POST', body: JSON.stringify({ name, layout: layout.value }),
    })
    templates.value = result.templates || []
    templateName.value = ''
    saved.value = `已保存模板：${result.template.name}`
  } catch (reason) {
    saved.value = reason instanceof Error ? reason.message : '模板保存失败'
  }
}

function applyTemplate(template: LayoutTemplate) {
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
  } catch (reason) {
    saved.value = reason instanceof Error ? reason.message : '删除失败'
  }
}

async function saveTheme() {
  if (!session.boot?.config || !session.admin) return
  try {
    await api('/api/admin/config', { method: 'PUT', body: JSON.stringify({ ...session.boot.config, ...theme }) })
    await session.loadBoot(true)
    applyTheme(session.config)
    saved.value = '主题配色已保存'
  } catch (reason) {
    saved.value = reason instanceof Error ? reason.message : '配色保存失败'
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
        <button class="btn" type="button" :disabled="saving || loading" @click="saveLayout">{{ saving ? '保存中…' : '保存布局' }}</button>
      </div>
    </header>

    <div v-if="loading" class="loading">正在读取布局…</div>
    <div v-else class="designer-layout">
      <aside class="designer-side">
        <template v-if="selectedBlock">
          <button class="back-library" type="button" @click="selectedIndex = null">← 组件库</button>
          <div class="side-title">
            <h2>{{ blockLabel(selectedBlock.type) }}</h2>
            <span class="help">{{ blockHint(selectedBlock.type) }}</span>
          </div>
          <label class="check-row"><input type="checkbox" :checked="selectedBlock.visible" @change="toggleSelected" />显示此组件</label>
          <div class="side-actions">
            <button type="button" @click="moveSelected(-1)">↑ 上移</button>
            <button type="button" @click="moveSelected(1)">↓ 下移</button>
            <button type="button" @click="removeSelected">删除</button>
          </div>
          <div v-for="field in customFields" :key="field.key" class="component-field">
            <label>{{ field.label }}</label>
            <textarea v-if="field.kind === 'textarea'" v-model="selectedBlock.props[field.key]" rows="3" />
            <select v-else-if="field.kind === 'select'" v-model="selectedBlock.props[field.key]">
              <option v-for="option in field.options" :key="option" :value="option">{{ option }}</option>
            </select>
            <input v-else-if="field.kind === 'checkbox'" v-model="selectedBlock.props[field.key]" type="checkbox" />
            <input v-else v-model="selectedBlock.props[field.key]" type="text" />
          </div>
          <p v-if="!customFields.length" class="help">这个基础区块没有额外参数，可在右侧拖动调整顺序。</p>
        </template>

        <template v-else>
          <section>
            <h2>添加基础区块</h2>
            <button v-for="definition in availableBlocks" :key="definition.type" class="palette-button" type="button" @click="addBlock(definition.type)">
              <span>{{ definition.label }}</span><small>{{ definition.hint }}</small>
            </button>
            <p v-if="!availableBlocks.length" class="help">基础区块已全部添加</p>
          </section>
          <section>
            <h2>添加自定义组件</h2>
            <button v-for="definition in customBlockDefinitions" :key="definition.type" class="palette-button" type="button" @click="addBlock(definition.type, true)">
              <span>{{ definition.label }}</span><small>{{ definition.hint }}</small>
            </button>
          </section>
          <section v-if="hiddenBlocks.length">
            <h2>已隐藏组件</h2>
            <button v-for="item in hiddenBlocks" :key="item.block.id" class="hidden-row" type="button" @click="choose(item.index)">
              {{ blockLabel(item.block.type) }} <small>点击恢复属性</small>
            </button>
          </section>
          <section>
            <h2>预设布局</h2>
            <button v-for="preset in presets" :key="preset.id" class="preset-button" type="button" @click="applyPreset(preset.id)">
              <strong>{{ preset.name }}</strong><small>{{ preset.description }}</small>
            </button>
          </section>
          <section>
            <h2>我的模板</h2>
            <div class="template-save"><input v-model="templateName" maxlength="40" placeholder="模板名称" @keyup.enter="createTemplate" /><button type="button" @click="createTemplate">保存当前</button></div>
            <div v-for="template in templates" :key="template.id" class="saved-template">
              <button type="button" class="saved-template-name" @click="applyTemplate(template)">{{ template.name }}</button>
              <button type="button" class="saved-template-delete" @click="deleteTemplate(template)">删除</button>
            </div>
            <p v-if="!templates.length" class="help">把当前布局保存为命名模板，下次可直接套用。</p>
          </section>
          <section>
            <h2>主题配色</h2>
            <div v-for="field in themeFields" :key="field.key" class="theme-color-row"><span>{{ field.label }}</span><input v-model="theme[field.key]" type="color" /></div>
            <label class="check-row"><input v-model="theme.buttonTextAuto" type="checkbox" />按钮文字自动对比</label>
            <button class="btn small" type="button" @click="saveTheme">保存配色</button>
          </section>
        </template>
      </aside>

      <main class="designer-canvas">
        <div class="canvas-head">
          <div><h2>实时预览</h2><p class="help">点击区块选中并展开左侧属性；拖动区块调整位置。</p></div>
          <span v-if="saved" class="save-status">{{ saved }}</span>
        </div>
        <div class="preview-phone">
          <div v-if="boot" class="phone-scroll">
            <EditableHomePreview :boot="boot" :layout="layout" :selected-index="selectedIndex" @select="choose" @move="onMove" />
          </div>
          <div v-else class="loading">读取首页数据…</div>
        </div>
      </main>
    </div>
  </div>
</template>