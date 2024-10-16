import { createApp } from 'vue'
import EnvCheck from './views/EnvCheck.vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

const app = createApp(EnvCheck)
app.use(ElementPlus)
app.mount('#app')
