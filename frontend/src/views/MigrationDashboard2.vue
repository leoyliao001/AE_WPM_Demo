<template>
  <PageShell
    title="Migration Dashboard (test)"
    subtitle="KPI concepts adapted from the WPM Power BI report — using current intake data and project styling."
    tag="Dashboard v2"
    back-label="Back to Welcome"
    full-width
  >
    <mc-notification
      v-if="loadError"
      appearance="error"
      fit="medium"
      heading="Unable to load projects"
      :body="loadError"
    />

    <mc-notification
      v-else-if="!loading && !projects.length"
      appearance="info"
      fit="medium"
      heading="No submitted projects yet"
      body="Submit a migration intake form to populate this test dashboard."
    >
      <mc-button
        slot="actions"
        appearance="primary"
        variant="filled"
        fit="small"
        label="Go to Intake Form"
        trailingicon="mi-arrow-right"
        @click="router.push('/migration-intake')"
      />
    </mc-notification>

    <div v-else class="dashboard-canvas">
      <div class="dashboard-layout">
        <nav class="page-tabs" aria-label="Dashboard pages">
          <button
            v-for="page in pages"
            :key="page.id"
            type="button"
            class="page-tabs__btn"
            :class="{ 'page-tabs__btn--active': activePage === page.id }"
            @click="activePage = page.id"
          >
            {{ page.label }}
          </button>
        </nav>

        <p class="page-note">{{ activePageMeta.note }}</p>

        <div v-if="activePage === 'executive'" class="executive-year-picker">
          <label class="compact-year-select">
            <span>BPM year</span>
            <select :value="bpmYear" @change="onBpmYearChange">
              <option v-for="year in bpmYearOptions" :key="year" :value="year">{{ year }}</option>
            </select>
          </label>
        </div>

        <template v-if="activePage === 'project-health'">
          <section class="project-health-filters">
            <mc-multi-select
              ref="migrationTypeMultiEl"
              :key="'migration-ms-' + projectHealthMigrationTypeKey"
              listsearch
              label="Migration Type"
              :value.prop="projectHealthFilters.migrationType"
              @input="(e) => setMultiFilterFromEvent(projectHealthFilters.migrationType, e)"
              @optionselected="(e) => setMultiFilterFromEvent(projectHealthFilters.migrationType, e)">
              <mc-option v-for="option in projectHealthMigrationTypeOptions" :key="option" :value="String(option)">{{ option }}</mc-option>
            </mc-multi-select>

            <mc-multi-select
              ref="ownerMultiEl"
              :key="'owner-ms-' + projectHealthOwnerKey"
              listsearch
              label="MM Name"
              :value.prop="projectHealthFilters.owner"
              @input="(e) => setMultiFilterFromEvent(projectHealthFilters.owner, e)"
              @optionselected="(e) => setMultiFilterFromEvent(projectHealthFilters.owner, e)">
              <mc-option v-for="option in projectHealthOwnerOptions" :key="option" :value="String(option)">{{ option }}</mc-option>
            </mc-multi-select>

            <mc-multi-select
              ref="regionMultiEl"
              :key="'region-ms-' + projectHealthRegionKey"
              listsearch
              label="Region"
              :value.prop="projectHealthFilters.region"
              @input="(e) => setMultiFilterFromEvent(projectHealthFilters.region, e)"
              @optionselected="(e) => setMultiFilterFromEvent(projectHealthFilters.region, e)">
              <mc-option v-for="option in projectHealthRegionOptions" :key="option" :value="String(option)">{{ option }}</mc-option>
            </mc-multi-select>

            <mc-multi-select
              ref="productMultiEl"
              :key="'product-ms-' + projectHealthProductKey"
              listsearch
              label="Product"
              :value.prop="projectHealthFilters.product"
              @input="(e) => setMultiFilterFromEvent(projectHealthFilters.product, e)"
              @optionselected="(e) => setMultiFilterFromEvent(projectHealthFilters.product, e)">
              <mc-option v-for="option in projectHealthProductOptions" :key="option" :value="String(option)">{{ option }}</mc-option>
            </mc-multi-select>

            <mc-multi-select
              ref="gscSiteMultiEl"
              :key="'gscsite-ms-' + projectHealthGscSiteKey"
              listsearch
              label="GSC Site"
              :value.prop="projectHealthFilters.gscSite"
              @input="(e) => setMultiFilterFromEvent(projectHealthFilters.gscSite, e)"
              @optionselected="(e) => setMultiFilterFromEvent(projectHealthFilters.gscSite, e)">
              <mc-option v-for="option in projectHealthGscSiteOptions" :key="option" :value="String(option)">{{ option }}</mc-option>
            </mc-multi-select>

            <div class="project-health-filter">
              <label>Budget Status</label>
              <div class="multi-select multi-select--placeholder">
                <button type="button" class="multi-select__trigger" disabled>
                  <span>0 selected</span>
                  <span class="multi-select__chevron">⌄</span>
                </button>
              </div>
              <small class="placeholder-hint">Placeholder — data not yet exposed</small>
            </div>

            <div class="project-health-filter">
              <label>Business Case</label>
              <div class="multi-select multi-select--placeholder">
                <button type="button" class="multi-select__trigger" disabled>
                  <span>0 selected</span>
                  <span class="multi-select__chevron">⌄</span>
                </button>
              </div>
              <small class="placeholder-hint">Placeholder — data not yet exposed</small>
            </div>

            <div class="project-health-filter">
              <label>TG Status</label>
              <div class="multi-select multi-select--placeholder">
                <button type="button" class="multi-select__trigger" disabled>
                  <span>0 selected</span>
                  <span class="multi-select__chevron">⌄</span>
                </button>
              </div>
            </div>
          </section>

          <section class="kpi-row">
            <article class="kpi-card">
              <div class="kpi-card__head">
                <span class="kpi-card__label">Total Project</span>
                <span class="overview-panel__badge overview-panel__badge--flat">Overview</span>
              </div>
              <strong class="kpi-card__value">{{ formatWholeNumber(kpis.totalProjects) }}</strong>
              <span class="kpi-card__hint">From intake submission list</span>
              <div class="kpi-card__pills">
                <span class="kpi-pill kpi-pill--muted">{{ formatWholeNumber(kpis.totalProjects) }} projects</span>
                <span class="kpi-pill kpi-pill--accent">{{ formatWholeNumber(kpis.migratableFte) }} FTE</span>
              </div>
            </article>

            <article class="kpi-card">
              <div class="kpi-card__head">
                <span class="kpi-card__label">Migratable FTE</span>
                <span class="overview-panel__badge overview-panel__badge--flat">Intake</span>
              </div>
              <strong class="kpi-card__value">{{ formatWholeNumber(kpis.migratableFte) }}</strong>
              <span class="kpi-card__hint">From intake FTE</span>
              <div class="kpi-card__pills">
                <span class="kpi-pill kpi-pill--muted">{{ kpis.totalProjects }} projects</span>
                <span class="kpi-pill kpi-pill--accent">{{ formatWholeNumber(Math.round(kpis.migratableFte / (kpis.totalProjects || 1))) }} avg / project</span>
              </div>
            </article>

            <article class="kpi-card">
              <div class="kpi-card__head">
                <span class="kpi-card__label">Actuals</span>
                <span class="overview-panel__badge overview-panel__badge--flat">Proxy</span>
              </div>
              <strong class="kpi-card__value">{{ formatWholeNumber(kpis.actuals) }}</strong>
              <span class="kpi-card__hint">Current status proxy</span>
              <div class="kpi-card__pills">
                <span class="kpi-pill kpi-pill--muted">{{ formatWholeNumber(kpis.pipeline) }} in flight</span>
                <span class="kpi-pill kpi-pill--accent">{{ formatWholeNumber(kpis.actuals) }} FTE</span>
              </div>
            </article>

            <article class="kpi-card">
              <div class="kpi-card__head">
                <span class="kpi-card__label">FTE GAP</span>
                <span class="overview-panel__badge overview-panel__badge--flat">Gap</span>
              </div>
              <strong class="kpi-card__value">{{ formatWholeNumber(kpis.fteGap) }}</strong>
              <span class="kpi-card__hint">Migratable − Actuals</span>
              <div class="kpi-card__pills">
                <span class="kpi-pill kpi-pill--muted">{{ formatWholeNumber(kpis.fteGap) }} open</span>
                <span class="kpi-pill kpi-pill--accent">{{ formatWholeNumber(kpis.pipeline) }} pipeline</span>
              </div>
            </article>

            <article class="kpi-card">
              <div class="kpi-card__head">
                <span class="kpi-card__label">Completion %</span>
                <span class="overview-panel__badge overview-panel__badge--flat">Status</span>
              </div>
              <strong class="kpi-card__value">{{ `${kpis.completionPct}%` }}</strong>
              <span class="kpi-card__hint">Status weighted approximation</span>
              <div class="kpi-card__pills">
                <span class="kpi-pill kpi-pill--muted">{{ formatWholeNumber(kpis.actuals) }} actuals</span>
                <span class="kpi-pill kpi-pill--accent">{{ `${kpis.completionPct}%` }}</span>
              </div>
            </article>
          </section>

          <section class="split-grid">
            <article class="dash-card">
              <div class="dash-card__head">
                <h3>Project Status Overview by Tollgate</h3>
                <span class="dash-card__meta">Current project flow</span>
              </div>
              <div class="tg-stack">
                            <div v-for="item in tgBarItems" :key="item.label" class="tg-stack__row">
                              <span class="tg-stack__label">{{ item.label }}</span>
                              <div class="tg-stack__track">
                                <template v-for="seg in item.segments">
                                  <span
                                    class="tg-stack__segment"
                                    :style="{ width: `${seg.pct}%`, background: seg.color }"
                                    :title="`${seg.label}: ${seg.count}`"
                                    >
                                    <span v-if="seg.count" class="tg-stack__segment-label">{{ seg.count }}</span>
                                  </span>
                                </template>
                              </div>
                              <strong class="tg-stack__value">{{ item.total }}</strong>
                            </div>
                          </div>
            </article>

            <article class="dash-card">
              <div class="dash-card__head">
                <h3>Project Status by Migration Manager</h3>
                <span class="dash-card__meta">Proxy by requestor / ownership mapping</span>
              </div>
              <div class="table-shell">
                <table class="data-table">
                  <thead>
                    <tr>
                      <th>MM Name</th>
                      <th>Project Count</th>
                      <th>Migratable FTE</th>
                      <th>Actuals</th>
                      <th>FTE GAP</th>
                    </tr>
                  </thead>
                  <tbody>
                    <template v-for="row in requestorRows.slice(0, 20)" :key="row.key">
                      <tr class="manager-row">
                        <td>
                          <button class="expand-btn" @click.stop="toggleManager(row.key)">{{ isManagerExpanded(row.key) ? '−' : '+' }}</button>
                          {{ row.label }}
                        </td>
                        <td>{{ formatWholeNumber(row.projects) }}</td>
                        <td>{{ formatWholeNumber(row.migratable) }}</td>
                        <td>{{ formatWholeNumber(row.actuals) }}</td>
                        <td>{{ formatWholeNumber(row.gap) }}</td>
                      </tr>

                      <template v-if="isManagerExpanded(row.key)">
                        <template v-for="typeRow in managerDetails[row.key]" :key="row.key + '::' + typeRow.type">
                          <tr class="nested-row level-1">
                            <td>
                              <button class="expand-btn small" @click.stop="toggleType(row.key, typeRow.type)">{{ isTypeExpanded(row.key, typeRow.type) ? '−' : '+' }}</button>
                              {{ typeRow.type }}
                            </td>
                            <td>{{ formatWholeNumber(typeRow.projects) }}</td>
                            <td>{{ formatWholeNumber(typeRow.migratable) }}</td>
                            <td>{{ formatWholeNumber(typeRow.actuals) }}</td>
                            <td>{{ formatWholeNumber(typeRow.gap) }}</td>
                          </tr>

                          <template v-if="isTypeExpanded(row.key, typeRow.type)">
                            <tr v-for="statusRow in typeRow.statuses" :key="row.key + '::' + typeRow.type + '::' + statusRow.status" class="nested-row level-2">
                              <td>{{ statusRow.status }}</td>
                              <td>{{ statusRow.count }}</td>
                              <td>{{ formatWholeNumber(statusRow.migratable) }}</td>
                              <td>{{ formatWholeNumber(statusRow.actuals) }}</td>
                              <td>{{ formatWholeNumber(statusRow.gap) }}</td>
                            </tr>
                          </template>
                        </template>
                      </template>

                    </template>
                  </tbody>
                </table>
              </div>
            </article>
          </section>
        </template>

        <template v-else-if="activePage === 'bowler-product'">
          <section class="bowler-product-filters">
            <mc-multi-select
              ref="bowlerProductMultiEl"
              :key="'bowler-ms-' + bowlerProductKey"
              listsearch
              label="Product"
              :value.prop="bowlerProductFilters.products"
              @input="(e) => setMultiFilterFromEvent(bowlerProductFilters.products, e)"
              @optionselected="(e) => setMultiFilterFromEvent(bowlerProductFilters.products, e)">
              <mc-option v-for="option in bowlerProductOptions" :key="option" :value="String(option)">{{ option }}</mc-option>
            </mc-multi-select>

            <mc-multi-select
              ref="bowlerRegionMultiEl"
              :key="'bowler-region-ms-' + bowlerRegionKey"
              listsearch
              label="Region"
              :value.prop="bowlerProductFilters.regions"
              @input="(e) => setMultiFilterFromEvent(bowlerProductFilters.regions, e)"
              @optionselected="(e) => setMultiFilterFromEvent(bowlerProductFilters.regions, e)">
              <mc-option v-for="option in bowlerRegionOptions" :key="option" :value="String(option)">{{ option }}</mc-option>
            </mc-multi-select>

            <mc-multi-select
              ref="bowlerAreaMultiEl"
              :key="'bowler-area-ms-' + bowlerAreaKey"
              listsearch
              label="Area"
              :value.prop="bowlerProductFilters.areas"
              @input="(e) => setMultiFilterFromEvent(bowlerProductFilters.areas, e)"
              @optionselected="(e) => setMultiFilterFromEvent(bowlerProductFilters.areas, e)">
              <mc-option v-for="option in bowlerAreaOptions" :key="option" :value="String(option)">{{ option }}</mc-option>
            </mc-multi-select>

            <mc-multi-select
              ref="bowlerCountryMultiEl"
              :key="'bowler-country-ms-' + bowlerCountryKey"
              listsearch
              label="Country"
              :value.prop="bowlerProductFilters.countries"
              @input="(e) => setMultiFilterFromEvent(bowlerProductFilters.countries, e)"
              @optionselected="(e) => setMultiFilterFromEvent(bowlerProductFilters.countries, e)">
              <mc-option v-for="option in bowlerCountryOptions" :key="option" :value="String(option)">{{ option }}</mc-option>
            </mc-multi-select>
          </section>

          <section class="kpi-row kpi-row--compact">
            <article class="kpi-card">
              <div class="kpi-card__head">
                <span class="kpi-card__label">Products in scope</span>
                <span class="overview-panel__badge overview-panel__badge--flat">Product</span>
              </div>
              <strong class="kpi-card__value">{{ formatWholeNumber(productRows.length) }}</strong>
              <span class="kpi-card__hint">Distinct product tags</span>
              <div class="kpi-card__pills">
                <span class="kpi-pill kpi-pill--muted">{{ formatWholeNumber(productRows.length) }} products</span>
                <span class="kpi-pill kpi-pill--accent">Tags</span>
              </div>
            </article>
            <article class="kpi-card">
              <div class="kpi-card__head">
                <span class="kpi-card__label">Migratable FTE</span>
                <span class="overview-panel__badge overview-panel__badge--flat">Product</span>
              </div>
              <strong class="kpi-card__value">{{ formatWholeNumber(productBowlerSummary.migratable) }}</strong>
              <span class="kpi-card__hint">Across filtered product tags</span>
              <div class="kpi-card__pills">
                <span class="kpi-pill kpi-pill--muted">{{ formatWholeNumber(productRows.length) }} tags</span>
                <span class="kpi-pill kpi-pill--accent">{{ formatWholeNumber(Math.round(productBowlerSummary.migratable / (productRows.length || 1))) }} avg / tag</span>
              </div>
            </article>
            <article class="kpi-card">
              <div class="kpi-card__head">
                <span class="kpi-card__label">Actuals</span>
                <span class="overview-panel__badge overview-panel__badge--flat">Product</span>
              </div>
              <strong class="kpi-card__value">{{ formatWholeNumber(productBowlerSummary.actuals) }}</strong>
              <span class="kpi-card__hint">Completed FTE proxy</span>
              <div class="kpi-card__pills">
                <span class="kpi-pill kpi-pill--muted">{{ formatWholeNumber(productBowlerSummary.actuals) }} actuals</span>
                <span class="kpi-pill kpi-pill--accent">{{ formatWholeNumber(productBowlerSummary.actuals) }}</span>
              </div>
            </article>
            <article class="kpi-card">
              <div class="kpi-card__head">
                <span class="kpi-card__label">Gap to target</span>
                <span class="overview-panel__badge overview-panel__badge--flat">Product</span>
              </div>
              <strong class="kpi-card__value">{{ formatWholeNumber(productBowlerSummary.gap) }}</strong>
              <span class="kpi-card__hint">Open gap by product mix</span>
              <div class="kpi-card__pills">
                <span class="kpi-pill kpi-pill--muted">Open gap</span>
                <span class="kpi-pill kpi-pill--accent">{{ formatWholeNumber(productBowlerSummary.gap) }}</span>
              </div>
            </article>
          </section>

          <section class="dash-card">
            <div class="dash-card__head">
              <h3>Product mix by month</h3>
              <span class="dash-card__meta">BPM ROFO / BPM Actual by product and month</span>
            </div>
            <div v-if="productMonthlyRows.length" class="table-shell table-shell--wide">
              <table class="data-table data-table--monthly">
                <thead>
                  <tr>
                    <th>Product</th>
                    <th v-for="month in bpmMonthColumns" :key="month.key">{{ month.label }}</th>
                    <th>Total</th>
                  </tr>
                </thead>
                <tbody>
                  <template v-for="group in productMonthlyRows" :key="group.product">
                    <tr v-for="rowType in ['target', 'actual', 'gap']" :key="`${group.product}-${rowType}`">
                      <td v-if="rowType === 'target'" class="table-group-label">{{ group.product }}</td>
                      <td v-else class="table-sub-label">{{ rowType === 'target' ? 'Target' : rowType === 'actual' ? 'Actual' : 'GAP' }}</td>
                      <td
                        v-for="month in bpmMonthColumns"
                        :key="`${group.product}-${rowType}-${month.key}`"
                        :class="monthCellClass(rowType, rowGroupValue(group, rowType, month.key))"
                      >
                        {{ formatWholeNumber(rowGroupValue(group, rowType, month.key)) }}
                      </td>
                      <td :class="monthCellClass(rowType, rowGroupValue(group, rowType, 'total'))">
                        {{ formatWholeNumber(rowGroupValue(group, rowType, 'total')) }}
                      </td>
                    </tr>
                  </template>
                </tbody>
              </table>
            </div>
            <p v-else class="summary-empty">No product data yet in current intake selection.</p>
          </section>
        </template>

        <!-- Executive Summary -->
        <template v-if="activePage === 'executive'">
          <section class="kpi-row kpi-row--bpm bpm-kpi-row">
            <article v-for="kpi in executiveKpis" :key="kpi.key" class="kpi-card bpm-kpi-card" :class="`bpm-kpi-card--${kpi.key}`">
              <div class="bpm-kpi-card__topline">
                <span class="kpi-card__label">{{ kpi.label }}</span>
                <span class="bpm-kpi-card__dot" aria-hidden="true" />
              </div>
              <strong class="kpi-card__value">{{ kpi.value }}</strong>
              <span class="kpi-card__hint">{{ kpi.hint }}</span>
              <small class="bpm-kpi-card__formula">{{ kpi.formula }}</small>
            </article>
          </section>

          <section class="split-grid--executive">
            <article class="dash-card exec-metrics">
              <div class="dash-card__head">
                <h3>{{ bpmYear }} offshoring — Target vs Gap</h3>
                <span class="dash-card__meta">BPM ROFO / BPM Actual summary</span>
              </div>

              <div>
                <table class="exec-table">
                  <tbody>
                    <tr>
                      <td class="label">Target</td>
                      <td class="value">{{ formatWholeNumber(bpmSummary.target) }}</td>
                      <td class="commentary">Commentary</td>
                      <td class="commentary-value">2026 offshoring target</td>
                    </tr>
                    <tr>
                      <td class="label">Less: Actual</td>
                      <td class="value">{{ formatWholeNumber(Number(bpmSummary.withinBudget || 0) + Number(bpmSummary.beyondBudget || 0)) }}</td>
                      <td class="commentary">Successfully onboarded to date</td>
                      <td class="commentary-value"></td>
                    </tr>
                    <tr>
                      <td class="label">&nbsp;</td>
                      <td></td>
                      <td class="label">Within</td>
                      <td class="value">{{ formatWholeNumber(bpmSummary.withinBudget) }}</td>
                    </tr>
                    <tr>
                      <td class="label">&nbsp;</td>
                      <td></td>
                      <td class="label">Beyond</td>
                      <td class="value">{{ formatWholeNumber(bpmSummary.beyondBudget) }}</td>
                    </tr>
                    <tr>
                      <td class="label">Less: Pipeline</td>
                      <td class="value">
                        <!-- showing a dummy value with explanation -->
                        <span class="dummy-number">{{ formatWholeNumber(DUMMY_PIPELINE) }}</span>
                        <div class="dummy-note">(dummy placeholder — real pipeline source not connected)</div>
                      </td>
                      <td class="commentary">Approved, pending onboarding</td>
                      <td></td>
                    </tr>
                    <tr>
                      <td class="label">GAP</td>
                      <td class="value">{{ formatWholeNumber(Math.max(0, Number(bpmSummary.target || 0) - (Number(bpmSummary.withinBudget || 0) + Number(bpmSummary.beyondBudget || 0) + Number(kpis.pipeline || 0)))) }}</td>
                      <td class="commentary">Remaining to reach target</td>
                      <td></td>
                    </tr>
                  </tbody>
                </table>


                <div class="further-potential">
                  <h4>Further potential</h4>
                  <div class="further-grid">
                    <div class="fcol">
                      <div class="fcell">Within Budget</div>
                      <div class="fvalue">{{ formatWholeNumber(DUMMY_FURTHER.within) }} <span class="badge-dummy">DUMMY</span></div>
                    </div>
                    <div class="fcol">
                      <div class="fcell">Beyond Budget</div>
                      <div class="fvalue">{{ formatWholeNumber(DUMMY_FURTHER.beyond) }} <span class="badge-dummy">DUMMY</span></div>
                    </div>
                    <div class="fcol">
                      <div class="fcell">Total</div>
                      <div class="fvalue">{{ formatWholeNumber(DUMMY_FURTHER.total) }} <span class="badge-dummy">DUMMY</span></div>
                    </div>
                  </div>
                  <div class="further-note">
                    <strong>Note:</strong> Numbers shown above are dummy placeholders for layout/demo purposes. Real values require a connected pipeline or BPM data source. Calculation (for reference): remaining = target − (within + beyond + pipeline).
                  </div>
                </div>

              </div>

            </article>

            <aside class="executive-note-column">
              <article v-for="note in executiveSummaryNotes" :key="note.section" class="executive-note-card" :class="`executive-note-card--${note.section}`">
                <div class="executive-note-card__head">
                  <div style="display:flex;gap:8px;align-items:center;">
                    <span class="executive-note-icon" aria-hidden="true">{{ note.section==='highlights' ? '✔️' : note.section==='focus' ? '⚠️' : '🚀' }}</span>
                    <span class="executive-note-card__eyebrow">{{ note.title }}</span>
                  </div>
                  <div class="executive-note-actions">
                    <button v-if="canEditExecutiveNotes" type="button" class="executive-note-card__edit" @click="openExecutiveNoteEditor(note)">Edit</button>
                    <button type="button" class="executive-note-card__link" @click="viewRelatedProjects(note.section)">View related projects</button>
                  </div>
                </div>
                <p class="executive-note-card__body">{{ note.body }}</p>
              </article>

              <div v-if="editingExecutiveNote" class="executive-note-editor">
                <div class="executive-note-editor__header">
                  <h3>{{ executiveNoteDraft.title }}</h3>
                  <button type="button" class="inline-btn" @click="editingExecutiveNote = null">Close</button>
                </div>
                <label class="editor-field">
                  <span>Title</span>
                  <input v-model="executiveNoteDraft.title" type="text" />
                </label>
                <label class="editor-field">
                  <span>Content</span>
                  <textarea v-model="executiveNoteDraft.body" rows="5" />
                </label>
                <div class="editor-actions">
                  <button type="button" class="inline-btn inline-btn--secondary" @click="editingExecutiveNote = null">Cancel</button>
                  <button type="button" class="inline-btn inline-btn--primary" @click="saveExecutiveNote">Save</button>
                </div>
              </div>
            </aside>

          </section>
        </template>

      </div>
    </div>
  </PageShell>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import PageShell from '../components/PageShell.vue'
