/*
	----------------------------------------------------------
	MIDI.Plugin : 0.3.4 : 2015-03-26
	----------------------------------------------------------
	https://github.com/mudcube/MIDI.js
	----------------------------------------------------------
	Inspired by javax.sound.midi (albeit a super simple version): 
		http://docs.oracle.com/javase/6/docs/api/javax/sound/midi/package-summary.html
	----------------------------------------------------------
	Technologies
	----------------------------------------------------------
		Web MIDI API - no native support yet (jazzplugin)
		Web Audio API - firefox 25+, chrome 10+, safari 6+, opera 15+
		HTML5 Audio Tag - ie 9+, firefox 3.5+, chrome 4+, safari 4+, opera 9.5+, ios 4+, android 2.3+
	----------------------------------------------------------
*/


function loader(root) { 'use strict';

	root.DEBUG = true;
	root.soundfontUrl = './soundfont/';

	/*
		MIDI.loadPlugin({
			onsuccess: function() { },
			onprogress: function(state, percent) { },
			targetFormat: 'mp3', // optionally can force to use MP3 (for instance on mobile networks)
			instrument: 'acoustic_grand_piano', // or 1 (default)
			instruments: [ 'acoustic_grand_piano', 'acoustic_guitar_nylon' ] // or multiple instruments
		});
	*/

	root.loadPlugin = function(opts) {
		if (typeof opts === 'function') {
			opts = {onsuccess: opts};
		}

		root.soundfontUrl = opts.soundfontUrl || root.soundfontUrl;

		var supports = root.supports;
		var hash = window.location.hash;
		var api = '';
		if (window.AudioContext || window.webkitAudioContext) { 
			api = 'webaudio';
		}
		if (connect[api]) {
			/// use audio/ogg when supported
			if (opts.targetFormat) {
				var audioFormat = opts.targetFormat;
			} else { // use best quality
				var audioFormat = supports['audio/ogg'] ? 'ogg' : 'mp3';
			}
			/// load the specified plugin
			root.__api = api;
			root.__audioFormat = audioFormat;
			root.supports = supports;
			root.loadResource(opts);
		}
		};

	root.loadResource = function(opts) {
		var instruments = opts.instruments || opts.instrument || 'acoustic_grand_piano';
		if (typeof instruments !== 'object') {
			if (instruments || instruments === 0) {
				instruments = [instruments];
			} else {
				instruments = [];
			}
		}
		opts.format = root.__audioFormat;
		opts.instruments = instruments;
		connect[root.__api](opts);
	};

	var connect = {
		webaudio: function(opts) {
			requestQueue(opts, 'WebAudio');
		}
	};

	var requestQueue = function(opts, context) {
		var audioFormat = opts.format;
		var instruments = opts.instruments;
		var onprogress = opts.onprogress;
		var onerror = opts.onerror;
		///
		var length = instruments.length;
		var pending = length;
		var waitForEnd = function() {
			if (!--pending) {
				onprogress && onprogress('load', 1.0);
				root.Soundfont = midiSoundfont;
				root[context].connect(opts);
			}
		};
		///
		for (var i = 0; i < length; i ++) {
			var instrumentId = instruments[i];
			if (root.Soundfont[instrumentId]) { // already loaded
				waitForEnd();
			} else { // needs to be requested
				sendRequest(instruments[i], audioFormat, function(evt, progress) {
					var fileProgress = progress / length;
					var queueProgress = (length - pending) / length;
					onprogress && onprogress('load', fileProgress + queueProgress, instrumentId);
				}, function() {
					waitForEnd();
				}, onerror);
			}
		};
	};

	var sendRequest = function(instrumentId, audioFormat, onprogress, onsuccess, onerror) {
		var soundfontPath = root.soundfontUrl + instrumentId + '-' + audioFormat + '.js';
		root.util.request({
			url: soundfontPath,
			format: 'text',
			onerror: onerror,
			onprogress: onprogress,
			onsuccess: function(event, responseText) {
				var script = document.createElement('script');
				script.language = 'javascript';
				script.type = 'text/javascript';
				script.text = responseText;
				document.body.appendChild(script);
				onsuccess();
			}
		});
	};

	root.setDefaultPlugin = function(midi) {
		for (var key in midi) {
			root[key] = midi[key];
		}
	};

}

export { loader };
