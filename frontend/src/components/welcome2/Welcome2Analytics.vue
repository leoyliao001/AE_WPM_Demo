<template>
  <section class="analytics">
    <mc-card class="hero-card" variant="bordered" fit="medium" heading="Future Service Model" contentalignment="left">
      <p slot="body" class="hero-lead">
        Integrated analytics from Project B — cost per transaction across <strong>Areas and GSC</strong>,
        volume distribution, readiness tiers, and country-level migration opportunity. Styled with Project A
        layout and MDS components.
      </p>
    </mc-card>

    <!-- Step 1 -->
    <div class="step-head">
      <span class="step-badge">1</span>
      <h2>Cost Position &amp; Three-Month Trend</h2>
    </div>

    <div class="two-col">
      <div class="stack">
        <div class="kpi-grid kpi-grid--2">
          <mc-card
            v-for="kpi in costPositionKpis"
            :key="kpi.id"
            class="kpi-card"
            variant="bordered"
            fit="small"
            contentalignment="left"
          >
            <div class="kpi-inner">
              <span class="metric-label">{{ kpi.label }}</span>
              <strong class="kpi-value" :style="{ color: kpi.accent }">{{ kpi.value }}</strong>
              <span class="kpi-sub">{{ kpi.sub }}</span>
            </div>
          </mc-card>
        </div>

        <mc-card variant="bordered" fit="medium" heading="Volume &amp; Cost Distribution" contentalignment="left">
          <SplitSegmentBar title="Volume split" :total="volumeSplit.total" :segments="volumeSplit.segments" />
          <SplitSegmentBar title="Cost split" :total="costSplit.total" :segments="costSplit.segments" />
          <div class="insight-box">
            Areas accounts for <strong>24% of volume and 52% of cost</strong>; GSC for 76% of volume and 48% of
            cost. The difference reflects the cost-per-transaction gap ($2.59 vs $0.72).
          </div>
        </mc-card>
      </div>

      <mc-card variant="bordered" fit="medium" heading="Three-Month Trend · Feb → Apr 2026" contentalignment="left">
        <TrendChartPanel v-model:metric="trendMetric" :months="trendMonths" :series="activeTrendSeries" />
        <div class="insight-box">{{ activeTrendInsight }}</div>
      </mc-card>
    </div>

    <mc-card
      class="section-card"
      variant="bordered"
      fit="medium"
      heading="Potential Benefit Case — by GSC Capability Tier"
      contentalignment="left"
    >
      <p class="section-intro">
        Area-handled tasks grouped by how much GSC already does the same work elsewhere. Cost saving = Area volume ×
        (Area $2.59/unit − GSC $0.72/unit) if that work ran at the GSC rate.
      </p>

      <div class="tier-grid">
        <mc-card
          v-for="tier in capabilityTiers"
          :key="tier.id"
          class="tier-card"
          variant="bordered"
          fit="small"
          :heading="tier.title"
          :body="`${tier.tasks} tasks · ${tier.fte} Area FTE`"
          contentalignment="left"
        >
          <div class="tier-metrics">
            <div>
              <span class="metric-label">Area Cost</span>
              <strong :style="{ color: tier.color }">{{ formatMoney(tier.areaCost) }}</strong>
            </div>
            <div>
              <span class="metric-label">Cost Saving</span>
              <strong :style="{ color: tier.color }">{{ formatMoney(tier.saving) }}</strong>
            </div>
          </div>
          <p class="tier-note">{{ tier.note }}</p>
        </mc-card>
      </div>

      <div class="quadrant-grid">
        <mc-card
          v-for="(meta, key) in quadrantSummary"
          :key="key"
          class="quadrant-card"
          :class="{ 'quadrant-card--active': activeQuadrant === key }"
          variant="bordered"
          fit="small"
          :heading="`${key} · ${meta.name}`"
          :body="`${meta.tasks} tasks`"
          clickable
          contentalignment="left"
          @click="toggleQuadrant(key)"
        >
          <div class="tier-metrics">
            <div><span class="metric-label">Area FTE</span><strong>{{ meta.areaFte }}</strong></div>
            <div><span class="metric-label">Area Cost</span><strong>{{ formatMoney(meta.areaCost) }}</strong></div>
            <div><span class="metric-label">Modelled diff.</span><strong>{{ formatMoney(meta.save) }}/mo</strong></div>
          </div>
        </mc-card>
      </div>

      <BubbleQuadrantChart :tasks="bubbleTasks" :active-quadrant="activeQuadrant" />

      <mc-card class="shift-card" variant="bordered" fit="medium" heading="Shift scenario — movable Area volume" contentalignment="left">
        <div class="shift-row">
          <label class="shift-label" for="shift-range">Shift {{ shiftPct }}% of movable Area volume to GSC</label>
          <input id="shift-range" v-model.number="shiftPct" class="shift-range" max="100" min="0" type="range" />
        </div>
        <div class="shift-out">
          <div class="shift-box">
            <div class="shift-value">{{ formatMoney(shiftSaving) }}</div>
            <div class="shift-caption">Monthly saving</div>
          </div>
          <div class="shift-box">
            <div class="shift-value">{{ formatMoney(shiftSaving * 12) }}</div>
            <div class="shift-caption">Annual saving</div>
          </div>
          <div class="shift-box">
            <div class="shift-value">{{ Math.round(shiftFte) }}</div>
            <div class="shift-caption">FTE released</div>
          </div>
        </div>
      </mc-card>
    </mc-card>

    <!-- Step 2 -->
    <div class="step-head">
      <span class="step-badge">2</span>
      <h2>The Opportunity — Area Resources &amp; Cost</h2>
    </div>

    <div class="kpi-grid kpi-grid--3">
      <mc-card
        v-for="kpi in opportunityKpis"
        :key="kpi.label"
        class="kpi-card kpi-card--area"
        variant="bordered"
        fit="small"
        contentalignment="left"
      >
        <div class="kpi-inner">
          <span class="metric-label">{{ kpi.label }}</span>
          <strong class="kpi-value kpi-value--area">{{ kpi.value }}</strong>
          <span class="kpi-sub">{{ kpi.sub }}</span>
        </div>
      </mc-card>
    </div>

    <div class="insight-box">
      The 24% of volume handled in Areas represents <strong>350 FTE and $1.20M/month</strong>. This is the resource
      and cost base examined below — by country, by process, and by design ownership.
    </div>

    <mc-card class="section-card" variant="bordered" fit="medium" heading="1 · By Country — Top 10 (51% of Area cost)" contentalignment="left">
      <div class="table-wrap">
        <mc-table
          :data.prop="areaCountryRows"
          :columns.prop="areaCountryColumns"
          datakey="id"
          caption="Top countries by area cost"
          fit="small"
          height="auto"
          outerborderstyle="solid"
          horizontallinestyle="solid"
        />
      </div>
    </mc-card>

    <mc-card class="section-card" variant="bordered" fit="medium" heading="2 · By Process — What Drives the Cost" contentalignment="left">
      <HorizontalBarList :items="processBarItems" />
      <div class="legend legend--design">
        <span><span class="swatch" style="background: #475569" />Designed Area</span>
        <span><span class="swatch" style="background: #94a3b8" />Dual</span>
        <span><span class="swatch" style="background: #0f172a" />Designed GSC</span>
      </div>
      <div class="table-wrap table-wrap--spaced">
        <mc-table
          :data.prop="processTableRows"
          :columns.prop="processTableColumns"
          datakey="id"
          caption="Process breakdown table"
          fit="small"
          height="auto"
          outerborderstyle="solid"
          horizontallinestyle="solid"
        />
      </div>
    </mc-card>

    <mc-card class="section-card" variant="bordered" fit="medium" heading="3 · By Design Ownership — Area, GSC or Both" contentalignment="left">
      <HorizontalBarList :items="designBarItems" />
      <div class="insight-box">
        Of the $1.20M Area cost, the Process Catalogue assigns <strong>83% to Area</strong>, <strong>10% to Dual</strong>,
        and <strong>0.7% to GSC</strong>; <strong>7%</strong> is on tasks not in the catalogue.
      </div>
    </mc-card>

    <!-- Step 2A -->
    <div class="step-head">
      <span class="step-badge step-badge--sub">2A</span>
      <h2>Compliance vs Scope for Design Change</h2>
      <span class="step-hint">two separate questions</span>
    </div>

    <div class="two-col">
      <mc-card variant="bordered" fit="medium" heading="A · Design Compliance" contentalignment="left">
        <HorizontalBarList :items="complianceBarItems" />
        <div class="insight-box">
          Compliance is high: <strong>83% of Area cost</strong> is on tasks the catalogue assigns to Area. Only
          <strong>0.7% ($7.9K)</strong> is on tasks designed for GSC but running in Areas.
        </div>
      </mc-card>

      <mc-card variant="bordered" fit="medium" heading="B · Scope for Design Change" contentalignment="left">
        <div class="scope-grid">
          <mc-card variant="bordered" fit="small" contentalignment="left">
            <div class="kpi-inner">
              <span class="metric-label">Redesign candidates</span>
              <strong class="kpi-value">$968K</strong>
              <span class="kpi-sub">201 tasks, GSC ≥20% elsewhere</span>
            </div>
          </mc-card>
          <mc-card variant="bordered" fit="small" contentalignment="left">
            <div class="kpi-inner">
              <span class="metric-label">Keep / pilot</span>
              <strong class="kpi-value">$26K</strong>
              <span class="kpi-sub">17 tasks, GSC not yet proven</span>
            </div>
          </mc-card>
        </div>
        <div class="insight-box">
          The opportunity is a <strong>design question, not a compliance one</strong>: $968K of Area cost (258 FTE) sits
          on tasks where GSC already handles ≥20% of volume elsewhere.
        </div>
      </mc-card>
    </div>

    <!-- Step 2B -->
    <div class="step-head">
      <span class="step-badge step-badge--sub">2B</span>
      <h2>Design Change — Process Readiness for GSC</h2>
      <span class="step-hint">ranked easiest to hardest</span>
    </div>

    <mc-card class="section-card" variant="bordered" fit="medium" contentalignment="left">
      <p class="section-intro section-intro--tight">
        Processes where Areas carries cost and GSC already handles part of the volume. <strong>Click the expand
        control on any row</strong> to see task-level detail — the action sits at task level.
      </p>
      <ExpandableMcTable
        :rows="designReadinessRows"
        :columns="designReadinessColumns"
        :nested-columns="processTaskDetailColumns"
        caption="Process readiness for GSC"
        nested-caption="Process task detail"
        :nested-title="processNestedTitle"
        :resolve-nested-rows="resolveProcessTasks"
      />
      <div class="legend legend--tiers">
        <span><span class="swatch" style="background: #334155" />Ready to scale (GSC ≥70%)</span>
        <span><span class="swatch" style="background: #64748b" />Partial capability (40–70%)</span>
        <span><span class="swatch" style="background: #94a3b8" />Early capability (&lt;40%)</span>
      </div>
      <div class="insight-box">
        The largest Area-cost processes — Cargo/Container ($514K), Documentation ($192K), Booking ($175K) — all sit in
        <strong>Ready to scale</strong> with GSC already handling 70–84% of their volume.
      </div>
    </mc-card>

    <!-- Step 2C -->
    <div class="step-head">
      <span class="step-badge step-badge--sub">2C</span>
      <h2>By Country — Tasks to Move to GSC</h2>
      <span class="step-hint">ranked by cost saving</span>
    </div>

    <mc-card class="section-card" variant="bordered" fit="medium" contentalignment="left">
      <p class="section-intro section-intro--tight">
        Area-handled tasks that are <strong>Ready to scale</strong> or <strong>Partially capable</strong> — candidates
        to move to GSC. <strong>Click the expand control on any country row</strong> to see its task list.
      </p>
      <ExpandableMcTable
        :rows="countryMoveRows"
        :columns="countryMoveColumns"
        :nested-columns="countryTaskDetailColumns"
        caption="Country-level movable tasks"
        nested-caption="Country task detail"
        :nested-title="countryNestedTitle"
        :resolve-nested-rows="resolveCountryTasks"
      />
      <div class="insight-box">
        Across the top 15 countries, the movable scope totals roughly <strong>$419K/month</strong> in modelled saving.
        India, Brazil, Argentina, Italy and Vietnam carry the largest movable task counts.
      </div>
    </mc-card>

    <p class="footnote">
      <strong>Method:</strong> April 2026 actuals, 262 tasks (Case Management, Cloud Telephony, IONIS). Capability tiers
      from GSC's current share of each task's volume. Cost saving = Area volume × (Area $2.59/unit − GSC $0.72/unit).
      Figures are illustrative and exclude transition cost.
    </p>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'
