import type { App } from 'vue'
import type { RouteRecordRaw } from 'vue-router'
import { createRouter, createWebHashHistory } from 'vue-router'
import EnvCheck from '@renderer/views/EnvCheck.vue'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@renderer/views/home.vue')
  },
  {
    path: '/agentconfig',
    name: 'AgentConfig',
    component: () => import('@renderer/views/agentconfig.vue')
  },
  {
    path: '/kbconfig',
    name: 'kbconfig',
    component: () => import('@renderer/views/knowledgebase/kbconfig.vue')
  },
  {
    path: '/env-check',
    name: 'EnvCheck',
    component: EnvCheck
  }
]

export const router = createRouter({
  history: createWebHashHistory(),
  routes,
  scrollBehavior: () => ({ left: 0, top: 0 })
})

export async function setupRouter(app: App) {
  app.use(router)
  await router.isReady()
}
