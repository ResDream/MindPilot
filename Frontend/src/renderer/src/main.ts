import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import { setupRouter } from './router'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import contextmenu from 'v-contextmenu'
import 'v-contextmenu/dist/themes/default.css'

const app = createApp(App)
const pinia = createPinia()

app.use(contextmenu)
app.use(pinia)
app.use(ElementPlus)
setupRouter(app)
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}
app.mount('#app')
