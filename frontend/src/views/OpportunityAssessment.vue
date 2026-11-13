<template>
  <section class="oa-page">
    <div v-if="loading || saving" class="oa-status" role="status">{{ saving ? 'Saving assessment…' : 'Loading opportunity assessment…' }}</div>
    <div v-if="error" class="oa-error" role="alert">
      <p>{{ error }}</p>
      <button type="button" @click="loadAssessment().catch(() => {})">Retry</button>
    </div>
    <iframe v-if="documentSource" ref="scopeFrame" :key="frameKey" :srcdoc="documentSource" title="Opportunity Assessment task-level scoping" class="oa-frame" />
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { onBeforeRouteLeave, useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { useTopbarBackLink } from '../composables/useTopbarBackLink.js'
import scopeTemplate from '../../../refer doc/WPM_Pulse_OA_Task_Scoping.html?raw'

const route = useRoute()
const router = useRouter()
const scopeFrame = ref(null)
const documentSource = ref('')
const frameKey = ref(0)
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const dirty = ref(false)
let revision = 0
let loadSequence = 0
const endpoint = computed(() => `/api/migration-dashboard/projects/${route.params.id}/opportunity-assessment/task-scope/`)
const backTo = computed(() => route.query.from === 'toll-gates'
  ? `/toll-gates?project=${route.query.project || route.params.id}`
  : `/migration-dashboard/${route.params.id}`)
const backLabel = computed(() => route.query.from === 'toll-gates' ? 'Back to Toll Gates' : 'Back to project')
useTopbarBackLink(backTo, backLabel)

function buildDocument(data) {
  const config = JSON.stringify(data).replace(/</g, '\\u003c')
  const catalogueAdditions = JSON.stringify(data.catalogue_additions || []).replace(/</g, '\\u003c')
  const fpoApprover = escapeHtml(data.fpo_approver_email || 'Not assigned')
  let source = scopeTemplate
    .replace(/<header class="top">[\s\S]*?<\/header>/, '')
    .replace(
      '<span id="fpoApprover">Not assigned</span>',
      `<span id="fpoApprover">${fpoApprover}</span>`
    )
    .replace('<script>', `<script>window.OA_CONFIG=${config};`)
    .replace(/const MIGRATION_ID=.*?;/, 'const MIGRATION_ID=window.OA_CONFIG.migration_request_id;')
    .replace(/const CAT=([^\r\n]*);/, (_match, catalogue) => `const CAT=${catalogue}.concat(${catalogueAdditions});`)
    .replace(/const INTAKE=.*?;\r?\n/, 'const INTAKE=window.OA_CONFIG.intake;\n')
    .replace(/const LOCATIONS=.*?;[^\r\n]*/, 'const LOCATIONS=window.OA_CONFIG.locations,DEFAULT_LOC=window.OA_CONFIG.default_location;')
    .replace(/function load\(\)\{[^\r\n]*/, 'function load(){S=JSON.parse(JSON.stringify(window.OA_CONFIG.state));S.task=S.task||[]}')
    .replace('opt([INTAKE.product])', 'opt(INTAKE.catalogue_products.length?INTAKE.catalogue_products:[INTAKE.product])')
    .replace('$("bP").value=INTAKE.product;', '$("bP").selectedIndex=0;')
    .replace('<select id="bP" hidden></select>', '<div class="f" id="productField" hidden><label>Product</label><select id="bP"></select><div class="hint"></div></div>')
    .replace(/<button class="btn" onclick="history\.back\(\)">[\s\S]*?<\/button>/, '')
    .replace('setDirty(ok>0);render();', 'if(ok)setDirty(true);render();')
    .replace('$("save").onclick=()=>{localStorage.setItem(STORE,JSON.stringify(S));setDirty(false);toast("Saved")};', '')
    .replace('$("reload").onclick=()=>{if(dirty&&!confirm("Discard unsaved changes?"))return;load();setDirty(false);if(mode)setMode(mode)};', '')
  const integration = `
const HOST_ORIGIN=parent.location.origin,requests=new Map();let requestSeq=0;
function requestParent(action,payload){return new Promise((resolve,reject)=>{const id=++requestSeq;requests.set(id,{resolve,reject});parent.postMessage({type:"oa-scope-request",id,action,payload},HOST_ORIGIN)})}
addEventListener("message",event=>{if(event.source!==parent||event.origin!==HOST_ORIGIN||event.data?.type!=="oa-scope-response")return;const pending=requests.get(event.data.id);if(!pending)return;requests.delete(event.data.id);event.data.error?pending.reject(new Error(event.data.error)):pending.resolve(event.data.data)});
function hierarchyKey(row){return [row.product??row.p,row.l1,row.l2,row.l3,row.l4].map(value=>String(value||"").trim().toLowerCase()).join("|")}
let pendingCatalogueRows=[];
function queueCatalogueAcknowledgement(rows){pendingCatalogueRows.push(...(rows||[]))}
function addCatalogueEntries(entries){const known=new Set(CAT.map(row=>row.slice(0,5).map(value=>String(value||"").trim().toLowerCase()).join("|")));let changed=false;(entries||[]).forEach(row=>{const key=hierarchyKey({product:row[0],l1:row[1],l2:row[2],l3:row[3],l4:row[4]});if(!known.has(key)){CAT.push(row);known.add(key);changed=true}});if(changed){if(mode==="cat"){ensureCat();buildFilters();render()}else if(mode==="task"){const selected=$("bL1").value;onBP();if(selected)$("bL1").value=selected;onBL1()}}}
async function refreshCatalogueRequests(){try{const data=await requestParent("fpo-catalogue-refresh");catalogueRequests=data.catalogue_requests||[];addCatalogueEntries(data.catalogue_additions);renderCatalogueReminders();return catalogueRequests}catch(error){toast(error.message||"Unable to refresh FPO request status.");return catalogueRequests}}
async function acknowledgeCatalogueRows(rows){await refreshCatalogueRequests();const candidates=rows||[];for(const item of [...catalogueRequests]){if(item.status!=="approved"||!candidates.some(row=>hierarchyKey(row)===hierarchyKey(item)))continue;try{await requestParent("fpo-catalogue-acknowledge",{request_id:item.id,product:item.product,l1:item.l1,l2:item.l2,l3:item.l3,l4:item.l4});catalogueRequests=catalogueRequests.filter(request=>request.id!==item.id)}catch(error){toast(error.message||"Unable to update the approved catalogue request.")}}renderCatalogueReminders()}
const originalSetDirty=setDirty;
setDirty=function(value){originalSetDirty(value);parent.postMessage({type:"oa-scope-dirty",dirty:value},HOST_ORIGIN)};
renderCatalogueReminders();
$("fpoCancel").onclick=closeFpoRequest;
$("fpoAddEntry").onclick=()=>{if(document.querySelectorAll("#fpoEntries .fpo-entry").length>=100){toast("A request can include up to 100 entries.");return}addFpoEntry()};
$("fpoRequestModal").addEventListener("click",event=>{if(event.target.id==="fpoRequestModal")closeFpoRequest()});
$("fpoRequestForm").addEventListener("submit",event=>{const entries=[...document.querySelectorAll("#fpoEntries .fpo-entry")];const seen=new Map();for(const [index,entry] of entries.entries()){const hierarchy=[...entry.querySelectorAll("[data-field]")].map(input=>input.value.trim().toLowerCase());const key=JSON.stringify(hierarchy);if(seen.has(key)){event.preventDefault();event.stopImmediatePropagation();toast("Hierarchy "+(index+1)+" duplicates Hierarchy "+seen.get(key)+". Change or remove the duplicate.");const field=entry.querySelector('[data-field="l1"]');field.focus();field.scrollIntoView({block:"center"});return}seen.set(key,index+1)}},true);
$("fpoRequestForm").addEventListener("submit",async event=>{event.preventDefault();const button=$("fpoSubmit");button.disabled=true;try{const entries=[...document.querySelectorAll("#fpoEntries .fpo-entry")].map(entry=>Object.fromEntries([...entry.querySelectorAll("[data-field]")].map(input=>[input.dataset.field,input.value.trim()])));const payload={product:$("fpoProduct").value,entries,request_comment:$("fpoReason").value.trim()};const created=await requestParent("fpo-catalogue-request",payload);for(const row of created.entries||[])catalogueRequests.unshift({id:row.id,batch_id:created.batch_id,...row,request_comment:payload.request_comment,status:created.status,decision_comment:"",created_at:new Date().toISOString()});renderCatalogueReminders();closeFpoRequest();const count=created.count||entries.length;toast(count+" FPO request entr"+(count===1?"y":"ies")+" submitted")}catch(error){toast(error?.response?.data?.error||error.message||"Unable to submit the FPO request.")}finally{button.disabled=false}});
if(INTAKE.products.length>1){$("productField").hidden=false;document.querySelector(".bbody").classList.add("multi-product")}
$("bP").onchange=onBP;
if(S.mode){setMode(S.mode);document.querySelectorAll(".mcard").forEach(button=>{const on=button.dataset.mode===S.mode;button.classList.toggle("on",on);button.setAttribute("aria-checked",String(on))})}
const originalSetMode=setMode;
setMode=function(value){originalSetMode(value);S.mode=value;setDirty(true)};
$("save").onclick=async()=>{if(!dirty)return;document.body.inert=true;try{S.mode=mode;const result=await requestParent("save",{migration_request_id:MIGRATION_ID,state:S});S=result.state;setDirty(false);render();const queued=pendingCatalogueRows;pendingCatalogueRows=[];await acknowledgeCatalogueRows(queued);toast("Saved to database")}catch(error){toast(error.message)}finally{document.body.inert=false}};
$("reload").onclick=async()=>{if(dirty&&!confirm("Discard unsaved changes?"))return;document.body.inert=true;try{await requestParent("reload")}catch(error){document.body.inert=false;toast(error.message)}};
document.querySelectorAll(".mcard").forEach(button=>{button.setAttribute("aria-label",button.querySelector("b").textContent)});
document.querySelectorAll(".f select").forEach(select=>{const label=select.closest(".f").querySelector("label");if(label)select.setAttribute("aria-label",label.textContent.replace("*","").trim())});
$("prev").setAttribute("aria-label","Previous page");$("next").setAttribute("aria-label","Next page");
const originalCell=cell;cell=function(row,column){return originalCell(row,column).replace(/<input data-id/g,'<input aria-label="'+esc(column.h)+'" data-id').replace(/<select data-id/g,'<select aria-label="'+esc(column.h)+'" data-id')};
if(mode)render();
`
  const styles = `
<style>
html,body{height:100%;letter-spacing:0}main{padding-bottom:82px}.mcard,.builder,.placeholder{border-radius:8px}.grid{max-height:calc(100vh - 420px);min-height:180px}.bbody.multi-product{grid-template-columns:repeat(5,minmax(0,1fr)) auto}.bbody .f{min-width:0}.foot{flex-wrap:wrap}.bar h1{font-size:18px}.mcard:focus-visible,.btn:focus-visible{outline:2px solid #0073ab;outline-offset:3px}.toast{max-width:calc(100vw - 24px);white-space:normal;overflow-wrap:anywhere}.gfilters .f{min-width:0}.f select,.ctry,.fbtn{max-width:100%}.mbody{min-width:0}.mbody b{overflow-wrap:anywhere}
@media(max-width:1000px){main{padding:12px 14px 90px}.tiles{grid-template-columns:repeat(3,minmax(0,1fr))}.bbody,.bbody.multi-product{grid-template-columns:repeat(2,minmax(0,1fr))}.grid{max-height:55vh}.ctx .src{margin-left:0}.bar{gap:8px}.bar .spacer{flex-basis:100%}}
@media(max-width:600px){.method{grid-template-columns:minmax(0,1fr);gap:10px}.tiles{grid-template-columns:repeat(2,minmax(0,1fr))}.tile{min-width:0;padding:9px}.tile .lbl{overflow-wrap:anywhere}.ctx{gap:8px 14px}.ctx span{overflow-wrap:anywhere;max-width:100%}.gfilters{display:grid;grid-template-columns:repeat(2,minmax(0,1fr))}.gfilters .f select{width:100%}.selbar{flex-wrap:wrap}.bbody,.bbody.multi-product{grid-template-columns:minmax(0,1fr)}.foot{padding:10px 14px}.lock{overflow-wrap:anywhere}.bar .chip{max-width:100%;overflow-wrap:anywhere}.pager{flex-wrap:wrap}.mcard{padding:12px}.mnum{width:26px;height:26px}.mbody b{font-size:13px}}
</style>`
  return source.replace('</head>', `${styles}</head>`).replace('<\/script></body>', `${integration}<\/script></body>`)
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

async function loadAssessment() {
  const sequence = ++loadSequence
  loading.value = true
  error.value = ''
  try {
    const { data } = await axios.get(endpoint.value)
    if (sequence !== loadSequence) return
    revision = data.revision
    dirty.value = false
    documentSource.value = buildDocument(data)
    frameKey.value += 1
  } catch (failure) {
    if (sequence === loadSequence) error.value = failure.response?.data?.error || 'Unable to load opportunity assessment.'
    throw failure
  } finally {
    if (sequence === loadSequence) loading.value = false
  }
}

async function onMessage(event) {
  if (event.source !== scopeFrame.value?.contentWindow || event.origin !== location.origin) return
  const message = event.data
  if (message?.type === 'oa-scope-dirty') {
    dirty.value = Boolean(message.dirty)
    return
  }
  if (message?.type !== 'oa-scope-request') return
  const target = event.source
  try {
    let data
    if (message.action === 'save') {
      if (saving.value) throw new Error('A save is already in progress.')
      saving.value = true
      const response = await axios.post(endpoint.value, { ...message.payload, revision })
      revision = response.data.revision
      data = response.data
    } else if (message.action === 'fpo-catalogue-request') {
      const response = await axios.post(
        `/api/migration-dashboard/projects/${route.params.id}/opportunity-assessment/catalogue-requests/`,
        message.payload
      )
      data = response.data
    } else if (message.action === 'fpo-catalogue-refresh') {
      const response = await axios.get(endpoint.value)
      data = { catalogue_requests: response.data.catalogue_requests || [], catalogue_additions: response.data.catalogue_additions || [] }
    } else if (message.action === 'fpo-catalogue-acknowledge') {
      const { request_id, ...payload } = message.payload
      const response = await axios.post(
        `/api/migration-dashboard/projects/${route.params.id}/opportunity-assessment/catalogue-requests/${request_id}/acknowledge/`,
        payload
      )
      data = response.data
    } else if (message.action === 'reload') {
      await loadAssessment()
    } else if (message.action === 'back') {
      await router.push(backTo.value)
    } else {
      return
    }
    target.postMessage({ type: 'oa-scope-response', id: message.id, data }, location.origin)
  } catch (failure) {
    target.postMessage({ type: 'oa-scope-response', id: message.id, error: failure.response?.data?.error || failure.message || 'Unable to save. Your changes have been kept.' }, location.origin)
  } finally {
    saving.value = false
  }
}

function beforeUnload(event) {
  if (dirty.value || saving.value) {
    event.preventDefault()
    event.returnValue = ''
  }
}

onBeforeRouteLeave(() => !saving.value && (!dirty.value || window.confirm('Discard unsaved assessment changes?')))
onMounted(() => {
  window.addEventListener('message', onMessage)
  window.addEventListener('beforeunload', beforeUnload)
})
onBeforeUnmount(() => {
  loadSequence += 1
  window.removeEventListener('message', onMessage)
  window.removeEventListener('beforeunload', beforeUnload)
})
watch(() => route.params.id, () => {
  documentSource.value = ''
  void loadAssessment().catch(() => {})
}, { immediate: true })
</script>

<style scoped>
.oa-page { position: relative; display: flex; flex: 1; flex-direction: column; min-height: 0; background: #fff; }
.oa-frame { flex: 1; width: 100%; min-height: 0; border: 0; }
.oa-status { padding: 10px 24px; background: #e1effa; color: #005a87; font-size: 13px; }
.oa-error { padding: 20px 24px; color: #b42318; }
.oa-error button { margin-right: 16px; padding: 6px 12px; cursor: pointer; }
</style>