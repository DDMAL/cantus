import Marionette from 'marionette';

import { parseVolpianoSyllables } from 'utils/VolpianoDisplayHelper';

import template from './chant-record.template.html';


function dynamicallyLoadScript(url) {
	var script = document.createElement("script");  // create a script DOM node
	script.src = url;  // set its src to the provided URL
	document.head.appendChild(script);  // add it to the end of the head section of the page (could change 'head' to 'body' to add it to the end of the body section instead)
}

//Dynamically load all of the files needed to use MIDI.js player
dynamicallyLoadScript('https://cdn.jsdelivr.net/gh/jacobsanz97/test502/inc/shim/Base64.js')
dynamicallyLoadScript('https://cdn.jsdelivr.net/gh/jacobsanz97/test502/inc/shim/Base64binary.js')
dynamicallyLoadScript('https://cdn.jsdelivr.net/gh/jacobsanz97/test502/inc/shim/WebAudioAPI.js')

dynamicallyLoadScript('https://cdn.jsdelivr.net/gh/jacobsanz97/test502/js/midi/audioDetect.js')
dynamicallyLoadScript('https://cdn.jsdelivr.net/gh/jacobsanz97/test502/js/midi/gm.js')
dynamicallyLoadScript('https://cdn.jsdelivr.net/gh/jacobsanz97/test502/js/midi/loader.js')
dynamicallyLoadScript('https://cdn.jsdelivr.net/gh/jacobsanz97/test502/js/midi/plugin.audiotag.js')
dynamicallyLoadScript('https://cdn.jsdelivr.net/gh/jacobsanz97/test502/js/midi/plugin.webaudio.js')
dynamicallyLoadScript('https://cdn.jsdelivr.net/gh/jacobsanz97/test502/js/midi/plugin.webmidi.js')

dynamicallyLoadScript('https://cdn.jsdelivr.net/gh/jacobsanz97/test502/js/util/dom_request_xhr.js')
dynamicallyLoadScript('https://cdn.jsdelivr.net/gh/jacobsanz97/test502/js/util/dom_request_script.js')

//string length that can deal with null inputs
function strLength(s) {
	if (s == null) {
		return 0;
	}
	return [...s].reduce(a => a + 1, 0);
}

//string spit that can deal with null inputs
function CustomSplit(str, delimiter, removeEmptyItems) {
	if (!delimiter || delimiter.length === 0) return [str];
	if (!str || str.length === 0) return [];
	var result = [];
	var j = 0;
	var lastStart = 0;
	for (var i = 0; i <= str.length;) {
		if (i == str.length || str.substr(i, delimiter.length) == delimiter) {
			if (!removeEmptyItems || lastStart != i) {
				result[j++] = str.substr(lastStart, i - lastStart);
			}
			lastStart = i + delimiter.length;
			i += delimiter.length;
		} else i++;
	}
	return result;
}

