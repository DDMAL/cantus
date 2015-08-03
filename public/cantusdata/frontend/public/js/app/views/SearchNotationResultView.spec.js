"use strict";

describe('SearchNotationResultView', function ()
{
    var testSetup = require('test/setup');
    var SearchNotationResultView = require('./SearchNotationResultView');
    var SearchResultCollection = require('collections/SearchNotationResultCollection');

    // Fixtures
    var testParameters = {
        field: "pnames",
        fieldName: "Pitch",
        query: "bcbccdcc",
        manuscript: "cdn-hsmu-m2149l4"
    };

    var testResponse = {
        status: 200,
        contentType: 'application/json',
        responseText: JSON.stringify({
            numFound: 2,
            results: [
                {
                    boxes: [
                        {y: 4284, p: "004r", x: 2604, w: 125, h: 55},
                        {y: 4452, p: "004r", x: 769, w: 244, h: 86}
                    ],
                    contour: ["u", "d", "u", "r", "u", "d", "r"],
                    intervals: ["u2", "d2", "u9", "r", "u2", "d2", "r"],
                    neumes: ["torculus", "punctum", "torculus", "punctum"],
                    pnames: ["b", "c", "b", "c", "c", "d", "c", "c"],
                    semitones: [1, -1, 13, 0, 2, -2, 0]
                },
                {
                    boxes: [
                        {y: 4123, p: "144v", x: 1564, w: 70, h: 112}
                    ],
                    contour: ["u", "d", "u", "r", "u", "d", "r"],
                    intervals: ["u2", "d2", "u2", "r", "u2", "d2", "r"],
                    neumes: ["torculus", "punctum", "punctum", "punctum", "punctum"],
                    pnames: ["b", "c", "b", "c", "c", "d", "c", "c"],
                    semitones: [1, -1, 1, 0, 2, -2, 0]
                }
            ]
        })
    };

    beforeEach(function ()
    {
        jasmine.Ajax.install();

        this.collection = new SearchResultCollection();

        this.view = new SearchNotationResultView({
            collection: this.collection
        });

        testSetup.showView(this.view);
    });

    afterEach(function ()
    {
        testSetup.clearView();
        jasmine.Ajax.uninstall();
    });

    it('should hide the result table if there are no results', function ()
    {
        expect(this.view.ui.table).not.toBeVisible();
    });

    it('should hide the table during a request until the results load', function ()
    {
        this.collection.updateParameters(testParameters);
        this.collection.fetch();

        expect(this.view.ui.table).not.toBeVisible();

        jasmine.Ajax.requests.mostRecent().respondWith(testResponse);

        expect(this.view.ui.table).toBeVisible();

        // Sanity check
        expect(this.view.$('tbody > tr')).toHaveLength(2);
    });

    it('should clear the results when the collection is reset', function ()
    {
        this.collection.updateParameters(testParameters);
        this.collection.fetch();

        jasmine.Ajax.requests.mostRecent().respondWith(testResponse);

        expect(this.view.ui.table).toBeVisible();
        this.collection.reset();
        expect(this.view.ui.table).not.toBeVisible();
    });
});