import {
  areaCountries,
  areaCountryColumns,
  bubbleTasks,
  capabilityTiers,
  complianceItems,
  costPositionKpis,
  costSplit,
  countryMoveCandidates,
  countryMoveColumns,
  designChangeProcesses,
  designOwnership,
  designReadinessColumns,
  opportunityKpis,
  processBreakdown,
  processTableColumns,
  processTaskDetailColumns,
  countryTaskDetailColumns,
  tierLabels,
  quadrantSummary,
  shiftDefaults,
  trendData,
  trendMonths,
  volumeSplit
} from '../../data/serviceModelData'
import { countryTasksByCountry, designChangeTasksByProcess } from '../../data/serviceModelExpandData'
import { formatMoney, formatNumber } from '../../utils/serviceModelFormat'
import SplitSegmentBar from './SplitSegmentBar.vue'
import TrendChartPanel from './TrendChartPanel.vue'
import HorizontalBarList from './HorizontalBarList.vue'
import BubbleQuadrantChart from './BubbleQuadrantChart.vue'
import ExpandableMcTable from './ExpandableMcTable.vue'
import '@maersk-global/mds-components-core/mc-card'
import '@maersk-global/mds-components-core/mc-table'

const trendMetric = ref('cpt')
const activeQuadrant = ref(null)
const shiftPct = ref(35)

