<template>
  <section class="oa-page">
    <div v-if="loading || saving" class="oa-status" role="status">{{ saving ? 'Saving assessment…' : 'Loading opportunity assessment…' }}</div>
    <div v-if="error" class="oa-error" role="alert">
      <p>{{ error }}</p>
      <button type="button" @click="loadAssessment().catch(() => {})">Retry</button>
    </div>
    <iframe v-if="documentSource" ref="scopeFrame" :key="frameKey" :srcdoc="documentSource" title="Opportunity Assessment task-level scoping" class="oa-frame" />
    <mc-dialog
      :open="deleteGroupOpen"
      heading="Delete country group?"
      dimension="small"
      showclosebutton
      hasfooterslot
      @closing="closeDeleteGroup(false)"
    >
      <div class="oa-dialog-copy">
        <p>This removes the complete {{ deleteGroupLabel }} country sheet and all assessment data entered for {{ deleteGroupCountries }}.</p>
        <strong>This action cannot be undone.</strong>
      </div>
      <mc-button
        slot="secondaryAction"
        appearance="neutral"
        variant="outlined"
        fit="medium"
        label="Cancel"
        @click="closeDeleteGroup(false)"
      />
      <mc-button
        slot="primaryAction"
        appearance="error"
        variant="filled"
        fit="medium"
        label="Delete group"
        @click="closeDeleteGroup(true)"
      />
    </mc-dialog>
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { onBeforeRouteLeave, useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { useTopbarBackLink } from '../composables/useTopbarBackLink.js'
import scopeTemplate from '../../../refer doc/WPM_Pulse_OA_Task_Scoping.html?raw'
import '@maersk-global/mds-components-core/mc-button'
import '@maersk-global/mds-components-core/mc-dialog'

const route = useRoute()
const router = useRouter()
const scopeFrame = ref(null)
const documentSource = ref('')
const frameKey = ref(0)
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const dirty = ref(false)
const deleteGroupOpen = ref(false)
const deleteGroupLabel = ref('')
const deleteGroupCountries = ref('')
let frameDialogRequest = null
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
    .replace(
      '<section class="builder hidden" id="builder">',
      `<section class="catcountry" id="catCountry">
        <div class="f"><label>Select country <em>*</em></label><button type="button" class="fbtn" id="catCountryBtn">Add country(s)</button><div class="hint">Select one or multiple countries and click Add to create a group.</div></div>
        <div class="countryStats selectorStats" id="countryStats">
          <div><b>Total Countries :</b> <span id="csTotal">0</span></div>
          <div><b>OA Started :</b> <span id="csStarted">0</span></div>
          <div><b>OA Completed :</b> <span id="csDone">0</span></div>
          <div><b>OA Pending :</b> <span id="csPending">0</span></div>
        </div>
      </section>
      <div class="tabrow"><div class="ctabs" id="catTabs"></div></div>
      <section class="builder hidden" id="builder">`
    )
    .replace(
      '<section class="gfilters">',
      '<div id="catGroupNote" class="hidden" role="status"></div><section class="gfilters">'
    )
    .replace(/<button class="btn" onclick="history\.back\(\)">[\s\S]*?<\/button>/, '')
    .replace('setDirty(ok>0);render();', 'if(ok)setDirty(true);render();')
    .replace('$("save").onclick=()=>{localStorage.setItem(STORE,JSON.stringify(S));setDirty(false);toast("Saved")};', '')
    .replace('$("reload").onclick=()=>{if(dirty&&!confirm("Discard unsaved changes?"))return;load();setDirty(false);if(mode)setMode(mode)};', '')
  const integration = `
const HOST_ORIGIN=parent.location.origin,requests=new Map();let requestSeq=0;
function requestParent(action,payload){return new Promise((resolve,reject)=>{const id=++requestSeq;requests.set(id,{resolve,reject});parent.postMessage({type:"oa-scope-request",id,action,payload},HOST_ORIGIN)})}
addEventListener("message",event=>{if(event.source!==parent||event.origin!==HOST_ORIGIN||event.data?.type!=="oa-scope-response")return;const pending=requests.get(event.data.id);if(!pending)return;requests.delete(event.data.id);event.data.error?pending.reject(new Error(event.data.error)):pending.resolve(event.data.data)});
const CATALOGUE_COUNTRIES=[...(window.OA_CONFIG.intake.catalogue_countries?.length?window.OA_CONFIG.intake.catalogue_countries:INTAKE.countries||[])];
const baseRender=render;
const catalogueRows=group=>CAT.map((item,index)=>({id:\`\${group.id}_\${index}\`,...rowFromCat(index),ctry:group.countries.join("; ")}));
function catalogueGroups(){if(!Array.isArray(S.catGroups))S.catGroups=[];return S.catGroups}
function usedCatalogueCountries(){return new Set(catalogueGroups().flatMap(group=>group.countries||[]))}
function activeCatalogueGroup(){return catalogueGroups().find(group=>group.id===S.activeCatGroup)}
function migrateCatalogueState(){
  catalogueGroups();
  if(catalogueGroups().length||!Array.isArray(S.cat)||!S.cat.length)return;
  const countries=[...new Set(S.cat.flatMap(row=>row.ctry&&row.ctry!=="All"?splitC(row.ctry):INTAKE.countries||[]))];
  const group={id:"cg_legacy_1",label:countries.length===1?countries[0]:"Group 1",countries,rows:S.cat};
  S.catGroups=[group];S.activeCatGroup=group.id;
}
function normalizeCatalogueGroupLabels(){
  let sequence=Number(S.catGroupSeq)||0;
  catalogueGroups().forEach((group,index)=>{
    const match=String(group.label||"").match(/^Group\s*(\d+)$/i);
    const number=match?Number(match[1]):index+1;
    group.label="Group"+number;
    sequence=Math.max(sequence,number);
  });
  S.catGroupSeq=sequence;
}
function availableCatalogueCountries(){const used=usedCatalogueCountries();return CATALOGUE_COUNTRIES.filter(country=>!used.has(country))}
function openCountryAddPicker(anchor,available,callback){
  pk.innerHTML=\`<div class="pklist">\${available.map(country=>\`<label><input type="checkbox" value="\${esc(country)}"> \${esc(country)}</label>\`).join("")}</div><div class="pkf"><button type="button" class="btn" id="pkX">Cancel</button><button type="button" class="btn pri" id="pkOk" disabled>Add</button></div>\`;
  const boxes=[...pk.querySelectorAll(".pklist input")],ok=pk.querySelector("#pkOk");
  boxes.forEach(box=>box.onchange=()=>{ok.disabled=!boxes.some(item=>item.checked)});
  pk.classList.remove("hidden");
  const rect=anchor.getBoundingClientRect(),height=pk.offsetHeight;
  pk.style.left=Math.max(8,Math.min(rect.left,innerWidth-262))+"px";
  pk.style.top=(rect.bottom+height+8>innerHeight?Math.max(8,rect.top-height-4):rect.bottom+4)+"px";
  pk.querySelector("#pkX").onclick=closePicker;
  ok.onclick=()=>{callback(boxes.filter(box=>box.checked).map(box=>box.value));closePicker()};
}
function commitCatalogueCountries(selected){
  const countries=[...new Set(selected)].filter(country=>availableCatalogueCountries().includes(country));
  if(!countries.length)return toast("Select at least one country");
  const sequence=Number(S.catGroupSeq||0)+1;S.catGroupSeq=sequence;
  const group={id:\`cg_\${Date.now()}_\${sequence}\`,label:\`Group\${sequence}\`,countries};
  group.rows=catalogueRows(group);
  catalogueGroups().push(group);S.activeCatGroup=group.id;syncActiveCatalogueRows();
  $("catCountryBtn").textContent="Add country(s)";
  renderCatalogueGroups();render();setDirty(true);toast(group.label+" created");
}
function updateCatalogueStats(){
  const started=usedCatalogueCountries().size;
  $("csTotal").textContent=CATALOGUE_COUNTRIES.length;$("csStarted").textContent=started;$("csDone").textContent=0;$("csPending").textContent=Math.max(0,CATALOGUE_COUNTRIES.length-started);
  $("countryStats").classList.toggle("show",mode==="cat");
}
function syncActiveCatalogueRows(){
  const group=activeCatalogueGroup();S.cat=group?group.rows:[];
}
function updateCatalogueVisibility(){
  const show=mode==="cat"&&!!activeCatalogueGroup();
  const countryBulkOption=[...$("bulkField").options].find(option=>option.value==="ctry");
  if(countryBulkOption){countryBulkOption.hidden=mode==="cat";if(mode==="cat"&&$("bulkField").value==="ctry"&&BULK[0]){$("bulkField").value=BULK[0].k;fillBulk()}}
  document.querySelector(".gfilters")?.classList.toggle("hidden",mode==="cat"&&!show);
  document.querySelector(".grid")?.classList.toggle("hidden",mode==="cat"&&!show);
  document.querySelector(".pager")?.classList.toggle("hidden",mode==="cat"&&!show);
  $("selbar").classList.toggle("hidden",mode==="cat"&&!show);
  updateCatalogueStats();
}
function renderCatalogueGroups(){
  updateCatalogueStats();
  const tabs=$("catTabs"),groups=catalogueGroups();
  if(!groups.length){tabs.classList.remove("show");tabs.innerHTML="";$("catGroupNote").classList.add("hidden");syncActiveCatalogueRows();return}
  if(!activeCatalogueGroup())S.activeCatGroup=groups[0].id;
  tabs.innerHTML=groups.map(group=>\`<button type="button" class="ctab \${group.id===S.activeCatGroup?"on":""}" data-group="\${esc(group.id)}">\${esc(group.label)} <span class="ctabx" data-delete="\${esc(group.id)}" role="button" aria-label="Delete \${esc(group.label)}">×</span></button>\`).join("");
  tabs.classList.add("show");
  tabs.querySelectorAll("[data-group]").forEach(button=>button.onclick=event=>{
    if(event.target.dataset.delete)return;
    S.activeCatGroup=button.dataset.group;syncActiveCatalogueRows();renderCatalogueGroups();baseRender();updateCatalogueVisibility();setDirty(true);
  });
  tabs.querySelectorAll("[data-delete]").forEach(button=>button.onclick=async event=>{
    event.stopPropagation();const group=catalogueGroups().find(item=>item.id===event.currentTarget.dataset.delete);if(!group)return;
    try{const confirmed=await requestParent("confirm-delete-catalogue-group",{label:group.label,countries:group.countries});if(!confirmed)return;S.catGroups=catalogueGroups().filter(item=>item.id!==group.id);if(S.activeCatGroup===group.id)S.activeCatGroup=S.catGroups[0]?.id||"";syncActiveCatalogueRows();$("catCountryBtn").textContent="Add country(s)";renderCatalogueGroups();baseRender();updateCatalogueVisibility();setDirty(true);toast(group.label+" country sheet deleted")}catch(error){toast(error.message)}
  });
  const group=activeCatalogueGroup();
  $("catGroupNote").innerHTML=\`<b>Note:</b> Countries included in \${esc(group.label)}: \${esc(group.countries.join(", "))}\`;
  $("catGroupNote").classList.remove("hidden");
}
render=function(){
  baseRender();
  updateCatalogueVisibility();
};
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
ensureCat=syncActiveCatalogueRows;
migrateCatalogueState();
normalizeCatalogueGroupLabels();
$("catCountryBtn").onclick=event=>{
  const available=availableCatalogueCountries();
  if(!available.length)return toast("All countries have already been added");
  openCountryAddPicker(event.currentTarget,available,selected=>commitCatalogueCountries(selected));
};
const originalSetMode=setMode;
setMode=function(value){
  originalSetMode(value);S.mode=value;
  $("catCountry").classList.toggle("show",value==="cat");
  if(value==="cat"){syncActiveCatalogueRows();renderCatalogueGroups()}
  else{$("catTabs").classList.remove("show");$("catGroupNote").classList.add("hidden")}
  render();setDirty(true);
};
if(S.mode){originalSetMode(S.mode);$("catCountry").classList.toggle("show",S.mode==="cat");if(S.mode==="cat"){syncActiveCatalogueRows();renderCatalogueGroups()}render();document.querySelectorAll(".mcard").forEach(button=>{const on=button.dataset.mode===S.mode;button.classList.toggle("on",on);button.setAttribute("aria-checked",String(on))});setDirty(false)}
$("save").onclick=async()=>{if(!dirty)return;document.body.inert=true;try{S.mode=mode;const result=await requestParent("save",{migration_request_id:MIGRATION_ID,state:S});S=result.state;setDirty(false);render();const queued=pendingCatalogueRows;pendingCatalogueRows=[];await acknowledgeCatalogueRows(queued);toast("Saved to database")}catch(error){toast(error.message)}finally{document.body.inert=false}};
$("reload").onclick=async()=>{if(dirty&&!confirm("Discard unsaved changes?"))return;document.body.inert=true;try{await requestParent("reload")}catch(error){document.body.inert=false;toast(error.message)}};
document.querySelectorAll(".mcard").forEach(button=>{button.setAttribute("aria-label",button.querySelector("b").textContent)});
document.querySelectorAll(".f select").forEach(select=>{const label=select.closest(".f").querySelector("label");if(label)select.setAttribute("aria-label",label.textContent.replace("*","").trim())});
$("prev").setAttribute("aria-label","Previous page");$("next").setAttribute("aria-label","Next page");
const originalCell=cell;cell=function(row,column){
  if(column.k==="ctry"&&mode==="cat"&&activeCatalogueGroup())return '<td><span class="countryLocked" title="'+esc(activeCatalogueGroup().countries.join(", "))+'">'+esc(ctryLabel(activeCatalogueGroup().countries.join("; ")))+'</span></td>';
  return originalCell(row,column).replace(/<input data-id/g,'<input aria-label="'+esc(column.h)+'" data-id').replace(/<select data-id/g,'<select aria-label="'+esc(column.h)+'" data-id')
};
function catalogueExportRows(){return catalogueGroups().flatMap(group=>group.rows||[])}
function csvCountries(value){return String(value||"").split(/[;,]/).map(country=>country.trim()).filter(Boolean)}
function csvCountryGroupKey(countries){return countries.map(country=>String(country).trim().toLowerCase()).sort().join("|")}
function csvHierarchyKey(values){return values.map(value=>String(value||"").trim().toLowerCase()).join("|")}
$("expBtn").onclick=()=>{
  if(!mode)return toast("Select a scoping method first");
  const exported=mode==="cat"?catalogueExportRows():(sel.size?rows().filter(row=>sel.has(row.id)):view());
  download("OA_Scope_"+MIGRATION_ID+".csv",[HEAD.map(csvCell).join(",")].concat(exported.map(line)).join("\\r\\n"));
  toast("Exported "+exported.length+" rows"+(mode==="cat"?" from all country groups":""));
};
$("tplBtn").onclick=()=>{
  if(!mode)return toast("Select a scoping method first");
  const templateRows=mode==="cat"?catalogueExportRows():view();
  download("OA_Scope_template_"+MIGRATION_ID+".csv",[HEAD.map(csvCell).join(",")].concat(templateRows.map(line)).join("\\r\\n"));
  toast("Template downloaded with current rows – update and upload");
};
$("file").onchange=event=>{
  const file=event.target.files[0];if(!file)return;
  const reader=new FileReader();
  reader.onload=()=>{
    const data=parseCsv(String(reader.result).replace(/^\ufeff/,""));
    const headers=(data.shift()||[]).map(value=>value.trim()),indexOf=name=>headers.indexOf(name);
    if(indexOf("migration_request_id")<0){toast("Upload failed: migration_request_id column not found");event.target.value="";return}
    if(mode==="cat"&&indexOf("Country")<0){toast("Upload failed: Country column not found");event.target.value="";return}
    const catalogueIndex=new Map(CAT.map((item,index)=>[csvHierarchyKey(item.slice(0,6)),index]));
    let updated=0,rejected=0;
    data.forEach(row=>{
      const value=name=>{const index=indexOf(name);return index<0? "":String(row[index]||"").trim()};
      if(value("migration_request_id")!==MIGRATION_ID){rejected++;return}
      const ref=catalogueIndex.get(csvHierarchyKey(["Product","L1","L2","L3","L4","Direction"].map(value)));
      if(ref===undefined){rejected++;return}
      let group=null;
      if(mode==="cat"){
        const key=csvCountryGroupKey(csvCountries(value("Country")));
        group=catalogueGroups().find(candidate=>csvCountryGroupKey(candidate.countries||[])===key);
        if(!group){rejected++;return}
      }
      let target=mode==="cat"?group.rows.find(item=>item.ref===ref):rows().find(item=>item.ref===ref);
      if(!target){
        if(mode==="cat"){rejected++;return}
        target={id:"t"+(S.seq++),...rowFromCat(ref)};S.task.push(target);
      }
      COLS.forEach(column=>{
        if(!EDIT.includes(column.k)||indexOf(column.h)<0)return;
        let next=value(column.h);
        if(column.k==="ctry"){
          if(mode==="cat")return;
          const countries=next.toLowerCase()==="all"||!next?COUNTRIES:next.split(/[;,]/).map(country=>country.trim()).filter(country=>COUNTRIES.includes(country));
          next=countries.length===COUNTRIES.length||!countries.length?"All":countries.join("; ");
        }
        if(column.k==="loc"&&next&&!LOCATIONS.includes(next))return;
        if(column.o&&next&&!column.o.includes(next))return;
        target[column.k]=next;
      });
      updated++;
    });
    setDirty(updated>0||dirty);render();
    toast("Bulk upload: "+updated+" rows updated/added"+(rejected?", "+rejected+" rejected":""));
    event.target.value="";
  };
  reader.onerror=()=>{toast("Upload failed: unable to read CSV file");event.target.value=""};
  reader.readAsText(file);
};
if(mode)render();
`
  const styles = `
<style>
html,body{height:100%;letter-spacing:0}main{padding-bottom:82px}.mcard,.builder,.placeholder{border-radius:8px}.grid{max-height:calc(100vh - 420px);min-height:180px}.bbody.multi-product{grid-template-columns:repeat(5,minmax(0,1fr)) auto}.bbody .f{min-width:0}.foot{flex-wrap:wrap}.bar h1{font-size:18px}.mcard:focus-visible,.btn:focus-visible{outline:2px solid #0073ab;outline-offset:3px}.toast{max-width:calc(100vw - 24px);white-space:normal;overflow-wrap:anywhere}.gfilters .f{min-width:0}.f select,.ctry,.fbtn{max-width:100%}.mbody{min-width:0}.mbody b{overflow-wrap:anywhere}
.catcountry{display:none;align-items:flex-end;gap:10px;flex-wrap:wrap;margin:10px 0;padding:10px 12px;border:1px solid var(--l);border-radius:8px;background:#fbfcfd}.catcountry.show{display:flex}.catcountry .fbtn{width:260px}.catcountry .btn{height:40px;margin:0 0 19px}.countryStats{display:none;color:#344054}.selectorStats{margin-left:auto;padding:0 12px 19px 24px;grid-template-columns:repeat(4,max-content);gap:8px 22px;align-items:center;font-size:12px}.selectorStats.show{display:grid}.countryStats b{color:#101828}.tabrow{display:flex;align-items:flex-end;margin:0 0 10px;border-bottom:1px solid var(--l)}.ctabs{display:none;gap:4px;min-width:0;overflow:auto}.ctabs.show{display:flex}.ctab{border:0;background:#fff;border-bottom:3px solid transparent;padding:8px 14px;font-weight:700;color:var(--mut);cursor:pointer;white-space:nowrap}.ctab.on{color:var(--b);border-bottom-color:var(--b)}.ctabx{margin-left:8px;border:0;background:transparent;color:#667085;font-weight:800;cursor:pointer;padding:0 2px}.ctabx:hover{color:var(--err)}.countryLocked{display:block;background:var(--ro);color:#667085;padding:8px;min-height:32px}#catGroupNote{margin:0 0 10px;padding:9px 12px;background:#f7f9fb;border:1px solid var(--l);border-radius:7px;color:#475467;font-size:12px}
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

function respondToFrameDialog(data) {
  const pending = frameDialogRequest
  frameDialogRequest = null
  if (!pending) return
  pending.target.postMessage({ type: 'oa-scope-response', id: pending.id, data }, location.origin)
}

function openDeleteGroup(message) {
  frameDialogRequest = { target: message.target, id: message.id }
  deleteGroupLabel.value = message.payload?.label || 'this group'
  deleteGroupCountries.value = (message.payload?.countries || []).join(', ')
  deleteGroupOpen.value = true
}

function closeDeleteGroup(confirmed) {
  if (!deleteGroupOpen.value && !frameDialogRequest) return
  deleteGroupOpen.value = false
  respondToFrameDialog(Boolean(confirmed))
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
  if (message.action === 'confirm-delete-catalogue-group') {
    openDeleteGroup({ ...message, target })
    return
  }
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
.oa-dialog-copy { margin: 0 0 16px; color: #475467; line-height: 1.5; }
.oa-dialog-actions { display: flex; justify-content: flex-end; gap: 8px; }
</style>