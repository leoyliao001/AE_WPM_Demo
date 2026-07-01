<template>
  <div class="intake-page">
    <div class="page-content">
      <header class="page-header">
        <router-link class="back-link" to="/">
          <mc-button
            appearance="neutral"
            variant="plain"
            fit="small"
            label="Back to Welcome"
            icon="mi-arrow-left"
          />
        </router-link>

        <div class="header-main">
          <mc-tag appearance="info" fit="small" label="Migration Request" />
          <h1 class="page-title">Migration Project Intake Form</h1>
          <p class="page-subtitle">
            Capture project details, scope, workforce requirements, and risks — then submit to the Project Attributes Database.
          </p>
        </div>

        <div class="flow-strip" aria-label="Submission flow">
          <div class="flow-step flow-step--active">
            <span class="flow-icon"><mc-icon icon="mi-user" size="20" /></span>
            <span class="flow-label">User Inputs</span>
          </div>
          <mc-icon class="flow-arrow" icon="mi-arrow-right" size="20" />
          <div class="flow-step flow-step--active">
            <span class="flow-icon"><mc-icon icon="mi-file" size="20" /></span>
            <span class="flow-label">Intake Form</span>
          </div>
          <mc-icon class="flow-arrow" icon="mi-arrow-right" size="20" />
          <div class="flow-step">
            <span class="flow-icon"><mc-icon icon="mi-database" size="20" /></span>
            <span class="flow-label">Project Attributes Database</span>
          </div>
        </div>
      </header>

      <div class="intake-form">
        <!-- Section 1 -->
        <section
          class="form-section"
          :class="{ 'form-section--elevated': elevatedSection === 'project-details' }"
          :style="{ '--section-accent': '#0077B8' }"
        >
          <div class="section-head">
            <span class="section-icon"><mc-icon icon="mi-map" size="24" /></span>
            <div>
              <h2 class="section-title">Project Details</h2>
              <p class="section-desc">Basic information to identify and classify the migration project.</p>
            </div>
          </div>

          <div class="section-body">
            <mc-input
              ref="projectNameRef"
              label="Project name"
              placeholder="Enter project name"
              :value="form.projectName"
              width="full-width"
              @input="onTextInput('projectName', $event)"
            />

            <div class="field-row">
              <mc-select
                ref="migrationTypeRef"
                label="Migration type"
                placeholder="Select migration type"
                :value="form.migrationType"
                width="full-width"
                @optionselected="onSelect('migrationType', $event)"
                @opened="onDropdownOpened('project-details')"
                @closed="onDropdownClosed('project-details')"
              >
                <mc-option
                  v-for="opt in migrationTypes"
                  :key="opt.value"
                  :value="opt.value"
                >
                  {{ opt.label }}
                </mc-option>
              </mc-select>

              <mc-select
                ref="regionRef"
                label="Region"
                placeholder="Select region"
                :value="form.region"
                width="full-width"
                @optionselected="onSelect('region', $event)"
                @opened="onDropdownOpened('project-details')"
                @closed="onDropdownClosed('project-details')"
              >
                <mc-option v-for="r in regions" :key="r" :value="r">{{ r }}</mc-option>
              </mc-select>

              <mc-select
                ref="areaRef"
                label="Area"
                placeholder="Select area"
                :value="form.area"
                width="full-width"
                @optionselected="onSelect('area', $event)"
                @opened="onDropdownOpened('project-details')"
                @closed="onDropdownClosed('project-details')"
              >
                <mc-option v-for="a in areas" :key="a" :value="a">{{ a }}</mc-option>
              </mc-select>
            </div>

            <mc-select
              ref="functionRef"
              label="Function"
              placeholder="Select function"
              hint="AIR, OCE, or HBDS"
              :value="form.function"
              width="full-width"
              @optionselected="onSelect('function', $event)"
              @opened="onDropdownOpened('project-details')"
              @closed="onDropdownClosed('project-details')"
            >
              <mc-option value="AIR">AIR</mc-option>
              <mc-option value="OCE">OCE</mc-option>
              <mc-option value="HBDS">HBDS</mc-option>
            </mc-select>

            <div class="product-field">
              <mc-multi-select
                :key="productSelectKey"
                ref="productsRef"
                label="Product"
                placeholder="Select one or more products"
                hint="Choose all products involved in this migration."
                listsearch
                filtertype="contains"
                optionsheight="360px"
                optionswidth="trigger"
                width="full-width"
                :data.prop="productData"
                :value.prop="form.products"
                @input="onProductsChange"
                @opened="onDropdownOpened('project-details')"
                @closed="onDropdownClosed('project-details')"
              />
            </div>
          </div>
        </section>

        <!-- Section 2 -->
        <section class="form-section" :style="{ '--section-accent': '#42B0D5' }">
          <div class="section-head">
            <span class="section-icon"><mc-icon icon="mi-crosshair" size="24" /></span>
            <div>
              <h2 class="section-title">Scope Definition</h2>
              <p class="section-desc">High-level scope, processes, FTEs, job levels, and activities being migrated.</p>
            </div>
          </div>

          <div class="section-body">
            <mc-textarea
              ref="scopeRef"
              label="Proposed scope of the project"
              placeholder="Describe processes, FTEs, job levels, and activities..."
              hint="Provide a high-level description of the processes, FTEs, job levels, and activities."
              rows="5"
              width="full-width"
              :value="form.proposedScope"
              @input="onTextInput('proposedScope', $event)"
            />
          </div>
        </section>

        <!-- Section 3 -->
        <section class="form-section" :style="{ '--section-accent': '#6DAA28' }">
          <div class="section-head">
            <span class="section-icon"><mc-icon icon="mi-users" size="24" /></span>
            <div>
              <h2 class="section-title">Workforce and Language</h2>
              <p class="section-desc">Language requirements and workforce sizing for scoping.</p>
            </div>
          </div>

          <div class="section-body">
            <div class="field-row field-row--two">
              <mc-input
                ref="languageRef"
                label="Language dependency"
                placeholder="e.g. English proficiency required"
                hint="Indicate justification and proficiency level."
                :value="form.languageDependency"
                width="full-width"
                @input="onTextInput('languageDependency', $event)"
              />

              <mc-input
                ref="fteRef"
                label="FTE number"
                placeholder="e.g. 12"
                hint="Value may change during scoping."
                inputmode="numeric"
                :value="form.fteNumber"
                width="full-width"
                @input="onTextInput('fteNumber', $event)"
              />
            </div>

            <div class="field-row field-row--three">
              <mc-input
                label="JL2"
                placeholder="Count"
                hint="Job Level 2"
                inputmode="numeric"
                :value="form.jl2"
                width="full-width"
                @input="onTextInput('jl2', $event)"
              />
              <mc-input
                label="JL3"
                placeholder="Count"
                hint="Job Level 3"
                inputmode="numeric"
                :value="form.jl3"
                width="full-width"
                @input="onTextInput('jl3', $event)"
              />
              <mc-input
                label="JL4"
                placeholder="Count"
                hint="Job Level 4"
                inputmode="numeric"
                :value="form.jl4"
                width="full-width"
                @input="onTextInput('jl4', $event)"
              />
            </div>
          </div>
        </section>

        <!-- Section 4 -->
        <section class="form-section form-section--optional" :style="{ '--section-accent': '#F3880E' }">
          <div class="section-head">
            <span class="section-icon"><mc-icon icon="mi-shield" size="24" /></span>
            <div>
              <div class="section-title-row">
                <h2 class="section-title">Risk Assessment</h2>
                <mc-tag appearance="neutral" fit="small" label="Optional" />
              </div>
              <p class="section-desc">Potential issues, challenges, and identified risks.</p>
            </div>
          </div>

          <div class="section-body">
            <mc-textarea
              ref="risksRef"
              label="Risks"
              placeholder="Describe potential issues, challenges, and what could go wrong..."
              hint="Describe potential issues, challenges."
              rows="4"
              width="full-width"
              :value="form.risks"
              @input="onTextInput('risks', $event)"
            />
          </div>
        </section>

        <footer class="form-footer">
          <div class="footer-target">
            <mc-icon icon="mi-arrow-down" size="20" />
            <span>Data will be sent to <strong>Project Attributes Database</strong></span>
          </div>

          <div class="footer-actions">
            <mc-button
              type="button"
              appearance="neutral"
              variant="outlined"
              fit="medium"
              label="Save Draft"
              icon="mi-floppy-disk"
              :loading="saving"
              @click="onSaveDraft"
            />
            <mc-button
              appearance="primary"
              variant="filled"
              fit="medium"
              label="Submit"
              trailingicon="mi-arrow-right"
              :loading="submitting"
              @click="onSubmit"
            />
          </div>
        </footer>

        <mc-notification
          v-if="notice.message"
          class="form-notice"
          :appearance="notice.type"
          :heading="notice.title"
          :body="notice.message"
          closable
          @close="clearNotice"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import '@maersk-global/mds-components-core/mc-button'