const activeTrendSeries = computed(() => trendData[trendMetric.value])
const activeTrendInsight = computed(() => trendData[trendMetric.value].insight)

const toggleQuadrant = (key) => {
  activeQuadrant.value = activeQuadrant.value === key ? null : key
}

const shiftSaving = computed(() =>
  (shiftDefaults.areaVol * shiftPct.value) / 100 * (shiftDefaults.areaCpu - shiftDefaults.gscCpu)
)
const shiftFte = computed(() =>
  (shiftDefaults.areaFte * shiftPct.value) / 100 * (1 - shiftDefaults.gscCpu / shiftDefaults.areaCpu)
)

const areaCountryRows = areaCountries.map((row, index) => ({
  id: index + 1,
  country: row.country,
  fte: row.fte.toFixed(1),
  cost: formatMoney(row.cost),
  volume: formatNumber(row.volume),
  redesignCost: formatMoney(row.redesignCost)
}))

const maxProcessCost = Math.max(...processBreakdown.map((p) => p.cost))

const processBarItems = processBreakdown.map((p) => ({
  label: p.name,
  scalePct: (p.cost / maxProcessCost) * 100,
  value: `${formatMoney(p.cost)} · ${p.fte.toFixed(0)} FTE`,
  segments: [
    { key: 'area', pct: (p.dArea / p.cost) * 100, color: '#475569', title: 'Designed Area', radius: '5px 0 0 5px' },
    { key: 'dual', pct: (p.dDual / p.cost) * 100, color: '#94a3b8', title: 'Dual' },
    {
      key: 'gsc',
      pct: (p.dGsc / p.cost) * 100,
      color: '#0f172a',
      title: 'Designed GSC',
      radius: '0 5px 5px 0'
    }
  ]
}))