import DashboardRankedList from '../components/dashboard/DashboardRankedList.vue'
import { regions } from '../data/regionAreaMapping.js'
import { canAccessAttributesTable, fetchMyAttributesAccess } from '../utils/attributesAccess.js'
import { formatStatusLabel } from '../utils/migrationDashboardProgress.js'
import '@maersk-global/mds-components-core/mc-tag'
import '@maersk-global/mds-components-core/mc-button'
import '@maersk-global/mds-components-core/mc-notification'
import '@maersk-global/mds-components-core/mc-input'
import '@maersk-global/mds-components-core/mc-multi-select'
import '@maersk-global/mds-components-core/mc-select'
import '@maersk-global/mds-components-core/mc-option'

const router = useRouter()

const loading = ref(true)
const loadError = ref('')
const projects = ref([])
const activePage = ref('executive')
const searchQuery = ref('')
const filterRegion = ref('')
const filterMigrationType = ref('')
const filterProduct = ref('')
const filterStatus = ref('')
const bpmYear = ref(new Date().getFullYear())
const bpmSummary = ref({ target: 0, withinBudget: 0, beyondBudget: 0 })
// Dummy placeholders for UI when pipeline / further potential data source is not connected
const DUMMY_PIPELINE = 975
const DUMMY_FURTHER = { within: 120, beyond: 45, total: 165 }
const bpmRofoRows = ref([])
const bpmActualRows = ref([])
const access = ref({ tables: {} })
const executiveSummaryNotes = ref([])
const editingExecutiveNote = ref(null)
const executiveNoteDraft = ref({ title: '', body: '' })

