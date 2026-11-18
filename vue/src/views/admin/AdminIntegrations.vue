<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
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
  wechatActName: string
  wechatTransferSceneId: string
}

const form = reactive<Record<string, string>>({})
const meta = ref<Integrations | null>(null)
const loading = ref(true)
const saving = ref(false)
const message = ref('')

onMounted(async () => {
  try {
    const data = await api<Integrations>('/api/admin/integrations')
    meta.value = data
    for (const key of ['wechatAppId', 'wechatMchId', 'wechatCertPath', 'wechatKeyPath', 'wechatClientIp', 'wechatSendName', 'wechatActName', 'wechatTransferSceneId']) form[key] = String((data as any)[key] || '')
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
  <AdminShell active="integrations" title="微信配置" subtitle="公众号、商户号和红包发放方式；密钥留空表示保持原值。">
    <p v-if="message" class="notice-bar">{{ message }}</p>
    <div v-if="loading" class="loading">读取配置…</div>
    <form v-else class="card admin-form" @submit.prevent="save">
      <div class="notice-box">当前密钥状态：AppSecret {{ meta?.hasWechatAppSecret ? '已配置' : '未配置' }} · 支付密钥 {{ meta?.hasWechatPayKey ? '已配置' : '未配置' }} · APIv3 {{ meta?.hasWechatApiV3Key ? '已配置' : '未配置' }}</div>
      <div class="form-grid">
        <label>公众号 AppID<input v-model="form.wechatAppId" /></label>
        <label>公众号 AppSecret<input v-model="form.wechatAppSecret" type="password" placeholder="留空不修改" /></label>
        <label>商户号<input v-model="form.wechatMchId" /></label>
        <label>支付 API 密钥<input v-model="form.wechatPayKey" type="password" placeholder="留空不修改" /></label>
        <label>APIv3 密钥<input v-model="form.wechatApiV3Key" type="password" placeholder="留空不修改" /></label>
        <label>发红包方式<select v-model="form.paymentProvider"><option value="demo">演示</option><option value="wechat_transfer">商家转账</option><option value="wechat_redpack">现金红包</option><option value="gateway">支付网关</option></select></label>
        <label>证书路径<input v-model="form.wechatCertPath" placeholder="/etc/..." /></label>
        <label>私钥路径<input v-model="form.wechatKeyPath" placeholder="/etc/..." /></label>
        <label>商户调用 IP<input v-model="form.wechatClientIp" /></label>
        <label>转账场景 ID<input v-model="form.wechatTransferSceneId" /></label>
        <label>红包发送名称<input v-model="form.wechatSendName" /></label>
        <label>活动名称<input v-model="form.wechatActName" /></label>
      </div>
      <div class="form-actions"><button class="btn" type="submit" :disabled="saving">{{ saving ? '保存中…' : '保存微信配置' }}</button></div>
    </form>
  </AdminShell>
</template>