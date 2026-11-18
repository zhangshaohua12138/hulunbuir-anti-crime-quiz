import { defineStore } from 'pinia'
import { api } from './api'
import type { AdminMe, Bootstrap, BootConfig } from './types'
import { normalizeLayout, type PageLayout } from './layout'

export const useSession = defineStore('session', {
  state: () => ({
    boot: null as Bootstrap | null,
    admin: null as AdminMe | null,
    loading: false,
  }),
  getters: {
    config(state): BootConfig | null {
      return state.boot?.config || null
    },
    account(state) {
      return state.boot?.account || null
    },
    layout(state): PageLayout {
      return normalizeLayout(state.boot?.config?.layout)
    },
  },
  actions: {
    async loadBoot(force = false) {
      if (this.boot && !force) return this.boot
      this.loading = true
      try {
        this.boot = await api<Bootstrap>('/api/bootstrap')
        return this.boot
      } finally {
        this.loading = false
      }
    },
    async loadAdmin(force = false) {
      if (this.admin && !force) return this.admin
      this.admin = await api<AdminMe>('/api/admin/me')
      return this.admin
    },
    async login(username: string, password: string) {
      const result = await api<AdminMe>('/api/admin/login', {
        method: 'POST',
        body: JSON.stringify({ username, password }),
      })
      this.admin = result
      return result
    },
    async logout() {
      await api('/api/logout', { method: 'POST' })
      this.admin = null
    },
  },
})

