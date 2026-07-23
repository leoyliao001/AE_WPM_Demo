import {
  ifDefined
} from "./chunk-N5UCH72U.js";
import {
  styleMap
} from "./chunk-QFRRPCYS.js";
import {
  o
} from "./chunk-RAGJIJAT.js";
import {
  classMap,
  i,
  property,
  queryAssignedNodes
} from "./chunk-TZBJS2LN.js";
import {
  LitElement,
  css,
  html,
  unsafeCSS
} from "./chunk-3OXU6R3A.js";
import "./chunk-5FUTL2UF.js";

// node_modules/@maersk-global/mds-components-core-card/index.js
var f = Object.defineProperty;
var y = Object.getOwnPropertyDescriptor;
var a = (_, l, t, n) => {
  for (var o2 = n > 1 ? void 0 : n ? y(l, t) : l, m = _.length - 1, h; m >= 0; m--) (h = _[m]) && (o2 = (n ? h(l, t, o2) : h(o2)) || o2);
  return n && o2 && f(l, t, o2), o2;
};
var g = css`:host{display:block}.mc-card{color:var(--mds_brand_appearance_neutral_default_on-background-color);display:flex;height:100%;text-align:left;transition-duration:var(--mds_global_transition_fast_duration);transition-property:all;transition-timing-function:var(--mds_global_transition_fast_timing);width:100%}.mc-card:focus-within .image-inner,.mc-card:hover .image-inner{backface-visibility:hidden}.mc-card.image-scale-strength-light:focus-within .image-inner,.mc-card.image-scale-strength-light:hover .image-inner{transform:scale(1.02)}.mc-card.image-scale-strength-medium:focus-within .image-inner,.mc-card.image-scale-strength-medium:hover .image-inner{transform:scale(1.08)}.mc-card.image-scale-strength-prominent:focus-within .image-inner,.mc-card.image-scale-strength-prominent:hover .image-inner{transform:scale(1.2)}.mc-card.image-scale-strength-none:focus-within .image-inner,.mc-card.image-scale-strength-none:hover .image-inner{transform:none}.mc-card.bordered{background:var(--mds_brand_appearance_neutral_default_background-color);border:var(--mds_global_border_width) var(--mds_global_border_style) var(--mds_brand_appearance_neutral_default_border-color);border-radius:var(--mds_brand_border_x-large_radius)}.mc-card.bordered.hover,.mc-card.bordered:focus-within,.mc-card.bordered:hover{box-shadow:var(--mds_brand_appearance_shadow_low_first-layer_offset-x) var(--mds_brand_appearance_shadow_low_first-layer_offset-y) var(--mds_brand_appearance_shadow_low_first-layer_blur-radius) var(--mds_brand_appearance_shadow_low_first-layer_spread-radius) var(--mds_brand_appearance_shadow_low_first-layer_color),var(--mds_brand_appearance_shadow_low_second-layer_offset-x) var(--mds_brand_appearance_shadow_low_second-layer_offset-y) var(--mds_brand_appearance_shadow_low_second-layer_blur-radius) var(--mds_brand_appearance_shadow_low_second-layer_spread-radius) var(--mds_brand_appearance_shadow_low_second-layer_color),var(--mds_brand_appearance_shadow_low_third-layer_offset-x) var(--mds_brand_appearance_shadow_low_third-layer_offset-y) var(--mds_brand_appearance_shadow_low_third-layer_blur-radius) var(--mds_brand_appearance_shadow_low_third-layer_spread-radius) var(--mds_brand_appearance_shadow_low_third-layer_color)}.mc-card.bordered.default-padding .image-inner-container{border-top-left-radius:var(--mds_brand_border_x-large_radius);border-top-right-radius:var(--mds_brand_border_x-large_radius)}.mc-card .content,.mc-card.vertical{flex-direction:column}.mc-card.vertical.borderless .content-inner{margin-bottom:0}.mc-card.vertical.borderless .image-inner-container{border-radius:var(--mds_brand_border_x-large_radius)}.mc-card.vertical.borderless .actions{margin-bottom:0}.mc-card.vertical.borderless.small .content{margin:12px 0 0;row-gap:24px}.mc-card.vertical.borderless.medium .content{margin:16px 0 0;row-gap:24px}.mc-card.vertical.borderless.large .content{margin:24px 0 0;row-gap:32px}.mc-card.horizontal.borderless.no-image .content,.mc-card.vertical.borderless.no-image .content{margin:0}.mc-card.horizontal .image,.mc-card.horizontal .image .image-inner-container{display:flex;flex:0 0 auto}.mc-card.horizontal .image .image-inner{width:100%}.mc-card.horizontal .content{flex:1 1 auto;height:auto}.mc-card.horizontal.bordered .image-inner-container{border-radius:0;border-bottom-left-radius:var(--mds_brand_border_x-large_radius);border-top-left-radius:var(--mds_brand_border_x-large_radius)}.mc-card.horizontal.borderless .image-inner-container{border-radius:var(--mds_brand_border_x-large_radius)}.mc-card.horizontal.borderless.no-image .actions,.mc-card.small.custom-padding .actions{margin-bottom:0}.mc-card .image .image-inner-container{overflow:hidden;width:100%;height:100%}.mc-card .image .image-inner{background-color:var(--mds_brand_appearance_neutral_weakest_background-color);background-position:50% 50%;background-size:cover;transition-duration:var(--mds_global_transition_fast_duration);transition-property:var(--mds_global_transition_properties);transition-timing-function:var(--mds_global_transition_timing)}.mc-card .image-as-slot .image-inner{background-color:transparent}.mc-card .content{display:flex;height:100%}.mc-card .content-inner{display:flex;flex-direction:column;flex:1}.mc-card.content-top .content-inner{justify-content:flex-start}.mc-card.content-middle .content-inner{justify-content:center}.mc-card.content-bottom .content-inner{justify-content:flex-end}.mc-card .header{display:flex;flex-direction:column-reverse}.mc-card .header .heading,.mc-card .header .sub-heading{margin:0}.mc-card .footer,.mc-card .header .sub-heading{color:var(--mds_brand_appearance_neutral_weak_text-color)}.mc-card.small .content{margin:20px 24px 0}.mc-card.small .content-inner{margin-bottom:24px;row-gap:8px}.mc-card.small .actions{margin-bottom:24px}.mc-card.small .header{row-gap:8px}.mc-card.small.custom-padding.vertical .content{margin-left:0;margin-right:0}.mc-card.small.custom-padding.horizontal .content{margin-top:0}.mc-card.medium.custom-padding .actions,.mc-card.small.custom-padding.no-actions .content-inner{margin-bottom:0}.mc-card.small .heading{font-family:var(--mds_brand_typography_headline_font-family),var(--mds_brand_typography_headline_font-family-fallback);font-size:var(--mds_brand_typography_headline_x-small_mobile_font-size);line-height:var(--mds_brand_typography_headline_x-small_mobile_line-height)}@media screen and (min-width:1025px){.mc-card.small .heading{font-size:var(--mds_brand_typography_headline_x-small_desktop_font-size);line-height:var(--mds_brand_typography_headline_x-small_desktop_line-height)}}.mc-card.small .heading{text-transform:var(--mds_brand_typography_headline_x-small_text-transform);font-style:var(--mds_brand_typography_headline_x-small_font-style);font-weight:var(--mds_brand_typography_headline_x-small_font-weight)}.mc-card.small,.mc-card.small .footer,.mc-card.small .sub-heading{font-family:var(--mds_brand_typography_text_font-family),var(--mds_brand_typography_text_font-family-fallback);font-size:var(--mds_brand_typography_text_small_mobile_font-size);line-height:var(--mds_brand_typography_text_small_mobile_line-height)}@media screen and (min-width:1025px){.mc-card.small .footer,.mc-card.small .sub-heading{font-size:var(--mds_brand_typography_text_small_desktop_font-size);line-height:var(--mds_brand_typography_text_small_desktop_line-height)}}.mc-card.small,.mc-card.small .footer,.mc-card.small .sub-heading{font-style:var(--mds_brand_typography_text_small_normal_font-style);font-weight:var(--mds_brand_typography_text_small_normal_font-weight)}@media screen and (min-width:1025px){.mc-card.small{font-size:var(--mds_brand_typography_text_small_desktop_font-size);line-height:var(--mds_brand_typography_text_small_desktop_line-height)}}.mc-card.medium .content{margin:20px 24px 0}.mc-card.medium .content-inner{margin-bottom:24px;row-gap:8px}.mc-card.medium .actions{margin-bottom:24px}.mc-card.medium .header{row-gap:8px}.mc-card.medium.custom-padding.vertical .content{margin-left:0;margin-right:0}.mc-card.medium.custom-padding.horizontal .content{margin-top:0}.mc-card.large.custom-padding .actions,.mc-card.medium.custom-padding.no-actions .content-inner{margin-bottom:0}.mc-card.medium .heading{font-family:var(--mds_brand_typography_headline_font-family),var(--mds_brand_typography_headline_font-family-fallback);font-size:var(--mds_brand_typography_headline_small_mobile_font-size);line-height:var(--mds_brand_typography_headline_small_mobile_line-height)}@media screen and (min-width:1025px){.mc-card.medium .heading{font-size:var(--mds_brand_typography_headline_small_desktop_font-size);line-height:var(--mds_brand_typography_headline_small_desktop_line-height)}}.mc-card.medium .heading{text-transform:var(--mds_brand_typography_headline_small_text-transform);font-style:var(--mds_brand_typography_headline_small_font-style);font-weight:var(--mds_brand_typography_headline_small_font-weight)}.mc-card.medium,.mc-card.medium .footer,.mc-card.medium .sub-heading{font-family:var(--mds_brand_typography_text_font-family),var(--mds_brand_typography_text_font-family-fallback);font-size:var(--mds_brand_typography_text_small_mobile_font-size);line-height:var(--mds_brand_typography_text_small_mobile_line-height)}@media screen and (min-width:1025px){.mc-card.medium .footer,.mc-card.medium .sub-heading{font-size:var(--mds_brand_typography_text_small_desktop_font-size);line-height:var(--mds_brand_typography_text_small_desktop_line-height)}}.mc-card.medium .footer,.mc-card.medium .sub-heading{font-style:var(--mds_brand_typography_text_small_normal_font-style);font-weight:var(--mds_brand_typography_text_small_normal_font-weight)}.mc-card.medium{font-size:var(--mds_brand_typography_text_medium_mobile_font-size);line-height:var(--mds_brand_typography_text_medium_mobile_line-height)}@media screen and (min-width:1025px){.mc-card.medium{font-size:var(--mds_brand_typography_text_medium_desktop_font-size);line-height:var(--mds_brand_typography_text_medium_desktop_line-height)}}.mc-card.medium{font-style:var(--mds_brand_typography_text_medium_normal_font-style);font-weight:var(--mds_brand_typography_text_medium_normal_font-weight)}.mc-card.large .content{margin:24px 32px 0}.mc-card.large .content-inner{margin-bottom:32px;row-gap:12px}.mc-card.large .actions{margin-bottom:32px}.mc-card.large .header{row-gap:12px}.mc-card.large.custom-padding.vertical .content{margin-left:0;margin-right:0}.mc-card.large.custom-padding.horizontal .content{margin-top:0}.mc-card.large.custom-padding.no-actions .content-inner{margin-bottom:0}.mc-card.large .heading{font-family:var(--mds_brand_typography_headline_font-family),var(--mds_brand_typography_headline_font-family-fallback);font-size:var(--mds_brand_typography_headline_small_mobile_font-size);line-height:var(--mds_brand_typography_headline_small_mobile_line-height)}@media screen and (min-width:1025px){.mc-card.large .heading{font-size:var(--mds_brand_typography_headline_small_desktop_font-size);line-height:var(--mds_brand_typography_headline_small_desktop_line-height)}}.mc-card.large .heading{text-transform:var(--mds_brand_typography_headline_small_text-transform);font-style:var(--mds_brand_typography_headline_small_font-style);font-weight:var(--mds_brand_typography_headline_small_font-weight)}.mc-card.large,.mc-card.large .footer,.mc-card.large .sub-heading{font-family:var(--mds_brand_typography_text_font-family),var(--mds_brand_typography_text_font-family-fallback);font-size:var(--mds_brand_typography_text_small_mobile_font-size);line-height:var(--mds_brand_typography_text_small_mobile_line-height)}@media screen and (min-width:1025px){.mc-card.large .footer,.mc-card.large .sub-heading{font-size:var(--mds_brand_typography_text_small_desktop_font-size);line-height:var(--mds_brand_typography_text_small_desktop_line-height)}}.mc-card.large .footer,.mc-card.large .sub-heading{font-style:var(--mds_brand_typography_text_small_normal_font-style);font-weight:var(--mds_brand_typography_text_small_normal_font-weight)}.mc-card.large{font-size:var(--mds_brand_typography_text_medium_mobile_font-size);line-height:var(--mds_brand_typography_text_medium_mobile_line-height)}@media screen and (min-width:1025px){.mc-card.large{font-size:var(--mds_brand_typography_text_medium_desktop_font-size);line-height:var(--mds_brand_typography_text_medium_desktop_line-height)}}.mc-card.large{font-style:var(--mds_brand_typography_text_medium_normal_font-style);font-weight:var(--mds_brand_typography_text_medium_normal_font-weight)}.mc-card.clickable,.mc-card.link{text-decoration:none;cursor:pointer}.mc-card.clickable,.mc-card.clickable:hover,.mc-card.clickable:visited,.mc-card.link,.mc-card.link:hover,.mc-card.link:visited{color:var(--mds_brand_appearance_neutral_default_on-background-color)}.mc-card.clickable:hover .heading,.mc-card.link:hover .heading{text-decoration:underline}.mc-card.clickable.bordered:focus-within,.mc-card.clickable.borderless:focus-within,.mc-card.link.bordered:focus-within,.mc-card.link.borderless:focus-within{outline:0;box-shadow:var(--mds_brand_appearance_state_focus_default_shadow_offset-x) var(--mds_brand_appearance_state_focus_default_shadow_offset-y) var(--mds_brand_appearance_state_focus_default_shadow_blur-radius) var(--mds_brand_appearance_state_focus_default_shadow_spread-radius) var(--mds_brand_appearance_state_focus_default_shadow_color)}.mc-card .hidden{display:none!important}`;
var p = [i, unsafeCSS(g)];
var e = class extends LitElement {
  constructor() {
    super(...arguments);
    this.hasbodyslot = false;
    this.hasactionsslot = false;
    this.hasimageslot = false;
    this.hasfooterslot = false;
    this.hassubheadingslot = false;
    this.variant = "bordered";
    this.orientation = "vertical";
    this.fit = "medium";
    this.contentalignment = "top";
    this.imagescalestrength = "light";
  }
  static get styles() {
    return p;
  }
  render() {
    let t = { "mc-card": true, link: !!(this.href && this.href !== ""), clickable: !!this.clickable, [`${this.fit}`]: true, [`${this.variant}`]: true, [`${this.orientation}`]: true, [`content-${this.contentalignment}`]: true, "no-image": !this.hasImage(), [`image-scale-strength-${this.imagescalestrength}`]: true, "custom-padding": !!this.padding, "default-padding": !this.padding, "no-actions": !this.hasactionsslot, [`${o(this.classList, ["hover", "focus", "active"])}`]: true }, n = {};
    return this.padding && (n.padding = this.padding), this.href && this.href !== "" ? html`<a part="container" href="${this.href}" rel="${ifDefined(this.rel === "" ? void 0 : this.rel)}" target="${ifDefined(this.target ? this.target : void 0)}" class="${classMap(t)}" style="${styleMap(n)}">${this.renderImage()} ${this.renderContent()}</a>` : html`<div part="container" class="${classMap(t)}" style="${styleMap(n)}">${this.renderImage()} ${this.renderContent()}</div>`;
  }
  renderImage() {
    return html`${this.renderImageAsSlot()}${this.renderImageAsBackground()}`;
  }
  onImageSlotChange() {
    this.hasimageslot = this.imageSlotNodes.length > 0;
  }
  hasImage() {
    return !!(this.hasimageslot || this.image && this.image !== "");
  }
  renderImageAsSlot() {
    let t = { hidden: !this.hasimageslot }, n = {};
    return this.imagebackgroundcolor && (n.backgroundColor = this.imagebackgroundcolor), html`<div class="image-as-slot image${classMap(t)}" part="image-container"><div class="image-inner-container"><div class="image-inner" part="image-inner" style="${styleMap(n)}"><slot name="image" @slotchange="${this.onImageSlotChange}"></slot></div></div></div>`;
  }
  renderImageAsBackground() {
    if (!(this.image && this.image !== "")) return html``;
    let t = this.imagepercent;
    t || (this.orientation === "vertical" ? t = 56.25 : t = 33);
    let n = {}, o2 = { backgroundImage: `url(${this.image})` };
    return this.imagebackgroundcolor && (o2.backgroundColor = this.imagebackgroundcolor), this.orientation === "vertical" ? o2.paddingTop = `${t}%` : n.width = `${t}%`, html`<div class="image-as-background image" style="${styleMap(n)}" part="image-container"><div class="image-inner-container"><div class="image-inner" part="image-inner" style="${styleMap(o2)}"></div></div></div>`;
  }
  renderContent() {
    let t = this.hasBody(), n = this.hasFooter(), o2 = { hidden: !this.heading && !this.subheading && !n && !t && !this.hasactionsslot, "no-image": !this.hasImage() }, m = { margin: !this.hasImage() && this.padding ? "0" : void 0 };
    return html`<div class="content ${classMap(o2)}" part="content-container" style="${styleMap(m)}"><div part="content-inner" class="content-inner">${this.renderHeading()} ${this.renderBody(t)} ${this.renderFooter(n)}</div>${this.renderActions(this.hasactionsslot)}</div>`;
  }
  renderHeading() {
    return !this.heading && !this.subheading && !this.hassubheadingslot ? html`` : html`<div class="header" part="header-container">${this.heading ? html`<h2 class="heading">${this.heading}</h2>` : ""} ${this.subheading ? html`<p class="sub-heading">${this.subheading}</p>` : ""}<slot name="subheading" @slotchange="${this.onSubheadingSlotChange}"></slot></div>`;
  }
  renderBody(t) {
    return html`<div class="body ${classMap({ hidden: !t })}" part="body-container"><slot @slotchange="${this.onBodySlotChange}">${this.body}</slot></div>`;
  }
  onBodySlotChange() {
    this.hasbodyslot = this.bodySlotNodes.length > 0;
  }
  hasBody() {
    return !!(this.hasbodyslot || this.body && this.body !== "");
  }
  renderFooter(t) {
    return html`<div class="${classMap({ footer: true, hidden: !t })}" part="footer-container"><slot name="footer" @slotchange="${this.onFooterSlotChange}">${this.footer}</slot></div>`;
  }
  onFooterSlotChange() {
    this.hasfooterslot = this.footerSlotNodes.length > 0;
  }
  hasFooter() {
    return !!(this.hasfooterslot || this.footer && this.footer !== "");
  }
  renderActions(t) {
    let n = { hidden: !!(!t || this.href && this.href !== "") };
    return this.href && this.href !== "" && t && console.warn('"actions" will not be rendered if a card has a "href"'), html`<div class="actions ${classMap(n)}" part="actions-container"><slot name="actions" @slotchange="${this.onActionsSlotChange}"></slot></div>`;
  }
  onActionsSlotChange() {
    this.hasactionsslot = this.actionsSlotNodes.length > 0;
  }
  onSubheadingSlotChange() {
    this.hassubheadingslot = this.subheadingSlotNodes.length > 0;
  }
};
a([property({ type: Boolean })], e.prototype, "hasbodyslot", 2), a([queryAssignedNodes({ slot: "", flatten: true })], e.prototype, "bodySlotNodes", 2), a([property({ type: Boolean })], e.prototype, "hasactionsslot", 2), a([queryAssignedNodes({ slot: "actions", flatten: true })], e.prototype, "actionsSlotNodes", 2), a([property({ type: Boolean })], e.prototype, "hasimageslot", 2), a([queryAssignedNodes({ slot: "image", flatten: true })], e.prototype, "imageSlotNodes", 2), a([property({ type: Boolean })], e.prototype, "hasfooterslot", 2), a([queryAssignedNodes({ slot: "footer", flatten: true })], e.prototype, "footerSlotNodes", 2), a([property({ type: Boolean })], e.prototype, "hassubheadingslot", 2), a([queryAssignedNodes({ slot: "subheading", flatten: true })], e.prototype, "subheadingSlotNodes", 2), a([property({ type: String })], e.prototype, "variant", 2), a([property({ type: String })], e.prototype, "orientation", 2), a([property({ type: String })], e.prototype, "fit", 2), a([property({ type: String })], e.prototype, "heading", 2), a([property({ type: String })], e.prototype, "subheading", 2), a([property({ type: String })], e.prototype, "body", 2), a([property({ type: String })], e.prototype, "footer", 2), a([property({ type: String })], e.prototype, "contentalignment", 2), a([property({ type: String })], e.prototype, "padding", 2), a([property({ type: String })], e.prototype, "image", 2), a([property({ type: Number })], e.prototype, "imagepercent", 2), a([property({ type: String })], e.prototype, "imagescalestrength", 2), a([property({ type: String })], e.prototype, "imagebackgroundcolor", 2), a([property({ type: String })], e.prototype, "href", 2), a([property({ type: String })], e.prototype, "rel", 2), a([property({ type: String })], e.prototype, "target", 2), a([property({ type: Boolean })], e.prototype, "clickable", 2);
customElements.get("mc-card") || customElements.define("mc-card", e);
export {
  e as McCard
};
//# sourceMappingURL=@maersk-global_mds-components-core_mc-card.js.map
