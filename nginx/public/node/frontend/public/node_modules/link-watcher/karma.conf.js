module.exports = function (config) {
  config.set({
    frameworks: ['jasmine'],
    browsers: ['PhantomJS'],
    files: ['src/link-watcher.js', 'test/*.js']
  });
};