const regionOptions = regions
const numberFormatter = new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 })
const bowlerProductFilters = ref({
  products: [],
  regions: [],
  areas: [],
  countries: []
})

const pages = [
{ id: 'executive', label: 'Executive Summary', note: 'KPI focus: portfolio volume, migratable FTE, actuals, gap, and completion.' },
{ id: 'project-health', label: 'Project Health Status', note: 'Portfolio view of project health using Intake + migration stage data.' },
{ id: 'bowler-product', label: 'Bowler Product Level', note: 'Product-level intake snapshot by product tag, migratable FTE, actuals, and gap.' }
]

const activePageMeta = computed(
  () => pages.find((page) => page.id === activePage.value) ?? pages[0]
)

const executiveSummaryOrder = ['highlights', 'focus', 'levers']
const canEditExecutiveNotes = computed(
  () =>
    canAccessAttributesTable(access.value, 'bpm_rofo') ||
    canAccessAttributesTable(access.value, 'bpm_actual')
)

const unavailablePages = [
  {
    title: 'ROFO vs Actual Overview',
    reason: 'No monthly ROFO target / actual time series in the app.'
  },
  {
    title: 'Overall Summary (Within / Beyond Budget)',
    reason: 'No within/beyond-budget FTE split or signed-off pipeline amounts.'
  },
  {
    title: 'WPM Bowler Area Level',
    reason: 'No monthly Target / Actual / GAP by area.'
  },
  {
    title: 'Tollgate TG1–TG7 RAG (Delayed / On Time)',
    reason: 'No tollgate dates or delay-day rules; only workflow status / milestones exist.'
  },
  {
    title: 'GSC Site Actuals chart',
    reason: 'Project overview API has no GSC site field.'
  },
  {
    title: 'True Migration Manager ownership table',
    reason: 'Product Ownership API is access-gated; requestor is used as a proxy instead.'
  }
]

const IN_FLIGHT = new Set(['in_review', 'planning', 'in_progress', 'at_risk'])
const COMPLETED = 'completed'

const parseFte = (value) => {
  const n = Number.parseInt(value, 10)
  return Number.isNaN(n) ? 0 : n
}

const formatWholeNumber = (value) => numberFormatter.format(Number(value) || 0)

const bpmYearOptions = computed(() => {
  const years = []
  const currentYear = new Date().getFullYear()
  for (let offset = -2; offset <= 2; offset += 1) {
    years.push(currentYear + offset)
  }
  return years
})

const normalizeBpmNumber = (value) => {
  if (value === null || value === undefined || value === '') return 0
  const raw = String(value).trim().replace(/,/g, '')
  const parsed = Number(raw)
  return Number.isFinite(parsed) ? parsed : 0
}

const normalizePartFlag = (value) => {
  if (value === null || value === undefined || value === '') return ''
  return String(value).trim().toLowerCase()
}

const normalizeMonthKey = (value, fallbackYear = null) => {
  if (value === null || value === undefined || value === '') return null
  const raw = String(value).trim()
  const short = raw.toLowerCase()
  const monthNames = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
  for (let index = 0; index < monthNames.length; index += 1) {
    if (short.includes(monthNames[index])) return index + 1
  }
  if (/\d{4}-\d{1,2}/.test(raw)) {
    const match = raw.match(/\d{4}-(\d{1,2})/)
    if (match) {
      const month = Number(match[1])
      if (month >= 1 && month <= 12) return month
    }
  }
  if (/\d{1,2}\/\d{1,2}\/\d{2,4}/.test(raw)) {
    const match = raw.match(/(\d{1,2})\/(\d{1,2})\/\d{2,4}/)
    if (match) {
      const month = Number(match[1])
      if (month >= 1 && month <= 12) return month
    }
  }
  const parsed = new Date(raw)
  if (!Number.isNaN(parsed.getTime())) {
    const month = parsed.getMonth() + 1
    return month >= 1 && month <= 12 ? month : null
  }
  if (fallbackYear && /\d{4}/.test(raw)) {
    const match = raw.match(/(\d{1,2})/)
    if (match) {
      const month = Number(match[1])
      if (month >= 1 && month <= 12) return month
    }
  }
  return null
}

const projectHealthFilters = ref({
  migrationType: [],
  owner: [],
  region: [],
  product: [],
  gscSite: []
})
const activeMultiFilter = ref('')
const multiFilterSearch = ref({
  migrationType: '',
  owner: '',
  region: '',
  product: '',
  gscSite: '',
  bowlerProducts: '',
  bowlerRegions: '',
  bowlerAreas: '',
  bowlerCountries: ''
})

// Refs to underlying mc-multi-select elements (Web Components) so we can read their .value when needed
const migrationTypeMultiEl = ref(null)
const ownerMultiEl = ref(null)
const regionMultiEl = ref(null)
const productMultiEl = ref(null)
const gscSiteMultiEl = ref(null)
const bowlerProductMultiEl = ref(null)
const bowlerRegionMultiEl = ref(null)
const bowlerAreaMultiEl = ref(null)
const bowlerCountryMultiEl = ref(null)

// Keys to force mc-multi-select remount when option sets change
const projectHealthMigrationTypeKey = computed(() => projectHealthMigrationTypeOptions.value.length)
const projectHealthOwnerKey = computed(() => projectHealthOwnerOptions.value.length)
const projectHealthRegionKey = computed(() => projectHealthRegionOptions.value.length)
const projectHealthProductKey = computed(() => projectHealthProductOptions.value.length)
const projectHealthGscSiteKey = computed(() => projectHealthGscSiteOptions.value.length)

const bowlerProductKey = computed(() => bowlerProductOptions.value.length)
const bowlerRegionKey = computed(() => bowlerRegionOptions.value.length)
const bowlerAreaKey = computed(() => bowlerAreaOptions.value.length)
const bowlerCountryKey = computed(() => bowlerCountryOptions.value.length)

// Helper to normalize various incoming shapes into string arrays
const normalizeToStringList = (value) => {
  if (typeof value === 'string') {
    return value
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean)
  }
  if (!Array.isArray(value)) return []
  return value
    .map((item) => {
      if (typeof item === 'string') return item.trim()
      if (item && typeof item === 'object') return String(item.value ?? item.label ?? '').trim()
      return ''
    })
    .filter(Boolean)
}

// Read event from mc-multi-select and write to target ref array
const setMultiFilterFromEvent = (targetRef, event) => {
  const el = event?.currentTarget ?? event?.target
  const detail = event?.detail
  if (Array.isArray(detail) && detail.length > 0 && detail.every((item) => item && typeof item === 'object')) {
    targetRef.splice(0, targetRef.length, ...normalizeToStringList(detail.map((it) => it.value ?? it.label ?? '')))
    return
  }
  if (el?.value != null) {
    targetRef.splice(0, targetRef.length, ...normalizeToStringList(el.value))
    return
  }
  const rawValue = detail?.value ?? detail ?? []
  targetRef.splice(0, targetRef.length, ...normalizeToStringList(rawValue))
}

// Ensure Vue ref arrays reflect the mc-multi-select DOM state before applying filters
const syncAllMultiFiltersFromDom = () => {
  if (migrationTypeMultiEl.value?.value != null) {
    projectHealthFilters.value.migrationType = normalizeToStringList(migrationTypeMultiEl.value.value)
  }
  if (ownerMultiEl.value?.value != null) {
    projectHealthFilters.value.owner = normalizeToStringList(ownerMultiEl.value.value)
  }
  if (regionMultiEl.value?.value != null) {
    projectHealthFilters.value.region = normalizeToStringList(regionMultiEl.value.value)
  }
  if (productMultiEl.value?.value != null) {
    projectHealthFilters.value.product = normalizeToStringList(productMultiEl.value.value)
  }
  if (gscSiteMultiEl.value?.value != null) {
    projectHealthFilters.value.gscSite = normalizeToStringList(gscSiteMultiEl.value.value)
  }
  if (bowlerProductMultiEl.value?.value != null) {
    bowlerProductFilters.value.products = normalizeToStringList(bowlerProductMultiEl.value.value)
  }
  if (bowlerRegionMultiEl.value?.value != null) {
    bowlerProductFilters.value.regions = normalizeToStringList(bowlerRegionMultiEl.value.value)
  }
  if (bowlerAreaMultiEl.value?.value != null) {
    bowlerProductFilters.value.areas = normalizeToStringList(bowlerAreaMultiEl.value.value)
  }
  if (bowlerCountryMultiEl.value?.value != null) {
    bowlerProductFilters.value.countries = normalizeToStringList(bowlerCountryMultiEl.value.value)
  }
}

const filteredMultiOptions = (options, query) => {
  const q = String(query || '').trim().toLowerCase()
  if (!q) return options
  return options.filter((option) => String(option).toLowerCase().includes(q))
}

