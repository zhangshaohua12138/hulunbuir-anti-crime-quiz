<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import AdminShell from '../../components/AdminShell.vue'
import { api } from '../../api'
import { useSession } from '../../store'

const session = useSession()
const isSuper = computed(() => session.admin?.role === 'super')
const config = ref<Record<string, any> | null>(null)
const loading = ref(true)
const saving = ref(false)
const message = ref('')
const startLocal = ref('')
const endLocal = ref('')

interface CopyField { key: string; label: string; placeholder?: string; top?: boolean; textarea?: boolean }
const copyDefaults: Record<string, string> = {
  loginTitle: '登录演示账号',
  resultEyebrow: '本次成绩',
  resultExpiredEyebrow: '本次答题已过期',
  resultPassTitle: '答题达标，收获满满！',
  resultFailTitle: '再接再厉，平安知识多一分',
  resultExpiredTitle: '本次答题已过期',
  resultPassTip: '达到合格分数后即可参与抽奖。',
  resultDrawnTip: '已抽奖，感谢参与。',
  resultFailTip: '学习的每一步都有意义，再来一次巩固知识吧。',
  resultExpiredTip: '本次状态及机会归还以服务器记录为准。',
  resultRankingButton: '查看积分榜',
  resultHomeButton: '返回首页',
  lotteryEyebrow: '答题有礼',
  lotteryTitle: '答题有礼，好运开启',
  rankingEyebrow: '共同进步',
  rankingTitle: '每一分努力，都值得被看见',
  rankingIntro: '榜单更新中，活动结束后冻结最终排名',
  rankingEmpty: '还没有上榜记录，快来开启你的知识之旅。',
  rankingHelp: '每日取最高分，跨天累加；同一天多套只计最高分，不重复累计；抽奖积分另行累加。',
  winnersEyebrow: '荣誉榜单',
  winnersTitle: '获奖名单公示',
  winnersIntro: '榜单已封存，排名以最终公示为准',
  awardsEyebrow: '我的奖品',
  awardsTitle: '我的奖品',
  awardsIntro: '记录每一份收获，也感谢你的每一次参与。',
  awardsEmpty: '暂无中奖记录。完成答题并达标后，可参与好礼抽取。',
  quizSingle: '单选题',
  quizMulti: '多选题',
  quizNext: '下一题 →',
  quizSubmit: '完成答题，交卷',
  quizHelpSingle: '单选题：只能选 1 项，选对得 8 分。',
  quizHelpMulti: '多选题：至少选 2 项，全部选对才得分；漏选、错选均不得分。',
}

const topDefaults: Record<string, string> = {
  title: '呼伦贝尔市深化扫黑除恶专项斗争有奖竞答活动',
  brandSubtitle: '全民参与 · 共建平安',
  shareDesc: '学到知识，守护平安家园',
  homeEyebrow: '深化扫黑除恶 · 共建平安家园',
  homeIntro: '让法治精神深入人心，让平安建设与你同行。',
  homeMeta: '全民参与 · 共护平安',
  homeCardTitle: '今天，也为平安加一分',
  homeCta: '开始答题，赢取好礼',
  homeGiftTitle: '知识有力量，参与有惊喜',
  footerText: '学法知法 · 守护平安 · 共建美好家园',
  rulesIntro: '开始前花一分钟，了解这场知识之旅。',
  loginTip: '此账号仅用于本地体验，不会连接微信或发放真实奖品。',
}

function applyTextDefaults(value: Record<string, any>) {
  if (!value.copy) value.copy = {}
  for (const group of copyGroups) {
    for (const field of group.fields) {
      if (field.top) {
        if (field.key !== 'rulesText' && !String(value[field.key] || '').trim()) value[field.key] = topDefaults[field.key] || ''
      } else if (!String(value.copy[field.key] || '').trim()) {
        value.copy[field.key] = copyDefaults[field.key] || ''
      }
    }
  }
}

