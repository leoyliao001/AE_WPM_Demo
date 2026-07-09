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

            <div class="field-row field-row--two">
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
            </div>

            <div v-if="form.region" class="field-row field-row--two area-strategy-row">
              <div class="area-field">
                <mc-checkbox-group
                  :key="`areas-${form.region}`"
                  legend="Area"
                  hint="Select one or more areas. Options are filtered by region."
                  orientation="vertical"
                  name="areas"
                  :value.prop="areaCheckboxValue"
                  @change="onAreasChange"
                >
                  <mc-checkbox
                    v-for="area in filteredAreas"
                    :key="area"
                    name="areas"
                    :value="area"
                    :label="area"
                  />
                </mc-checkbox-group>
              </div>

              <div class="location-strategy-field">
                <mc-checkbox-group
                  v-if="form.areas.length"
                  :key="`location-strategies-${form.areas.join('|')}`"
                  legend="Location Strategy"
                  hint="Filtered by selected areas. Each option maps to your area selection."
                  orientation="vertical"
                  name="locationStrategies"
                  :value.prop="locationStrategyCheckboxValue"
                  @change="onLocationStrategiesChange"
                >
                  <mc-checkbox
                    v-for="option in locationStrategyOptions"
                    :key="option.value"
                    name="locationStrategies"
                    :value="option.value"
                    :label="option.label"
                  />
                </mc-checkbox-group>
                <p v-else class="location-strategy-placeholder">
                  Select one or more areas to configure location strategy.
                </p>
              </div>
            </div>

            <div v-if="form.areas.length" class="country-panel">
              <div class="country-panel-head">
                <div>
                  <span class="country-panel-title">Country</span>
                  <p class="country-panel-desc">
                    Select one or more countries. Options are filtered by your area selection.
                  </p>
                </div>
                <mc-tag
                  v-if="form.countries.length"
                  appearance="info"
                  fit="small"
                  :label="`${form.countries.length} selected`"
                />
              </div>

              <mc-input
                label="Filter countries"
                hiddenlabel
                placeholder="Search countries..."
                :value="countryFilter"
                width="full-width"
                @input="onCountryFilterInput"
              />

              <mc-checkbox-group
                :key="`countries-${form.areas.join('|')}`"
                legend="Country"
                hiddenlegend
                orientation="vertical"
                name="countries"
                :value.prop="countryCheckboxValue"
                @change="onCountriesChange"
              >
                <mc-checkbox
                  v-for="country in visibleCountries"
                  :key="country"
                  name="countries"
                  :value="country"
                  :label="country"
                />
              </mc-checkbox-group>

              <p v-if="!visibleCountries.length" class="country-panel-empty">
                No countries match your search.
              </p>
            </div>

            <div v-if="form.locationStrategies.length" class="supporting-sites-panel">
              <div class="supporting-sites-head">
                <span class="supporting-sites-label">Supporting GSC Sites</span>
                <mc-tag
                  v-if="form.supportingGscSitesCustom"
                  appearance="warning"
                  fit="small"
                  label="Custom"
                />
              </div>

              <template v-if="!form.supportingGscSitesCustom">
                <p class="supporting-sites-hint">Default sites for selected areas. Select all that apply.</p>
                <mc-checkbox-group
                  :key="`default-sites-${activeAreas.join('|')}`"
                  legend="Supporting GSC Sites"
                  hiddenlegend
                  orientation="vertical"
                  name="supportingGscSites"
                  :value.prop="defaultSitesCheckboxValue"
                  @change="onDefaultSupportingSitesChange"
                >
                  <mc-checkbox
                    v-for="site in defaultSupportingSites"
                    :key="site"
                    name="supportingGscSites"
                    :value="site"
                    :label="site"
                  />
                </mc-checkbox-group>
              </template>

              <template v-else>
                <p class="supporting-sites-hint">
                  Custom selection:
                  {{ form.customSupportingGscSites.length ? form.customSupportingGscSites.join(', ') : 'None selected' }}
                </p>
                <p v-if="form.customSupportingJustification" class="custom-summary">
                  Justification provided.
                </p>
                <p v-if="customApprovalFileMeta.name" class="custom-summary">
                  Approval file: {{ customApprovalFileMeta.name }}
                </p>
              </template>

              <div class="supporting-sites-actions custom-sites-cta">
                <p class="custom-sites-cta-note">
                  Need a non-default site mix? Custom selection requires justification and approval.
                </p>
                <mc-button
                  v-if="!form.supportingGscSitesCustom"
                  class="custom-sites-cta-btn"
                  type="button"
                  appearance="secondary"
                  variant="filled"
                  fit="medium"
                  width="full-width"
                  label="Use custom supporting GSC sites"
                  icon="mi-pencil"
                  @click="openCustomSitesDialog"
                />
                <template v-else>
                  <mc-button
                    type="button"
                    appearance="neutral"
                    variant="outlined"
                    fit="small"
                    label="Edit custom selection"
                    @click="openCustomSitesDialog"
                  />
                  <mc-button
                    type="button"
                    appearance="neutral"
                    variant="plain"
                    fit="small"
                    label="Use defaults"
                    @click="resetToDefaultSupportingSites"
                  />
                </template>
              </div>
            </div>

            <mc-dialog
              :open="customSitesDialogOpen"
              heading="Custom Supporting GSC Sites"
              dimension="medium"
              showclosebutton
              @closing="onCustomDialogClosing"
            >
              <div class="custom-sites-dialog-body">
                <p class="custom-sites-dialog-desc">
                  Select supporting GSC sites, provide justification, and upload approval documentation
                  (email, Word, or image — max 4 MB).
                </p>

                <mc-checkbox-group
                  legend="Custom supporting GSC sites"
                  orientation="vertical"
                  name="customSupportingGscSites"
                  :value.prop="customSitesDialogSelection"
                  @change="onCustomSitesDialogSelectionChange"
                >
                  <mc-checkbox
                    v-for="site in customGscSiteOptions"
                    :key="site"
                    name="customSupportingGscSites"
                    :value="site"
                    :label="site"
                  />
                </mc-checkbox-group>

                <mc-textarea
                  label="Justification"
                  placeholder="Explain why custom supporting GSC sites are required..."
                  hint="Required when using custom supporting GSC sites."
                  rows="4"
                  width="full-width"
                  :value="customSitesDialogJustification"
                  :invalid="customDialogErrors.justification"
                  :errormessage="customDialogErrors.justification ? 'Justification is required.' : ''"
                  @input="onCustomJustificationInput"
                />

                <div class="approval-upload-field">
                  <label class="approval-upload-label">Approval attachment</label>
                  <input
                    ref="approvalFileInputRef"
                    class="approval-upload-input"
                    type="file"
                    :accept="approvalFileAccept"
                    @change="onApprovalFileChange"
                  />
                  <p class="approval-upload-hint">
                    Supported: email (.eml, .msg), Word (.doc, .docx), PDF, or images. Max 4 MB.
                  </p>
                  <p v-if="customSitesDialogFile" class="approval-upload-name">
                    Selected: {{ customSitesDialogFile.name }}
                    ({{ formatFileSize(customSitesDialogFile.size) }})
                  </p>
                  <p v-else-if="customApprovalFileMeta.name" class="approval-upload-name">
                    Current file: {{ customApprovalFileMeta.name }}
                    ({{ formatFileSize(customApprovalFileMeta.size) }})
                  </p>
                  <p v-if="customDialogErrors.file" class="approval-upload-error">
                    {{ customDialogErrors.file }}
                  </p>
                </div>

                <div class="custom-sites-dialog-footer">
                  <mc-button
                    type="button"
                    appearance="neutral"
                    variant="outlined"
                    fit="medium"
                    label="Cancel"
                    @click="closeCustomSitesDialog"
                  />
                  <mc-button
                    type="button"
                    appearance="primary"
                    variant="filled"
                    fit="medium"
                    label="Confirm"
                    @click="applyCustomSupportingSites"
                  />
                </div>
              </div>
            </mc-dialog>

            <mc-select
              ref="functionRef"
              label="Function"
              placeholder="Select function"
              hint="Select an activity function to filter available products."
              :value="form.function"
              width="full-width"
              @optionselected="onSelect('function', $event)"
              @opened="onDropdownOpened('project-details')"
              @closed="onDropdownClosed('project-details')"
            >
              <mc-option v-for="fn in functions" :key="fn" :value="fn">{{ fn }}</mc-option>
            </mc-select>

            <div class="product-field">
              <mc-input
                v-if="!form.function"
                label="Product"
                placeholder="Select function first"
                hint="Choose all products involved in this migration."
                width="full-width"
                disabled
              />

              <template v-else>
                <mc-input
                  v-if="filteredProducts.length > 8"
                  label="Filter products"
                  hiddenlabel
                  placeholder="Filter products..."
                  :value="productFilter"
                  width="full-width"
                  @input="onProductFilterInput"
                />

                <mc-checkbox-group
                  :key="`products-${form.function}`"
                  legend="Product"
                  hint="Choose all products involved in this migration."
                  orientation="vertical"
                  name="products"
                  :value.prop="productCheckboxValue"
                  @change="onProductsChange"
                >
                  <mc-checkbox
                    v-for="product in visibleProducts"
                    :key="product"
                    name="products"
                    :value="product"
                    :label="product"
                  />
                </mc-checkbox-group>
              </template>
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
            <div class="workforce-language-layout">
              <div class="language-field">
                <mc-input
                  label="Filter languages"
                  hiddenlabel
                  placeholder="Search languages..."
                  :value="languageFilter"
                  width="full-width"
                  @input="onLanguageFilterInput"
                />
                <mc-checkbox-group
                  legend="Language dependency"
                  hint="Select all languages required for this migration."
                  orientation="vertical"
                  name="languageDependencies"
                  :value.prop="languageCheckboxValue"
                  @change="onLanguageDependenciesChange"
                >
                  <mc-checkbox
                    v-for="lang in visibleLanguages"
                    :key="lang"
                    name="languageDependencies"
                    :value="lang"
                    :label="lang"
                  />
                </mc-checkbox-group>
                <p v-if="form.languageDependencies.length" class="language-selection-summary">
                  {{ form.languageDependencies.length }} language{{ form.languageDependencies.length === 1 ? '' : 's' }} selected
                </p>
              </div>

              <aside class="workforce-sizing-panel" aria-label="Workforce sizing">
                <div class="workforce-sizing-head">
                  <span class="workforce-sizing-title">Workforce sizing</span>
                  <p class="workforce-sizing-desc">FTE and job level counts. Values may change during scoping.</p>
                </div>

                <mc-input
                  ref="fteRef"
                  label="FTE number"
                  placeholder="e.g. 12"
                  inputmode="numeric"
                  pattern="[0-9]*"
                  maxlength="3"
                  :value="form.fteNumber"
                  :invalid="showWorkforceMismatchHint"
                  width="full-width"
                  @keydown="onNumericKeydown('fteNumber', $event)"
                  @beforeinput="onBeforeNumericInput('fteNumber', $event)"
                  @paste="onNumericPaste('fteNumber', $event)"
                  @compositionstart="blockNumericComposition"
                  @input="onNumericInput('fteNumber', $event)"
                />

                <div class="job-level-grid">
                  <mc-input
                    label="JL2"
                    placeholder="Count"
                    hint="Job Level 2"
                    inputmode="numeric"
                    pattern="[0-9]*"
                    maxlength="3"
                    :value="form.jl2"
                    :invalid="showWorkforceMismatchHint"
                    width="full-width"
                    @keydown="onNumericKeydown('jl2', $event)"
                    @beforeinput="onBeforeNumericInput('jl2', $event)"
                    @paste="onNumericPaste('jl2', $event)"
                    @compositionstart="blockNumericComposition"
                    @input="onNumericInput('jl2', $event)"
                  />
                  <mc-input
                    label="JL3"
                    placeholder="Count"
                    hint="Job Level 3"
                    inputmode="numeric"
                    pattern="[0-9]*"
                    maxlength="3"
                    :value="form.jl3"
                    :invalid="showWorkforceMismatchHint"
                    width="full-width"
                    @keydown="onNumericKeydown('jl3', $event)"
                    @beforeinput="onBeforeNumericInput('jl3', $event)"
                    @paste="onNumericPaste('jl3', $event)"
                    @compositionstart="blockNumericComposition"
                    @input="onNumericInput('jl3', $event)"
                  />
                  <mc-input
                    label="JL4"
                    placeholder="Count"
                    hint="Job Level 4"
                    inputmode="numeric"
                    pattern="[0-9]*"
                    maxlength="3"
                    :value="form.jl4"
                    :invalid="showWorkforceMismatchHint"
                    width="full-width"
                    @keydown="onNumericKeydown('jl4', $event)"
                    @beforeinput="onBeforeNumericInput('jl4', $event)"
                    @paste="onNumericPaste('jl4', $event)"
                    @compositionstart="blockNumericComposition"
                    @input="onNumericInput('jl4', $event)"
                  />
                </div>

                <div v-if="hasWorkforceInput" class="workforce-balance-tracker">
                  <span>FTE: <strong>{{ form.fteNumber || 0 }}</strong></span>
                  <span class="workforce-balance-tracker-sep">·</span>
                  <span>
                    JL2 + JL3 + JL4:
                    <strong>{{ jobLevelTotal }}</strong>
                    ({{ form.jl2 || 0 }} + {{ form.jl3 || 0 }} + {{ form.jl4 || 0 }})
                  </span>
                </div>

                <div
                  v-if="showWorkforceMismatchHint"
                  class="workforce-balance-alert workforce-balance-alert--error"
                  role="alert"
                  aria-live="polite"
                >
                  <mc-icon icon="mi-exclamation-triangle" size="20" />
                  <div>
                    <p class="workforce-balance-alert-title">Totals do not match</p>
                    <p class="workforce-balance-alert-body">
                      JL2 + JL3 + JL4 must equal FTE number. {{ workforceMismatchDetail }}
                    </p>
                  </div>
                </div>

                <div
                  v-else-if="showWorkforceBalancedHint"
                  class="workforce-balance-alert workforce-balance-alert--success"
                  role="status"
                  aria-live="polite"
                >
                  <mc-icon icon="mi-check-circle" size="20" />
                  <div>
                    <p class="workforce-balance-alert-title">Totals match</p>
                    <p class="workforce-balance-alert-body">
                      Job level counts add up to the FTE number.
                    </p>
                  </div>
                </div>
              </aside>
            </div>

            <mc-dialog
              :open="workforceMismatchDialogOpen"
              heading="Workforce totals do not match"
              dimension="small"
              showclosebutton
              @closing="onWorkforceMismatchDialogClosing"
            >
              <div class="workforce-mismatch-dialog-body">
                <p class="workforce-mismatch-dialog-desc">
                  JL2 + JL3 + JL4 must equal the FTE number before you can submit.
                </p>
                <ul class="workforce-mismatch-summary">
                  <li><strong>FTE number:</strong> {{ form.fteNumber || 0 }}</li>
                  <li>
                    <strong>JL2 + JL3 + JL4:</strong>
                    {{ jobLevelTotal }}
                    ({{ form.jl2 || 0 }} + {{ form.jl3 || 0 }} + {{ form.jl4 || 0 }})
                  </li>
                </ul>
              </div>

              <div slot="footer" class="workforce-mismatch-dialog-footer">
                <mc-button
                  type="button"
                  appearance="primary"
                  variant="filled"
                  fit="medium"
                  label="OK"
                  @click="closeWorkforceMismatchDialog"
                />
              </div>
            </mc-dialog>
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
              appearance="primary"
              variant="filled"
              fit="medium"
              label="Review and Submit"
              trailingicon="mi-arrow-right"
              @click="onReviewAndSubmit"
            />
          </div>
        </footer>

        <mc-dialog
          :open="validationDialogOpen"
          heading="Please complete required fields"
          dimension="medium"
          showclosebutton
          @closing="onValidationDialogClosing"
        >
          <div class="validation-dialog-body">
            <p class="validation-dialog-desc">
              The following required items are missing or invalid. Please complete them before submitting.
            </p>
            <ul class="validation-dialog-list">
              <li v-for="item in validationErrors" :key="item">{{ item }}</li>
            </ul>
          </div>

          <div slot="footer" class="validation-dialog-footer">
            <mc-button
              type="button"
              appearance="primary"
              variant="filled"
              fit="medium"
              label="OK"
              @click="closeValidationDialog"
            />
          </div>
        </mc-dialog>

        <mc-dialog
          :open="previewDialogOpen"
          heading="Review migration request"
          dimension="large"
          showclosebutton
          @closing="onPreviewDialogClosing"
        >
          <div v-if="submissionPreview" class="preview-dialog-shell">
            <div class="preview-dialog-body">
              <div class="preview-dialog-intro">
                <mc-tag appearance="info" fit="small" label="Preview" />
                <p>Please review all information below, then click Submit to confirm.</p>
              </div>

              <section
                v-for="section in previewSectionGroups"
                :key="section.id"
                class="preview-section"
              >
                <h3 class="preview-section-title">{{ section.title }}</h3>
                <dl class="preview-grid">
                  <div
                    v-for="item in section.items"
                    :key="`${section.id}-${item.label}`"
                    class="preview-row"
                    :class="{ 'preview-row--multiline': item.multiline }"
                  >
                    <dt class="preview-label">{{ item.label }}</dt>
                    <dd class="preview-value">{{ item.value }}</dd>
                  </div>
                </dl>
              </section>
            </div>

            <div class="preview-dialog-footer">
              <mc-button
                type="button"
                appearance="neutral"
                variant="outlined"
                fit="medium"
                label="Back to edit"
                @click="closePreviewDialog"
              />
              <mc-button
                type="button"
                appearance="primary"
                variant="filled"
                fit="medium"
                label="Submit"
                trailingicon="mi-arrow-right"
                :loading="submitting"
                @click="onSubmit"
              />
            </div>
          </div>
        </mc-dialog>

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
import { computed, onMounted, reactive, ref } from 'vue'
import axios from 'axios'
import { getAreasForRegion, regions } from '../data/regionAreaMapping'
import {
  buildAreaCountryPairs,
  filterValidCountries,
  getCountriesForAreas
} from '../data/areaCountryMapping'
import {
  APPROVAL_FILE_ACCEPT,
  MAX_APPROVAL_FILE_BYTES,
  buildAreaLocationPairs,
  customGscSiteOptions,
  filterAreasByLocationStrategies,
  filterValidLocationStrategies,
  getAreasForLocationStrategy,
  getDefaultSupportingSitesForAreasAndStrategies,
  getLocationStrategiesForAreas
} from '../data/areaLocationStrategyMapping'
import { languageOptions } from '../data/languageOptions'
import { functions, getProductsForFunction } from '../data/functionProductMapping'
import {
  buildSubmissionPreview,
  collectValidationErrors,
  previewSections
} from '../utils/migrationIntakeSubmit'
import '@maersk-global/mds-components-core/mc-button'
import '@maersk-global/mds-components-core/mc-icon'
import '@maersk-global/mds-components-core/mc-tag'
import '@maersk-global/mds-components-core/mc-input'
import '@maersk-global/mds-components-core/mc-select'
import '@maersk-global/mds-components-core/mc-option'
import '@maersk-global/mds-components-core/mc-checkbox'
import '@maersk-global/mds-components-core/mc-checkbox-group'
import '@maersk-global/mds-components-core/mc-textarea'
import '@maersk-global/mds-components-core/mc-notification'
import '@maersk-global/mds-components-core/mc-dialog'

