
import { audioDetect } from './audioDetect.js';
import { loader } from './loader.js';
import { gm } from './gm.js';
import { webAudio } from './plugin.webaudio.js';
import { requestXHR } from './dom_request_xhr.js';

if (typeof MIDI === 'undefined') {
	var MIDI = {};
}

audioDetect(MIDI);

MIDI.Soundfont = MIDI.Soundfont || {};
MIDI.Player = MIDI.Player || {};

loader(MIDI);
gm(MIDI);
webAudio(MIDI);
requestXHR(MIDI);

export { MIDI }


