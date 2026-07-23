import {
  ifDefined
} from "./chunk-N5UCH72U.js";
import {
  isSingleExpression,
  setCommittedValue
} from "./chunk-QJCHO7A2.js";
import {
  a,
  d,
  n2 as n,
  o,
  p
} from "./chunk-RAGJIJAT.js";
import {
  Directive,
  PartType,
  classMap,
  directive,
  i,
  property,
  query,
  queryAssignedElements,
  state
} from "./chunk-TZBJS2LN.js";
import {
  LitElement,
  css,
  html,
  noChange,
  nothing,
  unsafeCSS
} from "./chunk-3OXU6R3A.js";

// node_modules/lit-html/development/directives/live.js
var LiveDirective = class extends Directive {
  constructor(partInfo) {
    super(partInfo);
    if (!(partInfo.type === PartType.PROPERTY || partInfo.type === PartType.ATTRIBUTE || partInfo.type === PartType.BOOLEAN_ATTRIBUTE)) {
      throw new Error("The `live` directive is not allowed on child or event bindings");
    }
    if (!isSingleExpression(partInfo)) {
      throw new Error("`live` bindings can only contain a single expression");
    }
  }
  render(value) {
    return value;
  }
  update(part, [value]) {
    if (value === noChange || value === nothing) {
      return value;
    }
    const element = part.element;
    const name = part.name;
    if (part.type === PartType.PROPERTY) {
      if (value === element[name]) {
        return noChange;
      }
    } else if (part.type === PartType.BOOLEAN_ATTRIBUTE) {
      if (!!value === element.hasAttribute(name)) {
        return noChange;
      }
    } else if (part.type === PartType.ATTRIBUTE) {
      if (element.getAttribute(name) === String(value)) {
        return noChange;
      }
    }
    setCommittedValue(part);
    return value;
  }
};
var live = directive(LiveDirective);

// node_modules/@maersk-global/mds-components-utils/lib/host/input-disabled.styles.js
var t = css`:host([disabled]){cursor:unset;opacity:unset}:host([disabled]) *{pointer-events:unset;touch-action:unset;user-select:unset}:host([disabled]) .inner,:host([disabled]) .slot{cursor:not-allowed;opacity:var(--mds_brand_appearance_state_disabled_opacity)}:host([disabled]) .inner *,:host([disabled]) .slot slot{pointer-events:none;touch-action:none;user-select:none}`;

