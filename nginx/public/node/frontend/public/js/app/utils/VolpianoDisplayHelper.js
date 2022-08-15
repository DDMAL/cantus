import _ from 'underscore';
import $ from 'jquery';
import Syllabifier from './Syllabifier';


// Cache the Volpiano query which  was last turned into a regex
var lastVolpianoQuery = null,
    lastVolpianoRegex = null,
    lastLiteralVolpianoQuery = null,
    lastLiteralVolpianoRegex = null,
    volpianoMap = {};

// Build a mapping of equivalent Volpiano characters
_.forEach(['iwxyz', 'IWXYZ', 'eEmM', 'fF8(nN', 'gG9)oO', 'hHaApP', 'jJbBqQ', 'kKcCrR', 'lLdDsS'],
    function (equivalent)
    {
        _.forEach(equivalent, function (value)
        {
            volpianoMap[value] = equivalent;
        });
    });

/**
 * Helper method to use to make sure that all preparation has
 * been done before displaying the volpiano result
 * @param result
 * @param query
 * @param onlyLiteralMatches
 * @returns {*|string}
 */
export function formatVolpianoResult(text, volpiano, query, onlyLiteralMatches)
{
    var parsedVolpiano = parseVolpianoSyllables(text, volpiano);
    return highlightVolpianoResult(volpiano, parsedVolpiano, query, onlyLiteralMatches);
}

/**
 * Surrounds syllables (groups of notes with 2 dashes on each side)
 * with div tags with class .volpiano-syllable.
 * Also, add individual syllables from the text result under each.
 * @param {string} text
 * @param {string} volpiano
 * @returns {string}
 */
export function parseVolpianoSyllables(text, volpiano)
{
    var volpianoWords = volpiano.split("---");
    var textWordsSplit = text.split(" ");
    var finalString = "";

    // Text for areas with missing notes is surrounded by {}
    // Rejoin "words" surrounded by {} so that these are correctly
    // aligned with set of missing notes.
    var textWords = [];
    for (var i = 0; i < textWordsSplit.length; i++) {
        if (textWordsSplit[i].includes("{")){
            var foundClose = false;
            var rejoinedString = "";
            while (!foundClose){
                if (textWordsSplit[i].includes("}")){
                    rejoinedString += textWordsSplit[i];
                    textWords.push(rejoinedString);
                    foundClose = true;
                } else {
                    rejoinedString += textWordsSplit[i];
                    rejoinedString += " ";
                    i++;
                }
            }
        } else {
            textWords.push(textWordsSplit[i]);
        }
    }

    // We need a separate index for the text words since some
    // volpiano words like numbers are going to be skipped
    var textWordIndex = 0;

    for (var i = 0, len = volpianoWords.length; i < len && volpianoWords[i]; i++)
    {
        // Missing music is noted with "6------6" in Volpiano.
        // When split above, this results in the sequence of volpiano
        // words "6", "", "6". We check for, and deal with, this case
        // first. 
        if (volpianoWords[i] == "6" && volpianoWords[i + 1] == "" && volpianoWords[i+2] == "6"){
            finalString += '<div class="volpiano-syllable">6------6<span class="volpiano-text">' + 
            textWords[textWordIndex] + '</span></div>';
            textWordIndex++;
            // Skip the next two volpianoWords (the "" and "6")
            i += 2;
        } else {
            var wordString = '';
            var volpianoSyllables = volpianoWords[i].split("--");
            var textSyllables = Syllabifier.syllabifyWord(textWords[textWordIndex] || '');
    
            // The word is just a number, no text should be attached to it
            if (!isNaN(parseInt(volpianoWords[i])) && textWords[textWordIndex] !== '|')
            {
                textWordIndex--;
                textSyllables = [];
            }
    
            for (var j = 0; j < volpianoSyllables.length; j++)
            {
                // Add a blank character if there are no more text syllables.
                // This makes sure that the following divs will be correctly aligned
                if (!textSyllables[j])
                    textSyllables[j] = '&nbsp;';
    
                // This is not the end of the text
                if (i < volpianoWords.length - 1)
                {
                    if (j === volpianoSyllables.length - 1)  // End of a word
                        volpianoSyllables[j] += '---';
                    else // End of a syllable
                        volpianoSyllables[j] += '--';
                }
    
                // If the syllabification doesn't match the volpiano,
                // append the rest of the text to the last syllable
                if (j === volpianoSyllables.length - 1 && volpianoSyllables.length < textSyllables.length)
                {
                    for (var k = j + 1; k < textSyllables.length; k++)
                    {
                        textSyllables[j] += textSyllables[k];
                    }
                }
                else if (j < textSyllables.length - 1)  // This is not the end of a text word
                    textSyllables[j] += '-';
    
                wordString += '<div class="volpiano-syllable">' + volpianoSyllables[j] +
                    '<span class="volpiano-text">' + textSyllables[j] + '</span></div>';
            }
    
            finalString += wordString;
            textWordIndex++;
        }
    }

    return finalString;
}

