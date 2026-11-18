import { api } from './api'
import type { BootConfig } from './types'

declare global {
  interface Window {
    wx?: any
    WeixinJSBridge?: any
  }
}

let scriptPromise: Promise<void> | null = null

function loadScript() {
  if (scriptPromise) return scriptPromise
  scriptPromise = new Promise((resolve, reject) => {
    const existing = document.querySelector('script[data-wechat-jssdk]')
    if (existing) {
      resolve()
      return
    }
    const script = document.createElement('script')
    script.src = 'https://res.wx.qq.com/open/js/jweixin-1.6.0.js'
    script.dataset.wechatJssdk = '1'
    script.onload = () => resolve()
    script.onerror = () => reject(new Error('微信 JS-SDK 加载失败'))
    document.head.appendChild(script)
  })
  return scriptPromise
}

export async function configureWechatShare(config?: BootConfig | null) {
  if (!/MicroMessenger/i.test(navigator.userAgent)) return
  try {
    await loadScript()
    if (!window.wx) return
    const pageUrl = location.href.split('#')[0]
    const conf = await api<Record<string, unknown> & { imgUrl?: string }>(`/api/share/config?url=${encodeURIComponent(pageUrl)}`)
    const { imgUrl, ...wxConf } = conf
    window.wx.config({
      ...wxConf,
      jsApiList: ['updateAppMessageShareData', 'updateTimelineShareData', 'requestMerchantTransfer'],
    })
    window.wx.error((error: unknown) => console.warn('wx.config', error))
    window.wx.ready(() => {
      const data: Record<string, string> = {
        title: config?.title || document.title,
        desc: config?.shareDesc || '学法知法 · 守护平安 · 共建美好家园',
        link: config?.shareUrl || pageUrl,
      }
      if (imgUrl) data.imgUrl = String(imgUrl)
      window.wx.updateAppMessageShareData?.(data)
      window.wx.updateTimelineShareData?.(data)
    })
  } catch (error) {
    console.warn('wechat share setup failed', error)
  }
}