import '@maersk-global/mds-components-core/mc-icon'
import '@maersk-global/mds-components-core/mc-tag'
import '@maersk-global/mds-components-core/mc-input'
import '@maersk-global/mds-components-core/mc-select'
import '@maersk-global/mds-components-core/mc-option'
import '@maersk-global/mds-components-core/mc-multi-select'
import '@maersk-global/mds-components-core/mc-textarea'
import '@maersk-global/mds-components-core/mc-notification'

const DRAFT_KEY = 'ae-wpm-migration-intake-draft'

const migrationTypes = [
  { value: '1:1-transfer', label: '1:1 Transfer' },
  { value: 'new-additional', label: 'New/Additional work, tasks or activities' }
]

const regions = ['Asia Pacific', 'Europe', 'Americas', 'Africa', 'Middle East']
const areas = ['North', 'South', 'East', 'West', 'Central']

const productOptions = [
  'Lead Logistics',
  'Customs',
  'Landside Transportation',
  'Ground Freight',
  'LCL',
  'Ocean OTCY',
  'Ocean OPS',
  'E-commerce',
  'Contract Logistics',
  'Project Logistics',
  'Air',
  'Cold Chain',
  'Depots',
  'LTA',
  'OTC',
  'STP',
  'ATR'
]

const productData = productOptions.map((name) => ({
  label: name,
  value: name
}))

