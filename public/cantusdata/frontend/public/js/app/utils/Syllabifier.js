// jscs:disable
/* eslint-disable */
//
// Author(s):
// Matthew Spencer, OSJ <mspencer@osjusa.org>
//
// Taken from https://github.com/frmatthew/exsurge/blob/master/src/Exsurge.Text.js
//
// Copyright (c) 2008-2016 Fr. Matthew Spencer, OSJ
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in
// all copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
// THE SOFTWARE.
//

var Syllabifier =
{

    // fixme: should we include 'diphthongs' with accented vowels, e.g., áe?
    // fixme: ui is only diphthong in the exceptional cases below (according to Wheelock's Latin)
    diphthongs: ["ae", "au", "oe"],

    // some words that are simply exceptions to standard syllabification rules!
    // ui combos pronounced as dipthongs
    /*wordExceptions: {
        "huius": new Word(["hui", "us"]),
        "cuius": new Word(["cui", "us"]),
        "huic": new Word(["huic"]),
        "cui": new Word(["cui"]),
        "hui": new Word(["hui"])
    },*/

    vowels: ['a', 'e', 'i', 'o', 'u',
        'á', 'é', 'í', 'ó', 'ú',
        'æ', 'œ',
        'ǽ',  // no accented œ in unicode?
        'y'], // y is treated as a vowel; not native to Latin but useful for words borrowed from Greek

    muteConsonantsAndF: ['b', 'c', 'd', 'g', 'p', 't', 'f'],

    liquidConsonants: ['l', 'r'],

    // c must be lowercase!
    isVowel: function(c) {
        for(var i = 0, end = this.vowels.length; i < end; i++)
            if (this.vowels[i] == c)
                return true;

        return false;
    },

    /**
     * f is not a mute consonant, but we lump it together for syllabification
     * since it is syntactically treated the same way
     *
     * @param {String} c The character to test; must be lowercase
     * @return {boolean} true if c is an f or a mute consonant
     */
    isMuteConsonantOrF: function(c) {
        for(var i = 0, end = this.muteConsonantsAndF.length; i < end; i++)
            if (this.muteConsonantsAndF[i] == c)
                return true;

        return false;
    },

    /**
     *
     * @param {String} c The character to test; must be lowercase
     * @return {boolean} true if c is a liquid consonant
     */
    isLiquidConsonant: function(c) {
        for(var i = 0, end = this.liquidConsonants.length; i < end; i++)
            if (this.liquidConsonants[i] == c)
                return true;

        return false;
    },

    /**
     *
     * @param {String} s The string to test; must be lowercase
     * @return {boolean} true if s is a diphthong
     */
    isDiphthong: function(s) {
        for(var i = 0, end = this.diphthongs.length; i < end; i++)
            if (this.diphthongs[i] == s)
                return true;

        return false;
    },

    /**
     * Rules for Latin syllabification (from Collins, "A Primer on Ecclesiastical Latin")
     *
     * Divisions occur when:
     *   1. After open vowels (those not followed by a consonant) (e.g., "pi-us" and "De-us")
     *   2. After vowels followed by a single consonant (e.g., "vi-ta" and "ho-ra")
     *   3. After the first consonant when two or more consonants follow a vowel
     *      (e.g., "mis-sa", "minis-ter", and "san-ctus").
     *
     * Exceptions:
     *   1. In compound words the consonants stay together (e.g., "de-scribo").
     *   2. A mute consonant (b, c, d, g, p, t) or f followed by a liquid consonant (l, r)
     *      go with the succeeding vowel: "la-crima", "pa-tris"
     *
     * In addition to these rules, Wheelock's Latin provides this sound exception:
     *   -  Also counted as single consonants are qu and the aspirates ch, ph,
     *      th, which should never be separated in syllabification:
     *      architectus, ar-chi-tec-tus; loquacem, lo-qua-cem.
     *
     * @param {String} The word to divide into syllables
     * @returns {Array} The array of syllables
     */
    syllabifyWord: function(word) {
        var syllables = [];
        var haveCompleteSyllable = false;
        var previousWasVowel = false;
        var workingString = word.toLowerCase();
        var startSyllable = 0;

        var c, lookahead, haveLookahead;

        // a helper function to create syllables
        var makeSyllable = function(length) {
            if (haveCompleteSyllable) {
                syllables.push(word.substr(startSyllable, length));
                startSyllable += length;
            }

            haveCompleteSyllable = false;
        }

        for (var i = 0, wordLength = workingString.length; i < wordLength; i++) {

            c = workingString[i];

            // get our lookahead in case we need them...
            lookahead = '*';
            haveLookahead = (i + 1) < wordLength;

            if (haveLookahead)
                lookahead = workingString[i + 1];

            var cIsVowel = this.isVowel(c);

            // i is a special case for a vowel. when i is at the beginning
            // of the word (Iesu) or i is between vowels (alleluia),
            // then the i is treated as a consonant (y)
            if (c === 'i') {
                if (i === 0 && haveLookahead && this.isVowel(lookahead))
                    cIsVowel = false;
                else if (previousWasVowel && haveLookahead && this.isVowel(lookahead)) {
                    cIsVowel = false;
                }
            }

            if (c === '-') {

                // a hyphen forces a syllable break, which effectively resets
                // the logic...

                haveCompleteSyllable = true;
                previousWasVowel = false;
                makeSyllable(i - startSyllable);
                startSyllable++;

            } else if (cIsVowel) {

                // once we get a vowel, we have a complete syllable
                haveCompleteSyllable = true;

                if (previousWasVowel && !this.isDiphthong(workingString[i - 1] + "" + c)) {
                    makeSyllable(i - startSyllable);
                    haveCompleteSyllable = true;
                }

                previousWasVowel = true;

            } else if (haveLookahead) {

                if ((c === 'q' && lookahead === 'u') ||
                    (lookahead === 'h' && (c === 'c' || c === 'p' || c === 't'))) {
                    // handle wheelock's exceptions for qu, ch, ph and th
                    makeSyllable(i - startSyllable);
                    i++; // skip over the 'h' or 'u'
                } else if (previousWasVowel && this.isVowel(lookahead)) {
                    // handle division rule 2
                    makeSyllable(i - startSyllable);
                } else if (this.isMuteConsonantOrF(c) && this.isLiquidConsonant(lookahead)) {
                    // handle exception 2
                    makeSyllable(i - startSyllable);
                } else if (haveCompleteSyllable) {
                    // handle division rule 3
                    makeSyllable(i + 1 - startSyllable);
                }

                previousWasVowel = false;
            }
        }

        // if we have a complete syllable, we can add it as a new one. Otherwise
        // we tack the remaining characters onto the last syllable.
        if (haveCompleteSyllable)
            syllables.push(word.substr(startSyllable));
        else if (startSyllable > 0)
            syllables[syllables.length - 1] += word.substr(startSyllable);

        return syllables;
    }
};

export default Syllabifier;
