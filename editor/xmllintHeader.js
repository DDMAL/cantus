this.addEventListener('message', function(event){
  Module = event.data;
  Module['print'] = function(x) {
      postMessage(x);
    };
  Module['printErr'] = function(x) {
    postMessage(x);
  };
  validateXML(event.data);
}, false);
function validateXML(Module) {
  Module['preRun'] = function() {
    FS.createDataFile('/', Module['title'], Module['intArrayFromString'](Module['xml']), true, true);
    FS.createDataFile('/', 'test.rng', Module['intArrayFromString'](Module['schema']), true, true);
};
Module.arguments = ['--noout', '--relaxng', 'test.rng', Module['title']];