const DRAFT_KEY = 'ae-wpm-migration-intake-draft'

const migrationTypes = [
  { value: '1:1-transfer', label: '1:1 Transfer' },
  { value: 'new-additional', label: 'New/Additional work, tasks or activities' }
]

const filteredAreas = computed(() => getAreasForRegion(form.region))
const filteredProducts = computed(() => getProductsForFunction(form.function))
const productCheckboxValue = computed(() => [...form.products])
const productFilter = ref('')
const languageFilter = ref('')
const countryFilter = ref('')
const languageCheckboxValue = computed(() => [...form.languageDependencies])
const countryCheckboxValue = computed(() => [...form.countries])

const visibleCountries = computed(() => {
  const query = countryFilter.value.trim().toLowerCase()
  const options = getCountriesForAreas(form.areas)
  if (!query) return options
  return options.filter((country) => country.toLowerCase().includes(query))
})

const visibleLanguages = computed(() => {
  const query = languageFilter.value.trim().toLowerCase()
  if (!query) return languageOptions
  return languageOptions.filter((lang) => lang.toLowerCase().includes(query))
})

const visibleProducts = computed(() => {
  const query = productFilter.value.trim().toLowerCase()
  if (!query) return filteredProducts.value
  return filteredProducts.value.filter((product) => product.toLowerCase().includes(query))
})

