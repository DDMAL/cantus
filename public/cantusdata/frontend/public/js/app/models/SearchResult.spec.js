import SearchResult from './SearchResult';

describe('models/SearchResult', function()
{
    var searchResult = new SearchResult();

    // Note that c is k and e is m
    var query = 'm--ce'; // equivalent to e--ce
    var volpianoResult = 'cd-e--km--1-23ek-e-'; // equivalent to cd-e--ce--1-23ec-e-

    describe('getVolpianoRegex', function()
    {
        var expectedRegex = "/[eEmM][-1-7]*[kKcCrR][-1-7]*[eEmM]/g";
        var expectedLiteralRegex = "/[eEmM][1-7]*-[1-7]*-[1-7]*[kKcCrR][1-7]*[eEmM]/g";

        var expectedResultCount = 2;
        var expectedLiteralResultCount = 1;

        it('should create the proper regex and find all results when performing non-literal volpiano search', function()
        {
            var regex = searchResult.getVolpianoRegex(query, false);
            expect(String(regex)).toBe(expectedRegex);

            var resultCount = (volpianoResult.match(regex) || []).length;
            expect(resultCount).toBe(expectedResultCount);
        });

        it('should create the proper regex and find all results when performing literal volpiano search', function()
        {
            var regex = searchResult.getVolpianoRegex(query, true);
            expect(String(regex)).toBe(expectedLiteralRegex);

            var resultCount = (volpianoResult.match(regex) || []).length;
            expect(resultCount).toBe(expectedLiteralResultCount);
        });
    });

    describe('highlightVolpianoResult', function()
    {
        var expectedVolpianoHTML = "cd-<span class=\"bg-info\">e--km</span>--1-23<span class=\"bg-info\">ek-e</span>-";

        it('should add the proper html tags to the volpiano results', function()
        {
            var highlightedVolpiano = searchResult.highlightVolpianoResult(volpianoResult, query, false);
            expect(highlightedVolpiano).toBe(expectedVolpianoHTML);
        });
    });
});
