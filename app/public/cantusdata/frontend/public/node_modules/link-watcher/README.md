This is a utility library which simplifies handling click events for multiple links. It aims to provide simple and correct helpers which work with the DOM and with [generic URL syntax](http://tools.ietf.org/html/rfc3986).

# Usage

Using CommonJS:

```js
var LinkWatcher = require('link-watcher');

LinkWatcher.onLinkClicked(/* ... */);
```

As a browser global:

```html
<script src="link-watcher.min.js"></script>

<script>
  LinkWatcher.onLinkClicked(/* ... */);
</script>
```

# API

    onLinkClicked(rootElement, callback, options)
    getNavigationInfo(event, rootInfo)
    urlResolve(url)

# TODO

 - documentation
 - work out whether IRIs are supported
 - work with SVG links
 - work with form submission?