const form = reactive({
  projectName: '',
  migrationType: '',
  region: '',
  area: '',
  products: [],
  function: '',
  proposedScope: '',
  languageDependency: '',
  fteNumber: '',
  jl2: '',
  jl3: '',
  jl4: '',
  risks: ''
})

const productSelectKey = ref(0)
const elevatedSection = ref(null)
const openDropdownCount = ref(0)
const saving = ref(false)
const submitting = ref(false)
const notice = reactive({ type: 'success', title: '', message: '' })

const readEventValue = (event) => {
  const target = event?.target
  return target?.value ?? event?.detail?.value ?? ''
}

const onTextInput = (field, event) => {
  form[field] = readEventValue(event)
}

const onSelect = (field, event) => {
  form[field] = event?.detail?.value ?? readEventValue(event)
}

const onProductsChange = (event) => {
  const value = event?.detail?.value ?? event?.target?.value
  form.products = Array.isArray(value) ? [...value] : []
}

const onDropdownOpened = (sectionId) => {
  openDropdownCount.value += 1
  elevatedSection.value = sectionId
}

const onDropdownClosed = (sectionId) => {
  openDropdownCount.value = Math.max(0, openDropdownCount.value - 1)
  if (openDropdownCount.value === 0 && elevatedSection.value === sectionId) {
    elevatedSection.value = null
  }
}

