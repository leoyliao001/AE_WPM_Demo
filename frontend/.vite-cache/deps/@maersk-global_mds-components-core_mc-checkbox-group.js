import {
  t
} from "./chunk-PWXMWD6L.js";
import "./chunk-BTR5GQTV.js";
import {
  ifDefined
} from "./chunk-N5UCH72U.js";
import {
  d,
  e2 as e,
  p
} from "./chunk-RAGJIJAT.js";
import {
  classMap,
  i,
  property,
  query
} from "./chunk-TZBJS2LN.js";
import {
  LitElement,
  css,
  html,
  unsafeCSS
} from "./chunk-3OXU6R3A.js";
import "./chunk-5FUTL2UF.js";

// node_modules/@maersk-global/mds-components-core-multi-choice-fieldset/index.js
var c = Object.defineProperty;
var f = Object.getOwnPropertyDescriptor;
var s = (u, r, e3, t2) => {
  for (var n = t2 > 1 ? void 0 : t2 ? f(r, e3) : r, o = u.length - 1, a; o >= 0; o--) (a = u[o]) && (n = (t2 ? a(r, e3, n) : a(n)) || n);
  return t2 && n && c(r, e3, n), n;
};
var m = css`.mc-multi-choice-fieldset{padding:0;margin:0;border:0}.mc-multi-choice-fieldset legend{padding:0}.mc-multi-choice-fieldset .hiddenlegend{height:0}.mc-multi-choice-fieldset.small .slot{gap:8px;margin-top:8px}.mc-multi-choice-fieldset.small.horizontal .slot{column-gap:16px}.mc-multi-choice-fieldset.small.no-feedback .slot{margin-top:0}.mc-multi-choice-fieldset.medium .slot{gap:12px;margin-top:12px}.mc-multi-choice-fieldset.medium.horizontal .slot{column-gap:20px}.mc-multi-choice-fieldset.medium.no-feedback .slot{margin-top:0}.mc-multi-choice-fieldset.large .slot{gap:16px;margin-top:16px}.mc-multi-choice-fieldset.large.horizontal .slot{column-gap:24px}.mc-multi-choice-fieldset.large.no-feedback .slot{margin-top:0}.mc-multi-choice-fieldset.hidden-legend legend{display:none}.mc-multi-choice-fieldset,.mc-multi-choice-fieldset .slot{display:flex;flex-direction:column}.mc-multi-choice-fieldset.horizontal .slot{flex-direction:row}@media only screen and (max-width:640px){.mc-multi-choice-fieldset.autolayout .slot{flex-direction:column}}`;
var h = [i, t, unsafeCSS(m)];
var i2 = class extends p(d(LitElement)) {
  constructor() {
    super(...arguments);
    this.groupFirstUpdated = false;
    this.autolayoutdisabled = false;
    this.fit = "medium";
    this.hiddenlegend = false;
    this.invalid = false;
    this.legend = "Legend";
    this.name = "";
    this.orientation = "vertical";
    this.readonly = false;
    this.inputsSlotIsReady = () => {
      let e3 = this.pruneTextNodesFromSlottedElements();
      this.inputs = e3 == null ? void 0 : e3.filter((t2) => t2.nodeName !== "#text" && t2.nodeName.toLowerCase() !== "input"), !this.groupFirstUpdated && this.inputs && this.inputs.length > 0 && (this.groupFirstUpdated = true, this.value ? this.setCheckedStatusBySuppliedValue() : this.value = this.getSelectedValues(), this.setTheNamePropertyFromSlottedComponents(), this.addMirroredHiddenInput());
    };
  }
  static get styles() {
    return h;
  }
  render() {
    var _a;
    let e3 = { "no-feedback": this.hiddenlegend && !this.invalid && !((_a = this.hintElement) == null ? void 0 : _a.visible), autolayout: !this.autolayoutdisabled, [`${this.orientation}`]: true, [`${this.fit}`]: true };
    return html`<div role="group" aria-labelledby="label" class="mc-multi-choice-fieldset ${classMap(e3)}"><legend class="${this.hiddenlegend ? "hiddenlegend" : ""}" aria-label="${ifDefined(this.hiddenlegend ? this.legend : void 0)}"><mc-label id="label" .label="${this.legend}" .fit="${this.fit}" ?hiddenlabel="${this.hiddenlegend}"><slot name="legend">${this.legend}</slot></mc-label></legend><mc-error id="invalid" .errormessage="${this.errormessage}" .fit="${this.fit}" ?invalid="${this.invalid}"><slot name="errormessage">${this.errormessage}</slot></mc-error><mc-hint id="hint" .hint="${this.hint}" .fit="${this.fit}"><slot name="hint">${this.hint}</slot></mc-hint><div class="slot" part="fieldset-container"><slot></slot></div></div>`;
  }
  connectedCallback() {
    super.connectedCallback(), this.setAttribute("role", "group");
  }
  disconnectedCallback() {
    var _a;
    (_a = this.inputsSlot) == null ? void 0 : _a.removeEventListener("slotchange", this.inputsSlotIsReady), super.disconnectedCallback();
  }
  firstUpdated(e3) {
    var _a;
    super.firstUpdated(e3), this.initializeElements(), (_a = this.fieldset) == null ? void 0 : _a.addEventListener("change", (t2) => this.onChange(t2));
  }
  updated(e3) {
    super.updated(e3), this.inputs && (e(this.inputs, "fit", this.fit), e3.has("value") && this.setCheckedStatusBySuppliedValue(), this.disabled ? e(this.inputs, "disabled", true) : e3.has("disabled") && e(this.inputs, "disabled", false), this.readonly ? e(this.inputs, "readonly", true) : e3.has("readonly") && e(this.inputs, "readonly", false));
  }
  onChange(e3) {
    e3.stopPropagation(), this.value = this.getSelectedValues(), this.dispatchEvent(new CustomEvent("change", { detail: this.value }));
  }
  setCheckedStatusBySuppliedValue() {
    var _a;
    if (!this.inputs || !this.value && this.value !== "") return;
    let e3 = this.getValues();
    (_a = this.inputs) == null ? void 0 : _a.forEach((t2) => e3.find((n) => {
      let o = this.getStringifiedValue(n), a = this.getStringifiedValue(t2.localName === "mc-radio" ? t2.value : t2.cachedValue);
      return o === a;
    }) !== void 0 ? (t2.checked = true, true) : (t2.checked = false, false));
  }
  getStringifiedValue(e3) {
    return e3 && (Array.isArray(e3) || typeof e3 == "object") ? JSON.stringify(e3) : `${e3}`;
  }
  getValues() {
    return typeof this.value == "string" ? this.value.split(",") : Array.isArray(this.value) ? this.value : [this.value];
  }
  getSelectedValues() {
    var _a;
    if (this.inputs) return this.inputs[0].localName === "mc-radio" ? (_a = this.inputs.find((e3) => e3.checked)) == null ? void 0 : _a.value : this.inputs.reduce((e3, t2) => t2.checked ? [t2.value, ...e3] : e3, []);
  }
  initializeElements() {
    var _a, _b;
    this.inputsSlot = (_a = this.shadowRoot) == null ? void 0 : _a.querySelector("slot:not([name])"), (_b = this.inputsSlot) == null ? void 0 : _b.addEventListener("slotchange", this.inputsSlotIsReady);
  }
  setTheNamePropertyFromSlottedComponents() {
    if (this.inputs && this.inputs.length !== 0) {
      let e3 = this.inputs[0];
      this.setAttribute("name", e3.getAttribute("name") || "");
    }
  }
  pruneTextNodesFromSlottedElements() {
    var _a;
    let e3 = (_a = this.inputsSlot) == null ? void 0 : _a.assignedElements();
    return e3 == null ? void 0 : e3.filter((t2) => t2.nodeName === "#text").forEach((t2) => t2.remove()), e3;
  }
};
s([property({ type: Boolean })], i2.prototype, "autolayoutdisabled", 2), s([query(".mc-multi-choice-fieldset")], i2.prototype, "fieldset", 2), s([query("mc-hint")], i2.prototype, "hintElement", 2), s([query("mc-error")], i2.prototype, "errorElement", 2), s([property({ type: String })], i2.prototype, "errormessage", 2), s([property({ type: String })], i2.prototype, "fit", 2), s([property({ type: Boolean })], i2.prototype, "hiddenlegend", 2), s([property({ type: String })], i2.prototype, "hint", 2), s([property({ type: Boolean, reflect: true })], i2.prototype, "invalid", 2), s([property({ type: String })], i2.prototype, "legend", 2), s([property({ type: String, reflect: true })], i2.prototype, "name", 2), s([property({ type: String })], i2.prototype, "orientation", 2), s([property({ type: String, reflect: true })], i2.prototype, "value", 2), s([property({ type: Boolean })], i2.prototype, "readonly", 2);

// node_modules/@maersk-global/mds-components-core-checkbox-group/index.js
var e2 = class extends i2 {
};
customElements.get("mc-checkbox-group") || customElements.define("mc-checkbox-group", e2);
export {
  e2 as McCheckboxGroup
};
//# sourceMappingURL=@maersk-global_mds-components-core_mc-checkbox-group.js.map
