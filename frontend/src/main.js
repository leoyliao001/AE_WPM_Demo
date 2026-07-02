import { createApp } from 'vue'
import axios from 'axios'
import { MdsConfig } from '@maersk-global/mds-config'
import App from './App.vue'
import router from './router'

if (typeof window !== 'undefined') {
  const iconBasePath = import.meta.env.DEV
    ? '/node_modules/'
    : `${import.meta.env.BASE_URL}node_modules/`

  axios.defaults.baseURL = ''
  MdsConfig.iconsDynamicImportPath = iconBasePath
  window.MdsConfig = {
    ...(window.MdsConfig || {}),
    _iconsDynamicImportPath: iconBasePath
  }
}

const app = createApp(App)
app.use(router)
app.mount('#app')