const collectForm = () => ({ ...form, products: [...form.products] })

const loadDraft = () => {
  try {
    const raw = localStorage.getItem(DRAFT_KEY)
    if (!raw) return
    const saved = JSON.parse(raw)
    Object.assign(form, {
      projectName: saved.projectName ?? '',
      migrationType: saved.migrationType ?? '',
      region: saved.region ?? '',
      area: saved.area ?? '',
      products: Array.isArray(saved.products) ? saved.products : [],
      function: saved.function ?? '',
      proposedScope: saved.proposedScope ?? '',
      languageDependency: saved.languageDependency ?? '',
      fteNumber: saved.fteNumber ?? '',
      jl2: saved.jl2 ?? '',
      jl3: saved.jl3 ?? '',
      jl4: saved.jl4 ?? '',
      risks: saved.risks ?? ''
    })
    productSelectKey.value += 1
  } catch {
    // ignore corrupt draft
  }
}

const showNotice = (type, title, message) => {
  notice.type = type
  notice.title = title
  notice.message = message
}

const clearNotice = () => {
  notice.message = ''
}

const validate = () => {
  if (!form.projectName.trim()) return 'Project name is required.'
  if (!form.migrationType) return 'Migration type is required.'
  if (!form.region) return 'Region is required.'
  if (!form.area) return 'Area is required.'
  if (!form.products.length) return 'Please select at least one product.'
  if (!form.function) return 'Function is required.'
  if (!form.proposedScope.trim()) return 'Proposed scope is required.'
  if (!form.languageDependency.trim()) return 'Language dependency is required.'
  if (!form.fteNumber.trim()) return 'FTE number is required.'
  return ''
}

const onSaveDraft = async () => {
  saving.value = true
  try {
    localStorage.setItem(DRAFT_KEY, JSON.stringify(collectForm()))
    showNotice('success', 'Draft saved', 'Your progress has been saved locally. You can continue later.')
  } catch {
    showNotice('error', 'Save failed', 'Could not save draft to local storage.')
  } finally {
    saving.value = false
  }
}

const onSubmit = async () => {
  const error = validate()
  if (error) {
    showNotice('error', 'Validation error', error)
    return
  }

  submitting.value = true
  try {
    // 预留：POST /api/migration-intake/
    await new Promise((resolve) => setTimeout(resolve, 600))
    localStorage.removeItem(DRAFT_KEY)
    showNotice(
      'success',
      'Submitted successfully',
      'Your migration request has been recorded and will sync to the Project Attributes Database.'
    )
  } catch {
    showNotice('error', 'Submit failed', 'Unable to submit the form. Please try again.')
  } finally {
    submitting.value = false
  }
}

onMounted(loadDraft)
</script>

<style scoped>
.intake-page {
  background: #fff;
  min-height: 100vh;
  overflow-x: clip;
  position: relative;
}

.page-content {
  margin: 0 auto;
  max-width: 920px;
  padding: 40px 24px 72px;
  position: relative;
  z-index: 1;
}

.back-link {
  display: inline-block;
  margin-bottom: 20px;
  text-decoration: none;
}

.header-main {
  margin-bottom: 28px;
}