const copyGroups: Array<{ title: string; fields: CopyField[] }> = [
  {
    title: '首页与通用',
    fields: [
      { key: 'title', label: '活动名称（左上角标题）', top: true },
      { key: 'brandSubtitle', label: '品牌副标题', top: true },
      { key: 'shareDesc', label: '分享描述', top: true },
      { key: 'homeEyebrow', label: '首页眉题', top: true },
      { key: 'homeIntro', label: '首页主说明', top: true },
      { key: 'homeMeta', label: '首页底部短句', top: true },
      { key: 'homeCardTitle', label: '机会卡片标题', top: true },
      { key: 'homeCta', label: '开始答题按钮文案', top: true },
      { key: 'homeGiftTitle', label: '奖品卡片标题', top: true },
      { key: 'rulesIntro', label: '规则页引导语', top: true },
      { key: 'footerText', label: '页脚标语', top: true },
      { key: 'loginTitle', label: '登录弹窗标题' },
      { key: 'loginTip', label: '登录弹窗提示', top: true },
      { key: 'resultTip', label: '结果页补充提示', top: true },
      { key: 'rulesText', label: '活动规则正文（留空使用默认规则）', top: true, textarea: true },
    ],
  },
  {
    title: '答题页',
    fields: [
      { key: 'quizSingle', label: '单选题标签' },
      { key: 'quizMulti', label: '多选题标签' },
      { key: 'quizNext', label: '下一题按钮' },
      { key: 'quizSubmit', label: '交卷按钮' },
      { key: 'quizHelpSingle', label: '单选题提示' },
      { key: 'quizHelpMulti', label: '多选题提示' },
    ],
  },
  {
    title: '结果页',
    fields: [
      { key: 'resultEyebrow', label: '结果页眉题' },
      { key: 'resultExpiredEyebrow', label: '过期结果眉题' },
      { key: 'resultPassTitle', label: '达标结果标题' },
      { key: 'resultFailTitle', label: '未达标结果标题' },
      { key: 'resultExpiredTitle', label: '过期结果标题' },
      { key: 'resultPassTip', label: '达标提示' },
      { key: 'resultDrawnTip', label: '已抽奖提示' },
      { key: 'resultFailTip', label: '未达标提示' },
      { key: 'resultExpiredTip', label: '过期提示' },
      { key: 'resultRankingButton', label: '查看排行榜按钮' },
      { key: 'resultHomeButton', label: '返回首页按钮' },
    ],
  },
  {
    title: '抽奖与榜单',
    fields: [
      { key: 'lotteryEyebrow', label: '抽奖页眉题' },
      { key: 'lotteryTitle', label: '抽奖页标题' },
      { key: 'rankingEyebrow', label: '排行榜眉题' },
      { key: 'rankingTitle', label: '排行榜标题' },
      { key: 'rankingIntro', label: '排行榜说明' },
      { key: 'rankingEmpty', label: '排行榜空状态' },
      { key: 'rankingHelp', label: '排行榜底部说明' },
      { key: 'winnersEyebrow', label: '获奖公示眉题' },
      { key: 'winnersTitle', label: '获奖公示标题' },
      { key: 'winnersIntro', label: '获奖公示说明' },
    ],
  },
  {
    title: '我的奖品',
    fields: [
      { key: 'awardsEyebrow', label: '我的奖品眉题' },
      { key: 'awardsTitle', label: '我的奖品标题' },
      { key: 'awardsIntro', label: '我的奖品说明' },
      { key: 'awardsEmpty', label: '我的奖品空状态' },
    ],
  },
]

