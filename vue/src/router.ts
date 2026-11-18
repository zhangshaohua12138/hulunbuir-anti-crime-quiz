import { createRouter, createWebHashHistory } from 'vue-router'
import HomeView from './views/HomeView.vue'
import DesignerView from './views/DesignerView.vue'
import AdminLoginView from './views/AdminLoginView.vue'
import QuizView from './views/QuizView.vue'
import ResultView from './views/ResultView.vue'
import RulesView from './views/RulesView.vue'
import LotteryView from './views/LotteryView.vue'
import RankingView from './views/RankingView.vue'
import AwardsView from './views/AwardsView.vue'
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
    { path: '/admin/accounts', component: AdminAccounts, meta: { admin: true } },
    { path: '/admin/integrations', component: AdminIntegrations, meta: { admin: true } },
    { path: '/designer', component: DesignerView, meta: { admin: true } },
    { path: '/login', component: AdminLoginView },
  ],
})

router.beforeEach(async (to) => {
  if (!to.meta.admin) return true
  const session = useSession()
  try {
    await session.loadAdmin()
    return true
  } catch {
    return { path: '/login', query: { next: to.fullPath } }
  }
})

export default router