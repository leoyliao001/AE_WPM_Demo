import { createApp } from 'vue'
import axios from 'axios'
import { MdsConfig } from '@maersk-global/mds-config'
import '@maersk-global/mds-components-core/mc-icon'
import { McIcon } from '@maersk-global/mds-components-core-icon'
import { patchMcIconComponent } from './utils/mdsIcon.js'
import App from './App.vue'
import router from './router'

patchMcIconComponent(McIcon)

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
