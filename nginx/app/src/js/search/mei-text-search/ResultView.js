import NotationResultView from "../omr-search/ResultView";

import ResultItemView from "./ResultItemView";

import template from './result-list.template.html';

/** Notation search's result list, with text lines instead of notation */
export default NotationResultView.extend({
    template,
    childView: ResultItemView
});
