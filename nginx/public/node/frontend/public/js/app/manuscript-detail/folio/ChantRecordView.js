import Backbone from 'backbone';
import Marionette from 'marionette';

import { parseVolpianoSyllables } from 'utils/VolpianoDisplayHelper';

import template from './chant-record.template.html';

import { MIDI }  from 'utils/midi-player/midiPlayer.js';

var manuscriptChannel = Backbone.Radio.channel('manuscript');

MIDI.audioDetect(function (supports){
	MIDI.supports = supports;
	var soundfontUrl = "/static/soundfonts/";
	var instrument = "vowels";
	MIDI.loadPlugin({
		soundfontUrl: soundfontUrl,
		instrument: instrument,
		onprogress: function (state, progress) {
			console.log(state, progress);
		}, onsuccess: function(){
			MIDI.setVolume(0, 127);
		}
	});
	MIDI.instrument = instrument;
});

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

function audioStopReset(MIDI){
	var audioCxt = MIDI.getContext();
	audioCxt.close();
	if (MIDI.sources != undefined){
	for (var i = 0; i < MIDI.sources.length; i++){
		MIDI.sources[i].disconnect();
	}
	}
	var newAudioCxt = new (window.AudioContext || window.webkitAudioContext)();
	MIDI.setContext(newAudioCxt);
	$('.btnPlay').html("Play Audio");
	$('.btnPlay').attr("disabled", false);
}

// A basic function to handle flats.
// Flats are applied to B's that immediately follow a flat
// along with any B's in the same text syllable, unless
// a natural cancels it.
function handleFlats (inputStr){
	var flatReplDict = {};
	flatReplDict["y"] = ["b","t"]; // where flat is encoded as "y", change B3 to our make-shift encoding of Bb3
	flatReplDict["i"] = ["j","u"]; // where flat is encoded as "i", change B4 to our make-shift encoding of Bb4
	flatReplDict["z"] = ["q","v"]; // where flat is encoded as "z", change B5 to our make-shift encoding of Bb5
	function applyFlat(inputStr, flatStr){
		// find location of flat in syllable
		var flatIndex = inputStr.indexOf(flatStr);
		// find subsequent location of natural in syllable, if any
		var natIndex = inputStr.indexOf(flatStr.toUpperCase(), flatIndex);
		if (natIndex == -1){natIndex = inputStr.length}
		var preString = inputStr.slice(0, flatIndex);
		var toFlattenString = inputStr.slice(flatIndex, natIndex);
		var postString = inputStr.slice(natIndex, inputStr.length);
		var flattedString = toFlattenString.toLowerCase().replaceAll(flatReplDict[flatStr][0], flatReplDict[flatStr][1]);
		return preString + flattedString + postString;
	}
	if (inputStr.includes("y")) {
		var outputStr = applyFlat(inputStr, "y");
	} else if (inputStr.includes("i")){
		var outputStr = applyFlat(inputStr, "i");
	} else if (inputStr.includes("z")){
		var outputStr = applyFlat(inputStr, "z");
	}
	return outputStr
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
	pitch_dict['('] = 41; // liquescent low f
	pitch_dict[')'] = 43; // liquescent low g
	pitch_dict['t'] = 46; // make-shift Bb3
	pitch_dict['u'] = 58; // make-shift Bb4
	pitch_dict['v'] = 50; // make-shift Bb5

	// create array of volpiano characters representing barlines
	// for purposes of midi playback, these are treated as rests
	let rest_arr = ['3','4','5','6'];


	//iterate through each syllable
	
	var notes_played = 0;
	var sources = [];
	for (var i = 0; i < input_arr.length; i++) {
		var pitches = input_arr[i][0];
		if (pitches.includes("y") || pitches.includes("i") || pitches.includes("z")){
			pitches = handleFlats(pitches);
		}
		var vowel = input_arr[i][1];
		if (MIDI.instrument == "vowels"){
			MIDI.programChange(0, vowel);
		}
		//var notes_played = 0;
		//iterate through each note pitch character, check if in dictionary, play the corresponding pitch
		// characters in volpiano are converted to lowercase to play liquescent neumes, which 
		// are indicated in volpiano by uppercase characters
		for (var j = 0; j < pitches.length; j++) {
			if (pitches.charAt(j).toLowerCase() in pitch_dict) {
				var source = MIDI.NoteOn(0, pitch_dict[pitches.charAt(j).toLowerCase()], 127, notes_played * note_dur, notes_played * note_dur + note_dur);
				sources.push(source);
				notes_played++;
			}
			if (rest_arr.includes(pitches.charAt(j))) {
				notes_played++;
			}
		}
	}
	MIDI.sources = sources;
	// Clear sources and reset button after last note
	MIDI.sources[MIDI.sources.length - 1].addEventListener("ended", function(event){
		audioStopReset(MIDI);
	})
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
//Returns the number associated with the appropriate vowel sound in an input string (a=0,...,u=4). If no vowels, or empty string, return a=0.

function get_vowel(syllStr) {
	if (strLength(syllStr) < 1) {
		return 0;
	}
	for (var x = 0; x < strLength(syllStr); x++) {
		if (syllStr[x].toLowerCase() == "a") {
			// Handle "ae" diphthong
			if (x < strLength(syllStr) - 1){
				if (syllStr[x+1].toLowerCase() == "e"){
					return 1;
			} 
		}
			return 0;
		}
		if (syllStr[x].toLowerCase() == "e") {
			return 1;
		}
		if (syllStr[x].toLowerCase() == "i") {
			return 2;
		}
		if (syllStr[x].toLowerCase() == "o") {
			// Handle "oe" diphthong
			if (x < strLength(syllStr) - 1) {
				if (syllStr[x+1].toLowerCase() == "e"){
				return 1;
				}
			}
			return 3;
		}
		if (syllStr[x].toLowerCase() == "u") {
		// Handle "Qu" combination
			if (x > 0){
				if (syllStr[x-1].toLowerCase() == "q"){
					continue;
				}
			}
			return 4;
		}
		// Have "y" vowels sung the same as "i"
		if (syllStr[x].toLowerCase() == "y") {
			return 2;
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
		this.model.set({ 'cdb_link_url': 'https://cantusdatabase.org/chant/' + cdb_uri });
		manuscriptChannel.on('chantAccordion:click',this.stopChantAudio, this);
	},
	ui : {
		volpianoSyllables: ".volpiano-syllable",
		btnPlay: ".btnPlay",
		btnStop: ".btnStop"
	},
	events: {
		"click .btnPlay": "submit",
		"click .btnStop": "stop"
	},
	submit: function mainPlay() {
		var volArr = parse_volpiano(this.ui.volpianoSyllables);
		this.ui.btnPlay.html("Playing...");
		this.ui.btnPlay.attr("disabled", true);
		volpiano2midi(volArr, .6);
	},
	stop: function(){
		audioStopReset(MIDI);
	},
	stopChantAudio: function(){
		if (MIDI.getContext().state === "running"){
			audioStopReset(MIDI);
		}
	},
	onDestroy: function(){
		manuscriptChannel.off('chantAccordion:click',this.stopChantAudio, this);
	}
});
