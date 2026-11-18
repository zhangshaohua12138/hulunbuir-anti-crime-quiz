import { createRouter, createWebHashHistory } from 'vue-router'
import AdminLoginView from './views/AdminLoginView.vue'
import AdminDashboard from './views/admin/AdminDashboard.vue'
import AdminConfig from './views/admin/AdminConfig.vue'
import AdminQuestions from './views/admin/AdminQuestions.vue'
import AdminPrizes from './views/admin/AdminPrizes.vue'
import AdminUsers from './views/admin/AdminUsers.vue'
import AdminRecords from './views/admin/AdminRecords.vue'
import AdminAccounts from './views/admin/AdminAccounts.vue'
import AdminIntegrations from './views/admin/AdminIntegrations.vue'
import { useSession } from './store'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', redirect: '/admin' },
    { path: '/admin', component: AdminDashboard, meta: { admin: true } },
    { path: '/admin/config', component: AdminConfig, meta: { admin: true } },
    { path: '/admin/questions', component: AdminQuestions, meta: { admin: true } },
    { path: '/admin/prizes', component: AdminPrizes, meta: { admin: true } },
    { path: '/admin/users', component: AdminUsers, meta: { admin: true } },
    { path: '/admin/records', component: AdminRecords, meta: { admin: true } },
    { path: '/admin/accounts', component: AdminAccounts, meta: { admin: true, super: true } },
    { path: '/admin/integrations', component: AdminIntegrations, meta: { admin: true, super: true } },
    { path: '/login', component: AdminLoginView },
    { path: '/:pathMatch(.*)*', redirect: '/admin' },
  ],
})

router.beforeEach(async (to) => {
  if (!to.meta.admin) return true
  const session = useSession()
  try {
    await session.loadAdmin()
    if (to.meta.super && session.admin?.role !== 'super') return { path: '/admin' }
    return true
  } catch {
    return { path: '/login' }
  }
})

export default router