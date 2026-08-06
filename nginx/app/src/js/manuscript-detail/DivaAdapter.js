import "diva";

const diva = window.Diva;

// Backend-neutral event names mapped to the underlying Diva v6 topics,
// so callers depend on the adapter's vocabulary rather than Diva's own.
const EVENT_TOPICS = {
    "viewer:loaded": "ViewerDidLoad",
    "page:changed": "VisiblePageDidChange",
    "document:loaded": "DocumentDidLoad",
    "manifest:loaded": "ManifestDidLoad"
};

export default class DivaAdapter {
    constructor(options) {
        this.rootElementId = options.rootElementId;
        this.manifestUrl = options.manifestUrl;
        this.toolbarParentObject = options.toolbarParentObject;

        this.instance = null;
        this.eventHandles = [];
    }

    initialize() {
        var options = {
            toolbarParentObject: this.toolbarParentObject[0],

            enableAutoTitle: false,
            enableFilename: false,
            enableImageTitles: false,

            fixedHeightGrid: true,

            enableKeyScroll: false,
            enableSpaceScroll: false,

            objectData: '/manifest-proxy/' + this.manifestUrl,

            blockMobileMove: false
        };
        this.instance = new diva(this.rootElementId, options);

        // Rebind drag-to-pan here once the viewer exists.
        this.on("viewer:loaded", () => {
            if (window.resetDragscroll)
                window.resetDragscroll();
        });
    }

    /**
     * Subscribe to an adapter event, registering it for automatic deregistration
     * @param event one of the keys in EVENT_TOPICS
     * @param callback for 'page:changed', invoked with a normalized
     *                 { index, imageURI }; for other events, invoked with Diva's
     *                 original arguments unchanged (e.g. 'manifest:loaded'
     *                 receives the manifest)
     */
    on(event, callback) {
        var handler = callback;
        // Normalize the page-change payload to a backend-neutral shape rather
        // than leaking Diva's raw arguments to callers.
        if (event === "page:changed")
            handler = () => callback({
                index: this.instance.getActivePageIndex(),
                imageURI: this.instance.getCurrentPageURI()
            });
        this.eventHandles.push(diva.Events.subscribe(EVENT_TOPICS[event], handler));
    }

    resize() {
        // NOTE: the v6 viewer subscribes to this scoped to its instance, but
        // publishing *with* the instance throws (the scoped updatePanelSize
        // subscriber calls methods the public instance does not expose). The
        // unscoped publish reaches no subscriber and is effectively a no-op;
        // resize is handled natively (OSD ResizeObserver) once on v7.
        diva.Events.publish("PanelSizeDidChange");
    }

    gotoPageByURI(uri) {
        return this.instance.gotoPageByURI(uri);
    }

    getCurrentPageURI() {
        return this.instance.getCurrentPageURI();
    }

    getAllPageURIs() {
        return this.instance.getAllPageURIs();
    }

    getCurrentPageIndex() {
        return this.instance.getActivePageIndex();
    }

    goToNextPage() {
        // Advance a whole opening (two pages) in book view, otherwise one.
        var step = this.instance.getState().v === 'b' ? 2 : 1;
        this.instance.gotoPageByIndex(this.instance.getActivePageIndex() + step);
    }

    goToPreviousPage() {
        var step = this.instance.getState().v === 'b' ? 2 : 1;
        this.instance.gotoPageByIndex(this.instance.getActivePageIndex() - step);
    }

    changeView(view) {
        return this.instance.changeView(view);
    }

    getInstanceSelector() {
        return this.instance.getInstanceSelector();
    }

    /**
     * Display OMR highlight regions, clearing them when passed an empty array.
     *
     * NOTE: the v6 highlight plugin was removed during the v5 -> v6 upgrade, so
     * this is currently a no-op. Kept as the stable entry point for when
     * highlighting is reintroduced on v7.
     */
    setHighlights(regions) { // eslint-disable-line no-unused-vars
        // No-op: highlight rendering is not currently supported.
    }

    /**
     * Scroll the viewer so that a region of a page is roughly centred. The
     * region coordinates are in Diva's max-zoom pixel space.
     *
     * @param region { imageURI, x, y, width, height }
     *
     * NOTE: this scrolls rather than zooming and does not translate the region
     * width/height; both are to be addressed when reimplemented on the v7 viewport.
     */
    focusRegion(region) {
        if (!this.instance || !region)
            return;

        // Wait for the viewer to be ready before scrolling
        if (!this.instance.isReady()) {
            this.on("viewer:loaded", () => this.focusRegion(region));
            return;
        }

        var outer = this.instance.getSettings().outerObject;

        // Jump to the page the region is on
        var desiredPage = this.instance.getAllPageURIs().indexOf(region.imageURI);
        this.instance.gotoPageByIndex(desiredPage);

        // Vertical scroll to centre the region
        var regionTop = this.instance.translateFromMaxZoomLevel(region.y);
        var currentScrollTop = parseInt(outer.scrollTop(), 10);
        outer.scrollTop(regionTop + currentScrollTop - (outer.height() / 2) + (region.height / 2));

        // Horizontal scroll to centre the region
        var regionLeft = this.instance.translateFromMaxZoomLevel(region.x);
        outer.scrollLeft(regionLeft - (outer.width() / 2) + (region.width / 2));
    }

    destroy() {
        if (this.instance)
            this.instance.destroy();

        this.instance = null;

        this.eventHandles.forEach(handle => diva.Events.unsubscribe(handle));

        this.eventHandles.splice(0, this.eventHandles.length);
    }
}