/**
 *  Take a volpiano result string and highlight the substrings
 *  that are part of the query.
 *
 * @param result volpiano result string
 * @returns {string} highlighted string
 */
export function highlightVolpianoResult(originalVolpiano, parsedVolpiano, query, onlyLiteralMatches)
{
    // Format the Volpiano as a lenient regex
    var regex = getVolpianoRegex(query, onlyLiteralMatches);

    if (!regex)
        return parsedVolpiano;

    var matches = originalVolpiano.match(regex);

    if (!matches)
        return parsedVolpiano;

    // Parse the html from the volpiano string in order to ignore
    // the <br> and <span> tags later
    var htmlVolpiano = $.parseHTML(parsedVolpiano);

    // Find the start index of all the matches
    var startIndices = [];
    for (var i = 0; i < matches.length; i++)
        startIndices[i] = originalVolpiano.indexOf(matches[i], (startIndices[i - 1] + 1) || 0);

    var highlighted = '';  // The final result
    var textIndex = 0;  // The index in the original volpiano text
    var matchIndex = 0;  // The index of the current match to highlight
    var highlightIndex = 0; // The index of the next character in the match to highlight

    // Go through each syllable (1 div element per syllable)
    $.each(htmlVolpiano, function(index, element)
    {
        var $el = $(element);

        // Get only the text content of the element
        // Useful to ignore the <br> and <span> tags
        var $textEl = $el.contents().filter(function()
        {
            return this.nodeType === Node.TEXT_NODE;
        });

        var text = $textEl[0].nodeValue;
        var syllableIndex = 0;  // Used if there is more than one match in a single syllable
        var syllableText = '';

        while (startIndices[matchIndex] < textIndex + text.length)
        {
            var highlightStartIndex = startIndices[matchIndex] - textIndex + highlightIndex;

            var matchLength = matches[matchIndex].length;

            // String.substr(startIndex, length) --> 2nd arg is not the end index
            syllableText += text.substr(syllableIndex, highlightStartIndex - syllableIndex);
            syllableText += "<span class='bg-info'>";
            syllableText += text.substr(highlightStartIndex, matchLength - highlightIndex);
            syllableText += "</span>";

            // Update the syllable index
            syllableIndex = highlightStartIndex + matchLength - highlightIndex;

            // Either we reached the end of the result or the end of the syllable
            highlightIndex += Math.min(matchLength - highlightIndex, text.length - highlightStartIndex);
            if (highlightIndex === matchLength)  // We have reached the end of this match, move on
            {
                matchIndex++;
                highlightIndex = 0;
            }
            // Either we reached the end of the match or the end of the match is in the next syllable
            else
                break;
        }

        // Add the rest of the syllable text (all of it in the case where there was not match)
        syllableText += text.substr(syllableIndex);

        $textEl.replaceWith(syllableText);  // Update the text

        textIndex += text.length;
        highlighted += $el.prop('outerHTML');  // Get the string from the html
    });

    return highlighted;
}

/**
 * Create a RegExp which supports lenient matching against a Volpiano query.
 * Its behaviour should match that in the Solr installation at
 * mapping-ExtractVolpianoNotes.txt
 *
 * TODO: if we ever add highlighting for other fields, it would be good to
 * use Solr's built in highlighting functionality. But configuring that to
 * work character by character is non-trivial, so we'll just highlight on the
 * client side for now.
 *
 * @param volpiano {string} a Volpiano query
 * @returns {RegExp}
 */
export function getVolpianoRegex(volpiano, onlyLiteralMatches)
{
    // Use a cached regex if one is available
    if (!onlyLiteralMatches && volpiano === lastVolpianoQuery)
        return lastVolpianoRegex;
    if (onlyLiteralMatches && volpiano === lastLiteralVolpianoQuery)
        return lastLiteralVolpianoRegex;

    // Empty string that we will fill up
    var outputAsString = "";

    var queryLength = volpiano.length;

    for (var i = 0; i < queryLength; i++)
    {
        var symbol = volpiano.charAt(i);

        // Use this variable to check if the symbol is a dash and a
        // literal search is being performed.
        var isLiteralDash = onlyLiteralMatches && symbol === '-';

        if (!(symbol in volpianoMap) && !isLiteralDash)
            continue;

        // If this is not the start of the regex, allow optional
        // characters in between the new character and the prior ones
        // Add the dash symbol to the optional characters list if not
        // performing a literal search
        if (outputAsString)
            outputAsString += "[" + (onlyLiteralMatches ? '' : '-') + "1-7]*";

        outputAsString += isLiteralDash ? '-' : '[' + volpianoMap[symbol] + ']';
    }

    // Now we have a string representing a good regex, so we must
    // create an actual regex object
    var regex = null;
    if (outputAsString)
        regex = new RegExp(outputAsString, "g");

    // Cache the generated regex
    if (onlyLiteralMatches)
    {
        lastLiteralVolpianoQuery = volpiano;
        lastLiteralVolpianoRegex = regex;
    }
    else
    {
        lastVolpianoQuery = volpiano;
        lastVolpianoRegex = regex;
    }


    return regex;
}
