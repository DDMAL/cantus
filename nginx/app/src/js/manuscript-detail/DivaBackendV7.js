// OpenSeadragon version matching the one diva.js v7's own test harness loads.
// v7 references OpenSeadragon as a global and expects window.OpenSeadragon to
// exist before its bundle runs.
const OSD_SRC = "https://cdnjs.cloudflare.com/ajax/libs/openseadragon/5.0.1/openseadragon.min.js";

// Id of the <style> element Diva v7 injects its stylesheet into. v7 skips that
// global injection if an element with this id already exists (diva.ts), so we
// pre-create an empty one to keep v7's generic, unscoped CSS (.modal, .status,
// .thumbs, ...) off the page; the equivalent rules ship scoped to #diva-wrapper,
// generated from the vendored v7 styles at build time (see gulpfile.mjs
// bundle:css).
const DIVA_INLINE_STYLE_ID = "diva-inline-styles";

/**
 * Pre-empt Diva v7's global stylesheet injection by leaving an empty <style>
 * element under the id it looks for. Safe to call more than once.
 */
function suppressDivaGlobalStyles() {
    if (document.getElementById(DIVA_INLINE_STYLE_ID))
        return;

    var styleTag = document.createElement('style');
    styleTag.id = DIVA_INLINE_STYLE_ID;
    document.head.appendChild(styleTag);
}

/**
 * Inject the OpenSeadragon CDN script and resolve when loaded. Safe to call
 * more than once: reuses an already-loaded global or an in-flight script tag.
 */
function loadOpenSeadragon() {
    if (window.OpenSeadragon)
        return Promise.resolve();

    return new Promise((resolve, reject) => {
        var existing = document.querySelector('script[data-diva-osd]');
        if (existing) {
            existing.addEventListener('load', () => resolve());
            existing.addEventListener('error', reject);
            return;
        }

        var script = document.createElement('script');
        script.src = OSD_SRC;
        script.async = true;
        script.setAttribute('data-diva-osd', '');
        script.onload = () => resolve();
        script.onerror = reject;
        document.head.appendChild(script);
    });
}

/**
 * Stub Diva v7 backend.
 *
 * Stage 2 of the v6 -> v7 migration (issue #942) only proves the wiring: the
 * vendored v7 bundle, the webpack `diva7` alias, and the OpenSeadragon global
 * all load, and a v7 viewer mounts over the IIIF manifest. None of the
 * Cantus-facing behaviour (events, navigation, URI<->index, OMR focus, toolbar
 * chrome) is implemented yet -- those are migrated method-by-method in Stage 3.
 * In particular this backend deliberately does not emit "viewer:loaded", which
 * keeps DivaView's downstream toolbar/folio code dormant.
 */
export default class DivaBackendV7 {
    constructor(options) {
        this.rootElementId = options.rootElementId;
        this.manifestUrl = options.manifestUrl;

        this.instance = null;
        this.destroyed = false;
    }

    initialize() {
        // Each step is gated on `destroyed` so navigating away mid-load does
        // not construct a viewer against a DOM node that no longer exists.
        return loadOpenSeadragon()
            .then(() => {
                if (this.destroyed)
                    return undefined;
                suppressDivaGlobalStyles();
                return import(/* webpackChunkName: "diva-v7" */ 'diva7');
            })
            .then(() => {
                if (this.destroyed)
                    return;
                const Diva = window.Diva;
                if (!Diva)
                    throw new Error('Diva v7 bundle loaded but window.Diva is undefined');

                // No acceptHeaders: /manifest-proxy/ uses DRF's JSONRenderer,
                // which 406s anything other than application/json.
                // showTitle: false — Cantus shows the title in its own header.
                this.instance = new Diva(this.rootElementId, {
                    objectData: '/manifest-proxy/' + this.manifestUrl,
                    showTitle: false
                });
            });
    }

    // --- Stage 3 will implement these on top of the v7 / OSD APIs. ---
    on() {}
    resize() {}
    gotoPageByURI() {}
    getCurrentPageURI() { return null; }
    getAllPageURIs() { return []; }
    getCurrentPageIndex() { return 0; }
    goToNextPage() {}
    goToPreviousPage() {}
    changeView() {}
    getInstanceSelector() { return null; }
    setHighlights() {}
    focusRegion() {}

    destroy() {
        // Mark destroyed so an in-flight initialize() bails before constructing.
        this.destroyed = true;

        if (this.instance)
            this.instance.destroy();

        this.instance = null;
    }
}
