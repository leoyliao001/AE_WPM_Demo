import {
  isServer
} from "./chunk-3OXU6R3A.js";

// node_modules/@maersk-global/mds-config/lib/index.js
var t = class {
  static initializeGlobal() {
    !isServer && !window.MdsConfig && (window.MdsConfig = { _iconsDynamicImportPath: null, _isInitialized: false });
  }
  static get iconsDynamicImportPath() {
    return isServer ? this._ssrFallbackPath : (this.initializeGlobal(), window.MdsConfig._iconsDynamicImportPath);
  }
  static set iconsDynamicImportPath(i) {
    if (isServer) {
      this._ssrFallbackPath = i;
      return;
    }
    this.initializeGlobal(), window.MdsConfig._iconsDynamicImportPath = i, window.MdsConfig._isInitialized = true, i || console.warn(`[MdsConfig] Setting icons path to null. This may cause issues:
1. Icons will not be rendered properly
2. mc-icon component will fall back to empty icon
3. Dynamic imports will fail
Please provide a valid path to your icons directory.`);
  }
};
t._ssrFallbackPath = null;

export {
  t
};
//# sourceMappingURL=chunk-K3ZZTKUZ.js.map