const locationStrategiesForAreas = computed(() => getLocationStrategiesForAreas(form.areas))
const activeAreas = computed(() =>
  filterAreasByLocationStrategies(form.areas, form.locationStrategies)
)
const defaultSupportingSites = computed(() =>
  getDefaultSupportingSitesForAreasAndStrategies(form.areas, form.locationStrategies)
)
const locationStrategyOptions = computed(() =>
  locationStrategiesForAreas.value.map((strategy) => {
    const areas = getAreasForLocationStrategy(form.areas, strategy)
    return {
      value: strategy,
      label: areas.length ? `${strategy} (${areas.join(', ')})` : strategy
    }
  })
)
const areaCheckboxValue = computed(() => [...form.areas])
const locationStrategyCheckboxValue = computed(() => [...form.locationStrategies])
const defaultSitesCheckboxValue = computed(() =>
  form.supportingGscSitesCustom ? [] : [...form.defaultSupportingGscSites]
)

const jobLevelTotal = computed(
  () => Number(form.jl2 || 0) + Number(form.jl3 || 0) + Number(form.jl4 || 0)
)

const hasWorkforceInput = computed(() =>
  Boolean(form.fteNumber || form.jl2 || form.jl3 || form.jl4)
)

const isWorkforceBalanced = computed(
  () => Number(form.fteNumber || 0) === jobLevelTotal.value
)

