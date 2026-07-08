import { createApp } from 'vue'
import { createRouter, createMemoryHistory } from 'vue-router'
import App from './App.singlefile.vue'
import MigrationIntake from '@frontend/views/MigrationIntake.vue'

const router = createRouter({
  history: createMemoryHistory('/migration-intake'),
  routes: [
    { path: '/', name: 'Welcome', component: { template: '<div />' } },
    { path: '/migration-intake', name: 'MigrationIntake', component: MigrationIntake }
  ]
})

const app = createApp(App)
app.use(router)
app.mount('#app')
