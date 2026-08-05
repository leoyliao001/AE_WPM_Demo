import { createRouter, createWebHistory } from 'vue-router'
import Welcome from '../views/Welcome.vue'
import WelcomePhotoDemo from '../views/WelcomePhotoDemo.vue'
import MigrationIntake from '../views/MigrationIntake.vue'
import MigrationDashboard from '../views/MigrationDashboard.vue'
import MigrationProjectDetail from '../views/MigrationProjectDetail.vue'
import LDDashboard from '../views/LDDashboard.vue'
import MigrationChatbot from '../views/MigrationChatbot.vue'
import FpoMapping from '../views/FpoMapping.vue'
import ProductOwnership from '../views/ProductOwnership.vue'
import GscSiteMapping from '../views/GscSiteMapping.vue'
import ServiceCatalogue from '../views/ServiceCatalogue.vue'
import MigrationIntakeSubmissions from '../views/MigrationIntakeSubmissions.vue'
import ProjectAttributesDatabase from '../views/ProjectAttributesDatabase.vue'
import AttributesAccessControl from '../views/AttributesAccessControl.vue'
import OpportunityAssessment from '../views/OpportunityAssessment.vue'
import ProjectGantt from '../views/ProjectGantt.vue'
import ProjectGanttAttributes from '../views/ProjectGanttAttributes.vue'
import {
  canAccessAttributesTable,
  fetchMyAttributesAccess
} from '../utils/attributesAccess.js'

const ATTRIBUTE_ROUTE_KEYS = {
  '/fpo-mapping': 'fpo_mapping',
  '/product-ownership': 'product_ownership',
  '/gsc-site-mapping': 'gsc_site_mapping',
  '/service-catalogue': 'service_catalogue',
  '/migration-intake-submissions': 'migration_intake',
  '/project-gantt-attributes': 'project_gantt',
  '/attributes-access-control': 'access_control'
}

const routes = [
  { path: '/', name: 'Welcome', component: Welcome },
  { path: '/welcome', redirect: '/' },
  {
    path: '/welcome-photo-demo',
    name: 'WelcomePhotoDemo',
    component: WelcomePhotoDemo
  },
  // Hidden for now — redirect direct URLs back to Welcome
  { path: '/future-service-model', redirect: '/' },
  { path: '/welcome2', redirect: '/' },
  { path: '/final-ci-review', redirect: '/' },
  { path: '/migration-intake', name: 'MigrationIntake', component: MigrationIntake },
  { path: '/migration-dashboard', name: 'MigrationDashboard', component: MigrationDashboard },
  {
    path: '/migration-dashboard/:id',
    name: 'MigrationProjectDetail',
    component: MigrationProjectDetail
  },
  {
    path: '/migration-dashboard/:id/opportunity-assessment',
    name: 'OpportunityAssessment',
    component: OpportunityAssessment
  },
  {
    path: '/migration-dashboard/:id/gantt',
    name: 'ProjectGantt',
    component: ProjectGantt
  },
  { path: '/ld-dashboard', name: 'LDDashboard', component: LDDashboard },
  // Project: current user's submitted projects only (?mine=1)
  { path: '/project-dashboard', name: 'ProjectDashboard', component: MigrationDashboard },
  { path: '/project-dashboard/:section', redirect: '/project-dashboard' },
  { path: '/migration-chatbot', name: 'MigrationChatbot', component: MigrationChatbot },
  {
    path: '/project-attributes',
    name: 'ProjectAttributesDatabase',
    component: ProjectAttributesDatabase
  },
  { path: '/product-ownership', name: 'ProductOwnership', component: ProductOwnership },
  { path: '/gsc-site-mapping', name: 'GscSiteMapping', component: GscSiteMapping },
  { path: '/service-catalogue', name: 'ServiceCatalogue', component: ServiceCatalogue },
  {
    path: '/migration-intake-submissions',
    name: 'MigrationIntakeSubmissions',
    component: MigrationIntakeSubmissions
  },
  { path: '/fpo-mapping', name: 'FpoMapping', component: FpoMapping },
  {
    path: '/project-gantt-attributes',
    name: 'ProjectGanttAttributes',
    component: ProjectGanttAttributes
  },
  {
    path: '/attributes-access-control',
    name: 'AttributesAccessControl',
    component: AttributesAccessControl
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to) => {
  // Project Attributes hub is Super Admin only (nav entry + direct URL).
  if (to.path === '/project-attributes') {
    const access = await fetchMyAttributesAccess({ force: true })
    if (!access?.is_super_admin) {
      return { path: '/' }
    }
    return true
  }

  const tableKey = ATTRIBUTE_ROUTE_KEYS[to.path]
  if (!tableKey) return true
  // Always re-fetch so Access Control edits apply without a full app reload.
  const access = await fetchMyAttributesAccess({ force: true })
  if (!canAccessAttributesTable(access, tableKey)) {
    return access?.is_super_admin ? { path: '/project-attributes' } : { path: '/' }
  }
  return true
})

export default router