const showWorkforceMismatchHint = computed(
  () => hasWorkforceInput.value && !isWorkforceBalanced.value
)

const showWorkforceBalancedHint = computed(
  () => Boolean(form.fteNumber) && isWorkforceBalanced.value
)

const workforceMismatchDetail = computed(() => {
  const fte = Number(form.fteNumber || 0)
  const total = jobLevelTotal.value
  const diff = Math.abs(fte - total)

  if (total > fte) {
    return `Job level total exceeds FTE number by ${diff}.`
  }
  if (total < fte) {
    return `Job level total is ${diff} less than FTE number.`
  }
  return ''
})

const previewSectionGroups = computed(() =>
  submissionPreview.value ? previewSections(submissionPreview.value) : []
)

const approvalFileAccept = APPROVAL_FILE_ACCEPT
const customSitesDialogOpen = ref(false)
const customSitesDialogSelection = ref([])
const customSitesDialogJustification = ref('')
const customSitesDialogFile = ref(null)
const approvalFileInputRef = ref(null)
const customDialogErrors = reactive({ justification: false, file: '' })
const customApprovalFileMeta = reactive({ name: '', size: 0, type: '' })
const workforceMismatchDialogOpen = ref(false)
const validationDialogOpen = ref(false)
const validationErrors = ref([])
const previewDialogOpen = ref(false)
const submissionPreview = ref(null)

const form = reactive({
  projectName: '',
  migrationType: '',
  region: '',
  areas: [],
  countries: [],
  locationStrategies: [],
  defaultSupportingGscSites: [],
  customSupportingGscSites: [],
  supportingGscSitesCustom: false,
  customSupportingJustification: '',
  products: [],
  function: '',
  proposedScope: '',
  languageDependencies: [],
  fteNumber: '',
  jl2: '',
  jl3: '',
  jl4: '',
  risks: ''
})

const elevatedSection = ref(null)
const openDropdownCount = ref(0)
const submitting = ref(false)
const notice = reactive({ type: 'success', title: '', message: '' })

const readEventValue = (event) => {
  const target = event?.target
  return target?.value ?? event?.detail?.value ?? ''
}

const MAX_WORKFORCE_DIGITS = 3

const NUMERIC_ALLOWED_KEYS = new Set([
  'Backspace',
  'Delete',
  'Tab',
  'Escape',
  'Enter',
  'ArrowLeft',
  'ArrowRight',
  'ArrowUp',
  'ArrowDown',
  'Home',
  'End'
])

const sanitizeNumericInput = (value) =>
  String(value ?? '')
    .replace(/\D/g, '')
    .slice(0, MAX_WORKFORCE_DIGITS)

const onNumericKeydown = (field, event) => {
  if (event.ctrlKey || event.metaKey || event.altKey) return

  if (NUMERIC_ALLOWED_KEYS.has(event.key)) return

  if (/^\d$/.test(event.key)) {
    if (form[field].length >= MAX_WORKFORCE_DIGITS) {
      event.preventDefault()
    }
    return
  }

  event.preventDefault()
}

const onBeforeNumericInput = (field, event) => {
  const inputType = event.inputType ?? ''

  if (inputType.startsWith('delete') || inputType === 'historyUndo' || inputType === 'historyRedo') {
    return
  }

  if (inputType === 'insertFromPaste') {
    event.preventDefault()
    return
  }

  const data = event.data ?? ''
  if (!data) return

  if (!/^\d+$/.test(data)) {
    event.preventDefault()
    return
  }

  if (form[field].length + data.length > MAX_WORKFORCE_DIGITS) {
    event.preventDefault()
  }
}

const getInputElement = (event) => {
  const path = event.composedPath?.() ?? []
  for (const node of path) {
    if (node instanceof HTMLInputElement) return node
  }
  return null
}

