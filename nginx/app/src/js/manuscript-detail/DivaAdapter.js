import GlobalVars from '../config/GlobalVars';

import DivaBackendV6 from './DivaBackendV6';
import DivaBackendV7 from './DivaBackendV7';

/**
 * Pick the Diva backend. A `divaBackend` localStorage entry ("v6"|"v7")
 * overrides the GlobalVars.divaBackend default, for local A/B testing without a
 * rebuild: localStorage.setItem("divaBackend", "v7") and reload (removeItem to
 * revert).
 */
function selectBackend() {
    var requested;
    try {
        requested = window.localStorage.getItem('divaBackend');
    } catch (e) {
        // localStorage may be unavailable (e.g. disabled); fall back to the default.
    }

    if (requested === 'v6' || requested === 'v7')
        return requested;

    return GlobalVars.divaBackend === 'v7' ? 'v7' : 'v6';
}

/**
 * Facade owning 100% of the Cantus-to-Diva surface (issue #942). It delegates
 * to one of two interchangeable backends, constructed synchronously in
 * initialize() (so `this.backend` is set before any other method runs):
 *
 *  - DivaBackendV6: the behaviour-preserving v6 implementation.
 *  - DivaBackendV7: the v7 implementation. Both backend classes are imported
 *    statically, but the heavy v7 bundle + OpenSeadragon load lazily from inside
 *    DivaBackendV7.initialize(), so they never touch the v6 path. (Both bundles
 *    define window.Diva, so only one can be the active global -- hence v7's
 *    bundle loads on demand only.)
 */
export default class DivaAdapter {
    constructor(options) {
        this.options = options;
        this.backend = null;
    }

    initialize() {
        var backendName = selectBackend();
        // Surface the active backend so it can be confirmed from the browser
        // console during the v6 -> v7 A/B testing (issue #942).
        console.info('[Diva] using ' + backendName + ' backend'); // eslint-disable-line no-console

        var Backend = backendName === 'v7' ? DivaBackendV7 : DivaBackendV6;
        this.backend = new Backend(this.options);
        return this.backend.initialize();
    }

    on(event, callback) {
        return this.backend.on(event, callback);
    }

    resize() {
        return this.backend.resize();
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

    changeView(view) {
        return this.backend.changeView(view);
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
