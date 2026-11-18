import { createRouter, createWebHashHistory } from 'vue-router'
import HomeView from './views/HomeView.vue'
import DesignerView from './views/DesignerView.vue'
import AdminLoginView from './views/AdminLoginView.vue'
import QuizView from './views/QuizView.vue'
import ResultView from './views/ResultView.vue'
import RulesView from './views/RulesView.vue'
import { useSession } from './store'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', component: HomeView },
    { path: '/rules', component: RulesView },
    { path: '/quiz/:id', component: QuizView },
    { path: '/result/:id', component: ResultView },
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