import {
  h,
  t
} from "./chunk-ELVOGCWC.js";
import "./chunk-BTR5GQTV.js";
import "./chunk-RU35FA3K.js";
import "./chunk-BZYDNCBH.js";
import {
  ifDefined
} from "./chunk-N5UCH72U.js";
import "./chunk-QJCHO7A2.js";
import "./chunk-K3ZZTKUZ.js";
import "./chunk-QFRRPCYS.js";
import {
  d,
  o,
  p
} from "./chunk-RAGJIJAT.js";
import {
  classMap,
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

// node_modules/@maersk-global/mds-components-core-textarea/index.js
var f = Object.defineProperty;
var b = Object.getOwnPropertyDescriptor;
var e = (p2, a, l, r) => {
  for (var n = r > 1 ? void 0 : r ? b(a, l) : a, d2 = p2.length - 1, u; d2 >= 0; d2--) (u = p2[d2]) && (n = (r ? u(a, l, n) : u(n)) || n);
  return r && n && f(a, l, n), n;
};
var h2 = css`.mc-input.small .field{min-height:60px;height:auto}.mc-input.small .field .input{padding:6px 7px}.mc-input.medium .field{min-height:72px;height:auto}.mc-input.medium .field .input{padding:8px 11px}.mc-input.large .field{min-height:80px;height:auto}.mc-input.large .field .input{padding:12px 15px}.mc-input textarea.input{width:100%;resize:vertical;transition:none}.mc-input .character-counter{color:var(--mds_brand_appearance_neutral_weak_text-color);margin-top:4px;font-family:var(--mds_brand_typography_text_font-family),var(--mds_brand_typography_text_font-family-fallback);font-size:var(--mds_brand_typography_text_small_mobile_font-size);line-height:var(--mds_brand_typography_text_small_mobile_line-height)}@media screen and (min-width:1025px){.mc-input .character-counter{font-size:var(--mds_brand_typography_text_small_desktop_font-size);line-height:var(--mds_brand_typography_text_small_desktop_line-height)}}.mc-input .character-counter{font-style:var(--mds_brand_typography_text_small_normal_font-style);font-weight:var(--mds_brand_typography_text_small_normal_font-weight)}.mc-input .footer{display:flex;justify-content:space-between}`;
var m = [unsafeCSS(h2), t];
var t2 = class extends p(d(LitElement)) {
  constructor() {
    super(...arguments);
    this.charCounter = false;
    this.controlType = "textarea";
    this.focused = false;
    this.autofocus = false;
    this.cols = 20;
    this.errormessage = "";
    this.fit = "medium";
    this.hiddenlabel = false;
    this.hint = "";
    this.id = "";
    this.invalid = false;
    this.label = "Label";
    this.labelposition = "top";
    this.maxlength = -1;
    this.minlength = -1;
    this.name = "";
    this.placeholder = "";
    this.readonly = false;
    this.required = false;
    this.rows = 2;
    this.width = "auto";
  }
  get inputId() {
    return `${this.id ?? "field"}-input`;
  }
  static get styles() {
    return [h, m];
  }
  render() {
    this.maxlength && this.maxlength !== -1 ? this.charCounter = true : (this.maxlength = void 0, this.charCounter = false);
    let l = this.charCounter && this.maxlength !== -1, r = { [`${this.fit}`]: true, [`${this.labelposition}`]: true };
    return html`<div class="mc-input ${classMap(r)}">${this.renderLabel()}<div class="container ${classMap(r)}"><div class="inner"><div class="field ${this.disabled ? "disabled" : null}" part="field" style="${this.width === "auto" ? "" : `width:${this.width}%`}">${this.renderInput()}</div></div><div class="footer"><div>${this.renderError()} ${this.renderHint()}</div>${this.renderCharCounter(l)}</div></div></div>`;
  }
  renderInput() {
    let l = this.minlength === -1 ? void 0 : this.minlength, r = this.maxlength === -1 ? void 0 : this.maxlength;
    return html`<textarea part="textarea" aria-labelledby="label" aria-describedby="hint" class="input ${o(this.classList, ["hover", "focus", "active"])}" .value="${this.value || ""}" rows="${this.rows}" cols="${this.cols}" ?autofocus="${this.autofocus}" ?disabled="${this.disabled}" ?invalid="${this.invalid}" id="${this.inputId}" aria-invalid="${ifDefined(this.invalid ? this.invalid : void 0)}" placeholder="${this.placeholder}" ?required="${this.required}" ?readonly="${this.readonly}" minlength="${ifDefined(l)}" maxlength="${ifDefined(r)}" name="${ifDefined(this.name === "" ? void 0 : this.name)}" @input="${this.handleInputChange}" @blur="${this.onInputBlur}">
    </textarea>`;
  }
  renderLabel() {
    return html`<label class="${this.hiddenlabel ? "hiddenlabel" : ""}" for="${this.inputId}"><mc-label exportparts="label" id="label" .label="${this.label}" .fit="${this.fit}" ?hiddenlabel="${this.hiddenlabel}" .labelposition="${this.labelposition}"><slot name="label">${this.label}</slot></mc-label></label>`;
  }
  renderError() {
    return html`<mc-error id="invalid" .errormessage="${this.errormessage}" .fit="${this.fit}" ?invalid="${this.invalid}"><slot name="errormessage">${this.errormessage}</slot></mc-error>`;
  }
  renderHint() {
    return html`<mc-hint id="hint" .hint="${this.hint}" .fit="${this.fit}"><slot name="hint">${this.hint}</slot></mc-hint>`;
  }
  renderCharCounter(l) {
    if (!this.maxlength) return null;
    let r = Math.min(this.value ? this.value.length : 0, this.maxlength);
    return l ? html`<span class="character-counter" data-cy="character-counter">${r} / ${this.maxlength}</span>` : null;
  }
  focus() {
    var _a, _b;
    let l = new FocusEvent("focus");
    (_a = this.textarea) == null ? void 0 : _a.dispatchEvent(l), (_b = this.textarea) == null ? void 0 : _b.focus();
  }
  onInputFocus() {
    this.focused = true;
  }
  blur() {
    var _a, _b;
    let l = new FocusEvent("blur");
    (_a = this.textarea) == null ? void 0 : _a.dispatchEvent(l), (_b = this.textarea) == null ? void 0 : _b.blur();
  }
  onInputBlur() {
    this.focused = false;
  }
  handleInputChange() {
    this.textarea && (this.value = this.textarea.value);
  }
};
e([query("textarea")], t2.prototype, "textarea", 2), e([property({ type: Boolean, reflect: true })], t2.prototype, "autofocus", 2), e([property({ type: Number })], t2.prototype, "cols", 2), e([property({ type: String })], t2.prototype, "errormessage", 2), e([property({ type: String })], t2.prototype, "fit", 2), e([property({ type: Boolean })], t2.prototype, "hiddenlabel", 2), e([property({ type: String })], t2.prototype, "hint", 2), e([property({ type: String, reflect: true })], t2.prototype, "id", 2), e([property({ type: Boolean, reflect: true })], t2.prototype, "invalid", 2), e([property({ type: String })], t2.prototype, "label", 2), e([property({ type: String })], t2.prototype, "labelposition", 2), e([property({ type: Number })], t2.prototype, "maxlength", 2), e([property({ type: Number })], t2.prototype, "minlength", 2), e([property({ type: String, reflect: true })], t2.prototype, "name", 2), e([property({ type: String })], t2.prototype, "placeholder", 2), e([property({ type: Boolean })], t2.prototype, "readonly", 2), e([property({ type: Boolean, reflect: true })], t2.prototype, "required", 2), e([property({ type: Number })], t2.prototype, "rows", 2), e([property({ type: String, reflect: true })], t2.prototype, "value", 2), e([property({ type: String })], t2.prototype, "width", 2);
customElements.get("mc-textarea") || customElements.define("mc-textarea", t2);
export {
  t2 as McTextarea
};
//# sourceMappingURL=@maersk-global_mds-components-core_mc-textarea.js.map
