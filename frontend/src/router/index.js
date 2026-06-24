import { createRouter, createWebHistory } from 'vue-router'
import WellManagement from '../views/WellManagement.vue'
import WellPrediction from '../views/WellPrediction.vue'
import PredictionRecords from '../views/PredictionRecords.vue'

const routes = [
  { path: '/', redirect: '/manage' },
  { path: '/manage', name: 'manage', component: WellManagement },
  { path: '/predict', name: 'predict', component: WellPrediction },
  { path: '/records', name: 'records', component: PredictionRecords },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
