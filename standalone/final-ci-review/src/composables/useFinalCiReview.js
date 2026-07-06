import { computed, onMounted, reactive, ref } from 'vue'
import { seedInitiatives } from '../data/mockInitiatives'
import {
  STORAGE_KEY,
  buildApprovalChainSteps,
  buildApprovalDetail,
  getDocumentIcon,
  loadInitiativesFromStorage,
  mapInitiativeToProject,
  persistInitiativeToStorage,
  pickInitiativeRaw,
  normalizeEmail,
  pickInitiativeValue
} from '../utils/finalCiReviewLogic'

export function useFinalCiReview() {
  const allProjects = ref([])
  const selectedProject = ref(null)
  const searchTerm = ref('')
  const statusFilter = ref('')
  const activeTab = ref('approval')
  const expandedStages = reactive({})
  const formState = reactive({
    ciSignOffComment: '',
    execLeaderRecipients: '',
    elPidDetails: '',
    elComment: ''
  })
  const documentsLoading = ref(false)
  const documents = ref([])

  const statusOptions = computed(() => {
    const statuses = [
      ...new Set(
        allProjects.value
          .map((p) => String(p.automationStatus || '').trim())
          .filter((s) => s && s !== 'N/A')
      )
    ].sort()
    return [{ label: 'All Automation Status', value: '' }, ...statuses.map((s) => ({ label: s, value: s }))]
  })

  const filteredProjects = computed(() => {
    const term = searchTerm.value.toLowerCase()
    return allProjects.value.filter((project) => {
      const matchesSearch =
        project.name.toLowerCase().includes(term) || String(project.id).toLowerCase().includes(term)
      const matchesStatus = !statusFilter.value || project.automationStatus === statusFilter.value
      return matchesSearch && matchesStatus
    })
  })

  const approvalSteps = computed(() => buildApprovalChainSteps(selectedProject.value))

  const approvalDetail = computed(() =>
    buildApprovalDetail(selectedProject.value, formState)
  )

  function resetFormState() {
    formState.ciSignOffComment = ''
    formState.execLeaderRecipients = ''
    formState.elPidDetails = ''
    formState.elComment = ''
  }

  function loadProjects() {
    let initiatives = loadInitiativesFromStorage()
    if (!initiatives.length) {
      initiatives = seedInitiatives
      localStorage.setItem(STORAGE_KEY, JSON.stringify(initiatives))
    }

    allProjects.value = initiatives
      .map((item) => mapInitiativeToProject(item))
      .filter(Boolean)
      .sort((a, b) => {
        const priority = { Complete: 0, Completed: 0, 'Value Realized': 0, 'Value Realised': 0 }
        return (priority[a.automationStatus] ?? 999) - (priority[b.automationStatus] ?? 999)
      })

    if (allProjects.value.length) {
      selectProject(allProjects.value[0])
    }
  }

  function selectProject(project) {
    selectedProject.value = project
    resetFormState()
    Object.keys(expandedStages).forEach((k) => delete expandedStages[k])
    loadDocuments()
  }

  function toggleStage(key) {
    expandedStages[key] = !expandedStages[key]
  }

  function isStageExpanded(key) {
    return Boolean(expandedStages[key])
  }

  async function loadDocuments() {
    if (!selectedProject.value) {
      documents.value = []
      return
    }
    documentsLoading.value = true
    await new Promise((r) => setTimeout(r, 200))
    documents.value = [...(selectedProject.value.documents || [])]
    documentsLoading.value = false
  }

  function refreshSelectedProject() {
    if (!selectedProject.value?.rawInitiative) return
    const refreshed = mapInitiativeToProject(selectedProject.value.rawInitiative)
    if (!refreshed) return
    const index = allProjects.value.findIndex((p) => p.id === refreshed.id)
    if (index >= 0) allProjects.value[index] = refreshed
    selectedProject.value = refreshed
    loadDocuments()
  }

  async function approveCISignOff() {
    const comment = String(formState.ciSignOffComment || '').trim()
    if (!comment) {
      alert('CI Final Comment is required before approving sign-off.')
      return
    }
    const today = new Date()
    const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`
    const initiative = selectedProject.value.rawInitiative
    Object.assign(initiative, {
      signoff: 'Approved',
      ciSignOffComment: comment,
      ciSignOffDate: todayStr,
      emailSentToCI: todayStr
    })
    persistInitiativeToStorage(initiative)
    refreshSelectedProject()
  }

  async function emailExecutionLeader() {
    const initiative = selectedProject.value?.rawInitiative || {}
    const emailSentToELRaw = pickInitiativeRaw(initiative, ['EmailsenttoEL', 'emailSentToEL'])
    if (emailSentToELRaw !== null && String(emailSentToELRaw).trim() !== '') {
      alert('Execution Leader email is already sent for this initiative.')
      return
    }
    const toEmails = String(formState.execLeaderRecipients || '').trim()
    if (!toEmails) {
      alert('Enter EL email under Sign-off before sending.')
      return
    }
    const elEmail = toEmails.split(/[;,]/)[0]?.trim() || ''
    const today = new Date()
    const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`
    Object.assign(initiative, { elFinalVL: elEmail, emailSentToEL: todayStr })
    persistInitiativeToStorage(initiative)
    alert(`Execution Leader email sent successfully (prototype — no server call).`)
    refreshSelectedProject()
  }

  async function markValueRealized() {
    const initiative = selectedProject.value?.rawInitiative || {}
    const comment = String(formState.elComment || '').trim()
    const pidDetails = String(formState.elPidDetails || '').trim()
    const currentUserEmail = String(localStorage.getItem('intake_requestor_email') || '')
      .trim()
      .toLowerCase()
    const ciSignOffDateRaw = pickInitiativeRaw(initiative, ['ciSignOffDate', 'CISignoffDate'])
    const hasCISignOffDate = ciSignOffDateRaw !== null && String(ciSignOffDateRaw).trim() !== ''
    const elOwnerEmail = normalizeEmail(pickInitiativeValue(initiative, ['elFinalVL']))
    if (!hasCISignOffDate) {
      alert('Value Realised is locked until CI Sign Off Date is set.')
      return
    }
    if (normalizeEmail(currentUserEmail) !== elOwnerEmail) {
      alert('Only EL Final VL can mark Value Realised.')
      return
    }
    if (!comment) {
      alert('Comment is required.')
      return
    }
    if (!pidDetails) {
      alert('PID details are required.')
      return
    }
    const today = new Date()
    const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`
    Object.assign(initiative, {
      automationStatus: 'Value Realized',
      elComment: comment,
      pidDetails,
      elApprovedDate: todayStr,
      executionLeaderDate: todayStr,
      elFinalVL: currentUserEmail || elOwnerEmail,
      developerComments: comment
    })
    persistInitiativeToStorage(initiative)
    refreshSelectedProject()
  }

  const canSendElEmail = computed(() => {
    if (!approvalDetail.value?.signOff) return false
    const { approved, locked, hasEmailSentToEL } = approvalDetail.value.signOff
    if (hasEmailSentToEL) return false
    if (!approved && locked) return false
    return Boolean(String(formState.execLeaderRecipients || '').trim())
  })

  onMounted(loadProjects)

  return {
    allProjects,
    selectedProject,
    searchTerm,
    statusFilter,
    activeTab,
    expandedStages,
    formState,
    documents,
    documentsLoading,
    statusOptions,
    filteredProjects,
    approvalSteps,
    approvalDetail,
    canSendElEmail,
    selectProject,
    toggleStage,
    isStageExpanded,
    approveCISignOff,
    emailExecutionLeader,
    markValueRealized,
    getDocumentIcon
  }
}
