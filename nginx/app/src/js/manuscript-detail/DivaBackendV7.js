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
 * Load the OpenSeadragon global from its CDN, resolving once available. The
 * global check short-circuits once it has loaded, so this only injects a script
 * on the first call (any redundant tag from a rare concurrent call is harmless).
 */
function loadOpenSeadragon() {
    if (window.OpenSeadragon)
        return Promise.resolve();

    return new Promise((resolve, reject) => {
        var script = document.createElement('script');
        script.src = OSD_SRC;
        script.async = true;
        script.onload = () => resolve();
        script.onerror = () => reject(new Error('Failed to load OpenSeadragon from ' + OSD_SRC));
        document.head.appendChild(script);
    });
}

/**
 * Diva v7 backend for DivaAdapter.
 *
 * Implements (issue #942, Stage 3) the v7 viewer lifecycle: it lazily loads
 * OpenSeadragon and the vendored v7 bundle, mounts the viewer, and translates
 * v7's DOM CustomEvents into the adapter's backend-neutral events, tracking the
 * current page index and page URIs along the way.
 */
export default class DivaBackendV7 {
    constructor(options) {
        this.rootElementId = options.rootElementId;
        this.manifestUrl = options.manifestUrl;

        this.instance = null;
        this.destroyed = false;

        // Adapter event subscribers. DivaView subscribes synchronously right
        // after initialize(), before the viewer exists, so on() only records
        // callbacks here; they fire once the underlying DOM events arrive.
        this.subscribers = {
            'viewer:loaded': [],
            'page:changed': [],
            'document:loaded': [],
            'manifest:loaded': []
        };

        // Current page index, tracked from diva-page-change.
        this.currentIndex = 0;

        // Page image URIs in v7's page order, filled on the first page render.
        this.pageURIs = [];

        // The first diva-page-change is v7's reliable "ready" signal, so it also
        // stands in for viewer:loaded / document:loaded; diva-loading-change
        // reports loading:false before anything renders, so it cannot be used.
        this.firstPageHandled = false;

        // The element we listen on, and a stable bound handler so the same
        // reference can be both added and removed.
        this.viewerElement = null;
        this.onPageChange = this.handlePageChange.bind(this);
    }

    initialize() {
        // Each step is gated on `destroyed` so navigating away mid-load does not
        // construct a viewer against a DOM node that no longer exists.
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

                // v7 dispatches its CustomEvents on the #main-viewer element with
                // bubbles:false, so we listen on that element directly (a listener
                // on #diva-wrapper would never fire). Elm renders it synchronously
                // during construction, so it exists by now.
                this.viewerElement = document.getElementById('main-viewer');
                this.viewerElement.addEventListener('diva-page-change', this.onPageChange);
            });
    }

    /**
     * Record a callback for an adapter event; see the constructor note on why
     * dispatch is deferred. For 'page:changed' the callback receives
     * { index, imageURI }; the load events pass no argument.
     */
    on(event, callback) {
        if (this.subscribers[event])
            this.subscribers[event].push(callback);
    }

    /**
     * Track the new page index and re-emit the adapter's events. The first event
     * also stands in for viewer:loaded / document:loaded (see firstPageHandled).
     */
    handlePageChange(event) {
        this.currentIndex = event.detail.index;

        if (!this.firstPageHandled) {
            this.firstPageHandled = true;
            this.pageURIs = this.readPageURIs();
            this.emit('viewer:loaded');
            this.emit('document:loaded');
        }

        this.emit('page:changed', {
            index: this.currentIndex,
            imageURI: this.getCurrentPageURI()
        });
    }

    emit(event, payload) {
        this.subscribers[event].forEach(callback => callback(payload));
    }

    /**
     * Read the page image URIs in v7's page order from the #main-viewer element.
     *
     * v7 stores per-page tile sources there as "<service-base>/info.json"; Cantus
     * identifies folios by the bare service base URI (matching Folio.image_uri in
     * Django/Solr and the OMR result coordinates), so strip the suffix. Reading
     * from the viewer keeps the array index-aligned with v7's own pages, which
     * drop any canvas that has no image.
     *
     * NOTE: `tileSources` is a TypeScript-private field, readable at runtime but
     * not part of v7's public API (a future Diva bump could rename it).
     */
    readPageURIs() {
        return this.viewerElement.tileSources.map(
            tileSource => tileSource.replace(/\/info\.json$/, ''));
    }

    getCurrentPageURI() {
        return this.pageURIs[this.currentIndex] || null;
    }

    getAllPageURIs() {
        return this.pageURIs.slice();
    }

    getCurrentPageIndex() {
        return this.currentIndex;
    }

    resize() {}
    gotoPageByURI() {}
    goToNextPage() {}
    goToPreviousPage() {}
    changeView() {}
    getInstanceSelector() { return null; }
    setHighlights() {}
    focusRegion() {}

    destroy() {
        // Mark destroyed so an in-flight initialize() bails before constructing.
        this.destroyed = true;

        if (this.viewerElement) {
            this.viewerElement.removeEventListener('diva-page-change', this.onPageChange);
            this.viewerElement = null;
        }

        if (this.instance)
            this.instance.destroy();

        this.instance = null;
    }
}
