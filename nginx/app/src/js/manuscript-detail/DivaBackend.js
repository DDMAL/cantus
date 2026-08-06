import extractImageAttribution from './manifestMetadata';

// Id of the <style> element Diva injects its stylesheet into. Diva skips that
// global injection if an element with this id already exists, so we pre-create
// an empty one to keep Diva's generic, unscoped CSS (.modal, .status, .thumbs,
// ...) off the page; the equivalent rules ship scoped to #diva-wrapper,
// generated from the vendored Diva styles at build time (see gulpfile.mjs
// bundle:css).
const DIVA_INLINE_STYLE_ID = "diva-inline-styles";

/**
 * Pre-empt Diva's global stylesheet injection by leaving an empty <style>
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
 * Load OpenSeadragon and expose it as the window.OpenSeadragon global that
 * Diva's bundle reads before it runs. OSD is vendored locally
 * (dependencies/openseadragon/, version paired with Diva's README) and pulled in
 * as its own lazy chunk; the global check short-circuits once it has loaded.
 */
function loadOpenSeadragon() {
    if (window.OpenSeadragon)
        return Promise.resolve();

    return import(/* webpackChunkName: "openseadragon" */ 'openseadragon')
        .then(module => {
            // The vendored UMD build assigns the OpenSeadragon function to
            // module.exports; expose it under the global Diva reads.
            window.OpenSeadragon = module.default || module;
        });
}

// OMR result focus: Diva's zoomToRegion padding is a fraction of the region, so
// one value can't frame both small and large boxes. Instead frame each result to
// span at least this fraction of the page, so results of any size zoom alike.
const OMR_MIN_VIEW_FRACTION = 0.4;
// Padding kept around a region already larger than that minimum span.
const OMR_MIN_ZOOM_PADDING = 2;

/**
 * Diva backend for DivaAdapter. Lazily loads OpenSeadragon and the vendored Diva
 * bundle, mounts the viewer, and adapts Diva's public API to the adapter's
 * events, tracking the current page index and page URIs along the way.
 */
export default class DivaBackend {
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
            'manifest:loaded': []
        };

        // Current page index, tracked from Diva's pagechange event.
        this.currentIndex = 0;

        // Page image URIs in Diva's page order, filled once the viewer is ready.
        this.pageURIs = [];

        // True once Diva's `ready` promise has resolved; page state must not be
        // read nor viewer commands issued before then.
        this.ready = false;

        this.onPageChange = this.handlePageChange.bind(this);
    }

    initialize() {
        // Diva exposes no manifest attribution, so fetch the manifest ourselves;
        // kept off initialize()'s promise so a failed fetch can't reject it.
        this.loadManifestMetadata();

        // Each step is gated on `destroyed` so navigating away mid-load does not
        // construct a viewer against a DOM node that no longer exists.
        return loadOpenSeadragon()
            .then(() => {
                if (this.destroyed)
                    return undefined;
                suppressDivaGlobalStyles();
                return import(/* webpackChunkName: "diva" */ 'diva');
            })
            .then(() => {
                if (this.destroyed)
                    return undefined;
                const Diva = window.Diva;
                if (!Diva)
                    throw new Error('Diva bundle loaded but window.Diva is undefined');

                // No acceptHeaders: /manifest-proxy/ uses DRF's JSONRenderer,
                // which 406s anything other than application/json.
                // showTitle: false — Cantus shows the title in its own header.
                // showSidebar: false — start with the sidebar collapsed; the
                // reader opens it from the toolbar.
                this.instance = new Diva(this.rootElementId, {
                    objectData: '/manifest-proxy/' + this.manifestUrl,
                    showTitle: false,
                    showSidebar: false
                });

                this.instance.addEventListener('pagechange', this.onPageChange);

                // Cantus's folio label and chants panel track one folio at a
                // time, so open single-page.
                return this.instance.ready
                    .then(() => this.instance.setLayoutMode('single'))
                    .then(() => this.handleViewerReady());
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
     * dispatch is deferred. 'page:changed' passes { index, imageURI };
     * 'manifest:loaded' passes the attribution metadata; 'viewer:loaded' passes
     * no argument.
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

    // Placeholder for a future OMR result-highlight overlay; no overlay is drawn yet.
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

        var page = this.instance.getPages()[index];
        // pageSpan is 0 when the manifest omits page dimensions; the max() below
        // then falls back to OMR_MIN_ZOOM_PADDING.
        var pageSpan = Math.max(page.width || 0, page.height || 0);
        var boxSpan = Math.max(region.width, region.height);
        var padding = Math.max(
            OMR_MIN_ZOOM_PADDING,
            (pageSpan * OMR_MIN_VIEW_FRACTION / boxSpan - 1) / 2
        );

        this.instance.zoomToRegion(index, {
            x: region.x,
            y: region.y,
            width: region.width,
            height: region.height
        }, { padding: padding });
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