const currentMultiSelectionLabel = (selected, options) => {
  const list = Array.isArray(selected) ? selected : []
  const count = list.length
  if (!count) return 'Select all'
  const total = options.length || count
  return `${count} out of ${total} selected`
}

const toggleMultiFilter = (key) => {
  activeMultiFilter.value = activeMultiFilter.value === key ? '' : key
}

const toggleMultiValue = (key, value) => {
  const list = (() => {
    if (key === 'bowlerProducts') return bowlerProductFilters.value.products
    if (key === 'bowlerRegions') return bowlerProductFilters.value.regions
    if (key === 'bowlerAreas') return bowlerProductFilters.value.areas
    if (key === 'bowlerCountries') return bowlerProductFilters.value.countries
    return projectHealthFilters.value[key] ?? []
  })()

  const next = list.includes(value) ? list.filter((item) => item !== value) : [...list, value]

  if (key === 'bowlerProducts') bowlerProductFilters.value.products = next
  if (key === 'bowlerRegions') bowlerProductFilters.value.regions = next
  if (key === 'bowlerAreas') bowlerProductFilters.value.areas = next
  if (key === 'bowlerCountries') bowlerProductFilters.value.countries = next
  if (key in projectHealthFilters.value) projectHealthFilters.value[key] = next
}

const toggleSelectAll = (key) => {
  const source = {
    migrationType: projectHealthMigrationTypeOptions.value,
    owner: projectHealthOwnerOptions.value,
    region: projectHealthRegionOptions.value,
    product: projectHealthProductOptions.value,
    gscSite: projectHealthGscSiteOptions.value,
    bowlerProducts: bowlerProductOptions.value,
    bowlerRegions: bowlerRegionOptions.value,
    bowlerAreas: bowlerAreaOptions.value,
    bowlerCountries: bowlerCountryOptions.value
  }
  const target = source[key] || []
  if (key in projectHealthFilters.value) {
    projectHealthFilters.value[key] = projectHealthFilters.value[key].length === target.length ? [] : [...target]
  }
  if (key === 'bowlerProducts') bowlerProductFilters.value.products = bowlerProductFilters.value.products.length === target.length ? [] : [...target]
  if (key === 'bowlerRegions') bowlerProductFilters.value.regions = bowlerProductFilters.value.regions.length === target.length ? [] : [...target]
  if (key === 'bowlerAreas') bowlerProductFilters.value.areas = bowlerProductFilters.value.areas.length === target.length ? [] : [...target]
  if (key === 'bowlerCountries') bowlerProductFilters.value.countries = bowlerProductFilters.value.countries.length === target.length ? [] : [...target]
}

const projectHealthMigrationTypeOptions = computed(() => {
  const values = new Set(projects.value.map((p) => p.migrationType).filter(Boolean))
  const opts = [...values].sort()
  return ['All', ...opts]
})

const uniqStrings = (items) => {
  const values = new Set()
  for (const item of items) {
    const value = String(item ?? '').trim()
    if (value) values.add(value)
  }
  return [...values].sort()
}

const projectHealthOwnerOptions = computed(() => {
  const values = [
    ...projects.value.map((p) => p.owner || p.requestor),
    ...bpmRofoRows.value.map((row) => row.bpm_owner),
    ...bpmActualRows.value.map((row) => row.bpm_owner)
  ]
  const opts = uniqStrings(values)
  return ['All', ...opts]
})

const projectHealthRegionOptions = computed(() => {
  const values = [
    ...projects.value.map((p) => p.region),
    ...bpmRofoRows.value.map((row) => row.region),
    ...bpmActualRows.value.map((row) => row.region)
  ]
  const opts = uniqStrings(values)
  return ['All', ...opts]
})

const projectHealthProductOptions = computed(() => {
  const values = []
  for (const project of projects.value) {
    for (const product of project.products ?? []) {
      values.push(product)
    }
  }
  values.push(...bpmRofoRows.value.map((row) => row.product))
  values.push(...bpmActualRows.value.map((row) => row.product))
  const opts = uniqStrings(values)
  return ['All', ...opts]
})

const projectHealthGscSiteOptions = computed(() => {
  const values = projects.value.map((p) => p.gscSite || p.site).filter(Boolean)
  const opts = uniqStrings(values)
  return ['All', ...opts]
})

const migrationTypeOptions = computed(() => {
  const types = new Set(projects.value.map((p) => p.migrationType).filter(Boolean))
  return [...types].sort()
})

const productOptions = computed(() => {
  const products = new Set()
  for (const project of projects.value) {
    for (const product of project.products ?? []) {
      const name = String(product).trim()
      if (name) products.add(name)
    }
  }
  return [...products].sort()
})

const hasActiveFilters = computed(
  () =>
    Boolean(searchQuery.value.trim()) ||
    Boolean(filterRegion.value) ||
    Boolean(filterMigrationType.value) ||
    Boolean(filterProduct.value) ||
    Boolean(filterStatus.value)
)

const filteredProjects = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  const normalizeMultiSelectionForFiltering = (raw) => {
    const list = Array.isArray(raw) ? raw.map((v) => String(v).trim()).filter(Boolean) : []
    // If user selected explicit 'All', treat as no filter
    if (list.some((v) => v.toLowerCase() === 'all')) return []
    return list
  }

  const selectedMigrationTypes = normalizeMultiSelectionForFiltering(projectHealthFilters.value.migrationType)
  const selectedOwners = normalizeMultiSelectionForFiltering(projectHealthFilters.value.owner)
  const selectedRegions = normalizeMultiSelectionForFiltering(projectHealthFilters.value.region)
  const selectedProducts = normalizeMultiSelectionForFiltering(projectHealthFilters.value.product)
  const selectedSites = normalizeMultiSelectionForFiltering(projectHealthFilters.value.gscSite)

  return projects.value.filter((project) => {
    if (filterRegion.value && project.region !== filterRegion.value) return false
    if (filterMigrationType.value && project.migrationType !== filterMigrationType.value) return false
    if (filterStatus.value && project.status !== filterStatus.value) return false
    if (filterProduct.value) {
      const products = (project.products ?? []).map((p) => String(p).trim())
      if (!products.includes(filterProduct.value)) return false
    }
    if (selectedMigrationTypes.length && !selectedMigrationTypes.includes(project.migrationType)) return false
    if (selectedOwners.length) {
      const owner = project.owner || project.requestor || ''
      if (!selectedOwners.includes(owner)) return false
    }
    if (selectedRegions.length && !selectedRegions.includes(project.region)) return false
    if (selectedProducts.length) {
      const products = (project.products ?? []).map((p) => String(p).trim())
      const matches = products.some((item) => selectedProducts.includes(item))
      if (!matches) return false
    }
    if (selectedSites.length) {
      const site = project.gscSite || project.site || ''
      if (!selectedSites.includes(site)) return false
    }
    if (!query) return true
    const haystack = [
      project.projectName,
      project.migrationRequestId,
      project.requestor,
      project.region,
      project.migrationType,
      ...(project.products ?? [])
    ]
      .join(' ')
      .toLowerCase()
    return haystack.includes(query)
  })
})

const projectMatchesExecutiveYear = (project) => {
  const directYear = Number(
    project.year ?? project.bpmYear ?? project.onboardingYear ?? project.onboarding_year ?? project.onboardingYearValue ?? 0
  )
  if (Number.isFinite(directYear) && directYear > 0) {
    return directYear === bpmYear.value
  }

  const monthCandidates = [
    project.onboardingMonth,
    project.onboarding_month,
    project.onboarding,
    project.startMonth,
    project.start_month
  ]

  for (const candidate of monthCandidates) {
    const value = String(candidate ?? '').trim()
    if (!value) continue

    const match = value.match(/(19|20)\d{2}/)
    if (match) {
      const yearValue = Number(match[0])
      if (Number.isFinite(yearValue)) return yearValue === bpmYear.value
    }

    const month = normalizeMonthKey(value, bpmYear.value)
    if (Number.isFinite(month) && month >= 1 && month <= 12) return true
  }

  return true
}

const executiveFilteredProjects = computed(() =>
  filteredProjects.value.filter((project) => projectMatchesExecutiveYear(project))
)

const projectMetrics = (project) => {
  const fte = parseFte(project.fteNumber)
  const isCompleted = project.status === COMPLETED
  const isPipeline = IN_FLIGHT.has(project.status)
  return {
    migratable: fte,
    actuals: isCompleted ? fte : 0,
    pipeline: isPipeline ? fte : 0,
    gap: isCompleted ? 0 : fte
  }
}

const kpis = computed(() => {
  let totalProjects = 0
  let migratableFte = 0
  let actuals = 0
  let pipeline = 0

  for (const project of executiveFilteredProjects.value) {
    totalProjects += 1
    const m = projectMetrics(project)
    migratableFte += m.migratable
    actuals += m.actuals
    pipeline += m.pipeline
  }

  const fteGap = Math.max(0, migratableFte - actuals)
  const completionPct = migratableFte ? Math.round((actuals / migratableFte) * 100) : 0

  return {
    totalProjects,
    migratableFte,
    actuals,
    pipeline,
    fteGap,
    completionPct
  }
})

// Percentage of offshoring target achieved (0..100)
const execAchievedPct = computed(() => {
  const target = Number(bpmSummary.value.target || 0)
  if (!target) return 0
  const achieved = Number(bpmSummary.value.withinBudget || 0) + Number(bpmSummary.value.beyondBudget || 0)
  return Math.round(Math.min(100, Math.max(0, (achieved / target) * 100)))
})

// Executive KPIs for the BPM panel
const executiveKpis = computed(() => [
  {
    key: 'bpm-target',
    label: 'Target',
    value: formatWholeNumber(bpmSummary.value.target),
    hint: 'ROFO positions in GSC',
    formula: 'Sum of Positions to be Offshored in GSC from BPM ROFO for the selected year.'
  },
  {
    key: 'bpm-within',
    label: 'Actual within budget',
    value: formatWholeNumber(bpmSummary.value.withinBudget),
    hint: 'Part of ROFO = Yes',
    formula: 'Actual values where Part/Not part of ROFO is Yes in BPM Actual.'
  },
  {
    key: 'bpm-beyond',
    label: 'Actual beyond budget',
    value: formatWholeNumber(bpmSummary.value.beyondBudget),
    hint: 'Part of ROFO = No',
    formula: 'Actual values where Part/Not part of ROFO is No in BPM Actual.'
  }
])

const productKpis = computed(() => [
  {
    key: 'products',
    label: 'Products in scope',
    value: formatWholeNumber(productRows.value.length),
    hint: 'Distinct product tags'
  },
  {
    key: 'migratable',
    label: 'Migratable FTE',
    value: formatWholeNumber(kpis.value.migratableFte),
    hint: 'Across tagged products'
  },
  {
    key: 'gap',
    label: 'Open GAP',
    value: formatWholeNumber(kpis.value.fteGap),
    hint: 'Still to deliver'
  },
  {
    key: 'pipeline',
    label: 'Pipeline FTE',
    value: formatWholeNumber(kpis.value.pipeline),
    hint: 'In-flight statuses'
  }
])

// Further potential — split remaining gap into Within/Beyond using actuals ratio when possible.
const furtherPotential = computed(() => {
  const target = Number(bpmSummary.target || 0)
  const within = Number(bpmSummary.withinBudget || 0)
  const beyond = Number(bpmSummary.beyondBudget || 0)
  const pipeline = Number(kpis.value?.pipeline || 0)

  const actualTotal = within + beyond
  const remaining = Math.max(0, target - actualTotal - pipeline)

  let withinPotential = 0
  let beyondPotential = 0

  if (actualTotal > 0) {
    // distribute remaining according to existing within/beyond proportions
    const withinRatio = within / actualTotal
    withinPotential = Math.round(remaining * withinRatio)
    beyondPotential = remaining - withinPotential
  } else {
    // No actual split known — try to infer from BPM rows: use proportion of rofo-like values if available
    const rofoSum = bpmRofoRows.value.reduce((s, r) => s + (Number(r.positions_to_be_offshored_in_gsc || r.rofo_value || 0) || 0), 0)
    const actualRofoRatio = rofoSum > 0 ? Math.min(1, rofoSum / (target || 1)) : 0
    if (actualRofoRatio > 0) {
      // if ROFO exists treat most as within
      withinPotential = Math.round(remaining * 0.8)
      beyondPotential = remaining - withinPotential
    } else {
      // fallback: all to within
      withinPotential = remaining
      beyondPotential = 0
    }
  }

  return {
    within: Math.max(0, withinPotential),
    beyond: Math.max(0, beyondPotential),
    total: Math.max(0, withinPotential + beyondPotential)
  }
})

