import {
  ifDefined
} from "./chunk-N5UCH72U.js";
import {
  classMap,
  i,
  property
} from "./chunk-TZBJS2LN.js";
import {
  LitElement,
  css,
  html,
  unsafeCSS
} from "./chunk-3OXU6R3A.js";

// node_modules/@maersk-global/mds-components-core-loading-indicator/index.js
var g = Object.defineProperty;
var b = Object.getOwnPropertyDescriptor;
var a = (l, i2, n, o) => {
  for (var e = o > 1 ? void 0 : o ? b(i2, n) : i2, d = l.length - 1, c; d >= 0; d--) (c = l[d]) && (e = (o ? c(i2, n, e) : c(e)) || e);
  return o && e && g(i2, n, e), e;
};
var p = css`@keyframes ring{0%{transform:rotate(220deg)}to{transform:rotate(580deg)}}@keyframes bar{0%{left:0;transform:translateX(-100%)}to{left:100%;transform:translateX(0)}}.mc-loading-indicator{align-items:center;display:flex;justify-content:center}.mc-loading-indicator.horizontal{flex-direction:row}.mc-loading-indicator.vertical{flex-direction:column}.mc-loading-indicator label:empty{display:none}.mc-loading-indicator.ring.horizontal{gap:8px}.mc-loading-indicator.ring.vertical{gap:6px}.mc-loading-indicator.ring svg{animation:ring 1s infinite}.mc-loading-indicator.ring.primary .label{color:var(--mds_brand_appearance_primary_text-color)}.mc-loading-indicator.ring.primary .track{stroke:var(--mds_brand_appearance_opacity_inverse_10)}.mc-loading-indicator.ring.primary .progress{stroke:var(--mds_brand_appearance_primary_default_background-color)}.mc-loading-indicator.ring.neutral-inverse .label{color:var(--mds_brand_appearance_neutral_inverse_text-color)}.mc-loading-indicator.ring.neutral-inverse .track{stroke:var(--mds_brand_appearance_opacity_default_30)}.mc-loading-indicator.ring.neutral-inverse .progress{stroke:var(--mds_brand_appearance_primary_default_on-background-color)}.mc-loading-indicator.ring.success .label{color:var(--mds_brand_appearance_success_text-color)}.mc-loading-indicator.ring.success .track{stroke:var(--mds_brand_appearance_opacity_inverse_10)}.mc-loading-indicator.ring.success .progress{stroke:var(--mds_brand_appearance_success_default_background-color)}.mc-loading-indicator.ring.warning .label{color:var(--mds_brand_appearance_warning_text-color)}.mc-loading-indicator.ring.warning .track{stroke:var(--mds_brand_appearance_opacity_inverse_10)}.mc-loading-indicator.ring.warning .progress{stroke:var(--mds_brand_appearance_warning_default_background-color)}.mc-loading-indicator.ring.error .label{color:var(--mds_brand_appearance_error_text-color)}.mc-loading-indicator.ring.error .track{stroke:var(--mds_brand_appearance_opacity_inverse_10)}.mc-loading-indicator.ring.error .progress{stroke:var(--mds_brand_appearance_error_default_background-color)}.mc-loading-indicator.bar.horizontal{gap:12px}.mc-loading-indicator.bar.vertical{align-items:flex-start;gap:8px}.mc-loading-indicator.bar .wrapper{overflow:hidden;position:relative;min-width:60px}.mc-loading-indicator.bar .progress{animation:bar 1.2s infinite;left:0;position:absolute;right:auto;top:0;width:40%}.mc-loading-indicator.bar.primary .label{color:var(--mds_brand_appearance_primary_text-color)}.mc-loading-indicator.bar.primary .track{background-color:var(--mds_brand_appearance_opacity_inverse_10)}.mc-loading-indicator.bar.primary .progress{background-color:var(--mds_brand_appearance_primary_default_background-color)}.mc-loading-indicator.bar.neutral-inverse .label{color:var(--mds_brand_appearance_neutral_inverse_text-color)}.mc-loading-indicator.bar.neutral-inverse .track{background-color:var(--mds_brand_appearance_opacity_default_30)}.mc-loading-indicator.bar.neutral-inverse .progress{background-color:var(--mds_brand_appearance_primary_default_on-background-color)}.mc-loading-indicator.bar.success .label{color:var(--mds_brand_appearance_success_text-color)}.mc-loading-indicator.bar.success .track{background-color:var(--mds_brand_appearance_opacity_inverse_10)}.mc-loading-indicator.bar.success .progress{background-color:var(--mds_brand_appearance_success_default_background-color)}.mc-loading-indicator.bar.warning .label{color:var(--mds_brand_appearance_warning_text-color)}.mc-loading-indicator.bar.warning .track{background-color:var(--mds_brand_appearance_opacity_inverse_10)}.mc-loading-indicator.bar.warning .progress{background-color:var(--mds_brand_appearance_warning_default_background-color)}.mc-loading-indicator.bar.error .label{color:var(--mds_brand_appearance_error_text-color)}.mc-loading-indicator.bar.error .track{background-color:var(--mds_brand_appearance_opacity_inverse_10)}.mc-loading-indicator.bar.error .progress{background-color:var(--mds_brand_appearance_error_default_background-color)}.small .label{font-family:var(--mds_brand_typography_text_font-family),var(--mds_brand_typography_text_font-family-fallback);font-size:var(--mds_brand_typography_text_small_mobile_font-size);line-height:var(--mds_brand_typography_text_small_mobile_line-height)}@media screen and (min-width:1025px){.small .label{font-size:var(--mds_brand_typography_text_small_desktop_font-size);line-height:var(--mds_brand_typography_text_small_desktop_line-height)}}.small .label{font-style:var(--mds_brand_typography_text_small_normal_font-style);font-weight:var(--mds_brand_typography_text_small_normal_font-weight)}.small.ring svg{height:16px;width:16px}.small.ring svg .progress,.small.ring svg .track{stroke-width:2}.small.bar .track,.small.bar .wrapper{height:2px;width:100%}.small.bar .progress{height:2px}.medium .label{font-family:var(--mds_brand_typography_text_font-family),var(--mds_brand_typography_text_font-family-fallback);font-size:var(--mds_brand_typography_text_small_mobile_font-size);line-height:var(--mds_brand_typography_text_small_mobile_line-height)}@media screen and (min-width:1025px){.medium .label{font-size:var(--mds_brand_typography_text_small_desktop_font-size);line-height:var(--mds_brand_typography_text_small_desktop_line-height)}}.medium .label{font-style:var(--mds_brand_typography_text_small_normal_font-style);font-weight:var(--mds_brand_typography_text_small_normal_font-weight)}.medium.ring svg{height:20px;width:20px}.medium.ring svg .progress,.medium.ring svg .track{stroke-width:2.5}.medium.bar .track,.medium.bar .wrapper{height:4px;width:100%}.medium.bar .progress{height:4px}.large .label{font-family:var(--mds_brand_typography_text_font-family),var(--mds_brand_typography_text_font-family-fallback);font-size:var(--mds_brand_typography_text_small_mobile_font-size);line-height:var(--mds_brand_typography_text_small_mobile_line-height)}@media screen and (min-width:1025px){.large .label{font-size:var(--mds_brand_typography_text_small_desktop_font-size);line-height:var(--mds_brand_typography_text_small_desktop_line-height)}}.large .label{font-style:var(--mds_brand_typography_text_small_normal_font-style);font-weight:var(--mds_brand_typography_text_small_normal_font-weight)}.large.ring svg{height:24px;width:24px}.large.ring svg .progress,.large.ring svg .track{stroke-width:3}.large.bar .track,.large.bar .wrapper{height:8px;width:100%}.large.bar .progress{height:8px}.no-animation *,.no-animation ::after,.no-animation ::before,:host(.no-animation) *,:host(.no-animation) ::after,:host(.no-animation) ::before{animation:none!important}`;
var _ = [i, unsafeCSS(p)];
var r = class extends LitElement {
  constructor() {
    super(...arguments);
    this.appearance = "primary";
    this.fit = "medium";
    this.hiddenlabel = false;
    this.label = "Loading";
    this.arialabel = "";
    this.variant = "ring";
    this.orientation = "vertical";
  }
  get ringSize() {
    return this.fit === "small" ? 20 : this.fit === "large" ? 28 : 24;
  }
  get ringRadius() {
    return this.fit === "small" ? 8 : this.fit === "large" ? 12 : 10;
  }
  get ringDash() {
    return this.fit === "small" ? 8 : this.fit === "large" ? 12 : 10;
  }
  get ringStrokeDasharray() {
    return `${this.ringDash} 100`;
  }
  get ringStrokeDashoffset() {
    return "0";
  }
  get ringTransform() {
  }
  static get styles() {
    return _;
  }
  render() {
    let n = { [`${this.fit}`]: true, ring: this.variant === "ring" || this.variant === "spinner", bar: this.variant === "bar", [`${this.orientation}`]: true, primary: this.appearance === "primary" || this.appearance === "default", "neutral-inverse": this.appearance === "neutral-inverse" || this.appearance === "inverse", success: this.appearance === "success", warning: this.appearance === "warning", error: this.appearance === "error" };
    return html`<div role="progressbar" aria-valuemin="0" aria-valuemax="1" aria-label="${ifDefined(this.arialabel) ? this.arialabel : this.label}" class="mc-loading-indicator ${classMap(n)}">${this.variant === "ring" || this.variant === "spinner" ? this.renderRing() : this.renderBar()} ${this.renderText()}</div>`;
  }
  renderText() {
    return this.hiddenlabel ? null : html`<div class="label" part="label">${this.label}</div>`;
  }
  renderRing() {
    return html`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${this.ringSize} ${this.ringSize}"><circle class="track" fill="none" part="track" cx="${this.ringSize / 2}" cy="${this.ringSize / 2}" r="${this.ringRadius}"></circle><circle class="progress" fill="none" part="progress" cx="${this.ringSize / 2}" cy="${this.ringSize / 2}" r="${this.ringRadius}" stroke-dasharray="${this.ringStrokeDasharray}" stroke-dashoffset="${this.ringStrokeDashoffset}" transform="${ifDefined(this.ringTransform) ? this.ringTransform : void 0}"></circle></svg>`;
  }
  renderBar() {
    return html`<div class="wrapper" part="wrapper"><div class="track" part="track"></div><div class="progress" part="progress"></div></div>`;
  }
};
a([property({ type: String })], r.prototype, "appearance", 2), a([property({ type: String })], r.prototype, "fit", 2), a([property({ type: Boolean })], r.prototype, "hiddenlabel", 2), a([property({ type: String })], r.prototype, "label", 2), a([property({ type: String })], r.prototype, "arialabel", 2), a([property({ type: String })], r.prototype, "variant", 2), a([property({ type: String })], r.prototype, "orientation", 2);
customElements.get("mc-loading-indicator") || customElements.define("mc-loading-indicator", r);

export {
  r
};
//# sourceMappingURL=chunk-BZYDNCBH.js.map