// node_modules/@maersk-global/mds-components-core-input/index.js
var g = Object.defineProperty;
var x = Object.getOwnPropertyDescriptor;
var e = (c, u, t2, a2) => {
  for (var l = a2 > 1 ? void 0 : a2 ? x(u, t2) : u, r = c.length - 1, p2; r >= 0; r--) (p2 = c[r]) && (l = (a2 ? p2(u, t2, l) : p2(l)) || l);
  return a2 && l && g(u, t2, l), l;
};
var f = css`.mc-input,.mc-input .container{display:flex;justify-content:center;flex-direction:column}.mc-input .container{flex:1;width:100%}.mc-input .container .inner{display:flex;align-items:flex-start}.mc-input .container .inner .field{background-color:var(--mds_brand_appearance_neutral_default_background-color);border-color:var(--mds_brand_appearance_neutral_default_border-color);border-radius:var(--mds_brand_border_medium_radius);border-style:var(--mds_global_border_style);border-width:var(--mds_global_border_width);display:flex;width:100%}.mc-input .container .inner .field .input-container{display:flex;justify-items:center;position:relative;width:100%}.mc-input .container .inner .field .input,.mc-input .container .inner .field ::slotted(input){background-color:var(--mds_brand_appearance_neutral_default_background-color);border-radius:var(--mds_brand_border_medium_radius)}.mc-input .container .inner .field.active,.mc-input .container .inner .field.hover,.mc-input .container .inner .field:active,.mc-input .container .inner .field:has(.input.active),.mc-input .container .inner .field:has(.input.hover),.mc-input .container .inner .field:hover{border-color:var(--mds_brand_appearance_state_neutral_default_hover_border-color)}.mc-input .container .inner .field.focused{outline:0;border-color:var(--mds_brand_appearance_state_focus_border-color);box-shadow:var(--mds_brand_appearance_state_focus_default_shadow_offset-x) var(--mds_brand_appearance_state_focus_default_shadow_offset-y) var(--mds_brand_appearance_state_focus_default_shadow_blur-radius) var(--mds_brand_appearance_state_focus_default_shadow_spread-radius) var(--mds_brand_appearance_state_focus_default_shadow_color)}.mc-input .container .inner .field:has(.input.focus),.mc-input .container .inner .field:has(.input:focus){outline:0;border-color:var(--mds_brand_appearance_state_focus_border-color);box-shadow:var(--mds_brand_appearance_state_focus_default_shadow_offset-x) var(--mds_brand_appearance_state_focus_default_shadow_offset-y) var(--mds_brand_appearance_state_focus_default_shadow_blur-radius) var(--mds_brand_appearance_state_focus_default_shadow_spread-radius) var(--mds_brand_appearance_state_focus_default_shadow_color)}.mc-input.small .field{height:32px;position:relative}.mc-input.small .field .input,.mc-input.small .field ::slotted(input){font-family:var(--mds_brand_typography_text_font-family),var(--mds_brand_typography_text_font-family-fallback);font-size:var(--mds_brand_typography_text_small_mobile_font-size);line-height:var(--mds_brand_typography_text_small_mobile_line-height)}@media screen and (min-width:1025px){.mc-input.small .field .input,.mc-input.small .field ::slotted(input){font-size:var(--mds_brand_typography_text_small_desktop_font-size);line-height:var(--mds_brand_typography_text_small_desktop_line-height)}}.mc-input.small .field .input,.mc-input.small .field ::slotted(input){font-style:var(--mds_brand_typography_text_small_normal_font-style);font-weight:var(--mds_brand_typography_text_small_normal_font-weight)}.mc-input.small .field .affix{align-items:center;display:flex;justify-content:center;font-family:var(--mds_brand_typography_text_font-family),var(--mds_brand_typography_text_font-family-fallback);font-size:var(--mds_brand_typography_text_small_mobile_font-size);line-height:var(--mds_brand_typography_text_small_mobile_line-height)}@media screen and (min-width:1025px){.mc-input.small .field .affix{font-size:var(--mds_brand_typography_text_small_desktop_font-size);line-height:var(--mds_brand_typography_text_small_desktop_line-height)}}.mc-input.small .field .affix{font-style:var(--mds_brand_typography_text_small_normal_font-style);font-weight:var(--mds_brand_typography_text_small_normal_font-weight)}.mc-input.small:not(.vanity) .input,.mc-input.small:not(.vanity) ::slotted(input){padding:0 7px}.mc-input.small:not(.vanity) .input[type=color]{padding-left:2px;padding-right:2px}.mc-input.small:not(.vanity).prefix .input,.mc-input.small:not(.vanity).prefix ::slotted(input){padding-left:2px}.mc-input.small:not(.vanity).suffix .input,.mc-input.small:not(.vanity).suffix ::slotted(input){padding-right:2px}.mc-input.small:not(.vanity) .affix.type-prefix{padding-left:7px}.mc-input.small:not(.vanity) .affix.type-suffix:last-child{padding-right:7px}.mc-input.small:not(.vanity) mc-icon.affix.type-prefix,.mc-input.small:not(.vanity) mc-icon.affix.type-suffix,.mc-input.small:not(.vanity) mc-icon.affix.type-suffix:last-child{padding-left:2px;padding-right:2px}.mc-input.small:not(.vanity) mc-icon.affix.type-prefix{margin-left:5px}.mc-input.small:not(.vanity) mc-button.affix.type-suffix{margin-right:2px}.mc-input.small:not(.vanity) mc-button.affix.type-suffix:last-child,.mc-input.small:not(.vanity) mc-icon.affix.type-suffix,.mc-input.small:not(.vanity) mc-icon.affix.type-suffix:last-child{margin-right:5px}.mc-input.small:not(.vanity) mc-button.affix.type-suffix:last-child{padding-left:0;padding-right:0}.mc-input.small.vanity.prefix .input,.mc-input.small.vanity.prefix ::slotted(input){padding-left:2px}.mc-input.small.vanity.suffix .input,.mc-input.small.vanity.suffix ::slotted(input){padding-right:2px}.mc-input.small.vanity .affix.type-prefix{padding-right:0}.mc-input.small.vanity .affix.type-suffix:last-child{padding-right:0}.mc-input.small.vanity mc-icon.affix.type-prefix,.mc-input.small.vanity mc-icon.affix.type-suffix,.mc-input.small.vanity mc-icon.affix.type-suffix:last-child{padding-left:2px;padding-right:2px}.mc-input.medium .field{height:40px;position:relative}.mc-input.medium .field .input,.mc-input.medium .field ::slotted(input){font-family:var(--mds_brand_typography_text_font-family),var(--mds_brand_typography_text_font-family-fallback);font-size:var(--mds_brand_typography_text_medium_mobile_font-size);line-height:var(--mds_brand_typography_text_medium_mobile_line-height)}@media screen and (min-width:1025px){.mc-input.medium .field .input,.mc-input.medium .field ::slotted(input){font-size:var(--mds_brand_typography_text_medium_desktop_font-size);line-height:var(--mds_brand_typography_text_medium_desktop_line-height)}}.mc-input.medium .field .input,.mc-input.medium .field ::slotted(input){font-style:var(--mds_brand_typography_text_medium_normal_font-style);font-weight:var(--mds_brand_typography_text_medium_normal_font-weight)}.mc-input.medium .field .affix{align-items:center;display:flex;justify-content:center;font-family:var(--mds_brand_typography_text_font-family),var(--mds_brand_typography_text_font-family-fallback);font-size:var(--mds_brand_typography_text_medium_mobile_font-size);line-height:var(--mds_brand_typography_text_medium_mobile_line-height)}@media screen and (min-width:1025px){.mc-input.medium .field .affix{font-size:var(--mds_brand_typography_text_medium_desktop_font-size);line-height:var(--mds_brand_typography_text_medium_desktop_line-height)}}.mc-input.medium .field .affix{font-style:var(--mds_brand_typography_text_medium_normal_font-style);font-weight:var(--mds_brand_typography_text_medium_normal_font-weight)}.mc-input.medium:not(.vanity) .input,.mc-input.medium:not(.vanity) ::slotted(input){padding:0 11px}.mc-input.medium:not(.vanity) .input[type=color]{padding-left:2px;padding-right:2px}.mc-input.medium:not(.vanity).prefix .input,.mc-input.medium:not(.vanity).prefix ::slotted(input){padding-left:4px}.mc-input.medium:not(.vanity).suffix .input,.mc-input.medium:not(.vanity).suffix ::slotted(input){padding-right:4px}.mc-input.medium:not(.vanity) .affix.type-prefix{padding-left:11px}.mc-input.medium:not(.vanity) .affix.type-suffix:last-child{padding-right:11px}.mc-input.medium:not(.vanity) mc-icon.affix.type-prefix,.mc-input.medium:not(.vanity) mc-icon.affix.type-suffix,.mc-input.medium:not(.vanity) mc-icon.affix.type-suffix:last-child{padding-left:4px;padding-right:4px}.mc-input.medium:not(.vanity) mc-icon.affix.type-prefix{margin-left:7px}.mc-input.medium:not(.vanity) mc-button.affix.type-suffix{margin-right:4px}.mc-input.medium:not(.vanity) mc-button.affix.type-suffix:last-child,.mc-input.medium:not(.vanity) mc-icon.affix.type-suffix,.mc-input.medium:not(.vanity) mc-icon.affix.type-suffix:last-child{margin-right:7px}.mc-input.medium:not(.vanity) mc-button.affix.type-suffix:last-child{padding-left:0;padding-right:0}.mc-input.medium.vanity.prefix .input,.mc-input.medium.vanity.prefix ::slotted(input){padding-left:4px}.mc-input.medium.vanity.suffix .input,.mc-input.medium.vanity.suffix ::slotted(input){padding-right:4px}.mc-input.medium.vanity .affix.type-prefix{padding-right:0}.mc-input.medium.vanity .affix.type-suffix:last-child{padding-right:0}.mc-input.medium.vanity mc-icon.affix.type-prefix,.mc-input.medium.vanity mc-icon.affix.type-suffix,.mc-input.medium.vanity mc-icon.affix.type-suffix:last-child{padding-left:4px;padding-right:4px}.mc-input.large .field{height:48px;position:relative}.mc-input.large .field .input,.mc-input.large .field ::slotted(input){font-family:var(--mds_brand_typography_text_font-family),var(--mds_brand_typography_text_font-family-fallback);font-size:var(--mds_brand_typography_text_medium_mobile_font-size);line-height:var(--mds_brand_typography_text_medium_mobile_line-height)}@media screen and (min-width:1025px){.mc-input.large .field .input,.mc-input.large .field ::slotted(input){font-size:var(--mds_brand_typography_text_medium_desktop_font-size);line-height:var(--mds_brand_typography_text_medium_desktop_line-height)}}.mc-input.large .field .input,.mc-input.large .field ::slotted(input){font-style:var(--mds_brand_typography_text_medium_normal_font-style);font-weight:var(--mds_brand_typography_text_medium_normal_font-weight)}.mc-input.large .field .affix{align-items:center;display:flex;justify-content:center;font-family:var(--mds_brand_typography_text_font-family),var(--mds_brand_typography_text_font-family-fallback);font-size:var(--mds_brand_typography_text_medium_mobile_font-size);line-height:var(--mds_brand_typography_text_medium_mobile_line-height)}@media screen and (min-width:1025px){.mc-input.large .field .affix{font-size:var(--mds_brand_typography_text_medium_desktop_font-size);line-height:var(--mds_brand_typography_text_medium_desktop_line-height)}}.mc-input.large .field .affix{font-style:var(--mds_brand_typography_text_medium_normal_font-style);font-weight:var(--mds_brand_typography_text_medium_normal_font-weight)}.mc-input.large:not(.vanity) .input,.mc-input.large:not(.vanity) ::slotted(input){padding:0 15px}.mc-input.large:not(.vanity) .input[type=color]{padding-left:2px;padding-right:2px}.mc-input.large:not(.vanity).prefix .input,.mc-input.large:not(.vanity).prefix ::slotted(input){padding-left:6px}.mc-input.large:not(.vanity).suffix .input,.mc-input.large:not(.vanity).suffix ::slotted(input){padding-right:6px}.mc-input.large:not(.vanity) .affix.type-prefix{padding-left:15px}.mc-input.large:not(.vanity) .affix.type-suffix:last-child{padding-right:15px}.mc-input.large:not(.vanity) mc-icon.affix.type-prefix,.mc-input.large:not(.vanity) mc-icon.affix.type-suffix,.mc-input.large:not(.vanity) mc-icon.affix.type-suffix:last-child{padding-left:4px;padding-right:4px}.mc-input.large:not(.vanity) mc-icon.affix.type-prefix{margin-left:11px}.mc-input.large:not(.vanity) mc-button.affix.type-suffix{margin-right:6px}.mc-input.large:not(.vanity) mc-button.affix.type-suffix:last-child,.mc-input.large:not(.vanity) mc-icon.affix.type-suffix,.mc-input.large:not(.vanity) mc-icon.affix.type-suffix:last-child{margin-right:11px}.mc-input.large:not(.vanity) mc-button.affix.type-suffix:last-child{padding-left:0;padding-right:0}.mc-input.large.vanity.prefix .input,.mc-input.large.vanity.prefix ::slotted(input){padding-left:6px}.mc-input.large.vanity.suffix .input,.mc-input.large.vanity.suffix ::slotted(input){padding-right:6px}.mc-input.large.vanity .affix.type-prefix{padding-right:0}.mc-input.large.vanity .affix.type-suffix:last-child{padding-right:0}.mc-input.large.vanity mc-icon.affix.type-prefix,.mc-input.large.vanity mc-icon.affix.type-suffix,.mc-input.large.vanity mc-icon.affix.type-suffix:last-child{padding-left:4px;padding-right:4px}.mc-input.left{flex-direction:row;align-items:flex-start}@media screen and (max-width:700px){.mc-input.left{flex-direction:column}}.mc-input .input,.mc-input ::slotted(input){border-width:0;color:var(--mds_brand_appearance_neutral_default_on-background-color);transition-duration:var(--mds_global_transition_fast_duration);transition-property:all;transition-timing-function:var(--mds_global_transition_fast_timing);width:100%}.mc-input .input::placeholder,.mc-input ::slotted(input)::placeholder{color:var(--mds_brand_appearance_neutral_weakest_text-color)}.mc-input .input.focus,.mc-input .input:focus,.mc-input ::slotted(input).focus,.mc-input ::slotted(input):focus{outline:0}.mc-input input::-webkit-inner-spin-button,.mc-input input::-webkit-outer-spin-button{-webkit-appearance:none;margin:0}.mc-input input[type=number]{-moz-appearance:textfield}.mc-input input[type=color]{height:100%;cursor:pointer;border-color:var(--mds_brand_appearance_neutral_default_border-color)}.mc-input input[type=color]::-moz-color-swatch-wrapper{border-color:var(--mds_brand_appearance_neutral_default_border-color)}.mc-input input[type=color]::-moz-color-swatch{border-color:var(--mds_brand_appearance_neutral_default_border-color)}.mc-input input[type=color]::-webkit-color-swatch{border-color:var(--mds_brand_appearance_neutral_default_border-color)}.mc-input input[type=color]:hover{border-color:var(--mds_brand_appearance_state_neutral_default_hover_border-color)}.mc-input input[type=color]:hover::-moz-color-swatch-wrapper{border-color:var(--mds_brand_appearance_state_neutral_default_hover_border-color)}.mc-input input[type=color]:hover::-moz-color-swatch{border-color:var(--mds_brand_appearance_state_neutral_default_hover_border-color)}.mc-input input[type=color]:hover::-webkit-color-swatch{border-color:var(--mds_brand_appearance_state_neutral_default_hover_border-color)}.mc-input .affix{color:var(--mds_brand_appearance_neutral_weakest_text-color)}.mc-input .affix::part(icon),.mc-input mc-button.clear::part(icon),.mc-input mc-button.iconbutton::part(icon){fill:var(--mds_brand_appearance_neutral_weakest_text-color)}.mc-input mc-button.clear.affix,.mc-input mc-button.iconbutton.affix{transition-duration:var(--mds_global_transition_fast_duration);transition-property:all;transition-timing-function:var(--mds_global_transition_fast_timing)}.mc-input mc-button.clear::part(button),.mc-input mc-button.iconbutton::part(button){width:auto}.mc-input mc-button.clear::part(button):active,.mc-input mc-button.clear::part(button):hover,.mc-input mc-button.iconbutton::part(button):active,.mc-input mc-button.iconbutton::part(button):hover{background-color:transparent}.mc-input mc-button.clear::part(icon):active,.mc-input mc-button.clear::part(icon):hover,.mc-input mc-button.iconbutton::part(icon):active,.mc-input mc-button.iconbutton::part(icon):hover{fill:var(--mds_brand_appearance_neutral_default_text-color)}.mc-input.vanity .container .inner .field{background-color:transparent;border-left-width:0;border-radius:0;border-right-width:0;border-top-width:0;color:var(--mds_brand_appearance_neutral_default_text-color);padding-left:0;padding-right:0}.mc-input.vanity .container .inner .field .input,.mc-input.vanity .container .inner .field ::slotted(input){background-color:transparent}.mc-input.vanity .container .inner .field:has(input.focus){outline:0;border-bottom-color:var(--mds_brand_appearance_state_focus_border-color);box-shadow:var(--mds_brand_appearance_state_focus_vanity_shadow_offset-x) var(--mds_brand_appearance_state_focus_vanity_shadow_offset-y) var(--mds_brand_appearance_state_focus_vanity_shadow_blur-radius) var(--mds_brand_appearance_state_focus_vanity_shadow_spread-radius) var(--mds_brand_appearance_state_focus_vanity_shadow_color)}.mc-input.vanity .type-prefix{justify-content:flex-start}.mc-input.vanity .type-suffix{justify-content:flex-end}.mc-input .hiddenlabel{height:0}:host([invalid]) .mc-input .field{border-color:var(--mds_brand_appearance_error_default_border-color)!important}:host([disabled]) .affix,:host([disabled]) .mc-input .input,:host([disabled]) .mc-input ::slotted(input){background-color:transparent!important}`;
var h = [i, t, unsafeCSS(f)];
var m = ["input", "trailingIconButton", "clearButton"];
var i2 = class extends p(d(LitElement)) {
  constructor() {
    super();
    this.uniqueId = n();
    this._valueAsNumber = NaN;
    this.clearButtonEnabled = false;
    this.controlType = "input";
    this.focused = false;
    this.isInputFocused = false;
    this.isClearButtonFocused = false;
    this.isTrailingIconFocused = false;
    this.autocapitalize = "";
    this.autocomplete = "";
    this.autofocus = false;
    this.clearbutton = false;
    this.errormessage = "";
    this.fit = "medium";
    this.hiddenlabel = false;
    this.hint = "";
    this.icon = "";
    this.id = "";
    this.invalid = false;
    this.keepclearbuttonvisible = false;
    this.label = "Label";
    this.labelposition = "top";
    this.loading = false;
    this.maxlength = -1;
    this.minlength = -1;
    this.name = "";
    this.pattern = "";
    this.placeholder = "";
    this.prefix = null;
    this.readonly = false;
    this.size = null;
    this.suffix = null;
    this.type = "text";
    this.trailingicon = "";
    this.clickabletrailingicon = false;
    this.trailingiconlabel = void 0;
    this.value = "";
    this.variant = "default";
    this.width = "auto";
    this.mask = void 0;
    this.maskController = void 0;
  }
  get inputLabel() {
    return this.hiddenlabel ? "" : this.labelElements && this.labelElements.length > 0 ? this.labelElements[0].cloneNode(true) : this.label;
  }
  get inputElement() {
    return this.slottedInput && this.slottedInput.length > 0 ? this.slottedInput[0] : this.defaultInputElement;
  }
  get inputId() {
    return `mc-input-${this.id ? this.id : this.uniqueId}`;
  }
  get valueAsNumber() {
    return this._valueAsNumber;
  }
  static get styles() {
    return h;
  }
  calculateClasses() {
    return { date: this.type === "date", disabled: this.disabled, prefix: !!(this.icon || this.prefix), suffix: this.trailingicon || this.suffix || this.loading || this.clearbutton, vanity: this.variant === "vanity", [`${this.fit}`]: true, [`${this.labelposition}`]: true };
  }
  render() {
    let t2 = this.calculateClasses();
    return html`<div data-cy="mc-input-container" class="mc-input ${classMap(t2)}">${this.renderLabel()}<div class="container"><div class="inner">${this.renderPrefixElement()} ${this.renderField()} ${this.renderSuffixElement()}</div>${this.renderError()} ${this.renderHint()}</div></div>`;
  }
  renderField() {
    let t2 = { focused: this.isInputFocused, disabled: this.disabled, [`${o(this.classList, ["hover", "focus", "active"])}`]: true };
    return html`<div data-id="field" id="field" part="field" class="field ${classMap(t2)}" style="${this.width === "auto" ? "" : `width:${this.width.includes("px") ? this.width : this.width + "%"}`}" tabindex="-1" @focusin="${this.onFieldFocus}" @focusout="${this.onFieldBlur}">${this.renderPrefix()} ${this.renderInput()} ${this.renderClearButton()} ${this.renderSuffix()}</div>`;
  }
  renderSuffixElement() {
    return null;
  }
  renderPrefixElement() {
    return null;
  }
  renderLabel() {
    return html`<label class="${this.hiddenlabel ? "hiddenlabel" : ""}" part="label-container" for="${this.inputId}"><mc-label exportparts="label" id="label" .label="${this.label}" .fit="${this.fit}" ?hiddenlabel="${this.hiddenlabel}" .labelposition="${this.labelposition}" @click="${(t2) => t2.stopPropagation()}"><slot name="label">${this.label}</slot></mc-label></label>`;
  }
  renderError() {
    return html`<mc-error id="invalid" .errormessage="${this.errormessage}" .fit="${this.fit}" ?invalid="${this.invalid}"><slot name="errormessage">${this.errormessage}</slot></mc-error>`;
  }
  renderHint() {
    return html`<mc-hint id="hint" .hint="${this.hint}" .fit="${this.fit}"><slot name="hint">${this.hint}</slot></mc-hint>`;
  }
  renderInput() {
    var _a;
    let t2 = this.minlength === -1 ? void 0 : this.minlength, a2 = this.maxlength === -1 ? void 0 : this.maxlength, l = this.autocomplete ? this.autocomplete : void 0, r = this.autocapitalize ? this.autocapitalize : void 0;
    return html`<div class="input-container">${this.renderSelectedOptionLabel()}<slot name="input" @click="${this.handleInputClick ?? this.handleInputClick}" @input="${this.handleInputChange}"><input ?autofocus="${this.autofocus}" ?disabled="${this.disabled}" ?invalid="${this.invalid}" ?readonly="${this.readonly}" ?required="${this.required}" .value="${this.mask ? ((_a = this.maskController) == null ? void 0 : _a.maskedValue) || "" : live(this.value)}" @blur="${this.onInputBlur}" @focus="${this.onInputFocus}" aria-describedby="hint" aria-invalid="${ifDefined(this.invalid ? this.invalid : void 0)}" aria-labelledby="label" autocapitalize="${ifDefined(r)}" autocomplete="${ifDefined(l)}" class="input ${o(this.classList, ["hover", "focus", "active"])}" data-cy="input" data-id="input" id="${this.inputId}" inputmode="${ifDefined(this.inputmode)}" max="${ifDefined(this.max === "" ? void 0 : this.max)}" maxlength="${ifDefined(a2)}" min="${ifDefined(this.min === "" ? void 0 : this.min)}" minlength="${ifDefined(t2)}" name="${ifDefined(this.name === "" ? void 0 : this.name)}" part="input" pattern="${ifDefined(this.pattern ? this.pattern : void 0)}" placeholder="${this.placeholder}" size="${ifDefined(this.size === null ? void 0 : this.size)}" step="${ifDefined(this.step ? +this.step : void 0)}" type="${this.type ? this.type : "text"}"></slot></div>`;
  }
  renderAffix(t2, a2) {
    return t2 !== "" ? html`<span class="affix type-${a2}" @click="${this.focus}">${t2}</span>` : "";
  }
  renderPrefix() {
    return this.prefix ? this.renderAffix(this.prefix, "prefix") : this.icon ? this.renderIcon("prefix", this.icon) : "";
  }
  renderSuffix() {
    return this.loading ? this.renderLoadingIndicator() : this.suffix ? this.renderAffix(this.suffix, "suffix") : this.trailingicon ? this.renderIcon("suffix", this.trailingicon) : "";
  }
  renderLoadingIndicator() {
    return this.loading ? html`<mc-loading-indicator class="affix type-suffix" .fit="${this.fit}" .label="${this.label} in progress" hiddenlabel></mc-loading-indicator>` : null;
  }
  renderClearButton() {
    var _a;
    return !this.readonly && this.clearbutton && this.clearButtonEnabled && ((_a = this.value) == null ? void 0 : _a.length) > 0 ? html`<mc-button id="clearButton" data-id="clearButton" data-cy="clearButton" class="affix type-suffix clear" label="Clear" fit="${this.fit}" appearance="neutral" variant="plain" padding="compact" border="none" icon="times" hiddenlabel tabindex="0" @click="${this.onClearButtonClick}" @mousedown="${this.onClearButtonMouseDown}" @keydown="${this.onClearButtonKeyDown}" @focus="${this.onClearButtonFocus}" @blur="${this.onClearButtonBlur}"></mc-button>` : null;
  }
  renderIcon(t2, a2) {
    return a2 !== "" ? this.clickabletrailingicon && t2 === "suffix" ? html`<mc-button id="iconButton" data-id="trailingIconButton" data-cy="trailingIconButton" class="affix type-suffix iconbutton" .label="${this.trailingiconlabel}" .title="${this.trailingiconlabel}" fit="${this.fit}" appearance="neutral" variant="plain" padding="compact" border="none" icon="${a2}" hiddenlabel @click="${this.onTrailingIconClick}" @focus="${this.onTrailingIconFocus}" @blur="${this.onTrailingIconBlur}"></mc-button>` : html`<mc-icon exportparts="icon" class="affix type-${t2}" icon="${a2}" size="${this.fit === "large" ? "24" : "20"}" tabindex="-1" @blur="${this.preventBlurOnIconPress}"></mc-icon>` : "";
  }
  renderSelectedOptionLabel() {
    return html``;
  }
  preventBlurOnIconPress(t2) {
    t2.preventDefault(), t2.stopPropagation();
  }
  onFieldFocus(t2) {
    let a2 = t2.target, l = a2 == null ? void 0 : a2.getAttribute("data-id"), r = t2.relatedTarget, p2 = r == null ? void 0 : r.getAttribute("data-id");
    a2 && l === "input" && (r === null || r && !m.includes(p2)) && (this.isInputFocused = true, this.clearButtonEnabled = this.clearbutton, this.focus());
  }
  onFieldBlur(t2) {
    let a2 = t2.target, l = a2 == null ? void 0 : a2.getAttribute("data-id"), r = t2.relatedTarget, p2 = r == null ? void 0 : r.getAttribute("data-id");
    if (r && p2 === "field" && a2 && m.includes(l)) {
      t2.preventDefault(), t2.stopPropagation();
      return;
    } else if (r && !m.includes(p2) || r === null) {
      this.clearButtonEnabled = !!this.keepclearbuttonvisible;
      return;
    }
  }
  toggleClearButton(t2) {
    !this.loading && this.clearbutton ? this.keepclearbuttonvisible && this.value ? this.clearButtonEnabled = true : t2 ? this.value ? this.clearButtonEnabled = true : this.clearButtonEnabled = false : this.clearButtonEnabled = false : this.clearButtonEnabled = false;
  }
  onClearButtonClick(t2) {
    t2.stopPropagation(), this.inputElement && (this.inputElement.value = "", setTimeout(() => this.focus(), 0), this.isInputFocused = true), this.handleInputChange(), this.dispatchEvent(new InputEvent("input")), this.dispatchEvent(new CustomEvent("clearbuttonclick"));
  }
  onClearButtonMouseDown(t2) {
    t2.stopPropagation();
  }
  onClearButtonKeyDown(t2) {
    (t2.key === "Enter" || t2.key === " ") && (t2.preventDefault(), t2.stopPropagation(), this.onClearButtonClick(t2));
  }
  onClearButtonFocus() {
    this.isClearButtonFocused = true, this.clearButtonEnabled = this.clearbutton;
  }
  onClearButtonBlur() {
    this.isClearButtonFocused = false, this.clearButtonEnabled = this.clearbutton;
  }
  onTrailingIconClick(t2) {
    t2.preventDefault(), t2.stopPropagation(), this.dispatchEvent(new CustomEvent("trailingiconclick"));
  }
  onTrailingIconFocus() {
    this.isTrailingIconFocused = true, this.clearButtonEnabled = this.clearbutton;
  }
  onTrailingIconBlur() {
    this.isTrailingIconFocused = false, this.clearButtonEnabled = this.clearbutton;
  }
  connectedCallback() {
    super.connectedCallback();
  }
  disconnectedCallback() {
    this.inputField = null, this.root = null, this.inputContainer = null, super.disconnectedCallback();
  }
  async firstUpdated(t2) {
    var _a;
    super.firstUpdated(t2), await this.updateComplete, this.initializeElements(), this.mask && this.initializeMaskController(), this.value && ((_a = this.maskController) == null ? void 0 : _a.mask) && (this.maskController.mask.value = this.value);
  }
  willUpdate(t2) {
    var _a;
    super.willUpdate(t2), (t2.has("keepclearbuttonvisible") || t2.has("clearbutton") || t2.has("loading") || t2.has("value")) && this.toggleClearButton(true), t2.has("value") && this.mask && this.maskController && this.maskController.mask && (this.maskController.mask.typedValue = this.value), t2.has("mask") && (this.mask && (this.maskController || this.initializeMaskController(), (_a = this.maskController) == null ? void 0 : _a.updateOptions(this.mask)), this.maskController && !this.mask && this.maskController.destroyMask());
  }
  initializeMaskController() {
    this.mask && this.inputElement && (this.maskController = new a(this, this.mask, this.inputElement), this.maskController.onAccept(() => {
      var _a;
      this.value = (_a = this.maskController) == null ? void 0 : _a.unmaskedValue;
    }));
  }
  focus() {
    var _a;
    this.inputElement === this.defaultInputElement && ((_a = this.inputElement) == null ? void 0 : _a.focus(), this.isInputFocused = true);
  }
  onInputFocus() {
    this.focused = true, this.isInputFocused = true;
  }
  blur() {
    var _a;
    this.inputElement === this.defaultInputElement && (this.isInputFocused = false, (_a = this.inputElement) == null ? void 0 : _a.blur());
  }
  onInputBlur() {
    this.isInputFocused = false, this.focused = false;
  }
  select() {
    var _a;
    (_a = this.inputElement) == null ? void 0 : _a.select();
  }
  click() {
    if (this.root) {
      this.root.focus(), this.root.click();
      return;
    }
    super.click();
  }
  handleInputChange() {
    var _a, _b;
    this.mask || (this.value = (_a = this.inputElement) == null ? void 0 : _a.value), this._valueAsNumber = ((_b = this.inputElement) == null ? void 0 : _b.valueAsNumber) ?? NaN;
  }
  initializeElements() {
    var _a, _b, _c;
    this.inputField = (_a = this.shadowRoot) == null ? void 0 : _a.querySelector(".field"), this.root = (_b = this.shadowRoot) == null ? void 0 : _b.querySelector(".container"), this.inputContainer = (_c = this.shadowRoot) == null ? void 0 : _c.querySelector(".mc-input");
  }
};
e([state()], i2.prototype, "clearButtonEnabled", 2), e([state()], i2.prototype, "inputField", 2), e([queryAssignedElements({ slot: "input", flatten: true })], i2.prototype, "slottedInput", 2), e([query(".input")], i2.prototype, "defaultInputElement", 2), e([queryAssignedElements({ slot: "label", flatten: true })], i2.prototype, "labelElements", 2), e([state()], i2.prototype, "focused", 2), e([state()], i2.prototype, "isInputFocused", 2), e([state()], i2.prototype, "isClearButtonFocused", 2), e([state()], i2.prototype, "isTrailingIconFocused", 2), e([property({ type: String })], i2.prototype, "autocapitalize", 2), e([property({ type: String })], i2.prototype, "autocomplete", 2), e([property({ type: Boolean, reflect: true })], i2.prototype, "autofocus", 2), e([property({ type: Boolean, reflect: true })], i2.prototype, "clearbutton", 2), e([property({ type: String })], i2.prototype, "errormessage", 2), e([property({ type: String })], i2.prototype, "fit", 2), e([property({ type: Boolean })], i2.prototype, "hiddenlabel", 2), e([property({ type: String })], i2.prototype, "hint", 2), e([property({ type: String })], i2.prototype, "icon", 2), e([property({ type: String, reflect: true })], i2.prototype, "id", 2), e([property({ type: String })], i2.prototype, "inputmode", 2), e([property({ type: Boolean, reflect: true })], i2.prototype, "invalid", 2), e([property({ type: Boolean })], i2.prototype, "keepclearbuttonvisible", 2), e([property({ type: String })], i2.prototype, "label", 2), e([property({ type: String })], i2.prototype, "labelposition", 2), e([property({ type: Boolean, reflect: true })], i2.prototype, "loading", 2), e([property({ type: String })], i2.prototype, "max", 2), e([property({ type: Number })], i2.prototype, "maxlength", 2), e([property({ type: String })], i2.prototype, "min", 2), e([property({ type: Number })], i2.prototype, "minlength", 2), e([property({ type: String, reflect: true })], i2.prototype, "name", 2), e([property({ type: String })], i2.prototype, "pattern", 2), e([property({ type: String })], i2.prototype, "placeholder", 2), e([property({ type: String })], i2.prototype, "prefix", 2), e([property({ type: Boolean, reflect: true })], i2.prototype, "readonly", 2), e([property({ type: Boolean })], i2.prototype, "required", 2), e([property({ type: Number })], i2.prototype, "size", 2), e([property({ type: Number })], i2.prototype, "step", 2), e([property({ type: String })], i2.prototype, "suffix", 2), e([property({ type: String })], i2.prototype, "type", 2), e([property({ type: String })], i2.prototype, "trailingicon", 2), e([property({ type: Boolean })], i2.prototype, "clickabletrailingicon", 2), e([property({ type: String })], i2.prototype, "trailingiconlabel", 2), e([property({ type: String, reflect: true })], i2.prototype, "value", 2), e([property({ type: Number })], i2.prototype, "valueAsNumber", 1), e([property({ type: String })], i2.prototype, "variant", 2), e([property({ type: String })], i2.prototype, "width", 2), e([property({ type: String })], i2.prototype, "mask", 2);
customElements.get("mc-input") || customElements.define("mc-input", i2);

export {
  t,
  h,
  i2 as i
};
/*! Bundled license information:

lit-html/development/directives/live.js:
  (**
   * @license
   * Copyright 2020 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)
*/
//# sourceMappingURL=chunk-ELVOGCWC.js.map