const stageColor = {
  new: '#42b0d5',
  in_review: '#f3b562',
  planning: '#94a3b8',
  in_progress: '#0077b8',
  at_risk: '#e85454',
  completed: '#6daa28'
}

const stageItems = computed(() => {
  const bucket = {}
  for (const project of executiveFilteredProjects.value) {
    const key = project.status || 'new'
    if (!bucket[key]) bucket[key] = 0
    bucket[key] += 1
  }
  const total = executiveFilteredProjects.value.length || 1
  return Object.entries(bucket)
    .map(([status, count]) => ({
      key: status,
      status,
      label: formatStatusLabel(status),
      count,
      pct: Math.round((count / total) * 100),
      color: stageColor[status] || '#94a3b8'
    }))
    .sort((a, b) => b.count - a.count)
})

const tgStageLabels = [
  'TG1 – Intake Submitted',
  'TG2 – Opportunity Assessment',
  'TG3 – Business Case',
  'TG4 – Approvals',
  'TG5 – Training',
  'TG6 – Gantt',
  'TG7 – Go-live'
]

const projectHealthStageItems = computed(() => {
  const bucket = {}
  for (const project of executiveFilteredProjects.value) {
    const status = project.status || 'new'
    let stageIndex = 0
    if (status === 'new') stageIndex = 0
    else if (status === 'in_review') stageIndex = 1
    else if (status === 'planning') stageIndex = 2
    else if (status === 'in_progress') stageIndex = 3
    else if (status === 'at_risk') stageIndex = 4
    else if (status === 'completed') stageIndex = 6

    const label = tgStageLabels[Math.min(stageIndex, tgStageLabels.length - 1)]
    if (!bucket[label]) bucket[label] = 0
    bucket[label] += 1
  }
  const total = executiveFilteredProjects.value.length || 1
  return Object.entries(bucket)
    .map(([label, count]) => ({
      key: label,
      label,
      count,
      pct: Math.round((count / total) * 100),
      color: '#0077b8'
    }))
    .sort((a, b) => b.count - a.count)
})

// Render TG stacked bars using backend summary.tg_summary when available
const tgBarItems = computed(() => {
  const list = tgSummary.value || []
  if (!list.length) return []

  // colors mapping
  const COLORS = {
    'Delayed': '#f37021',
    'Delayed < 30 Days': '#f3b562',
    'On Time': '#6daa28',
    'Update Pending': '#003f6e'
  }

  // compute max total across TGs to scale bar lengths
  let maxTotal = 0
  const normalized = list.map((tg) => {
    const delayed = Number((tg['Delayed'] && tg['Delayed'].count) || 0)
    const delayed30 = Number((tg['Delayed < 30 Days'] && tg['Delayed < 30 Days'].count) || 0)
    const ontime = Number((tg['On Time'] && tg['On Time'].count) || 0)
    const pending = Number((tg['Update Pending'] && tg['Update Pending'].count) || 0)
    const total = delayed + delayed30 + ontime + pending
    if (total > maxTotal) maxTotal = total
    return {
      label: tg.label,
      buckets: { delayed, delayed30, ontime, pending },
      total
    }
  })

  if (maxTotal === 0) maxTotal = 1

  return normalized.map((tg) => {
    const total = tg.total
    const segments = [
      { key: 'Delayed', label: 'Delayed', count: tg.buckets.delayed, color: COLORS['Delayed'] },
      { key: 'Delayed < 30 Days', label: 'Delayed < 30 Days', count: tg.buckets.delayed30, color: COLORS['Delayed < 30 Days'] },
      { key: 'On Time', label: 'On Time', count: tg.buckets.ontime, color: COLORS['On Time'] },
      { key: 'Update Pending', label: 'Update Pending', count: tg.buckets.pending, color: COLORS['Update Pending'] }
    ].map((seg) => ({
      ...seg,
      pct: total ? Math.round((seg.count / total) * 100) : 0
    }))

    // optionally scale overall bar length relative to maxTotal (use pct of max)
    const totalPct = Math.round((tg.total / maxTotal) * 100)

    return {
      label: tg.label,
      total: tg.total,
      totalPct,
      segments
    }
  })
})

const regionRows = computed(() => {
  const bucket = {}
  for (const project of executiveFilteredProjects.value) {
    const region = project.region || 'Unknown'
    if (!bucket[region]) bucket[region] = { migratable: 0, actuals: 0 }
    const m = projectMetrics(project)
    bucket[region].migratable += m.migratable
    bucket[region].actuals += m.actuals
  }

  const maxMigratable = Math.max(
    1,
    ...Object.values(bucket).map((value) => value.migratable)
  )

  return Object.entries(bucket)
    .map(([region, values]) => ({
      key: region,
      label: region,
      migratable: values.migratable,
      actuals: values.actuals,
      migratablePct: Math.round((values.migratable / maxMigratable) * 100),
      actualsPct: Math.round((values.actuals / maxMigratable) * 100)
    }))
    .sort((a, b) => b.migratable - a.migratable)
})

const requestorRows = computed(() => {
  const bucket = {}
  for (const project of executiveFilteredProjects.value) {
    const managerName = project.owner || project.requestor || 'Unknown'
    const key = managerName
    if (!bucket[key]) {
      bucket[key] = { key, label: managerName, projects: 0, migratable: 0, actuals: 0 }
    }
    const m = projectMetrics(project)
    bucket[key].projects += 1
    bucket[key].migratable += m.migratable
    bucket[key].actuals += m.actuals
  }
  return Object.values(bucket)
    .map((row) => ({
      ...row,
      gap: Math.max(0, row.migratable - row.actuals)
    }))
    .sort((a, b) => b.migratable - a.migratable)
    .slice(0, 20)
})

// Drilldown state & aggregated details by manager -> migrationType -> status
const expandedManagers = ref([])
const expandedTypeKeys = ref([])

const toggleManager = (key) => {
  const i = expandedManagers.value.indexOf(key)
  if (i >= 0) expandedManagers.value.splice(i, 1)
  else expandedManagers.value.push(key)
}
const isManagerExpanded = (key) => expandedManagers.value.includes(key)

const _typeKey = (managerKey, type) => `${managerKey}||${type}`
const toggleType = (managerKey, type) => {
  const k = _typeKey(managerKey, type)
  const i = expandedTypeKeys.value.indexOf(k)
  if (i >= 0) expandedTypeKeys.value.splice(i, 1)
  else expandedTypeKeys.value.push(k)
}
const isTypeExpanded = (managerKey, type) => expandedTypeKeys.value.includes(_typeKey(managerKey, type))

const managerDetails = computed(() => {
  const map = {}
  for (const project of executiveFilteredProjects.value) {
    const manager = project.owner || project.requestor || 'Unknown'
    const type = String(project.migrationType || 'Unknown')
    const status = String(project.status || '(blank)')
    if (!map[manager]) map[manager] = {}
    if (!map[manager][type]) {
      map[manager][type] = { type, projects: 0, migratable: 0, actuals: 0, statuses: {} }
    }
    const m = projectMetrics(project)
    map[manager][type].projects += 1
    map[manager][type].migratable += m.migratable
    map[manager][type].actuals += m.actuals

    if (!map[manager][type].statuses[status]) map[manager][type].statuses[status] = { status, count: 0, migratable: 0, actuals: 0 }
    map[manager][type].statuses[status].count += 1
    map[manager][type].statuses[status].migratable += m.migratable
    map[manager][type].statuses[status].actuals += m.actuals
  }

  const result = {}
  for (const [mgr, types] of Object.entries(map)) {
    result[mgr] = Object.values(types)
      .map((t) => ({
        ...t,
        gap: Math.max(0, t.migratable - t.actuals),
        statuses: Object.values(t.statuses).map((s) => ({ ...s, gap: Math.max(0, s.migratable - s.actuals) }))
          .sort((a, b) => b.count - a.count)
      }))
      .sort((a, b) => b.migratable - a.migratable)
  }
  return result
})

const bowlerProjectOptions = computed(() => {
  const values = new Set()
  for (const project of projects.value) {
    for (const product of project.products ?? []) {
      const label = String(product).trim()
      if (label) values.add(label)
    }
  }
  return [...values].sort()
})

// backward-compatible alias: template previously used bowlerProductOptions
const bowlerProductOptions = bowlerProjectOptions

const bowlerRegionOptions = computed(() => {
  const values = new Set()
  for (const project of projects.value) {
    const label = String(project.region || '').trim()
    if (label) values.add(label)
  }
  return [...values].sort()
})

const bowlerAreaOptions = computed(() => {
  const values = new Set()
  for (const project of projects.value) {
    for (const area of project.areas ?? []) {
      const label = String(area).trim()
      if (label) values.add(label)
    }
  }
  return [...values].sort()
})

const bowlerCountryOptions = computed(() => {
  const values = new Set()
  for (const project of projects.value) {
    for (const country of project.countries ?? []) {
      const label = String(country).trim()
      if (label) values.add(label)
    }
  }
  return [...values].sort()
})

const filteredBowlerProjects = computed(() => {
  const selectedProducts = bowlerProductFilters.value.products.filter(Boolean)
  const selectedRegions = bowlerProductFilters.value.regions.filter(Boolean)
  const selectedAreas = bowlerProductFilters.value.areas.filter(Boolean)
  const selectedCountries = bowlerProductFilters.value.countries.filter(Boolean)

  return filteredProjects.value.filter((project) => {
    if (selectedProducts.length) {
      const projectProducts = (project.products ?? []).map((item) => String(item).trim())
      const matchesProduct = projectProducts.some((item) => selectedProducts.includes(item))
      if (!matchesProduct) return false
    }
    if (selectedRegions.length && !selectedRegions.includes(project.region)) return false
    if (selectedAreas.length) {
      const projectAreas = (project.areas ?? []).map((item) => String(item).trim())
      const matchesArea = projectAreas.some((item) => selectedAreas.includes(item))
      if (!matchesArea) return false
    }
    if (selectedCountries.length) {
      const projectCountries = (project.countries ?? []).map((item) => String(item).trim())
      const matchesCountry = projectCountries.some((item) => selectedCountries.includes(item))
      if (!matchesCountry) return false
    }
    return true
  })
})

const productRows = computed(() => {
  const bucket = {}
  for (const project of filteredBowlerProjects.value) {
    const products = project.products?.length ? project.products : ['Unassigned']
    const m = projectMetrics(project)
    // Split FTE evenly across tagged products to avoid double-counting display inflation.
    const share = products.length || 1
    for (const raw of products) {
      const label = String(raw).trim() || 'Unassigned'
      if (!bucket[label]) {
        bucket[label] = {
          key: label,
          label,
          projects: 0,
          migratable: 0,
          actuals: 0,
          pipeline: 0
        }
      }
      bucket[label].projects += 1
      bucket[label].migratable += m.migratable / share
      bucket[label].actuals += m.actuals / share
      bucket[label].pipeline += m.pipeline / share
    }
  }
  return Object.values(bucket)
    .map((row) => ({
      ...row,
      migratable: Math.round(row.migratable),
      actuals: Math.round(row.actuals),
      pipeline: Math.round(row.pipeline),
      gap: Math.max(0, Math.round(row.migratable) - Math.round(row.actuals))
    }))
    .sort((a, b) => b.migratable - a.migratable)
})

