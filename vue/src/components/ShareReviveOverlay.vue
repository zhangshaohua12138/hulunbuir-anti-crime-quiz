<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { api } from '../api'
import { useSession } from '../store'
import { configureWechatShare } from '../wechat'

const props = defineProps<{ attemptId: string }>()
const session = useSession()
const emit = defineEmits<{ (event: 'close'): void; (event: 'granted'): void }>()
const status = ref('等待分享后返回…')
const busy = ref(false)
const leftForShare = ref(false)
const leftAt = ref(0)
let guardPushed = false
let interval: number | undefined

onMounted(() => {
  void configureWechatShare(session.config)
  try {
    history.pushState({ shareRevive: true }, '', location.href)
    guardPushed = true
  } catch {}
  document.addEventListener('visibilitychange', visibility)
  window.addEventListener('focus', onReturn)
  window.addEventListener('pageshow', onReturn)
  window.addEventListener('popstate', blockBack)
  interval = window.setInterval(check, 500)
})

onBeforeUnmount(() => {
  document.removeEventListener('visibilitychange', visibility)
  window.removeEventListener('focus', onReturn)
  window.removeEventListener('pageshow', onReturn)
  window.removeEventListener('popstate', blockBack)
  window.clearInterval(interval)
  if (guardPushed) {
    try {
      history.replaceState({}, '', location.href)
    } catch {}
  }
})

function visibility() {
  if (document.visibilityState === 'hidden') {
    leftForShare.value = true
    leftAt.value = Date.now()
  } else if (leftForShare.value) {
    window.setTimeout(claim, 600)
  }
}

function onReturn() {
  if (leftForShare.value) check()
}

function blockBack() {
  try {
    history.pushState({ shareRevive: true }, '', location.href)
    guardPushed = true
  } catch {}
}

function check() {
  if (!leftForShare.value || busy.value) return
  if (Date.now() - leftAt.value < 900) return
  claim()
}

async function claim() {
  if (busy.value || !leftForShare.value) return
  busy.value = true
  status.value = '正在领取复活机会…'
  try {
    await api('/api/revive', {
      method: 'POST',
      body: JSON.stringify({ attemptId: props.attemptId, channel: 'share' }),
    })
    emit('granted')
  } catch (reason) {
    busy.value = false
    status.value = reason instanceof Error ? reason.message : '领取失败'
  }
}

function close() {
  emit('close')
}
</script>

<template>
  <div class="share-mask" role="dialog" aria-modal="true" aria-label="分享复活">
    <div class="share-arrow" aria-hidden="true">↗</div>
    <div class="share-guide">
      <div class="share-guide-icon">礼</div>
      <div class="eyebrow">分享复活</div>
      <h2>分享到朋友圈<br />获得一次复活机会</h2>
      <p>点击右上角 <b>···</b>，选择「分享到朋友圈」。</p>
      <p class="share-tip">分享完成后返回本页，系统会自动发放复活机会。</p>
      <div class="share-status">{{ status }}</div>
      <button class="share-close" type="button" @click="close">暂不分享</button>
    </div>
  </div>
</template>