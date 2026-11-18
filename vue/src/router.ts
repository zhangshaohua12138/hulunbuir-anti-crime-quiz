import { createRouter, createWebHashHistory } from 'vue-router'
import HomeView from './views/HomeView.vue'
const DesignerView = () => import('./views/DesignerView.vue')
const AdminLoginView = () => import('./views/AdminLoginView.vue')
const QuizView = () => import('./views/QuizView.vue')
const ResultView = () => import('./views/ResultView.vue')
const RulesView = () => import('./views/RulesView.vue')
const LotteryView = () => import('./views/LotteryView.vue')
const RankingView = () => import('./views/RankingView.vue')
const AwardsView = () => import('./views/AwardsView.vue')
const AdminDashboard = () => import('./views/admin/AdminDashboard.vue')
const AdminConfig = () => import('./views/admin/AdminConfig.vue')
const AdminQuestions = () => import('./views/admin/AdminQuestions.vue')
const AdminPrizes = () => import('./views/admin/AdminPrizes.vue')
const AdminUsers = () => import('./views/admin/AdminUsers.vue')
const AdminRecords = () => import('./views/admin/AdminRecords.vue')
const AdminAccounts = () => import('./views/admin/AdminAccounts.vue')
const AdminIntegrations = () => import('./views/admin/AdminIntegrations.vue')
import { useSession } from './store'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', component: HomeView },
    { path: '/rules', component: RulesView },
    { path: '/quiz/:id', component: QuizView },
    { path: '/result/:id', component: ResultView },
    { path: '/lottery/:id', component: LotteryView },
    { path: '/ranking', component: RankingView },
    { path: '/winners', component: RankingView },
    { path: '/awards', component: AwardsView },
    { path: '/admin', component: AdminDashboard, meta: { admin: true } },
    { path: '/admin/config', component: AdminConfig, meta: { admin: true } },
    { path: '/admin/questions', component: AdminQuestions, meta: { admin: true } },
    { path: '/admin/prizes', component: AdminPrizes, meta: { admin: true } },
    { path: '/admin/users', component: AdminUsers, meta: { admin: true } },
    { path: '/admin/records', component: AdminRecords, meta: { admin: true } },
    { path: '/admin/accounts', component: AdminAccounts, meta: { admin: true, super: true } },
    { path: '/admin/integrations', component: AdminIntegrations, meta: { admin: true, super: true } },
    { path: '/designer', component: DesignerView, meta: { admin: true, super: true } },
    { path: '/login', component: AdminLoginView },
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
    return { path: '/login', query: { next: to.fullPath } }
  }
})

export default router