const productBowlerSummary = computed(() => {
  const summary = { migratable: 0, actuals: 0, gap: 0 }
  for (const row of productRows.value) {
    summary.migratable += row.migratable
    summary.actuals += row.actuals
  }
  summary.gap = Math.max(0, summary.migratable - summary.actuals)
  return summary
})

const bpmMonthColumns = computed(() => {
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
  return months.map((month, index) => ({
    key: index + 1,
    label: `${month} ${bpmYear.value}`
  }))
})

const productMonthlyRows = computed(() => {
  const monthBuckets = {}
  const productNames = new Set([...bpmRofoRows.value.map((row) => row.product), ...bpmActualRows.value.map((row) => row.product)])

  for (const product of productNames) {
    const name = String(product || '').trim() || 'Overall'
    monthBuckets[name] = {
      product: name,
      target: Array(13).fill(0),
      actual: Array(13).fill(0),
      gap: Array(13).fill(0)
    }
  }

  if (!productNames.size) {
    return [{ product: 'Overall', target: Array(13).fill(0), actual: Array(13).fill(0), gap: Array(13).fill(0) }]
  }

  for (const row of bpmRofoRows.value) {
    const product = String(row.product || '').trim() || 'Overall'
    const month = normalizeMonthKey(row.onboarding_month, bpmYear.value)
    if (!month) continue
    const value = normalizeBpmNumber(row.positions_to_be_offshored_in_gsc) || normalizeBpmNumber(row.rofo_value) || normalizeBpmNumber(row.positions_to_be_offshored)
    if (!monthBuckets[product]) monthBuckets[product] = { product, target: Array(13).fill(0), actual: Array(13).fill(0), gap: Array(13).fill(0) }
    monthBuckets[product].target[month] += value
    monthBuckets[product].target[12] += value
  }

  for (const row of bpmActualRows.value) {
    const product = String(row.product || '').trim() || 'Overall'
    const month = normalizeMonthKey(row.onboarding_month, bpmYear.value)
    if (!month) continue
    const value = normalizeBpmNumber(row.positions_to_be_offshored_in_gsc) || normalizeBpmNumber(row.actual_value) || normalizeBpmNumber(row.positions_to_be_offshored)
    if (!monthBuckets[product]) monthBuckets[product] = { product, target: Array(13).fill(0), actual: Array(13).fill(0), gap: Array(13).fill(0) }
    monthBuckets[product].actual[month] += value
    monthBuckets[product].actual[12] += value
  }

  const result = Object.values(monthBuckets).map((entry) => {
    for (let month = 1; month <= 12; month += 1) {
      entry.gap[month] = entry.target[month] - entry.actual[month]
    }
    entry.gap[12] = entry.target[12] - entry.actual[12]
    return entry
  })

  const overall = { product: 'Overall', target: Array(13).fill(0), actual: Array(13).fill(0), gap: Array(13).fill(0) }
  for (const entry of result) {
    for (let month = 1; month <= 12; month += 1) {
      overall.target[month] += entry.target[month]
      overall.actual[month] += entry.actual[month]
      overall.gap[month] = overall.target[month] - overall.actual[month]
    }
    overall.target[12] += entry.target[12]
    overall.actual[12] += entry.actual[12]
    overall.gap[12] = overall.target[12] - overall.actual[12]
  }

  return [overall, ...result.filter((entry) => entry.product !== 'Overall')].sort((a, b) => {
    if (a.product === 'Overall') return -1
    if (b.product === 'Overall') return 1
    return a.product.localeCompare(b.product)
  })
})

const rowGroupValue = (group, type, key) => {
  if (key === 'total') return group[type][12] ?? 0
  return group[type][key] ?? 0
}

const monthCellClass = (type, value) => {
  if (type === 'target') return value >= 0 ? 'month-cell month-cell--target' : 'month-cell month-cell--negative'
  if (type === 'actual') return value >= 0 ? 'month-cell month-cell--actual' : 'month-cell month-cell--negative'
  return value >= 0 ? 'month-cell month-cell--gap-positive' : 'month-cell month-cell--gap-negative'
}

const productRankedItems = computed(() => {
  const max = productRows.value[0]?.migratable || 1
  return productRows.value.slice(0, 8).map((row) => ({
    key: row.key,
    label: row.label,
    value: row.migratable,
    valueLabel: `${formatWholeNumber(row.migratable)} FTE`,
    shareLabel: `${Math.round((row.migratable / max) * 100)}%`,
    pct: Math.round((row.migratable / max) * 100),
    color: '#0077b8'
  }))
})

const narrativeRows = computed(() => {
  const target = kpis.value.migratableFte
  const actuals = kpis.value.actuals
  const pipeline = kpis.value.pipeline
  const gap = Math.max(0, target - actuals - pipeline)
  const pct = (value) => (target ? `${Math.round((value / target) * 100)}%` : '—')

  return [
    {
      label: 'Target (migratable)',
      fte: target,
      pct: '100%',
      commentary: 'Approx. from intake FTE in scope.'
    },
    {
      label: 'Less: Actuals',
      fte: actuals,
      pct: pct(actuals),
      commentary: 'Completed projects to date.'
    },
    {
      label: 'Less: Pipeline',
      fte: pipeline,
      pct: pct(pipeline),
      commentary: 'In review / planning / in progress / at risk.'
    },
    {
      label: 'GAP',
      fte: gap,
      pct: pct(gap),
      commentary: 'Remaining after actuals and pipeline.'
    }
  ]
})

const narrativeCallout = computed(() => {
  const { completionPct, actuals, migratableFte } = kpis.value
  return `${completionPct}% of migratable FTE has been completed (${formatWholeNumber(actuals)} of ${formatWholeNumber(migratableFte)} FTE).`
})

const narrativeBlocks = computed(() => {
  const topProduct = productRows.value[0]
  const atRisk = filteredProjects.value.filter((p) => p.status === 'at_risk').length
  const inFlight = filteredProjects.value.filter((p) => IN_FLIGHT.has(p.status)).length
  const completed = filteredProjects.value.filter((p) => p.status === COMPLETED).length

  const highlights = [
    completed
      ? `${formatWholeNumber(completed)} projects completed in the current selection.`
      : 'No completed projects yet in the current selection.',
    topProduct
      ? `${topProduct.label} leads demand with ~${formatWholeNumber(topProduct.migratable)} migratable FTE.`
      : 'Product mix will appear once intake tags are available.'
  ]

  const focus = [
    atRisk
      ? `${formatWholeNumber(atRisk)} project(s) flagged at risk need attention.`
      : 'No at-risk projects in the current selection.',
    kpis.value.fteGap
      ? `Open FTE gap remains ${formatWholeNumber(kpis.value.fteGap)} against migratable volume.`
      : 'No open FTE gap against migratable volume.'
  ]

  const levers = [
    inFlight
      ? `Keep ${formatWholeNumber(inFlight)} in-flight project(s) moving through approvals and delivery.`
      : 'Build pipeline by progressing new intake into review/planning.',
    'Use filters to isolate region / product pockets with the largest gap.',
    'Open project detail from the original dashboard when action is needed.'
  ]

  return [
    { title: 'Highlights', tone: 'success', items: highlights },
    { title: 'Focus', tone: 'warning', items: focus },
    { title: 'Levers', tone: 'info', items: levers }
  ]
})

const onSearchInput = (event) => {
  searchQuery.value = event.target?.value ?? ''
}
const onFilterRegion = (event) => {
  filterRegion.value = event.detail?.value ?? ''
}
const onFilterMigrationType = (event) => {
  filterMigrationType.value = event.detail?.value ?? ''
}
const onFilterProduct = (event) => {
  filterProduct.value = event.detail?.value ?? ''
}

const clearFilters = () => {
  searchQuery.value = ''
  filterRegion.value = ''
  filterMigrationType.value = ''
  filterProduct.value = ''
  filterStatus.value = ''
}

const onBpmYearChange = (event) => {
  bpmYear.value = Number(event.target?.value ?? new Date().getFullYear())
  void loadBpmExecutiveSummary()
  void loadExecutiveSummaryNotes()
}

const openExecutiveNoteEditor = (note) => {
  editingExecutiveNote.value = note.section
  executiveNoteDraft.value = {
    title: note.title || 'Highlights',
    body: note.body || ''
  }
}

const saveExecutiveNote = async () => {
  if (!editingExecutiveNote.value) return
  try {
    const { data } = await axios.post('/api/executive-summary-notes/data/', {
      year: bpmYear.value,
      section: editingExecutiveNote.value,
      title: executiveNoteDraft.value.title,
      body: executiveNoteDraft.value.body
    })
    const updated = data?.note
    if (updated) {
      const index = executiveSummaryNotes.value.findIndex((item) => item.section === updated.section)
      if (index >= 0) {
        executiveSummaryNotes.value[index] = { ...executiveSummaryNotes.value[index], ...updated }
      } else {
        executiveSummaryNotes.value.push(updated)
      }
    }
    editingExecutiveNote.value = null
  } catch (error) {
    console.error('Unable to save Executive Summary note', error)
  }
}

const loadExecutiveSummaryNotes = async () => {
  try {
    const { data } = await axios.get('/api/executive-summary-notes/', { params: { year: bpmYear.value } })
    const notes = Array.isArray(data?.notes) ? data.notes : []
    const ordered = executiveSummaryOrder.map((section) => {
      const match = notes.find((note) => note.section === section)
      return match || {
        id: null,
        section,
        title: section.charAt(0).toUpperCase() + section.slice(1),
        body: ''
      }
    })
    executiveSummaryNotes.value = ordered
  } catch (error) {
    executiveSummaryNotes.value = executiveSummaryOrder.map((section) => ({
      id: null,
      section,
      title: section.charAt(0).toUpperCase() + section.slice(1),
      body: ''
    }))
  }
}

const viewRelatedProjects = (section) => {
  // Route to migration intake — include bpmYear and section as query params to help filtering from the intake page if supported
  router.push({ path: '/migration-intake-submissions', query: { bpmYear: String(bpmYear.value), section } })
}

const loadBpmExecutiveSummary = async () => {
  try {
    const [rofoResponse, actualResponse] = await Promise.all([
      axios.get('/api/bpm-rofo/', { params: { year: bpmYear.value } }),
      axios.get('/api/bpm-actual/', { params: { year: bpmYear.value } })
    ])

    const rofoRows = rofoResponse.data?.rows ?? []
    const actualRows = actualResponse.data?.rows ?? []

    const target = rofoRows.reduce((sum, row) => {
      const value =
        normalizeBpmNumber(row.positions_to_be_offshored_in_gsc) ||
        normalizeBpmNumber(row.rofo_value) ||
        normalizeBpmNumber(row.positions_to_be_offshored) ||
        normalizeBpmNumber(row.value)
      return sum + value
    }, 0)

    const withinBudget = actualRows.reduce((sum, row) => {
      const partFlag = normalizePartFlag(
        row.part_not_part_of_rofo ?? row.part_not_part ?? row.part ?? row.rofo_flag ?? row.rofo_status
      )
      if (partFlag !== 'yes') return sum
      const value =
        normalizeBpmNumber(row.positions_to_be_offshored_in_gsc) ||
        normalizeBpmNumber(row.actual_value) ||
        normalizeBpmNumber(row.positions_to_be_offshored) ||
        normalizeBpmNumber(row.value)
      return sum + value
    }, 0)

    const beyondBudget = actualRows.reduce((sum, row) => {
      const partFlag = normalizePartFlag(
        row.part_not_part_of_rofo ?? row.part_not_part ?? row.part ?? row.rofo_flag ?? row.rofo_status
      )
      if (partFlag !== 'no') return sum
      const value =
        normalizeBpmNumber(row.positions_to_be_offshored_in_gsc) ||
        normalizeBpmNumber(row.actual_value) ||
        normalizeBpmNumber(row.positions_to_be_offshored) ||
        normalizeBpmNumber(row.value)
      return sum + value
    }, 0)

    bpmRofoRows.value = rofoRows
    bpmActualRows.value = actualRows

    bpmSummary.value = {
      target: Math.round(target),
      withinBudget: Math.round(withinBudget),
      beyondBudget: Math.round(beyondBudget)
    }
  } catch (error) {
    bpmRofoRows.value = []
    bpmActualRows.value = []
    bpmSummary.value = { target: 0, withinBudget: 0, beyondBudget: 0 }
  }
}

