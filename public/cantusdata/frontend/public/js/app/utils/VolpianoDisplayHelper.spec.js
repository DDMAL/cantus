import * as VolpianoHelper from './VolpianoDisplayHelper';

describe('utls/VolpianoDisplayHelper', function()
{
    // Note that c is k and e is m
    var query = 'm--ce'; // equivalent to e--ce
    var volpianoResult = 'cd-e--km--1-23ek-e-'; // equivalent to cd-e--ce--1-23ec-e-
    var textResult = 'veni vidi vici';

    describe('getVolpianoRegex', function()
    {
        var expectedRegex = "/[eEmM][-1-7]*[kKcCrR][-1-7]*[eEmM]/g";
        var expectedLiteralRegex = "/[eEmM][1-7]*-[1-7]*-[1-7]*[kKcCrR][1-7]*[eEmM]/g";

        var expectedResultCount = 2;
        var expectedLiteralResultCount = 1;

        it('should create the proper regex and find all results when performing non-literal volpiano search', function()
        {
            var regex = VolpianoHelper.getVolpianoRegex(query, false);
            expect(String(regex)).toBe(expectedRegex);

            var resultCount = (volpianoResult.match(regex) || []).length;
            expect(resultCount).toBe(expectedResultCount);
        });

        it('should create the proper regex and find all results when performing literal volpiano search', function()
        {
            var regex = VolpianoHelper.getVolpianoRegex(query, true);
            expect(String(regex)).toBe(expectedLiteralRegex);

            var resultCount = (volpianoResult.match(regex) || []).length;
            expect(resultCount).toBe(expectedLiteralResultCount);
        });
    });

    describe('parseVolpianoSyllables', function()
    {
        var expectedParsedVolpiano =
            '<div class="volpiano-syllable">cd-e<span class="volpiano-text">ve-</span></div>' +
            '<div class="volpiano-syllable">km<span class="volpiano-text">ni</span></div>' +
            '<div class="volpiano-syllable">1-23ek-e-<span class="volpiano-text">&nbsp;</span></div>';

        it('should separate the volpiano syllables with html divs', function()
        {
            var parsedVolpiano = VolpianoHelper.parseVolpianoSyllables(textResult, volpianoResult);
            expect(parsedVolpiano).toBe(expectedParsedVolpiano);
        });
    });

    describe('highlightVolpianoResult', function()
    {
        var expectedVolpianoHTML =
            '<div class="volpiano-syllable">cd-<span class="bg-info">e</span>' +
            '<span class="volpiano-text">ve-</span></div>' +
            '<div class="volpiano-syllable"><span class="bg-info">km</span>' +
            '<span class="volpiano-text">ni</span></div>' +
            '<div class="volpiano-syllable"><span class="bg-info">1-</span>23ek-e' +
            '<span class="bg-info">-</span><span class="volpiano-text">&nbsp;</span></div>';

        it('should add the proper html tags to the volpiano results', function()
        {
            var parsedVolpiano = VolpianoHelper.parseVolpianoSyllables(textResult, volpianoResult);
            var highlightedVolpiano = VolpianoHelper.highlightVolpianoResult(volpianoResult,
                parsedVolpiano, query, false);

            expect(highlightedVolpiano).toBe(expectedVolpianoHTML);
        });
    });
});