const onNumericPaste = (field, event) => {
  event.preventDefault()
  const pasted = sanitizeNumericInput(event.clipboardData?.getData('text') ?? '')
  if (!pasted) return

  const input = getInputElement(event)
  if (input && input.selectionStart != null && input.selectionEnd != null) {
    const value = form[field]
    const next = value.slice(0, input.selectionStart) + pasted + value.slice(input.selectionEnd)
    form[field] = sanitizeNumericInput(next)
    return
  }

  const remaining = MAX_WORKFORCE_DIGITS - form[field].length
  if (remaining <= 0) return

  form[field] = `${form[field]}${pasted}`.slice(0, MAX_WORKFORCE_DIGITS)
}

const blockNumericComposition = (event) => {
  event.preventDefault()
}

const onTextInput = (field, event) => {
  form[field] = readEventValue(event)
}

const onNumericInput = (field, event) => {
  form[field] = sanitizeNumericInput(readEventValue(event))
}

const closeWorkforceMismatchDialog = () => {
  workforceMismatchDialogOpen.value = false
}

const onWorkforceMismatchDialogClosing = () => {
  workforceMismatchDialogOpen.value = false
}

const closeValidationDialog = () => {
  validationDialogOpen.value = false
}

const onValidationDialogClosing = () => {
  validationDialogOpen.value = false
}

const closePreviewDialog = () => {
  if (submitting.value) return
  previewDialogOpen.value = false
}

const onPreviewDialogClosing = () => {
  if (submitting.value) return
  previewDialogOpen.value = false
}

const openSubmissionPreview = () => {
  submissionPreview.value = buildSubmissionPreview({
    form,
    customApprovalFileMeta,
    migrationTypes
  })
  logSupportingGscSitesState('review-preview')
  console.log('[Migration Intake] Submission preview payload', submissionPreview.value)
  previewDialogOpen.value = true
}

const logSupportingGscSitesState = (source) => {
  console.log(`[Migration Intake] Supporting GSC Sites (${source})`, {
    mode: form.supportingGscSitesCustom ? 'custom' : 'default',
    defaultSupportingGscSites: [...form.defaultSupportingGscSites],
    customSupportingGscSites: [...form.customSupportingGscSites]
  })
}

const resetSupportingSitesState = () => {
  form.locationStrategies = []
  form.countries = []
  form.defaultSupportingGscSites = []
  form.customSupportingGscSites = []
  form.supportingGscSitesCustom = false
  form.customSupportingJustification = ''
  customApprovalFileMeta.name = ''
  customApprovalFileMeta.size = 0
  customApprovalFileMeta.type = ''
}

const syncCountriesFromAreas = () => {
  form.countries = filterValidCountries(form.areas, form.countries)
  countryFilter.value = ''
}

const syncDefaultSupportingSites = () => {
  if (form.supportingGscSitesCustom) return

  const defaultSites = getDefaultSupportingSitesForAreasAndStrategies(
    form.areas,
    form.locationStrategies
  )
  form.defaultSupportingGscSites = form.defaultSupportingGscSites.filter((site) =>
    defaultSites.includes(site)
  )
  if (!form.defaultSupportingGscSites.length && defaultSites.length) {
    form.defaultSupportingGscSites = [...defaultSites]
  }
  form.customSupportingGscSites = []
  logSupportingGscSitesState('sync-default')
}

const syncLocationStrategiesFromAreas = () => {
  const validStrategies = getLocationStrategiesForAreas(form.areas)
  form.locationStrategies = filterValidLocationStrategies(form.areas, form.locationStrategies)
  for (const strategy of validStrategies) {
    if (!form.locationStrategies.includes(strategy)) {
      form.locationStrategies.push(strategy)
    }
  }
}

const formatFileSize = (bytes) => {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
}

const validateApprovalFile = (file) => {
  if (!file) return 'Approval attachment is required.'
  if (file.size > MAX_APPROVAL_FILE_BYTES) {
    return `File must not exceed ${formatFileSize(MAX_APPROVAL_FILE_BYTES)}.`
  }
  return ''
}

const onSelect = (field, event) => {
  const value = event?.detail?.value ?? readEventValue(event)
  if (field === 'region') {
    form.region = value
    const validAreas = getAreasForRegion(value)
    form.areas = form.areas.filter((area) => validAreas.includes(area))
    if (!form.areas.length) {
      resetSupportingSitesState()
    } else {
      syncLocationStrategiesFromAreas()
      syncCountriesFromAreas()
      if (!form.supportingGscSitesCustom) {
        syncDefaultSupportingSites()
      }
    }
    return
  }
  if (field === 'function') {
    form.function = value
    const validProducts = getProductsForFunction(value)
    form.products = form.products.filter((p) => validProducts.includes(p))
    productFilter.value = ''
    return
  }
  form[field] = value
}

const onAreasChange = (event) => {
  const value = event?.detail ?? event?.currentTarget?.value ?? event?.target?.value
  form.areas = Array.isArray(value) ? [...value] : []
  if (!form.areas.length) {
    resetSupportingSitesState()
    return
  }
  syncLocationStrategiesFromAreas()
  syncCountriesFromAreas()
  if (!form.supportingGscSitesCustom) {
    syncDefaultSupportingSites()
  }
}

const onLocationStrategiesChange = (event) => {
  const value = event?.detail ?? event?.currentTarget?.value ?? event?.target?.value
  const selected = Array.isArray(value) ? [...value] : []
  form.locationStrategies = filterValidLocationStrategies(form.areas, selected)
  form.areas = filterAreasByLocationStrategies(form.areas, form.locationStrategies)
  syncCountriesFromAreas()
  if (!form.locationStrategies.length || !form.areas.length) {
    form.defaultSupportingGscSites = []
    form.customSupportingGscSites = []
    form.supportingGscSitesCustom = false
    if (!form.areas.length) {
      form.locationStrategies = []
      form.countries = []
    }
    return
  }
  if (!form.supportingGscSitesCustom) {
    syncDefaultSupportingSites()
  }
}

const onProductFilterInput = (event) => {
  productFilter.value = readEventValue(event)
}

const onLanguageFilterInput = (event) => {
  languageFilter.value = readEventValue(event)
}

const onCountryFilterInput = (event) => {
  countryFilter.value = readEventValue(event)
}

const onCountriesChange = (event) => {
  const value = event?.detail ?? event?.currentTarget?.value ?? event?.target?.value
  form.countries = filterValidCountries(
    form.areas,
    Array.isArray(value) ? [...value] : []
  )
}

const onLanguageDependenciesChange = (event) => {
  const value = event?.detail ?? event?.currentTarget?.value ?? event?.target?.value
  form.languageDependencies = Array.isArray(value) ? [...value] : []
}

