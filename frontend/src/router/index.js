import { createRouter, createWebHistory } from 'vue-router'
import Welcome from '../views/Welcome.vue'
import Welcome2 from '../views/Welcome2.vue'
import MigrationIntake from '../views/MigrationIntake.vue'
import MigrationDashboard from '../views/MigrationDashboard.vue'
import LDDashboard from '../views/LDDashboard.vue'
import ProjectDashboard from '../views/ProjectDashboard.vue'
import ProjectMilestoneDetail from '../views/ProjectMilestoneDetail.vue'
import MigrationChatbot from '../views/MigrationChatbot.vue'
import FinalCiReview from '../views/FinalCiReview.vue'

const routes = [
  { path: '/', name: 'Welcome', component: Welcome },
  { path: '/welcome', redirect: '/' },
  { path: '/future-service-model', name: 'FutureServiceModel', component: Welcome2 },
  { path: '/welcome2', redirect: '/future-service-model' },
  { path: '/migration-intake', name: 'MigrationIntake', component: MigrationIntake },
  { path: '/migration-dashboard', name: 'MigrationDashboard', component: MigrationDashboard },
  { path: '/ld-dashboard', name: 'LDDashboard', component: LDDashboard },
  { path: '/project-dashboard', name: 'ProjectDashboard', component: ProjectDashboard },
  {
    path: '/project-dashboard/:section',
    name: 'ProjectMilestoneDetail',
    component: ProjectMilestoneDetail
  },
  { path: '/migration-chatbot', name: 'MigrationChatbot', component: MigrationChatbot },
  { path: '/final-ci-review', name: 'FinalCiReview', component: FinalCiReview }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
