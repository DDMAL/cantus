import $ from "jquery";
import Marionette from "marionette";

import template from './sidenav.template.html';

var SIDENAV_TRANSITION_MS = 300;
var BACKDROP_TRANSITION_MS = 150;

/**
 * Render a sidenav element
 *
 * Options:
 *  - content: a view or function returning a view to
 *    render when the sidenav is first shown
 *
 * Methods:
 *  - toggle
 *  - show
 *  - hide
 */
export default Marionette.LayoutView.extend({
    template,

    regions: {
        content: '.sidenav'
    },

    ui: {
        sidenav: '.sidenav'
    },

    initialize() {
        this._isExpanded = this._backdrop = null;
    },

    onRender() {
        const $body = $(document.body);
        this._isExpanded = this.ui.sidenav.hasClass('in');
        this.ui.sidenav.on('transitionend', () => {
            $body.removeClass('sidenav-animating');
        });
    },

    onDestroy() {
        if (this._backdrop)
            this._removeBackdrop();
    },

    _removeBackdrop() {
        this._backdrop.remove();
        this._backdrop = null;
    },

    /** Toggle the side nav open or closed */
    toggle() {
        if (!this._isExpanded)
            this.show();
        else
            this.hide();
    },

    /** Expand the side nav */
    show() {
        if (this._isExpanded)
            return;

        this._renderContent();

        this._isExpanded = true;

        if (!this._backdrop) {
            this._backdrop = $('<div class="sidenav-backdrop fade">');
            this._backdrop.on('click', () => this.hide());
        }

        const $body = $(document.body);

        this._backdrop.appendTo($body);

        $body.addClass('sidenav-animating');

        this._backdrop.addClass('in');
        this.ui.sidenav.addClass('in');
    },

    _renderContent() {
        if (!this.content.currentView) {
            let contentView = this.getOption('content');

            if (typeof contentView === 'function')
                contentView = contentView();

            if (contentView)
                this.content.show(contentView);
        }
    },

    /** Collapse the side nav */
    hide() {
        if (!this._isExpanded)
            return;

        this._isExpanded = false;

        const $body = $(document.body);
        $body.addClass('sidenav-animating');

        this.ui.sidenav.removeClass('in');
        this._backdrop.removeClass('in');
        this._removeBackdrop();
    }
});