const onProductsChange = (event) => {
  const value = event?.detail ?? event?.currentTarget?.value ?? event?.target?.value
  form.products = Array.isArray(value) ? [...value] : []
}

const onDefaultSupportingSitesChange = (event) => {
  if (form.supportingGscSitesCustom) return
  const value = event?.detail ?? event?.currentTarget?.value ?? event?.target?.value
  form.defaultSupportingGscSites = Array.isArray(value) ? [...value] : []
  form.customSupportingGscSites = []
  logSupportingGscSitesState('default-change')
}

const openCustomSitesDialog = () => {
  customSitesDialogSelection.value = form.supportingGscSitesCustom
    ? [...form.customSupportingGscSites]
    : []
  customSitesDialogJustification.value = form.customSupportingJustification
  customSitesDialogFile.value = null
  customDialogErrors.justification = false
  customDialogErrors.file = ''
  if (approvalFileInputRef.value) {
    approvalFileInputRef.value.value = ''
  }
  customSitesDialogOpen.value = true
}

const closeCustomSitesDialog = () => {
  customSitesDialogOpen.value = false
}

const onCustomDialogClosing = () => {
  customSitesDialogOpen.value = false
}

const onCustomSitesDialogSelectionChange = (event) => {
  const value = event?.detail ?? event?.currentTarget?.value ?? event?.target?.value
  customSitesDialogSelection.value = Array.isArray(value) ? [...value] : []
}

const onCustomJustificationInput = (event) => {
  customSitesDialogJustification.value = readEventValue(event)
  if (customSitesDialogJustification.value.trim()) {
    customDialogErrors.justification = false
  }
}

const onApprovalFileChange = (event) => {
  const file = event?.target?.files?.[0] ?? null
  customSitesDialogFile.value = file
  customDialogErrors.file = file ? validateApprovalFile(file) : ''
}

const applyCustomSupportingSites = () => {
  const justification = customSitesDialogJustification.value.trim()
  customDialogErrors.justification = !justification

  const hasExistingFile = Boolean(customApprovalFileMeta.name)
  const fileError = customSitesDialogFile.value
    ? validateApprovalFile(customSitesDialogFile.value)
    : hasExistingFile
      ? ''
      : 'Approval attachment is required.'

  if (!customSitesDialogSelection.value.length) {
    customDialogErrors.file = fileError || 'Select at least one supporting GSC site.'
  } else {
    customDialogErrors.file = fileError
  }

  if (
    customDialogErrors.justification ||
    customDialogErrors.file ||
    !customSitesDialogSelection.value.length
  ) {
    return
  }

  form.supportingGscSitesCustom = true
  form.customSupportingGscSites = [...customSitesDialogSelection.value]
  form.defaultSupportingGscSites = []
  form.customSupportingJustification = justification
  if (customSitesDialogFile.value) {
    customApprovalFileMeta.name = customSitesDialogFile.value.name
    customApprovalFileMeta.size = customSitesDialogFile.value.size
    customApprovalFileMeta.type = customSitesDialogFile.value.type
  }
  customSitesDialogOpen.value = false
  logSupportingGscSitesState('custom-confirm')
}