.page-title {
  color: var(--mds_brand_appearance_neutral_default_text-color, #161616);
  font-family: 'Maersk Headline', 'Maersk Text', sans-serif;
  font-size: clamp(28px, 4vw, 40px);
  font-weight: 700;
  letter-spacing: -0.02em;
  line-height: 1.15;
  margin: 12px 0 10px;
}

.page-subtitle {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  font-size: 15px;
  line-height: 1.6;
  margin: 0;
  max-width: 680px;
}

.flow-strip {
  align-items: center;
  background: rgba(255, 255, 255, 0.75);
  border: 1px solid rgba(22, 22, 22, 0.08);
  border-radius: 14px;
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  padding: 16px 20px;
}

.flow-step {
  align-items: center;
  color: var(--mds_brand_appearance_neutral_weak_text-color, #9aa0a6);
  display: flex;
  gap: 10px;
}

.flow-step--active {
  color: var(--mds_brand_appearance_neutral_default_text-color, #161616);
}

.flow-icon {
  align-items: center;
  background: rgba(0, 119, 184, 0.08);
  border-radius: 10px;
  color: #0077b8;
  display: inline-flex;
  height: 36px;
  justify-content: center;
  width: 36px;
}

.flow-step--active .flow-icon {
  background: rgba(0, 119, 184, 0.14);
}

.flow-label {
  font-size: 13px;
  font-weight: 600;
}

.flow-arrow {
  color: rgba(22, 22, 22, 0.25);
  flex-shrink: 0;
}

.intake-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
  margin-top: 32px;
}

.form-section {
  animation: fade-up 0.45s ease both;
  background: #fff;
  border: 1px solid rgba(22, 22, 22, 0.08);
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(22, 22, 22, 0.04);
  overflow: visible;
  position: relative;
  z-index: 1;
}

.form-section--elevated {
  z-index: 200;
}

.form-section--elevated .section-body,
.form-section--elevated .product-field,
.form-section--elevated .field-row {
  overflow: visible;
}

.form-section::before {
  background: var(--section-accent, #0077b8);
  content: '';
  height: 3px;
  left: 0;
  position: absolute;
  top: 0;
  width: 100%;
}

.section-head {
  align-items: flex-start;
  border-bottom: 1px solid rgba(22, 22, 22, 0.06);
  display: flex;
  gap: 16px;
  padding: 22px 24px 18px;
}

.section-icon {
  align-items: center;
  background: color-mix(in srgb, var(--section-accent) 12%, white);
  border-radius: 12px;
  color: var(--section-accent);
  display: inline-flex;
  flex-shrink: 0;
  height: 44px;
  justify-content: center;
  width: 44px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 4px;
}

.section-title-row {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.section-desc {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  font-size: 13px;
  line-height: 1.5;
  margin: 0;
}

.section-body {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 22px 24px 24px;
}

.field-row {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.field-row--two {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.field-row--three {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.product-field {
  overflow: visible;
  position: relative;
  width: 100%;
}

.form-section--elevated mc-multi-select::part(popover-content),
.form-section--elevated mc-select::part(popover-content) {
  z-index: 300;
}

.form-footer {
  align-items: center;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.6) 0%, #fff 100%);
  border: 1px solid rgba(22, 22, 22, 0.08);
  border-radius: 16px;
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  justify-content: space-between;
  padding: 20px 24px;
}

.footer-target {
  align-items: center;
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  display: flex;
  font-size: 13px;
  gap: 8px;
}

.footer-target mc-icon {
  color: #0077b8;
}

.footer-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.form-notice {
  margin-top: 4px;
}

@keyframes fade-up {
  from {
    opacity: 0;
    transform: translateY(12px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 768px) {
  .page-content {
    padding: 24px 16px 48px;
  }

  .field-row,
  .field-row--two,
  .field-row--three {
    grid-template-columns: 1fr;
  }

  .flow-strip {
    flex-direction: column;
    align-items: flex-start;
  }

  .flow-arrow {
    display: none;
  }

  .form-footer {
    flex-direction: column;
    align-items: stretch;
  }

  .footer-actions {
    justify-content: stretch;
  }

  .footer-actions mc-button {
    width: 100%;
  }
}
</style>

<style>
/* MDS 下拉层需穿透 shadow DOM，且层级高于后续表单区块 */
mc-multi-select::part(popover-content),
mc-select::part(popover-content) {
  z-index: 10000;
}
</style>