const tgSummary = ref([])

const loadProjects = async () => {
  loading.value = true
  loadError.value = ''
  try {
    const { data } = await axios.get('/api/migration-dashboard/projects/')
    projects.value = data.rows ?? []
    // backend now returns tg_summary inside summary
    tgSummary.value = (data.summary && data.summary.tg_summary) || []
  } catch (error) {
    loadError.value =
      error?.response?.data?.error ?? 'Unable to load migration projects. Please try again.'
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  access.value = await fetchMyAttributesAccess({ force: true })
  loadProjects()
  void loadBpmExecutiveSummary()
  void loadExecutiveSummaryNotes()
})
</script>

<style scoped>
.dashboard-canvas {
  --dash-accent: #42b0d5;
  --dash-primary: #0077b8;
  --dash-deep: #003f6e;
  --dash-success: #6daa28;
  --dash-warning: #f3880e;
  --dash-border: rgba(22, 22, 22, 0.08);
  --dash-shadow: 0 2px 3px rgba(15, 23, 42, 0.05), 0 10px 22px rgba(0, 63, 110, 0.08);
}

.dashboard-layout {
  display: grid;
  gap: 20px;
}

.dash-toolbar {
  align-items: end;
  display: grid;
  gap: 12px;
  grid-template-columns: minmax(0, 1fr) auto;
}

.dash-toolbar__filters {
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.dash-toolbar__actions {
  align-items: center;
  display: flex;
  gap: 8px;
}

.page-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.page-tabs__btn {
  background: #fff;
  border: 1px solid var(--dash-border);
  border-radius: 999px;
  color: #425466;
  cursor: pointer;
  font-family: 'Maersk Text', sans-serif;
  font-size: 13px;
  font-weight: 600;
  padding: 8px 14px;
  transition: background 0.15s ease, border-color 0.15s ease, color 0.15s ease;
}

.page-tabs__btn--active {
  background: #003f6e;
  border-color: #003f6e;
  color: #fff;
}

.page-note {
  color: #5b6b7c;
  font-size: 13px;
  margin: 0;
}

.project-health-filters,
.bowler-product-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 18px;
}

.project-health-filter,
.bowler-product-filter {
  display: flex;
  flex: 1 1 180px;
  flex-direction: column;
  gap: 6px;
  min-width: 180px;
}

.project-health-filter label,
.bowler-product-filter label {
  color: #425466;
  font-size: 12px;
  font-weight: 600;
}

.multi-select {
  position: relative;
  width: 100%;
}

.multi-select__trigger {
  align-items: center;
  background: #fff;
  border: 1px solid rgba(15, 23, 42, 0.18);
  border-radius: 8px;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.4);
  color: #161616;
  cursor: pointer;
  display: flex;
  font: inherit;
  justify-content: space-between;
  min-height: 42px;
  padding: 8px 12px;
  text-align: left;
  width: 100%;
}

.multi-select__trigger:disabled {
  background: #f5f7fa;
  color: #7a8794;
  cursor: not-allowed;
}

.multi-select__panel {
  background: #fff;
  border: 1px solid rgba(15, 23, 42, 0.18);
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.12);
  margin-top: 6px;
  max-height: 260px;
  overflow: hidden;
  position: absolute;
  width: 100%;
  z-index: 10;
}

.multi-select__search {
  border: 1px solid rgba(15, 23, 42, 0.14);
  border-radius: 6px;
  box-sizing: border-box;
  color: #161616;
  font: inherit;
  margin: 10px 10px 8px;
  padding: 9px 10px;
  width: calc(100% - 20px);
}

.multi-select__select-all {
  background: transparent;
  border: 0;
  color: #0077b8;
  cursor: pointer;
  font: inherit;
  font-weight: 600;
  padding: 0 10px 8px;
  text-align: left;
}

.multi-select__list {
  display: flex;
  flex-direction: column;
  max-height: 190px;
  overflow-y: auto;
  padding: 0 6px 10px;
}

.multi-select__option {
  align-items: center;
  cursor: pointer;
  display: flex;
  gap: 10px;
  padding: 8px 8px;
}

.multi-select__option:hover {
  background: #f3f8fc;
  border-radius: 6px;
}

.multi-select__option input {
  accent-color: #0077b8;
  margin: 0;
}

.multi-select__chevron {
  color: #425466;
  font-size: 18px;
  line-height: 1;
}

.placeholder-hint {
  color: #7a8794;
  font-size: 10px;
  line-height: 1.35;
}

.executive-year-picker {
  display: flex;
  justify-content: flex-end;
  margin-top: -8px;
}

.compact-year-select {
  align-items: center;
  background: #fff;
  border: 1px solid var(--dash-border);
  border-radius: 10px;
  box-shadow: var(--dash-shadow);
  display: inline-flex;
  gap: 8px;
  padding: 7px 10px;
}

.compact-year-select span {
  color: #5b6b7c;
  font-size: 12px;
  font-weight: 600;
}

.compact-year-select select {
  background: #f8fafc;
  border: 1px solid rgba(15, 23, 42, 0.12);
  border-radius: 8px;
  color: #161616;
  font: inherit;
  padding: 6px 10px;
}

.kpi-row {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(5, minmax(0, 1fr));
}