const resetToDefaultSupportingSites = () => {
  form.supportingGscSitesCustom = false
  form.customSupportingGscSites = []
  form.customSupportingJustification = ''
  customApprovalFileMeta.name = ''
  customApprovalFileMeta.size = 0
  customApprovalFileMeta.type = ''
  form.defaultSupportingGscSites = [
    ...getDefaultSupportingSitesForAreasAndStrategies(form.areas, form.locationStrategies)
  ]
  logSupportingGscSitesState('reset-to-default')
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

const collectForm = () => ({
  ...form,
  products: [...form.products],
  languageDependencies: [...form.languageDependencies],
  areas: [...form.areas],
  countries: [...form.countries],
  locationStrategies: [...form.locationStrategies],
  areaLocationPairs: buildAreaLocationPairs(form.areas, form.locationStrategies),
  areaCountryPairs: buildAreaCountryPairs(form.areas, form.countries),
  defaultSupportingGscSites: [...form.defaultSupportingGscSites],
  customSupportingGscSites: [...form.customSupportingGscSites],
  customApprovalFile: customApprovalFileMeta.name
    ? { ...customApprovalFileMeta }
    : null
})

const loadDraft = () => {
  try {
    const raw = localStorage.getItem(DRAFT_KEY)
    if (!raw) return
    const saved = JSON.parse(raw)
    Object.assign(form, {
      projectName: saved.projectName ?? '',
      migrationType: saved.migrationType ?? '',
      region: regions.includes(saved.region) ? saved.region : '',
      areas: [],
      countries: [],
      locationStrategies: [],
      defaultSupportingGscSites: [],
      customSupportingGscSites: [],
      supportingGscSitesCustom: false,
      customSupportingJustification: '',
      products: [],
      function: functions.includes(saved.function) ? saved.function : '',
      proposedScope: saved.proposedScope ?? '',
      languageDependencies: [],
      fteNumber: sanitizeNumericInput(saved.fteNumber ?? ''),
      jl2: sanitizeNumericInput(saved.jl2 ?? ''),
      jl3: sanitizeNumericInput(saved.jl3 ?? ''),
      jl4: sanitizeNumericInput(saved.jl4 ?? ''),
      risks: saved.risks ?? ''
    })
    customApprovalFileMeta.name = ''
    customApprovalFileMeta.size = 0
    customApprovalFileMeta.type = ''
    if (form.region) {
      const validAreas = getAreasForRegion(form.region)
      const savedAreas = Array.isArray(saved.areas)
        ? saved.areas
        : saved.area
          ? [saved.area]
          : []
      form.areas = savedAreas.filter((area) => validAreas.includes(area))
      const savedCountries = Array.isArray(saved.countries) ? saved.countries : []
      form.countries = filterValidCountries(form.areas, savedCountries)
    }
    if (form.areas.length) {
      const validStrategies = getLocationStrategiesForAreas(form.areas)
      const savedStrategies = Array.isArray(saved.locationStrategies)
        ? saved.locationStrategies
        : saved.locationStrategy
          ? [saved.locationStrategy]
          : []
      form.locationStrategies = savedStrategies.filter((strategy) => validStrategies.includes(strategy))
      if (!form.locationStrategies.length) {
        form.locationStrategies = [...validStrategies]
      }
      const defaultSites = getDefaultSupportingSitesForAreasAndStrategies(
        form.areas,
        form.locationStrategies
      )
      const savedDefaultSites = Array.isArray(saved.defaultSupportingGscSites)
        ? saved.defaultSupportingGscSites
        : []
      const savedCustomSites = Array.isArray(saved.customSupportingGscSites)
        ? saved.customSupportingGscSites
        : []
      const legacySites = Array.isArray(saved.supportingGscSites) ? saved.supportingGscSites : []
      form.supportingGscSitesCustom = Boolean(saved.supportingGscSitesCustom)
      form.customSupportingJustification = saved.customSupportingJustification ?? ''
      if (form.supportingGscSitesCustom) {
        form.customSupportingGscSites = savedCustomSites.length ? savedCustomSites : legacySites
        form.defaultSupportingGscSites = []
        if (saved.customApprovalFile?.name) {
          customApprovalFileMeta.name = saved.customApprovalFile.name
          customApprovalFileMeta.size = saved.customApprovalFile.size ?? 0
          customApprovalFileMeta.type = saved.customApprovalFile.type ?? ''
        }
      } else {
        form.customSupportingGscSites = []
        form.defaultSupportingGscSites = savedDefaultSites.length
          ? savedDefaultSites.filter((site) => defaultSites.includes(site))
          : legacySites.filter((site) => defaultSites.includes(site))
        if (!form.defaultSupportingGscSites.length) {
          form.defaultSupportingGscSites = [...defaultSites]
        }
      }
      logSupportingGscSitesState('load-draft')
    }
    if (form.function) {
      const validProducts = getProductsForFunction(form.function)
      const savedProducts = Array.isArray(saved.products) ? saved.products : []
      form.products = savedProducts.filter((p) => validProducts.includes(p))
    }
    const savedLanguages = Array.isArray(saved.languageDependencies)
      ? saved.languageDependencies
      : saved.languageDependency
        ? [saved.languageDependency]
        : []
    form.languageDependencies = savedLanguages.filter((lang) => languageOptions.includes(lang))
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

const validateForm = () =>
  collectValidationErrors({
    form,
    customApprovalFileMeta,
    isWorkforceBalanced: isWorkforceBalanced.value
  })

const onReviewAndSubmit = () => {
  clearNotice()
  const missing = validateForm()
  if (missing.length) {
    validationErrors.value = missing
    validationDialogOpen.value = true
    return
  }

  openSubmissionPreview()
}

const onSubmit = async () => {
  if (!submissionPreview.value) return

  logSupportingGscSitesState('submit')
  console.log('[Migration Intake] Submit payload', submissionPreview.value)

  submitting.value = true
  try {
    const { data } = await axios.post('/api/migration-intake/submit/', submissionPreview.value)
    localStorage.removeItem(DRAFT_KEY)
    previewDialogOpen.value = false
    showNotice(
      'success',
      'Submitted successfully',
      data.message ??
        `Migration request ${submissionPreview.value.migrationRequestId} has been saved to the database.`
    )
  } catch (error) {
    const message =
      error?.response?.data?.error ??
      'Unable to submit the request. Please try again.'
    showNotice('error', 'Submit failed', message)
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

.area-strategy-row {
  align-items: start;
}

.country-panel {
  background: rgba(0, 119, 184, 0.03);
  border: 1px solid rgba(22, 22, 22, 0.08);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px 18px;
}

.country-panel-head {
  align-items: flex-start;
  display: flex;
  gap: 12px;
  justify-content: space-between;
}

.country-panel-title {
  color: var(--mds_brand_appearance_neutral_default_text-color, #161616);
  display: block;
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 4px;
}

.country-panel-desc {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  font-size: 12px;
  line-height: 1.5;
  margin: 0;
}

.country-panel mc-checkbox-group::part(fieldset-container) {
  border: 1px solid rgba(22, 22, 22, 0.08);
  border-radius: 12px;
  max-height: 220px;
  overflow-y: auto;
  padding: 8px 12px;
}

.country-panel-empty {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  font-size: 13px;
  margin: 0;
  text-align: center;
}

.location-strategy-field {
  display: flex;
  flex-direction: column;
  gap: 10px;
  width: 100%;
}

.location-strategy-placeholder {
  border: 1px dashed rgba(22, 22, 22, 0.12);
  border-radius: 12px;
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  font-size: 13px;
  line-height: 1.5;
  margin: 28px 0 0;
  padding: 16px;
}

.supporting-sites-panel {
  background: rgba(0, 119, 184, 0.04);
  border: 1px solid rgba(22, 22, 22, 0.08);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 4px;
  padding: 16px 18px;
  width: 100%;
}

.supporting-sites-head {
  align-items: center;
  display: flex;
  gap: 8px;
  justify-content: space-between;
}

.supporting-sites-label {
  color: var(--mds_brand_appearance_neutral_default_text-color, #161616);
  font-size: 14px;
  font-weight: 600;
}

.supporting-sites-hint {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  font-size: 12px;
  line-height: 1.5;
  margin: 0;
}

.custom-summary {
  color: var(--mds_brand_appearance_neutral_default_text-color, #161616);
  font-size: 13px;
  margin: 0;
}

.supporting-sites-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 4px;
  padding-top: 12px;
  border-top: 1px dashed rgba(0, 119, 184, 0.25);
}

.custom-sites-cta {
  background: linear-gradient(180deg, rgba(243, 136, 14, 0.1) 0%, rgba(243, 136, 14, 0.04) 100%);
  border: 1px solid rgba(243, 136, 14, 0.35);
  border-radius: 10px;
  border-top: 1px solid rgba(243, 136, 14, 0.35);
  flex-direction: column;
  gap: 10px;
  margin-top: 8px;
  padding: 12px;
  width: 100%;
}

.custom-sites-cta-note {
  color: #9a5b00;
  font-size: 12px;
  line-height: 1.5;
  margin: 0;
}

.custom-sites-cta-btn {
  width: 100%;
}

.custom-sites-cta-btn::part(button) {
  background-color: #f3880e;
  border-color: #f3880e;
  color: #fff;
}

.custom-sites-cta-btn::part(button):hover {
  background-color: #d9770c;
  border-color: #d9770c;
}

.custom-sites-cta-btn::part(icon) {
  fill: #fff;
}

.supporting-sites-panel mc-checkbox-group::part(fieldset-container) {
  border: none;
  max-height: 200px;
  overflow-y: auto;
  padding: 0;
}

.custom-sites-dialog-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.custom-sites-dialog-desc {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  font-size: 14px;
  line-height: 1.5;
  margin: 0;
}

.custom-sites-dialog-footer {
  border-top: 1px solid rgba(22, 22, 22, 0.08);
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 8px;
  padding-top: 16px;
}

.approval-upload-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.approval-upload-label {
  color: var(--mds_brand_appearance_neutral_default_text-color, #161616);
  font-size: 14px;
  font-weight: 600;
}

.approval-upload-input {
  font-size: 13px;
}

.approval-upload-hint {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  font-size: 12px;
  margin: 0;
}

.approval-upload-name {
  color: var(--mds_brand_appearance_neutral_default_text-color, #161616);
  font-size: 13px;
  margin: 0;
}

.approval-upload-error {
  color: #c4000a;
  font-size: 12px;
  margin: 0;
}

.product-field {
  overflow: visible;
  position: relative;
  width: 100%;
}

.product-field mc-checkbox-group::part(fieldset-container) {
  border: 1px solid rgba(22, 22, 22, 0.08);
  border-radius: 12px;
  max-height: 280px;
  overflow-y: auto;
  padding: 8px 12px;
}

.workforce-language-layout {
  align-items: start;
  display: grid;
  gap: 20px;
  grid-template-columns: minmax(0, 1.25fr) minmax(260px, 0.75fr);
}

.language-field {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 0;
}

.language-selection-summary {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  font-size: 12px;
  line-height: 1.4;
  margin: 0;
}

.language-field mc-checkbox-group::part(fieldset-container) {
  border: 1px solid rgba(22, 22, 22, 0.08);
  border-radius: 12px;
  max-height: 240px;
  overflow-y: auto;
  padding: 8px 12px;
}

.workforce-sizing-panel {
  background: rgba(109, 170, 40, 0.06);
  border: 1px solid rgba(109, 170, 40, 0.18);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 16px 18px;
}

.workforce-sizing-head {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.workforce-sizing-title {
  color: var(--mds_brand_appearance_neutral_default_text-color, #161616);
  font-size: 14px;
  font-weight: 600;
}

.workforce-sizing-desc {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  font-size: 12px;
  line-height: 1.5;
  margin: 0;
}

.job-level-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.workforce-balance-tracker {
  background: rgba(22, 22, 22, 0.03);
  border-radius: 8px;
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  display: flex;
  flex-wrap: wrap;
  font-size: 12px;
  gap: 6px;
  line-height: 1.5;
  padding: 8px 10px;
}

.workforce-balance-tracker strong {
  color: var(--mds_brand_appearance_neutral_default_text-color, #161616);
}

.workforce-balance-tracker-sep {
  opacity: 0.5;
}

.workforce-balance-alert {
  align-items: flex-start;
  border-radius: 10px;
  display: flex;
  gap: 10px;
  padding: 10px 12px;
}

.workforce-balance-alert--error {
  background: rgba(196, 0, 10, 0.06);
  border: 1px solid rgba(196, 0, 10, 0.2);
  color: #9b0010;
}

.workforce-balance-alert--success {
  background: rgba(109, 170, 40, 0.1);
  border: 1px solid rgba(109, 170, 40, 0.25);
  color: #4a7a18;
}

.workforce-balance-alert-title {
  font-size: 13px;
  font-weight: 600;
  line-height: 1.4;
  margin: 0;
}

.workforce-balance-alert-body {
  font-size: 12px;
  line-height: 1.5;
  margin: 4px 0 0;
  opacity: 0.92;
}

.workforce-mismatch-dialog-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.workforce-mismatch-dialog-desc {
  color: var(--mds_brand_appearance_neutral_default_text-color, #161616);
  font-size: 14px;
  line-height: 1.5;
  margin: 0;
}

.workforce-mismatch-summary {
  background: rgba(243, 136, 14, 0.08);
  border: 1px solid rgba(243, 136, 14, 0.25);
  border-radius: 10px;
  color: var(--mds_brand_appearance_neutral_default_text-color, #161616);
  font-size: 14px;
  line-height: 1.6;
  list-style: none;
  margin: 0;
  padding: 12px 14px;
}

.workforce-mismatch-summary li + li {
  margin-top: 8px;
}

.workforce-mismatch-dialog-footer {
  display: flex;
  justify-content: flex-end;
}

.validation-dialog-body,
.preview-dialog-shell {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.preview-dialog-shell {
  max-height: min(75vh, 720px);
}

.preview-dialog-body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding-right: 4px;
}

.preview-dialog-footer {
  background: #fff;
  border-top: 1px solid rgba(22, 22, 22, 0.08);
  display: flex;
  flex-shrink: 0;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: flex-end;
  padding-top: 16px;
}

.validation-dialog-desc,
.preview-dialog-intro p {
  color: var(--mds_brand_appearance_neutral_default_text-color, #161616);
  font-size: 14px;
  line-height: 1.5;
  margin: 0;
}

.validation-dialog-list {
  background: rgba(196, 0, 10, 0.06);
  border: 1px solid rgba(196, 0, 10, 0.18);
  border-radius: 10px;
  color: #9b0010;
  font-size: 14px;
  line-height: 1.6;
  margin: 0;
  padding: 12px 14px 12px 28px;
}

.validation-dialog-footer {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: flex-end;
}

.preview-dialog-intro {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.preview-section + .preview-section {
  border-top: 1px solid rgba(22, 22, 22, 0.08);
  margin-top: 4px;
  padding-top: 16px;
}

.preview-section-title {
  color: var(--mds_brand_appearance_neutral_default_text-color, #161616);
  font-size: 15px;
  font-weight: 600;
  margin: 0 0 12px;
}

.preview-grid {
  display: grid;
  gap: 10px;
  margin: 0;
}

.preview-row {
  display: grid;
  gap: 4px 16px;
  grid-template-columns: minmax(140px, 220px) minmax(0, 1fr);
}

.preview-row--multiline .preview-value {
  white-space: pre-wrap;
}

.preview-label {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  font-size: 13px;
  font-weight: 500;
  margin: 0;
}

.preview-value {
  color: var(--mds_brand_appearance_neutral_default_text-color, #161616);
  font-size: 14px;
  line-height: 1.5;
  margin: 0;
  word-break: break-word;
}

@media (max-width: 768px) {
  .preview-row {
    grid-template-columns: 1fr;
  }
}

.area-field {
  display: flex;
  flex-direction: column;
  gap: 10px;
  width: 100%;
}

.area-field mc-checkbox-group::part(fieldset-container),
.location-strategy-field mc-checkbox-group::part(fieldset-container) {
  border: 1px solid rgba(22, 22, 22, 0.08);
  border-radius: 12px;
  max-height: 200px;
  overflow-y: auto;
  padding: 8px 12px;
}

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

  .workforce-language-layout {
    grid-template-columns: 1fr;
  }

  .job-level-grid {
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
mc-select::part(popover-content) {
  z-index: 10000;
}
</style>
