/* eslint-env commonjs */

// Initialization
import 'init/GlobalSetup';
import 'jasmine-jquery';
import 'jasmine-ajax';

const INIT_REGEX = /\.\/init\//;

// Load all source files excluding entry points to ensure they're counted for
// code coverage, and load all spec files to run them
const testAndSrcContext = require.context('../app/', true, /\.js$/);

testAndSrcContext.keys().forEach(function (key)
{
    if (!INIT_REGEX.test(key))
        testAndSrcContext(key);
});
