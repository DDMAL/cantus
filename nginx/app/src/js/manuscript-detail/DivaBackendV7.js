import extractImageAttribution from './manifestMetadata';

// OpenSeadragon version matching the one in diva.js v7's README. v7 references
// it and expects window.OpenSeadragon to exist before its bundle runs.
const OSD_SRC = "https://cdn.jsdelivr.net/npm/openseadragon@6.0.2/build/openseadragon/openseadragon.min.js";

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
 * OpenSeadragon and the vendored v7 bundle, mounts the viewer, and adapts v7's
 * public API (v7.4.0) to the adapter's backend-neutral events, tracking the
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
        // callbacks here; they fire once the underlying viewer events arrive.
        this.subscribers = {
            'viewer:loaded': [],
            'page:changed': [],
            'document:loaded': [],
            'manifest:loaded': []
        };

        // Current page index, tracked from v7's pagechange event.
        this.currentIndex = 0;

        // Page image URIs in v7's page order, filled once the viewer is ready.
        this.pageURIs = [];

        // True once v7's `ready` promise has resolved; per v7's README, page
        // state must not be read nor viewer commands issued before then.
        this.ready = false;

        this.onPageChange = this.handlePageChange.bind(this);
    }

    initialize() {
        // v7 exposes no manifest attribution, so fetch the manifest ourselves;
        // kept off initialize()'s promise so a failed fetch can't reject it.
        this.loadManifestMetadata();

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
                    return undefined;
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

                this.instance.addEventListener('pagechange', this.onPageChange);

                return this.instance.ready.then(() => this.handleViewerReady());
            });
    }

    /**
     * Fetch the IIIF manifest and emit 'manifest:loaded' with the flattened
     * attribution metadata. Runs independently of initialize()'s load chain.
     */
    loadManifestMetadata() {
        fetch('/manifest-proxy/' + this.manifestUrl)
            .then(response => response.json())
            .then(manifest => {
                if (!this.destroyed)
                    this.emit('manifest:loaded', extractImageAttribution(manifest));
            })
            .catch(error => {
                console.error('Failed to load the IIIF manifest metadata', error); // eslint-disable-line no-console
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

    handleViewerReady() {
        if (this.destroyed)
            return;

        // Strip "/info.json" so each URI matches Folio.image_uri in Django/Solr.
        this.pageURIs = this.instance.getPages().map(
            page => page.primaryImage.id.replace(/\/info\.json$/, ''));
        this.currentIndex = this.instance.getState().currentPageIndex || 0;
        this.ready = true;

        this.emit('viewer:loaded');
        this.emit('document:loaded');
        this.emitPageChanged();
    }

    handlePageChange(event) {
        this.currentIndex = event.detail.pageIndex;

        if (this.ready)
            this.emitPageChanged();
    }

    emitPageChanged() {
        this.emit('page:changed', {
            index: this.currentIndex,
            imageURI: this.getCurrentPageURI()
        });
    }

    emit(event, payload) {
        this.subscribers[event].forEach(callback => callback(payload));
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

    /** Go to the page with the given image URI, if the viewer has it. */
    gotoPageByURI(uri) {
        var index = this.pageURIs.indexOf(uri);
        if (index >= 0)
            this.instance.goToPage(index);
    }

    // next()/previous() follow the current layout, advancing a full opening in
    // a spread layout (both pages of an opening share one scroll position).
    goToNextPage() {
        this.instance.next();
    }

    goToPreviousPage() {
        this.instance.previous();
    }

    // No-op: OpenSeadragon's autoResize reflows the viewer when its container resizes.
    resize() {}

    // No-op: v7 sets its layout from the manifest; the reader toggles it in the toolbar.
    changeView() {}

    setHighlights() {}

    /**
     * Go to an OMR result's page and zoom to its region, given in
     * full-resolution image pixels.
     */
    focusRegion(region) {
        // A search can run before the viewer is ready; retry once it is, so
        // pageURIs is populated.
        if (!this.ready) {
            this.on('viewer:loaded', () => this.focusRegion(region));
            return;
        }

        var index = this.pageURIs.indexOf(region.imageURI);
        if (index < 0)
            return;

        this.instance.zoomToRegion(index, {
            x: region.x,
            y: region.y,
            width: region.width,
            height: region.height
        });
    }

    destroy() {
        // Mark destroyed so an in-flight initialize() bails before constructing.
        this.destroyed = true;

        if (this.instance) {
            this.instance.removeEventListener('pagechange', this.onPageChange);
            this.instance.destroy();
        }

        this.instance = null;
    }
}
