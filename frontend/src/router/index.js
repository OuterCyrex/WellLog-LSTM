import { createRouter, createWebHistory } from 'vue-router'
import { isAuthenticated } from '../auth'
import AuthView from '../views/AuthView.vue'
import WellManagement from '../views/WellManagement.vue'
import WellPrediction from '../views/WellPrediction.vue'
import PredictionRecords from '../views/PredictionRecords.vue'

const routes = [
  { path: '/', redirect: '/auth' },
  { path: '/auth', name: 'auth', component: AuthView, meta: { guestOnly: true } },
  { path: '/manage', name: 'manage', component: WellManagement, meta: { requiresAuth: true } },
  { path: '/predict', name: 'predict', component: WellPrediction, meta: { requiresAuth: true } },
  { path: '/records', name: 'records', component: PredictionRecords, meta: { requiresAuth: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const authed = isAuthenticated()
  if (to.meta.requiresAuth && !authed) return { name: 'auth' }
  if (to.meta.guestOnly && authed) return { name: 'manage' }
  return true
})

export default router