const processTableRows = processBreakdown.map((row, index) => ({
  id: index + 1,
  name: row.name,
  fte: row.fte.toFixed(1),
  cost: formatMoney(row.cost),
  volume: formatNumber(row.volume),
  dArea: formatMoney(row.dArea),
  dDual: formatMoney(row.dDual),
  dGsc: formatMoney(row.dGsc)
}))

const maxDesignCost = Math.max(...designOwnership.map((d) => d.cost))

const designBarItems = designOwnership.map((d) => ({
  label: d.name,
  pct: Math.max((d.cost / maxDesignCost) * 100, 1),
  color: d.color,
  value: `${formatMoney(d.cost)} · ${d.fte.toFixed(0)} FTE · ${d.tasks} tasks`
}))

const maxComplianceCost = Math.max(...complianceItems.map((c) => c.cost))

const complianceBarItems = complianceItems.map((c) => ({
  label: c.label,
  pct: Math.max((c.cost / maxComplianceCost) * 100, 1),
  color: c.color,
  value: `${formatMoney(c.cost)} · ${c.pct}%`
}))

const designReadinessRows = designChangeProcesses.map((row, index) => ({
  id: index + 1,
  processKey: row.process,
  l3: row.l3,
  process: row.process,
  system: row.system,
  nsub: row.nsub,
  ntask: row.ntask,
  areaFte: row.areaFte.toFixed(1),
  areaCost: formatMoney(row.areaCost),
  save: formatMoney(row.save),
  gscShare: `${row.gscShare}%`,
  gscCountries: row.gscCountries,
  gapCountries: row.gapCountries,
  tier: row.tier
}))

