import DivaBackend from './DivaBackend';

/**
 * Facade owning 100% of the Cantus-to-Diva surface. It delegates
 * to DivaBackend, constructed synchronously in initialize() (so `this.backend`
 * is set before any other method runs); the heavy Diva bundle + OpenSeadragon
 * load lazily from inside DivaBackend.initialize().
 */
export default class DivaAdapter {
    constructor(options) {
        this.options = options;
        this.backend = null;
    }

    initialize() {
        this.backend = new DivaBackend(this.options);
        return this.backend.initialize();
    }

    on(event, callback) {
        return this.backend.on(event, callback);
    }

    gotoPageByURI(uri) {
        return this.backend.gotoPageByURI(uri);
    }

    getCurrentPageURI() {
        return this.backend.getCurrentPageURI();
    }

    getAllPageURIs() {
        return this.backend.getAllPageURIs();
    }

    getCurrentPageIndex() {
        return this.backend.getCurrentPageIndex();
    }

    goToNextPage() {
        return this.backend.goToNextPage();
    }

    goToPreviousPage() {
        return this.backend.goToPreviousPage();
    }

    setHighlights(regions) {
        return this.backend.setHighlights(regions);
    }

    focusRegion(region) {
        return this.backend.focusRegion(region);
    }

    destroy() {
        if (this.backend) {
            this.backend.destroy();
            this.backend = null;
        }
    }
}