///////////////////////////////////////////////////////////////////////////////////
//Plays the volpiano notes using MIDI.js
function volpiano2midi(input_arr, note_dur) {

	//construct dictionary with pitch values
	var pitch_dict = {};
	pitch_dict['9'] = 43;
	pitch_dict['a'] = 45;
	pitch_dict['b'] = 47;
	pitch_dict['c'] = 48;
	pitch_dict['d'] = 50;
	pitch_dict['e'] = 52;
	pitch_dict['f'] = 53;
	pitch_dict['g'] = 55;
	pitch_dict['h'] = 57;
	pitch_dict['j'] = 59;
	pitch_dict['k'] = 60;
	pitch_dict['l'] = 62;
	pitch_dict['m'] = 64;
	pitch_dict['n'] = 65;
	pitch_dict['o'] = 67;
	pitch_dict['p'] = 69;
	pitch_dict['q'] = 71;
	pitch_dict['r'] = 72;
	pitch_dict['s'] = 74;
	// add liquescent neumes to pitch dictionary
	pitch_dict['('] = 41; // liquescent low f
	pitch_dict[')'] = 43; // liquescent low g
	pitch_dict['A'] = 45;
	pitch_dict['B'] = 47;
	pitch_dict['C'] = 48;
	pitch_dict['D'] = 50;
	pitch_dict['E'] = 52;
	pitch_dict['F'] = 53;
	pitch_dict['G'] = 55;
	pitch_dict['H'] = 57;
	pitch_dict['J'] = 59;
	pitch_dict['K'] = 60;
	pitch_dict['L'] = 62;
	pitch_dict['M'] = 64;
	pitch_dict['N'] = 65;
	pitch_dict['O'] = 67;
	pitch_dict['P'] = 69;
	pitch_dict['Q'] = 71;
	pitch_dict['R'] = 72;
	pitch_dict['S'] = 74;

	// create array of volpiano characters representing barlines
	// for purposes of midi playback, these are treated as rests
	let rest_arr = ['3','4','5','6'];

	MIDI.loadPlugin({
		soundfontUrl: "https://cdn.jsdelivr.net/gh/jacobsanz97/test502/soundfont/",
		instrument: "vowels",
		onprogress: function (state, progress) {
			console.log(state, progress);
		},
		onsuccess: function () {
			//iterate through each syllable
			MIDI.setVolume(0, 127);
			var notes_played = 0;
			for (var i = 0; i < input_arr.length; i++) {
				var pitches = input_arr[i][0]
				var vowel = input_arr[i][1]
				MIDI.programChange(0, vowel);
				//var notes_played = 0;
				//iterate through each note pitch character, convert  lowercase, check if in dictionary, play the corresponding pitch
				for (var j = 0; j < pitches.length; j++) {
					if (pitches.charAt(j) in pitch_dict) {
						MIDI.noteOn(0, pitch_dict[pitches.charAt(j)], 127, notes_played * note_dur);
						MIDI.noteOff(0, pitch_dict[pitches.charAt(j)], notes_played * note_dur + note_dur);
						notes_played++;
					}
					if (rest_arr.includes(pitches.charAt(j))) {
						notes_played++;
					}
				}
			}
		}
	});
};

//////////////////////////////////////////////////////////////////////////
//Parses an array of Volpiano syllables, and returns a nested array in the form [["pitches", vowelNum],...].  Example: [["cdf", 0] , ["pa-", 4]]

function parse_volpiano(syllableArray) {
	var final_parse = []
	if (syllableArray.length < 1) {
		var empty_syll = ["", 0];
		return [empty_syll]
	}
	for (var i = 0; i < syllableArray.length; i++) {
		var current = syllableArray[i].textContent; //get textContext and split by the '--' token
		var split_curr = CustomSplit(current, "--", false);
		var pitches = split_curr[0];
		var vowel = get_vowel(split_curr[1]); //get vowel associated with lyrics.
		final_parse.push([pitches, vowel])
	}
	return final_parse;
}

////////////////////////////////////////////////////////////////////////
//Returns the number associated with first vowel in an input string (a=0,...,u=4). If no vowels, or empty string, return a=0.

function get_vowel(texti) {
	if (strLength(texti) < 1) {
		return 0;
	}
	for (var x = 0; x < strLength(texti); x++) {
		if (texti[x].toLowerCase() == "a") {
			return 0;
		}
		if (texti[x].toLowerCase() == "e") {
			return 1;
		}
		if (texti[x].toLowerCase() == "i") {
			return 2;
		}
		if (texti[x].toLowerCase() == "o") {
			return 3;
		}
		if (texti[x].toLowerCase() == "u") {
			return 4;
		}
	}
	return 0;
}

export default Marionette.ItemView.extend({
	template,

	initialize: function () {
		// Add a text underlay to the volpiano
		var volpiano = this.model.get('volpiano');
		var text = this.model.get('full_text_ms');
		var formattedVolpiano = parseVolpianoSyllables(text, volpiano);
		this.model.set('volpiano', formattedVolpiano);
		var cdb_uri = this.model.get('cdb_uri');
		this.model.set({ 'cdb_link_url': 'https://cantus.uwaterloo.ca/node/' + cdb_uri })
	},
	ui : {
		volpianoSyllables: ".volpiano-syllable"
	},
	events: {
		"click .btnPlay": "submit"
	},
	submit: function mainPlay() {
		var volArr = parse_volpiano(this.ui.volpianoSyllables);
		volpiano2midi(volArr, .6);
	}
});