const processNestedTitle = (row) =>
  `Task-level detail · ${row.process} (${(designChangeTasksByProcess[row.processKey] || []).length} tasks) — action sits here`

const resolveProcessTasks = (row) =>
  (designChangeTasksByProcess[row.processKey] || []).map((task, index) => ({
    id: `${row.id}-${index + 1}`,
    task: task.task,
    sub: task.sub,
    system: task.sys,
    areaFte: task.area_fte.toFixed(1),
    areaCost: formatMoney(task.area_cost),
    save: formatMoney(task.save),
    gscShare: `${task.gsc_share}%`,
    gap: task.gap
  }))

const countryMoveRows = countryMoveCandidates.map((row, index) => ({
  id: index + 1,
  countryKey: row.country,
  country: row.country,
  movableTasks: row.movableTasks,
  areaFte: row.areaFte.toFixed(1),
  movableCost: formatMoney(row.movableCost),
  saving: formatMoney(row.saving)
}))

const countryNestedTitle = (row) => {
  const count = (countryTasksByCountry[row.countryKey] || []).length
  return `Movable tasks · ${row.country} (${count} tasks)`
}

const resolveCountryTasks = (row) =>
  (countryTasksByCountry[row.countryKey] || []).map((task, index) => ({
    id: `${row.id}-${index + 1}`,
    task: task.task,
    areaFte: task.area_fte.toFixed(1),
    areaCost: formatMoney(task.area_cost),
    save: formatMoney(task.save),
    gscShare: `${task.gsc_share}%`,
    tier: tierLabels[task.tier] || `Tier ${task.tier}`
  }))
</script>

<style scoped>
.analytics {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-top: 48px;
}