const configured = computed(() => Boolean(config.value))
const stateLabel = computed(() => {
  if (!config.value) return '读取中'
  if (config.value.paused) return '已暂停'
  const now = Date.now()
  const start = new Date(config.value.startAt).getTime()
  const end = new Date(config.value.endAt).getTime()
  if (now < start) return '未开始'
  if (now > end) return '已结束'
  return '进行中'
})
function toLocalInput(value: string) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`
}

function fromLocalInput(value: string) {
  if (!value) return value
  return value.length === 16 ? `${value}:00+08:00` : value
}

const durationDays = computed(() => {
  if (!config.value) return 0
  const start = new Date(config.value.startAt).getTime()
  const end = new Date(config.value.endAt).getTime()
  return Number.isNaN(start) || Number.isNaN(end) ? 0 : Math.max(1, Math.ceil((end - start) / 86400000))
})

const budgetYuan = computed(() => ((Number(config.value?.budgetCents || 0)) / 100).toFixed(2))
const dailyYuan = computed(() => ((Number(config.value?.dailyBudgetCents || 0)) / 100).toFixed(2))

onMounted(async () => {
  try {
    config.value = await api<Record<string, any>>('/api/admin/config')
    applyTextDefaults(config.value)
    startLocal.value = toLocalInput(String(config.value.startAt || ''))
    endLocal.value = toLocalInput(String(config.value.endAt || ''))
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
    config.value.startAt = fromLocalInput(startLocal.value)
    config.value.endAt = fromLocalInput(endLocal.value)
    config.value = await api<Record<string, any>>('/api/admin/config', {
      method: 'PUT',
      body: JSON.stringify(config.value),
    })
    applyTextDefaults(config.value)
    startLocal.value = toLocalInput(String(config.value.startAt || ''))
    endLocal.value = toLocalInput(String(config.value.endAt || ''))
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

    <section class="settings-overview">
      <div>
        <div class="eyebrow">ACTIVITY SETTINGS</div>
        <h2>活动运行配置</h2>
        <p class="help">保存后立即生效；活动封榜后部分结算参数不可修改。</p>
      </div>
      <div class="overview-chips">
        <span class="overview-chip" :class="{ ok: stateLabel === '进行中' }">{{ stateLabel }}</span>
        <span class="overview-chip">预算 ¥{{ budgetYuan }}</span>
        <span class="overview-chip accent">每日 ¥{{ dailyYuan }}</span>
      </div>
    </section>

    <div v-if="loading" class="loading">读取配置…</div>
    <form v-else-if="config" class="settings-grid" @submit.prevent="save">
      <section class="settings-card time-card">
        <header class="card-head">
          <span class="card-icon">时</span>
          <div class="card-heading"><h2>活动时间与状态</h2><p>活动起止时间、暂停和参与窗口</p></div>
          <span class="card-state" :class="{ ok: stateLabel === '进行中' }">{{ stateLabel }}</span>
        </header>
        <div class="card-fields">
          <label>开始时间<input v-model="startLocal" type="datetime-local" /></label>
          <label>结束时间<input v-model="endLocal" type="datetime-local" /></label>
          <label class="switch-row wide"><input v-model="config.paused" type="checkbox" />暂停活动</label>
        </div>
        <div class="card-summary">
          <div><span>活动天数</span><strong>{{ durationDays }} 天</strong></div>
          <div><span>当前状态</span><strong>{{ stateLabel }}</strong></div>
          <div><span>每日机会</span><strong>{{ config.dailyFree }} 次</strong></div>
        </div>
      </section>

      <section class="settings-card settings-rules-card">
        <header class="card-head">
          <span class="card-icon">规</span>
          <div class="card-heading"><h2>答题规则</h2><p>机会、分数、时长和榜单人数</p></div>
          <span class="card-state">满分 100</span>
        </header>
        <div class="card-fields">
          <label>每日免费次数<input v-model.number="config.dailyFree" type="number" min="1" /></label>
          <label>每日复活上限<input v-model.number="config.reviveLimit" type="number" min="0" /></label>
          <label>抽奖达标分数<input v-model.number="config.passScore" type="number" min="1" max="100" /></label>
          <label>整卷限时（秒）<input v-model.number="config.timeLimitSeconds" type="number" min="60" /></label>
          <label>排行榜展示条数<input v-model.number="config.leaderboardLimit" type="number" min="1" /></label>
          <label>获奖人数<input v-model.number="config.winnerCount" type="number" min="1" /></label>
        </div>
        <div class="card-foot"><span>单选 5 题 · 多选 5 题</span><span>满分 100 分</span></div>
      </section>

      <section class="settings-card budget-card">
        <header class="card-head">
          <span class="card-icon">算</span>
          <div class="card-heading"><h2>红包预算</h2><p>总预算、每日额度和自动平均</p></div>
          <span class="card-state">当前 ¥{{ budgetYuan }}</span>
        </header>
        <div class="card-fields">
          <label>总红包预算（分）<input v-model.number="config.budgetCents" type="number" min="0" /></label>
          <label>每日红包预算（分）<input v-model.number="config.dailyBudgetCents" type="number" min="0" /></label>
          <label class="switch-row wide"><input v-model="config.budgetAutoDaily" type="checkbox" />每日预算按总预算 / 活动天数自动计算</label>
        </div>
        <div class="card-foot"><span>约 ¥{{ budgetYuan }}</span><span>每日约 ¥{{ dailyYuan }}</span></div>
      </section>

      <section class="settings-card share-card">
        <header class="card-head">
          <span class="card-icon">享</span>
          <div class="card-heading"><h2>分享复活</h2><p>未达标用户获取复活机会的方式</p></div>
          <span class="card-state accent">{{ config.shareMode === 'sdk' ? '微信分享' : config.shareMode === 'manual' ? '人工确认' : config.shareMode === 'free' ? '直接领取' : '已关闭' }}</span>
        </header>
        <div class="card-fields">
          <label class="wide">复活方式<select v-model="config.shareMode"><option value="manual">人工确认</option><option value="sdk">微信分享</option><option value="free">直接领取</option><option value="disabled">关闭</option></select></label>
        </div>
        <div class="share-note">
          <span>{{ config.shareMode === 'sdk' ? '用户分享到朋友圈后返回页面自动领取。' : config.shareMode === 'manual' ? '用户分享后由运营人工确认发放。' : config.shareMode === 'free' ? '用户无需分享，直接领取复活机会。' : '当前已关闭分享复活入口。' }}</span>
        </div>
      </section>

      <section class="settings-card award-card wide-card">
        <header class="card-head">
          <span class="card-icon">评</span>
          <div class="card-heading"><h2>评优说明</h2><p>活动结束后展示给参与者的获奖说明</p></div>
          <span class="card-state">前 {{ config.winnerCount }} 名</span>
        </header>
        <div class="card-fields">
          <label class="wide">评优与奖品说明<textarea v-model="config.awardDescription" rows="4" /></label>
        </div>
      </section>

      <section v-if="isSuper" class="settings-card copy-card wide-card">
        <header class="card-head">
          <span class="card-icon">文</span>
          <div class="card-heading"><h2>移动端页面文案</h2><p>对应原生 H5 的首页、答题、结果、抽奖、榜单和领奖页文字；留空使用默认文案。</p></div>
          <span class="card-state">超级管理员</span>
        </header>
        <div class="copy-groups">
          <div v-for="group in copyGroups" :key="group.title" class="copy-group">
            <h3>{{ group.title }}</h3>
            <div class="card-fields">
              <label v-for="field in group.fields" :key="field.key" :class="{ wide: field.textarea }">
                {{ field.label }}
                <textarea v-if="field.textarea" v-model="config[field.key]" rows="3" placeholder="留空使用默认规则" />
                <input v-else-if="field.top" v-model="config[field.key]" placeholder="留空使用默认" />
                <input v-else v-model="config.copy[field.key]" placeholder="留空使用默认" />
              </label>
            </div>
          </div>
        </div>
      </section>

      <div class="settings-save">
        <div><strong>保存后立即生效</strong><p class="help">修改活动时间或预算前，请确认当前活动状态和资金安排。</p></div>
        <button class="btn" type="submit" :disabled="saving">{{ saving ? '保存中…' : '保存活动配置' }}</button>
      </div>
    </form>
  </AdminShell>
</template>