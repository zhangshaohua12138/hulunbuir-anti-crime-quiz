<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import AdminShell from '../../components/AdminShell.vue'
import { api } from '../../api'

interface Integrations {
  wechatAppId: string
  hasWechatAppSecret: boolean
  wechatMchId: string
  hasWechatPayKey: boolean
  hasWechatApiV3Key: boolean
  wechatCertPath: string
  wechatKeyPath: string
  wechatClientIp: string
  paymentProvider: string
  wechatSendName: string
  wechatWishing: string
  wechatActName: string
  wechatTransferSceneId: string
  wechatTransferSceneInfoType: string
  wechatTransferSceneInfoContent: string
  wechatTransferSceneReward: string
  wechatTransferRemark: string
  wechatUserRecvPerception: string
  wechatUserRecvStyle: string
  callbackUrl?: string
}

const form = reactive<Record<string, string>>({})
const meta = ref<Integrations | null>(null)
const loading = ref(true)
const saving = ref(false)
const message = ref('')

const providerLabel = computed(() => ({ demo: '演示模式', wechat_transfer: '商家转账', wechat_redpack: '现金红包', gateway: '支付网关' }[form.paymentProvider] || form.paymentProvider))

onMounted(async () => {
  try {
    const data = await api<Integrations>('/api/admin/integrations')
    meta.value = data
    const editable = [
      'wechatAppId', 'wechatMchId', 'wechatCertPath', 'wechatKeyPath', 'wechatClientIp',
      'wechatSendName', 'wechatWishing', 'wechatActName', 'wechatTransferSceneId',
      'wechatTransferSceneInfoType', 'wechatTransferSceneInfoContent', 'wechatTransferSceneReward',
      'wechatTransferRemark', 'wechatUserRecvPerception', 'wechatUserRecvStyle',
    ]
    for (const key of editable) form[key] = String((data as any)[key] || '')
    form.paymentProvider = data.paymentProvider
    form.wechatAppSecret = ''
    form.wechatPayKey = ''
    form.wechatApiV3Key = ''
  } catch (reason) {
    message.value = reason instanceof Error ? reason.message : '读取微信配置失败'
  } finally {
    loading.value = false
  }
})

async function save() {
  saving.value = true
  message.value = ''
  try {
    meta.value = await api<Integrations>('/api/admin/integrations', { method: 'PUT', body: JSON.stringify(form) })
    form.wechatAppSecret = ''
    form.wechatPayKey = ''
    form.wechatApiV3Key = ''
    message.value = '微信配置已保存'
  } catch (reason) {
    message.value = reason instanceof Error ? reason.message : '保存失败'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <AdminShell active="integrations" title="微信配置" subtitle="按公众号、支付、商家转账、红包文案和证书分类维护。">
    <p v-if="message" class="notice-bar">{{ message }}</p>
    <div v-if="loading" class="loading">读取配置…</div>
    <form v-else class="integration-form" @submit.prevent="save">
      <section class="card integration-section">
        <div class="integration-head">
          <div><h2>公众号</h2><p class="help">网页授权、关注校验和 JS-SDK 分享。</p></div>
          <span class="integration-badge">{{ meta?.hasWechatAppSecret ? 'AppSecret 已配置' : 'AppSecret 未配置' }}</span>
        </div>
        <div class="form-grid">
          <label>公众号 AppID<input v-model="form.wechatAppId" placeholder="wx..." /></label>
          <label>公众号 AppSecret<input v-model="form.wechatAppSecret" type="password" placeholder="留空不修改" /></label>
          <label class="span-2">OAuth 回调地址<input :value="meta?.callbackUrl" readonly /></label>
        </div>
      </section>

      <section class="card integration-section">
        <div class="integration-head">
          <div><h2>商户与支付</h2><p class="help">商户号、支付模式和接口密钥。</p></div>
          <span class="integration-badge">{{ providerLabel }}</span>
        </div>
        <div class="form-grid">
          <label>商户号<input v-model="form.wechatMchId" placeholder="商户号" /></label>
          <label>发红包方式<select v-model="form.paymentProvider"><option value="demo">演示</option><option value="wechat_transfer">商家转账</option><option value="wechat_redpack">现金红包</option><option value="gateway">支付网关</option></select></label>
          <label>支付 API 密钥<input v-model="form.wechatPayKey" type="password" placeholder="留空不修改" /></label>
          <label>APIv3 密钥<input v-model="form.wechatApiV3Key" type="password" placeholder="留空不修改" /></label>
          <label>商户调用 IP<input v-model="form.wechatClientIp" placeholder="服务器公网 IP" /></label>
        </div>
        <div class="integration-status">
          <span>支付密钥 {{ meta?.hasWechatPayKey ? '已配置' : '未配置' }}</span>
          <span>APIv3 {{ meta?.hasWechatApiV3Key ? '已配置' : '未配置' }}</span>
        </div>
      </section>

      <section class="card integration-section">
        <div class="integration-head">
          <div><h2>商家转账</h2><p class="help">商家转账场景、收款样式和用户提示。</p></div>
          <span class="integration-badge">场景 {{ form.wechatTransferSceneId || '—' }}</span>
        </div>
        <div class="form-grid">
          <label>转账场景 ID<input v-model="form.wechatTransferSceneId" placeholder="1000" /></label>
          <label>场景信息类型<input v-model="form.wechatTransferSceneInfoType" maxlength="32" /></label>
          <label class="span-2">场景信息内容<input v-model="form.wechatTransferSceneInfoContent" maxlength="32" /></label>
          <label>奖励说明<input v-model="form.wechatTransferSceneReward" maxlength="32" /></label>
          <label>转账备注<input v-model="form.wechatTransferRemark" maxlength="32" /></label>
          <label>用户收款感知<input v-model="form.wechatUserRecvPerception" maxlength="32" /></label>
          <label>收款样式<select v-model="form.wechatUserRecvStyle"><option value="RED_PACKET">红包</option><option value="CONFIRM_PAGE">确认页</option></select></label>
        </div>
      </section>

      <section class="card integration-section">
        <div class="integration-head">
          <div><h2>红包文案</h2><p class="help">现金红包和活动展示文案。</p></div>
          <span class="integration-badge">发送名称 / 活动名称</span>
        </div>
        <div class="form-grid">
          <label>红包发送名称<input v-model="form.wechatSendName" maxlength="32" /></label>
          <label>活动名称<input v-model="form.wechatActName" maxlength="32" /></label>
          <label class="span-2">红包祝福语<input v-model="form.wechatWishing" maxlength="100" /></label>
        </div>
      </section>

      <section class="card integration-section">
        <div class="integration-head">
          <div><h2>证书与网络</h2><p class="help">双向证书路径，仅超级管理员可修改。</p></div>
          <span class="integration-badge">服务器路径</span>
        </div>
        <div class="form-grid">
          <label>证书路径<input v-model="form.wechatCertPath" placeholder="/etc/hulunbuir-quiz/wechat/apiclient_cert.pem" /></label>
          <label>私钥路径<input v-model="form.wechatKeyPath" placeholder="/etc/hulunbuir-quiz/wechat/apiclient_key.pem" /></label>
        </div>
      </section>

      <div class="integration-actions">
        <button class="btn" type="submit" :disabled="saving">{{ saving ? '保存中…' : '保存微信配置' }}</button>
      </div>
    </form>
  </AdminShell>
</template>