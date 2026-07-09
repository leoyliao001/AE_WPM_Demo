import { createApp } from 'vue'
import { createRouter, createMemoryHistory } from 'vue-router'
import { MdsConfig } from '@maersk-global/mds-config'
import App from './App.singlefile.vue'
import MigrationIntake from '@frontend/views/MigrationIntake.vue'

if (typeof window !== 'undefined') {
  const iconBasePath = 'https://assets.maerskline.com/mds/icons/latest/svg/20px/'
  MdsConfig.iconsDynamicImportPath = iconBasePath
  window.MdsConfig = {
    ...(window.MdsConfig || {}),
    _iconsDynamicImportPath: iconBasePath
  }
}

const router = createRouter({
  history: createMemoryHistory(),
  routes: [
    {
      path: '/migration-intake',
      name: 'MigrationIntake',
      component: MigrationIntake
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/migration-intake'
    }
  ]
})

const app = createApp(App)
app.use(router)

router.isReady().then(() => {
  app.mount('#app')
})
