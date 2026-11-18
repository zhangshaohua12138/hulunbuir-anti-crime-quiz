import type { LayoutBlock, PageLayout } from '../types'

export const blockDefinitions = [
  { type: 'hero', label: '主视觉', hint: '标题、口号、活动状态' },
  { type: 'stats', label: '数据卡', hint: '剩余机会、积分、达标分数' },
  { type: 'cta', label: '答题按钮', hint: '开始/继续答题' },
  { type: 'latest', label: '最近成绩', hint: '最近一次成绩入口' },
  { type: 'steps', label: '活动步骤', hint: '学习、答题、抽奖、评优' },
  { type: 'prizes', label: '奖品说明', hint: '红包、积分、评优' },
  { type: 'notice', label: '提示说明', hint: '活动提示和规则入口' },
  { type: 'features', label: '功能入口', hint: '规则、榜单、奖品' },
  { type: 'ranking', label: '榜单预览', hint: '排行榜入口' },
] as const

export const customBlockDefinitions = [
  { type: 'custom-text', label: '自定义文本', hint: '标题、正文、对齐和背景' },
  { type: 'custom-image', label: '自定义图片', hint: '图片地址、链接、圆角和说明' },
  { type: 'custom-search', label: '搜索框', hint: '占位文字、按钮和跳转地址' },
  { type: 'custom-button', label: '自定义按钮', hint: '文案、链接、颜色和宽度' },
  { type: 'custom-divider', label: '分割线', hint: '颜色和上下间距' },
] as const

export const customDefaults: Record<string, Record<string, unknown>> = {
  'custom-text': { title: '自定义标题', body: '这是一段可以自由编辑的正文。', align: 'left', color: '', background: '', padding: '20', radius: '12' },
  'custom-image': { src: '/static/theme-previews/template-1.png', alt: '活动图片', link: '', align: 'center', width: '100%', radius: '12', caption: '' },
  'custom-search': { placeholder: '搜索活动内容…', buttonText: '搜索', action: '#/ranking', background: '', color: '', radius: '10' },
  'custom-button': { label: '了解更多', link: '#/rules', align: 'center', background: '', color: '', radius: '10', full: false },
  'custom-divider': { color: '', margin: '18' },
}

export const allBlockDefinitions = [...blockDefinitions, ...customBlockDefinitions] as const

export type BlockDefinition = (typeof blockDefinitions)[number]

export const defaultLayout: PageLayout = {
  version: 1,
  blocks: [
    { id: 'hero', type: 'hero', visible: true, props: {} },
    { id: 'stats', type: 'stats', visible: true, props: {} },
    { id: 'cta', type: 'cta', visible: true, props: {} },
    { id: 'latest', type: 'latest', visible: true, props: {} },
    { id: 'steps', type: 'steps', visible: true, props: {} },
    { id: 'prizes', type: 'prizes', visible: true, props: {} },
    { id: 'notice', type: 'notice', visible: true, props: {} },
    { id: 'features', type: 'features', visible: true, props: {} },
    { id: 'ranking', type: 'ranking', visible: false, props: {} },
  ],
}

export const presets: Array<{ id: string; name: string; description: string; blocks: LayoutBlock[] }> = [
  {
    id: 'government',
    name: '政府风 · 完整',
    description: '双列信息完整，适合正式活动',
    blocks: defaultLayout.blocks.map((block) => ({ ...block })),
  },
  {
    id: 'autumn',
    name: '金秋风 · 单列',
    description: '单列聚焦，突出奖品和行动按钮',
    blocks: [
      { id: 'hero', type: 'hero', visible: true, props: {} },
      { id: 'stats', type: 'stats', visible: true, props: {} },
      { id: 'cta', type: 'cta', visible: true, props: {} },
      { id: 'prizes', type: 'prizes', visible: true, props: {} },
      { id: 'notice', type: 'notice', visible: false, props: {} },
      { id: 'features', type: 'features', visible: false, props: {} },
    ],
  },
  {
    id: 'festival',
    name: '节日风 · 精简',
    description: '主视觉和行动优先，适合朋友圈传播',
    blocks: [
      { id: 'hero', type: 'hero', visible: true, props: {} },
      { id: 'cta', type: 'cta', visible: true, props: {} },
      { id: 'prizes', type: 'prizes', visible: true, props: {} },
      { id: 'features', type: 'features', visible: true, props: {} },
    ],
  },
]

export function normalizeLayout(input?: PageLayout | null): PageLayout {
  const blocks = input?.blocks
  if (!Array.isArray(blocks) || blocks.length === 0) return { ...defaultLayout, blocks: defaultLayout.blocks.map((block) => ({ ...block })) }
  return {
    version: 1,
    blocks: blocks
      .filter((block) => allBlockDefinitions.some((definition) => definition.type === block.type))
      .map((block) => ({
        id: block.id || block.type,
        type: block.type,
        visible: block.visible !== false,
        props: block.props && typeof block.props === 'object' ? block.props : {},
      })),
  }
}