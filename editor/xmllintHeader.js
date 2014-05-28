this.addEventListener('message', function(event){
  postMessage('received');
  Module = event.data;
  Module['print'] = function(x) {
      postMessage(x);
    };
  }
  Module['printErr'] = function(x) {
    postMessage(x);
  };
  validateXML(event.data);
}, false);
function validateXML(Module) {
  Module['preRun'] = function() {
    FS.createDataFile('/', 'test.xml', Module['intArrayFromString'](Module['xml']), true, true);
    FS.createDataFile('/', 'test.rng', Module['intArrayFromString'](Module['schema']), true, true);
    postMessage("here");
};
Module.arguments = ['--noout', '--relaxng', 'test.rng', 'test.xml'];