.kpi-row--compact {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.kpi-row--bpm {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.bpm-kpi-row {
  margin-top: 12px;
}

.bpm-kpi-card {
  border-top: 4px solid var(--dash-primary);
  position: relative;
  overflow: hidden;
}

.bpm-kpi-card--bpm-target {
  background: linear-gradient(180deg, rgba(0, 119, 184, 0.08), #fff 30%);
  border-top-color: #0077b8;
}

.bpm-kpi-card--bpm-within {
  background: linear-gradient(180deg, rgba(36, 174, 110, 0.08), #fff 30%);
  border-top-color: #24ae6e;
}

.bpm-kpi-card--bpm-beyond {
  background: linear-gradient(180deg, rgba(232, 84, 84, 0.08), #fff 30%);
  border-top-color: #e85454;
}

.bpm-kpi-card__topline {
  align-items: center;
  display: flex;
  justify-content: space-between;
  gap: 8px;
}

.bpm-kpi-card__dot {
  background: currentColor;
  border-radius: 50%;
  display: inline-block;
  height: 10px;
  width: 10px;
  opacity: 0.8;
}

.bpm-kpi-card__formula {
  color: #5b6b7c;
  font-size: 10px;
  line-height: 1.4;
}

.executive-summary-notes {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin-top: 22px;
}

.executive-note-card {
  background: #fff;
  border: 1px solid var(--dash-border);
  border-radius: 16px;
  box-shadow: var(--dash-shadow);
  display: grid;
  gap: 12px;
  min-height: 180px;
  padding: 16px 18px;
}

.executive-note-card--highlights {
  border-top: 4px solid #24ae6e;
}

.executive-note-card--focus {
  border-top: 4px solid #f3880e;
}

.executive-note-card--levers {
  border-top: 4px solid #0077b8;
}

.executive-note-card__head {
  align-items: center;
  display: flex;
  justify-content: space-between;
  gap: 8px;
}

.executive-note-icon {
  font-size: 18px;
  line-height: 1;
}

.executive-note-card__eyebrow {
  color: #425466;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.executive-note-actions {
  display:flex;
  gap:8px;
  align-items:center;
}

.executive-note-card__link {
  background: transparent;
  border: 1px solid rgba(0,63,110,0.12);
  color: #003f6e;
  padding: 6px 10px;
  border-radius: 8px;
  cursor: pointer;
}

.executive-note-card__edit,
.inline-btn {
  background: #003f6e;
  border: 0;
  border-radius: 8px;
  color: #fff;
  cursor: pointer;
  font: inherit;
  font-weight: 600;
  padding: 7px 11px;
}

.executive-note-card__body {
  color: #263745;
  line-height: 1.6;
  margin: 0;
}

/* Further potential */
.further-potential {
  margin-top: 18px;
}
.further-potential h4 {
  margin: 0 0 12px 0;
  color: #263745;
  font-size: 14px;
  font-weight: 800;
  letter-spacing: 0.02em;
}
.further-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}
.fcol {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  background: linear-gradient(180deg, #ffffff, #fbfdff);
  border: 1px solid rgba(0,63,110,0.06);
  border-radius: 12px;
  padding: 18px 18px;
  text-align: left;
  min-height: 80px;
  box-shadow: 0 8px 22px rgba(2,48,84,0.04);
  position: relative;
}

.fcol::after {
  /* top-right small dot */
  content: '';
  position: absolute;
  right: 12px;
  top: 12px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: rgba(0,63,110,0.12);
}

.fcell {
  color: #425466;
  font-weight: 700;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.fcell::before {
  content: '';
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #0077b8;
  opacity: 0.95;
}

.fcol:nth-child(1) .fcell::before { background: #24ae6e; }
.fcol:nth-child(2) .fcell::before { background: #e85454; }
.fcol:nth-child(3) .fcell::before { background: #0077b8; }

.fvalue {
  font-size: 28px;
  font-weight: 900;
  margin-top: 8px;
  color: #0f2a3b;
}

.further-note {
  margin-top: 14px;
  color: #6b7784;
  font-size: 12px;
  line-height: 1.4;
  background: #ffffff;
  border: 1px dashed rgba(0,63,110,0.04);
  padding: 10px 12px;
  border-radius: 8px;
}

.fcol:hover {
  transform: translateY(-4px);
  transition: transform 0.18s ease;
  box-shadow: 0 14px 34px rgba(2,48,84,0.06);
}
.fcell {
  color: #425466;
  font-weight: 700;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.fcell::before {
  content: '';
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #0077b8;
  opacity: 0.95;
}
.fcol:nth-child(1) .fcell::before { background: #24ae6e; }
.fcol:nth-child(2) .fcell::before { background: #e85454; }
.fcol:nth-child(3) .fcell::before { background: #0077b8; }
.fvalue {
  font-size: 26px;
  font-weight: 900;
  margin-top: 8px;
  color: #0f2a3b;
}
.further-note {
  margin-top: 12px;
  color: #6b7784;
  font-size: 12px;
  line-height: 1.4;
  background: #fbfdff;
  border: 1px dashed rgba(0,63,110,0.04);
  padding: 10px 12px;
  border-radius: 8px;
}

/* dummy badges and pipeline note */
.dummy-number { font-weight: 900; color: #003f6e }
.dummy-note { font-size: 12px; color: #7a8794; margin-top: 6px }
.badge-dummy {
  display: inline-block;
  margin-left: 8px;
  padding: 4px 8px;
  font-size: 11px;
  background: rgba(0,63,110,0.06);
  color: #003f6e;
  border-radius: 999px;
  font-weight: 700;
}


/* subtle hover emphasis for interactive feel */
.fcol:hover {
  transform: translateY(-4px);
  transition: transform 0.18s ease;
  box-shadow: 0 10px 26px rgba(2,48,84,0.06);
}

/* make exec table values stronger to match the updated cards */
.exec-table .value {
  font-size: 22px;
  color: #003f6e;
}



/* Exec commentary */
.exec-table .commentary { color:#425466; font-weight:700; width:180px }
.exec-table .commentary-value { color:#263745 }

/* Executive split layout: left = metrics, right = notes */
.split-grid--executive {
  display: grid;
  gap: 16px;
  grid-template-columns: minmax(0, 1fr) 360px;
  align-items: start;
  margin-top: 20px;
}

.exec-metrics {
  display: grid;
  gap: 12px;
}

.exec-table {
  width: 100%;
  border-collapse: collapse;
}

.exec-table td {
  padding: 12px 10px;
  vertical-align: middle;
}

.exec-table .label {
  width: 160px;
  color: #425466;
  font-weight: 700;
}

.exec-table .value {
  font-size: 20px;
  font-weight: 800;
}


.executive-note-column {
  display: grid;
  gap: 12px;
}

.executive-note-editor {
  background: #fff;
  border: 1px solid var(--dash-border);
  border-radius: 16px;
  box-shadow: var(--dash-shadow);
  display: grid;
  gap: 12px;
  margin-top: 16px;
  padding: 18px;
}

.executive-note-editor__header {
  align-items: center;
  display: flex;
  justify-content: space-between;
  gap: 8px;
}

.executive-note-editor__header h3 {
  color: #161616;
  font-family: 'Maersk Headline', 'Maersk Text', sans-serif;
  font-size: 18px;
  margin: 0;
}

.editor-field {
  display: grid;
  gap: 6px;
}

.editor-field span {
  color: #425466;
  font-size: 12px;
  font-weight: 700;
}

.editor-field input,
.editor-field textarea {
  border: 1px solid rgba(15, 23, 42, 0.18);
  border-radius: 8px;
  font: inherit;
  padding: 9px 10px;
}

.editor-field textarea {
  resize: vertical;
}

.editor-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.inline-btn--secondary {
  background: #f3f8fc;
  color: #003f6e;
}

.inline-btn--primary {
  background: #003f6e;
}

.kpi-card,
.dash-card {
  background: #fff;
  border: 1px solid var(--dash-border);
  border-radius: 16px;
  box-shadow: var(--dash-shadow);
}

.kpi-card {
  display: grid;
  gap: 6px;
  padding: 16px 18px;
}

.kpi-card__label {
  color: #5b6b7c;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.kpi-card__value {
  color: #161616;
  font-family: 'Maersk Headline', 'Maersk Text', sans-serif;
  font-size: 32px;
  font-weight: 800;
  line-height: 1.08;
}

.kpi-card__hint {
  color: #7a8794;
  font-size: 12px;
}

.kpi-card__head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.kpi-card__pills {
  display: flex;
  gap: 8px;
  margin-top: 10px;
}

.kpi-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: 999px;
  font-weight: 700;
  font-size: 12px;
}

.kpi-pill--muted {
  background: rgba(22, 22, 22, 0.04);
  color: #425466;
}

.kpi-pill--accent {
  /* Use MDS shallow blue when not representing achievement */
  background: color-mix(in srgb, var(--dash-primary) 12%, white);
  color: var(--dash-primary);
}

.dash-card {
  display: grid;
  gap: 14px;
  padding: 18px;
  /* ensure card content aligns to top when neighbouring grid column is taller */
  align-content: start;
  min-height: 0;
}

.dash-card__head {
  align-items: baseline;
  display: flex;
  gap: 12px;
  justify-content: space-between;
}

.dash-card__head h3 {
  color: #161616;
  font-family: 'Maersk Headline', 'Maersk Text', sans-serif;
  font-size: 16px;
  font-weight: 700;
  margin: 0;
}

.dash-card__meta {
  color: #7a8794;
  font-size: 12px;
}

.split-grid {
  display: grid;
  gap: 16px;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1.1fr);
}

.split-grid--narrative {
  grid-template-columns: minmax(0, 1.3fr) minmax(260px, 0.9fr);
}

.narrative-left,
.narrative-right {
  display: grid;
  gap: 16px;
}

.stage-stack {
  display: grid;
  gap: 8px;
}

.stage-stack__row {
  align-items: center;
  background: transparent;
  border: 0;
  cursor: pointer;
  display: grid;
  gap: 10px;
  grid-template-columns: minmax(96px, 130px) minmax(0, 1fr) auto;
  padding: 0;
  text-align: left;
}

.stage-stack__label {
  color: #425466;
  font-size: 13px;
}

.stage-stack__track {
  background: #eef3f8;
  border-radius: 999px;
  height: 10px;
  overflow: hidden;
}

.stage-stack__fill {
  display: block;
  height: 100%;
  border-radius: inherit;
}

.stage-stack__value {
  color: #161616;
  font-size: 13px;
  min-width: 28px;
  text-align: right;
}

.region-compare {
  display: grid;
  gap: 12px;
}

/* TG stacked bars (uses backend summary.tg_summary) */
.tg-stack {
  display: grid;
  gap: 8px;
}

.tg-stack__row {
  align-items: center;
  background: transparent;
  border: 0;
  display: grid;
  gap: 10px;
  grid-template-columns: minmax(96px, 130px) minmax(0, 1fr) auto;
  padding: 0;
  text-align: left;
}

.tg-stack__label {
  color: #425466;
  font-size: 13px;
}

.tg-stack__track {
  background: #eef3f8;
  border-radius: 8px;
  height: 28px;
  overflow: hidden;
  display: flex;
  align-items: center;
}

.tg-stack__segment {
  height: 100%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 600;
  font-size: 12px;
  white-space: nowrap;
  overflow: hidden;
}

.tg-stack__segment-label {
  padding: 0 6px;
}

.tg-stack__value {
  color: #161616;
  font-size: 13px;
  min-width: 28px;
  text-align: right;
}

/* Nested rows for drilldown */
.manager-row td {
  padding: 8px 12px;
}

.nested-row td {
  padding: 6px 12px;
}

.nested-row.level-1 td:first-child {
  padding-left: 28px;
}

.nested-row.level-2 td:first-child {
  padding-left: 48px;
  font-size: 13px;
  color: #1f2d3a;
}

.expand-btn {
  width: 28px;
  height: 24px;
  margin-right: 8px;
  border-radius: 4px;
  border: 1px solid rgba(0,0,0,0.08);
  background: #fff;
}

.expand-btn.small {
  width: 20px;
  height: 20px;
  font-size: 12px;
}

.region-compare__row {
  display: grid;
  gap: 6px;
}

.region-compare__head {
  align-items: baseline;
  color: #5b6b7c;
  display: flex;
  font-size: 12px;
  justify-content: space-between;
}

.region-compare__head strong {
  color: #161616;
  font-size: 13px;
}

.region-compare__track {
  background: #eef3f8;
  border-radius: 999px;
  height: 12px;
  overflow: hidden;
  position: relative;
}

.region-compare__fill {
  border-radius: inherit;
  display: block;
  height: 100%;
  left: 0;
  position: absolute;
  top: 0;
}

.region-compare__fill--migratable {
  background: rgba(0, 119, 184, 0.28);
}

.region-compare__fill--actuals {
  background: #42b0d5;
}

.legend-row {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
}

.legend-row__item {
  align-items: center;
  color: #5b6b7c;
  display: inline-flex;
  font-size: 12px;
  gap: 6px;
}

.legend-row__item i {
  border-radius: 3px;
  display: inline-block;
  height: 10px;
  width: 10px;
}

.table-shell {
  overflow: auto;
}

.table-shell--wide {
  overflow-x: auto;
}

.data-table {
  border-collapse: collapse;
  min-width: 640px;
  width: 100%;
}

.data-table--monthly {
  min-width: 980px;
}

.data-table th,
.data-table td {
  border-bottom: 1px solid var(--dash-border);
  font-size: 13px;
  padding: 10px 12px;
  text-align: left;
}

.data-table th {
  background: #f5f8fc;
  color: #425466;
  font-weight: 700;
}

.data-table tfoot td {
  background: #f8fafc;
  font-weight: 700;
}

.table-group-label,
.table-sub-label {
  font-weight: 700;
  white-space: nowrap;
}

.table-group-label {
  background: rgba(0, 119, 184, 0.04);
}

.month-cell {
  color: #161616;
  font-weight: 700;
  text-align: center;
  white-space: nowrap;
}

.month-cell--target {
  background: rgba(0, 119, 184, 0.08);
}

.month-cell--actual {
  background: rgba(36, 174, 110, 0.1);
}

.month-cell--gap-positive {
  background: rgba(255, 166, 0, 0.08);
}

.month-cell--gap-negative {
  background: rgba(220, 38, 38, 0.08);
}

.month-cell--negative {
  color: #7a1f1f;
}

.is-gap {
  color: #c2410c;
  font-weight: 700;
}

.is-ahead {
  color: #3f7d14;
  font-weight: 700;
}

.callout {
  background: linear-gradient(135deg, #003f6e 0%, #0077b8 100%);
  border-radius: 16px;
  color: #fff;
  font-family: 'Maersk Text', sans-serif;
  font-size: 15px;
  font-weight: 600;
  line-height: 1.45;
  padding: 18px 20px;
}

.insight-block ul {
  display: grid;
  gap: 8px;
  margin: 0;
  padding-left: 18px;
}

.insight-block li {
  color: #425466;
  font-size: 13px;
  line-height: 1.45;
}

.insight-block__head {
  align-items: center;
  display: flex;
  gap: 8px;
}

.insight-block__accent {
  border-radius: 999px;
  flex-shrink: 0;
  height: 14px;
  width: 4px;
}

.insight-block--success .insight-block__accent {
  background: var(--dash-success);
}

.insight-block--warning .insight-block__accent {
  background: var(--dash-warning);
}

.insight-block--info .insight-block__accent {
  background: var(--dash-primary);
}

.unavailable-list {
  display: grid;
  gap: 12px;
  list-style: none;
  margin: 0;
  padding: 0;
}

.unavailable-list li {
  border: 1px solid var(--dash-border);
  border-radius: 12px;
  display: grid;
  gap: 4px;
  padding: 12px 14px;
}

.unavailable-list strong {
  color: #161616;
  font-size: 14px;
}

.unavailable-list span {
  color: #5b6b7c;
  font-size: 13px;
}

.summary-empty {
  color: #7a8794;
  font-size: 13px;
  margin: 0;
}

@media (max-width: 1100px) {
  .kpi-row,
  .kpi-row--compact,
  .dash-toolbar__filters,
  .split-grid,
  .split-grid--narrative {
    grid-template-columns: 1fr;
  }

  .dash-toolbar {
    grid-template-columns: 1fr;
  }
}

/* Ported visual tokens from MigrationDashboard.vue to harmonize look */
.overview-panel__label {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.overview-panel__hero-row {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.overview-panel__hero-value {
  color: var(--dash-deep);
  font-size: clamp(28px, 3.4vw, 40px);
  font-weight: 800;
  letter-spacing: -0.04em;
  line-height: 1;
}

.overview-panel__badge {
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  padding: 5px 11px;
}

.overview-panel__badge--up {
  background: color-mix(in srgb, var(--dash-success) 16%, white);
  color: #3d6a12;
}

.overview-panel__badge--down {
  background: color-mix(in srgb, #e85454 12%, white);
  color: #b42318;
}

.overview-panel__badge--flat {
  background: rgba(22, 22, 22, 0.06);
  color: #6c757d;
}

.overview-panel__hero-hint {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  font-size: 13px;
  line-height: 1.5;
  margin: 0;
}

.composition-bar__track {
  background: #eef2f6;
  border-radius: 999px;
  display: flex;
  height: 8px;
  overflow: hidden;
}

.composition-bar__segment {
  border: 0;
  cursor: pointer;
  min-width: 3px;
  padding: 0;
  transition: filter 0.18s ease;
}

.composition-bar__segment:hover {
  filter: brightness(1.06);
}

.composition-bar__segment--active {
  box-shadow: inset 0 0 0 2px rgba(0, 63, 110, 0.3);
}

.composition-bar__labels--inline {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 14px;
}

.composition-bar__label {
  align-items: center;
  background: transparent;
  border: 0;
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  cursor: pointer;
  display: inline-flex;
  font-size: 11px;
  gap: 5px;
  padding: 0;
}

.composition-bar__label:hover,
.composition-bar__label--active {
  color: #161616;
}

.composition-bar__label strong {
  color: #161616;
  font-size: 11px;
  font-weight: 700;
}

.composition-bar__dot {
  border-radius: 999px;
  flex-shrink: 0;
  height: 7px;
  width: 7px;
}

.composition-bar__name {
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
