import { createRouter, createWebHistory } from 'vue-router'
import Welcome from '../views/Welcome.vue'
import MigrationIntake from '../views/MigrationIntake.vue'
import MigrationDashboard from '../views/MigrationDashboard.vue'
import MigrationProjectDetail from '../views/MigrationProjectDetail.vue'
import LDDashboard from '../views/LDDashboard.vue'
import MigrationChatbot from '../views/MigrationChatbot.vue'
import FpoMapping from '../views/FpoMapping.vue'
import ProductOwnership from '../views/ProductOwnership.vue'
import GscSiteMapping from '../views/GscSiteMapping.vue'
import ProjectAttributesDatabase from '../views/ProjectAttributesDatabase.vue'
import AttributesAccessControl from '../views/AttributesAccessControl.vue'
import OpportunityAssessment from '../views/OpportunityAssessment.vue'
import {
  canAccessAttributesTable,
  fetchMyAttributesAccess
} from '../utils/attributesAccess.js'

const ATTRIBUTE_ROUTE_KEYS = {
  '/fpo-mapping': 'fpo_mapping',
  '/product-ownership': 'product_ownership',
  '/gsc-site-mapping': 'gsc_site_mapping',
  '/attributes-access-control': 'access_control'
}

const routes = [
  { path: '/', name: 'Welcome', component: Welcome },
  { path: '/welcome', redirect: '/' },
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
  { path: '/ld-dashboard', name: 'LDDashboard', component: LDDashboard },
  // Project: same list for now; later filter to current user's projects
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
  { path: '/fpo-mapping', name: 'FpoMapping', component: FpoMapping },
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
  const tableKey = ATTRIBUTE_ROUTE_KEYS[to.path]
  if (!tableKey) return true
  const access = await fetchMyAttributesAccess()
  if (!canAccessAttributesTable(access, tableKey)) {
    return { path: '/project-attributes' }
  }
  return true
})

export default router
