<template>
  <section class="oa-page">
    <div v-if="loading || saving" class="oa-status" role="status">{{ saving ? 'Saving assessment…' : 'Loading opportunity assessment…' }}</div>
    <div v-if="error" class="oa-error" role="alert">
      <p>{{ error }}</p>
      <button type="button" @click="loadAssessment().catch(() => {})">Retry</button>
      <router-link :to="backTo">Back to project</router-link>
    </div>
    <iframe v-if="documentSource" ref="scopeFrame" :key="frameKey" :srcdoc="documentSource" title="Opportunity Assessment task-level scoping" class="oa-frame" />
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { onBeforeRouteLeave, useRoute, useRouter } from 'vue-router'
import axios from 'axios'
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

function buildDocument(data) {
  const config = JSON.stringify(data).replace(/</g, '\\u003c')
  let source = scopeTemplate
    .replace(/<header class="top">[\s\S]*?<\/header>/, '')
    .replace('<script>', `<script>window.OA_CONFIG=${config};`)
    .replace(/const MIGRATION_ID=.*?;/, 'const MIGRATION_ID=window.OA_CONFIG.migration_request_id;')
    .replace(/const INTAKE=.*?;\r?\n/, 'const INTAKE=window.OA_CONFIG.intake;\n')
    .replace(/const LOCATIONS=.*?;[^\r\n]*/, 'const LOCATIONS=window.OA_CONFIG.locations,DEFAULT_LOC=window.OA_CONFIG.default_location;')
    .replace(/function load\(\)\{[^\r\n]*/, 'function load(){S=JSON.parse(JSON.stringify(window.OA_CONFIG.state));S.task=S.task||[]}')
    .replace('opt([INTAKE.product])', 'opt(INTAKE.catalogue_products.length?INTAKE.catalogue_products:[INTAKE.product])')
    .replace('$("bP").value=INTAKE.product;', '$("bP").selectedIndex=0;')
    .replace('<select id="bP" hidden></select>', '<div class="f" id="productField" hidden><label>Product</label><select id="bP"></select><div class="hint"></div></div>')
    .replace('onclick="history.back()"', 'id="backBtn"')
    .replace('setDirty(ok>0);render();', 'if(ok)setDirty(true);render();')
    .replace('$("save").onclick=()=>{localStorage.setItem(STORE,JSON.stringify(S));setDirty(false);toast("Saved")};', '')
    .replace('$("reload").onclick=()=>{if(dirty&&!confirm("Discard unsaved changes?"))return;load();setDirty(false);if(mode)setMode(mode)};', '')
  const integration = `
const HOST_ORIGIN=parent.location.origin,requests=new Map();let requestSeq=0;
function requestParent(action,payload){return new Promise((resolve,reject)=>{const id=++requestSeq;requests.set(id,{resolve,reject});parent.postMessage({type:"oa-scope-request",id,action,payload},HOST_ORIGIN)})}
addEventListener("message",event=>{if(event.source!==parent||event.origin!==HOST_ORIGIN||event.data?.type!=="oa-scope-response")return;const pending=requests.get(event.data.id);if(!pending)return;requests.delete(event.data.id);event.data.error?pending.reject(new Error(event.data.error)):pending.resolve(event.data.data)});
const originalSetDirty=setDirty;
setDirty=function(value){originalSetDirty(value);parent.postMessage({type:"oa-scope-dirty",dirty:value},HOST_ORIGIN)};
if(INTAKE.products.length>1){$("productField").hidden=false;document.querySelector(".bbody").classList.add("multi-product")}
$("bP").onchange=onBP;
$("backBtn").onclick=()=>requestParent("back").catch(error=>toast(error.message));
if(S.mode){setMode(S.mode);document.querySelectorAll(".mcard").forEach(button=>{const on=button.dataset.mode===S.mode;button.classList.toggle("on",on);button.setAttribute("aria-checked",String(on))})}
const originalSetMode=setMode;
setMode=function(value){originalSetMode(value);S.mode=value;setDirty(true)};
$("save").onclick=async()=>{if(!dirty)return;document.body.inert=true;try{S.mode=mode;const result=await requestParent("save",{migration_request_id:MIGRATION_ID,state:S});S=result.state;setDirty(false);render();toast("Saved to database")}catch(error){toast(error.message)}finally{document.body.inert=false}};
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