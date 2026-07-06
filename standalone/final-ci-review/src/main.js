import { createApp } from 'vue'
import { MdsConfig } from '@maersk-global/mds-config'
import App from './App.vue'
import '@maersk-global/mds-components-core/mc-top-bar'
import '@maersk-global/mds-components-core/mc-button'
import '@maersk-global/mds-components-core/mc-card'
import '@maersk-global/mds-components-core/mc-input'
import '@maersk-global/mds-components-core/mc-select'
import '@maersk-global/mds-components-core/mc-option'
import '@maersk-global/mds-components-core/mc-textarea'
import '@maersk-global/mds-components-core/mc-tag'
import '@maersk-global/mds-components-core/mc-icon'
import '@maersk-global/mds-components-core/mc-notification'
import '@maersk-global/mds-components-core/mc-loading-indicator'

if (typeof window !== 'undefined') {
  const iconBasePath = import.meta.env.DEV
    ? '/node_modules/'
    : `${import.meta.env.BASE_URL}node_modules/`
  MdsConfig.iconsDynamicImportPath = iconBasePath
  window.MdsConfig = { ...(window.MdsConfig || {}), _iconsDynamicImportPath: iconBasePath }
}

createApp(App).mount('#app')