.hero-card::part(container) {
  background: linear-gradient(135deg, #0077b8 0%, #003f6e 100%);
  border: none;
  color: #fff;
}

.hero-card::part(header-container),
.hero-card::part(body-container) {
  color: rgba(255, 255, 255, 0.95);
}

.hero-lead {
  font-size: 14px;
  line-height: 1.65;
  margin: 0;
  max-width: 860px;
}

.step-head {
  align-items: baseline;
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 8px;
}

.step-head h2 {
  font-size: 18px;
  font-weight: 700;
  margin: 0;
}

.step-badge {
  align-items: center;
  background: #0077b8;
  border-radius: 50%;
  color: #fff;
  display: inline-flex;
  flex-shrink: 0;
  font-size: 13px;
  font-weight: 800;
  height: 30px;
  justify-content: center;
  width: 30px;
}

.step-badge--sub {
  font-size: 11px;
}

.step-hint {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  font-size: 12px;
  margin-left: auto;
}

.two-col {
  display: grid;
  gap: 18px;
  grid-template-columns: 1fr 1fr;
}

.stack {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.kpi-grid {
  display: grid;
  gap: 14px;
}

.kpi-grid--2 {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.kpi-grid--3 {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.kpi-card::part(container) {
  border-left: 4px solid #d9dee3;
}

.kpi-card--area::part(container) {
  border-left-color: #f3880e;
}

.kpi-inner {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.kpi-sub {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  font-size: 12px;
}

.kpi-value {
  font-size: 24px;
  font-weight: 800;
  letter-spacing: -0.02em;
}

.kpi-value--area {
  color: #f3880e;
}

.section-card::part(container),
.hero-card::part(container) {
  border-radius: 14px;
}

.section-intro {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  font-size: 13px;
  line-height: 1.6;
  margin: 0 0 16px;
}

.section-intro--tight {
  margin-bottom: 12px;
}

.insight-box {
  background: rgba(0, 119, 184, 0.06);
  border: 1px solid rgba(0, 119, 184, 0.15);
  border-radius: 10px;
  color: var(--mds_brand_appearance_neutral_default_text-color, #334155);
  font-size: 13px;
  line-height: 1.6;
  margin-top: 14px;
  padding: 13px 16px;
}

.tier-grid,
.quadrant-grid,
.scope-grid {
  display: grid;
  gap: 14px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin-bottom: 16px;
}

.quadrant-card--active::part(container) {
  box-shadow: 0 0 0 2px #0077b8;
}

.tier-metrics {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-top: 8px;
}

.metric-label {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  display: block;
  font-size: 10px;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.tier-note {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  font-size: 11.5px;
  line-height: 1.55;
  margin: 12px 0 0;
}

.shift-card::part(container) {
  background: linear-gradient(135deg, #1e293b, #334155);
  color: #fff;
}

.shift-card::part(header-container) {
  color: #fff;
}

.shift-row {
  margin-top: 8px;
}

.shift-label {
  display: block;
  font-size: 13px;
  margin-bottom: 10px;
}

.shift-range {
  appearance: none;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 5px;
  height: 8px;
  outline: none;
  width: 100%;
}

.shift-range::-webkit-slider-thumb {
  appearance: none;
  background: #fff;
  border-radius: 50%;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
  cursor: pointer;
  height: 24px;
  width: 24px;
}

.shift-out {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(3, 1fr);
  margin-top: 20px;
}

.shift-box {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 10px;
  padding: 14px;
  text-align: center;
}

.shift-value {
  font-size: 24px;
  font-weight: 800;
}

.shift-caption {
  font-size: 11px;
  margin-top: 2px;
  opacity: 0.85;
}

.table-wrap {
  overflow-x: auto;
}

.table-wrap--spaced {
  margin-top: 16px;
}

.legend {
  color: var(--mds_brand_appearance_neutral_weak_text-color, #6c757d);
  display: flex;
  flex-wrap: wrap;
  font-size: 12px;
  gap: 18px;
  margin-top: 8px;
}

.legend span {
  align-items: center;
  display: inline-flex;
  gap: 6px;
}

.swatch {
  border-radius: 3px;
  display: inline-block;
  height: 10px;
  width: 14px;
}

.legend--tiers {
  margin-top: 14px;
}

.footnote {
  color: #94a3b8;
  font-size: 11px;
  line-height: 1.6;
  margin: 8px 0 0;
}

@media (max-width: 1000px) {
  .two-col,
  .kpi-grid--3,
  .tier-grid,
  .quadrant-grid,
  .scope-grid,
  .shift-out {
    grid-template-columns: 1fr;
  }

  .kpi-grid--2 {
    grid-template-columns: 1fr;
  }

  .step-hint {
    margin-left: 0;
    width: 100%;
  }
}
</style>
