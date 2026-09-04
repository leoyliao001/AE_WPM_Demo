import { createRouter, createWebHistory } from 'vue-router'
import Welcome from '../views/Welcome.vue'
import MigrationIntake from '../views/MigrationIntake.vue'
import MigrationDashboard from '../views/MigrationDashboard.vue'
import MigrationDashboard2 from '../views/MigrationDashboard2.vue'
import MigrationProjectDetail from '../views/MigrationProjectDetail.vue'
import LDDashboard from '../views/LDDashboard.vue'
import MigrationChatbot from '../views/MigrationChatbot.vue'
import FpoMapping from '../views/FpoMapping.vue'
import ProductOwnership from '../views/ProductOwnership.vue'
import GscSiteMapping from '../views/GscSiteMapping.vue'
import ServiceCatalogue from '../views/ServiceCatalogue.vue'
import WorkingHours from '../views/WorkingHours.vue'
import MigrationIntakeSubmissions from '../views/MigrationIntakeSubmissions.vue'
import ApprovalWorkflow from '../views/ApprovalWorkflow.vue'
import ApprovalInput from '../views/ApprovalInput.vue'
import ProjectAttributesDatabase from '../views/ProjectAttributesDatabase.vue'
import AttributesAccessControl from '../views/AttributesAccessControl.vue'
import OpportunityAssessment from '../views/OpportunityAssessment.vue'
import ProjectGantt from '../views/ProjectGantt.vue'
import ProjectGanttAttributes from '../views/ProjectGanttAttributes.vue'
import BpmRofo from '../views/BpmRofo.vue'
import BpmActual from '../views/BpmActual.vue'
import ApprovalCycle from '../views/ApprovalCycle.vue'
import BusinessCase from '../views/BusinessCase.vue'
import ApprovalFinalReview from '../views/ApprovalFinalReview.vue'
import {
  canAccessAttributesTable,
  fetchMyAttributesAccess
} from '../utils/attributesAccess.js'

const ATTRIBUTE_ROUTE_KEYS = {
  '/fpo-mapping': 'fpo_mapping',
  '/product-ownership': 'product_ownership',
  '/gsc-site-mapping': 'gsc_site_mapping',
  '/service-catalogue': 'service_catalogue',
  '/working-hours': 'working_hours',
  '/migration-intake-submissions': 'migration_intake',
  '/approval-workflow': 'approval_workflow',
  '/input-for-approval': 'input_for_approval',
  '/project-gantt-attributes': 'project_gantt',
  '/bpm-rofo': 'bpm_rofo',
  '/bpm-actual': 'bpm_actual',
  '/attributes-access-control': 'access_control'
}

const routes = [
  { path: '/', name: 'Welcome', component: Welcome },
  { path: '/welcome', redirect: '/' },
  { path: '/welcome-photo-demo', redirect: '/' },
  // Hidden for now — redirect direct URLs back to Welcome
  { path: '/future-service-model', redirect: '/' },
  { path: '/welcome2', redirect: '/' },
  { path: '/final-ci-review', redirect: '/' },
  { path: '/migration-intake', name: 'MigrationIntake', component: MigrationIntake },
  { path: '/migration-dashboard', name: 'MigrationDashboard', component: MigrationDashboard },
  {
    path: '/migration-dashboard2',
    name: 'MigrationDashboard2',
    component: MigrationDashboard2
  },
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
  {
    path: '/migration-dashboard/:id/business-case',
    name: 'BusinessCase',
    component: BusinessCase
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
  { path: '/working-hours', name: 'WorkingHours', component: WorkingHours },
  {
    path: '/migration-intake-submissions',
    name: 'MigrationIntakeSubmissions',
    component: MigrationIntakeSubmissions
  },
  {
    path: '/approval-workflow',
    name: 'ApprovalWorkflow',
    component: ApprovalWorkflow
  },
  {
    path: '/input-for-approval',
    name: 'ApprovalInput',
    component: ApprovalInput
  },
  { path: '/fpo-mapping', name: 'FpoMapping', component: FpoMapping },
  {
    path: '/project-gantt-attributes',
    name: 'ProjectGanttAttributes',
    component: ProjectGanttAttributes
  },
  {
    path: '/bpm-rofo',
    name: 'BpmRofo',
    component: BpmRofo
  },
  {
    path: '/bpm-actual',
    name: 'BpmActual',
    component: BpmActual
  },
  {
    path: '/attributes-access-control',
    name: 'AttributesAccessControl',
    component: AttributesAccessControl
  },
  { path: '/approval-cycle', name: 'ApprovalCycle', component: ApprovalCycle },
  {
    path: '/approval-cycle/review/:migrationRequestId/:role',
    name: 'ApprovalFinalReview',
    component: ApprovalFinalReview
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to) => {
  // Project Attributes hub is available to anyone with any table access.
  if (to.path === '/project-attributes') {
    const access = await fetchMyAttributesAccess({ force: true })
    const hasDatabaseAccess = !!access?.is_super_admin || Object.values(access?.tables || {}).some(Boolean)
    if (!hasDatabaseAccess) {
      return { path: '/' }
    }
    return true
  }

  const tableKey = ATTRIBUTE_ROUTE_KEYS[to.path]
  if (!tableKey) return true
  // Always re-fetch so Access Control edits apply without a full app reload.
  const access = await fetchMyAttributesAccess({ force: true })
  if (!canAccessAttributesTable(access, tableKey)) {
    return access?.is_super_admin || Object.values(access?.tables || {}).some(Boolean)
      ? { path: '/project-attributes' }
      : { path: '/' }
  }
  return true
})

export default router
