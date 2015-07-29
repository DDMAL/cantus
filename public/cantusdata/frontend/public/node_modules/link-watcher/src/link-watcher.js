/**
 * @license
 * This file incorporates code from [AngularJS](https://github.com/angular/angular.js)
 * v1.3.9
 *
 *   Copyright (c) 2010-2014 Google, Inc. http://angularjs.org
 *
 *   Permission is hereby granted, free of charge, to any person obtaining a copy
 *   of this software and associated documentation files (the "Software"), to deal
 *   in the Software without restriction, including without limitation the rights
 *   to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 *   copies of the Software, and to permit persons to whom the Software is
 *   furnished to do so, subject to the following conditions:
 *
 *   The above copyright notice and this permission notice shall be included in
 *   all copies or substantial portions of the Software.
 *
 *   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 *   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 *   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 *   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 *   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 *   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 *   THE SOFTWARE.
 */


(function (window, factory) {
  'use strict';
  /* global define, exports */

  // AMD
  if (typeof define === 'function' && define.amd) {
    define([], function() {
      return factory({}, window);
    });

  // CommonJS
  } else if (typeof exports !== 'undefined') {
    factory(exports, window);

  // global
  } else {
    /**
     * Restore the initial value of LinkWatcher and return this module.
     * Defined when used as a browser global.
     */
    var noConflict = function () {
      window.LinkWatcher = oldLinkWatcher;
      return LinkWatcher;
    };

    var oldLinkWatcher = window.LinkWatcher;
    var LinkWatcher = window.LinkWatcher = factory({noConflict: noConflict}, window);

  }
}(function () {return this;}(), function (exports, window) {
  'use strict';

  // Export functions
  exports.onLinkClicked     = onLinkClicked;
  exports.getNavigationInfo = getNavigationInfo;
  exports.urlResolve        = urlResolve;

  // Use a local reference to the location so that it can be easily mocked in tests
  exports._location = window.location;

  /**
   * Initialize an event listener which listens for clicks on anchor objects
   * with hrefs
   *
   * Options:
   *
   *  - `rootHref`: A URL to treat as the root for relative path detection. It
   *    is resolved against the current location and defaults to `window.location.href`.
   *
   * @param {HTMLElement|jQuery} rootElement The root element to watch
   * @param {Function=} callback Called with the event object and the path info
   * @param {Object=} options
   * @returns The bound listener function, so that it can be unbound
   */
  function onLinkClicked(rootElement, callback, options) {
    options = options || {};

    // Get values for options
    var rootHref = options.rootHref || exports._location.href;

    // Get the event listener callback
    var listener = getListener(rootHref, callback);

    // Bind the listener
    if (rootElement.jquery) {
      rootElement.on('click', listener);
    } else {
      rootElement.addEventListener('click', listener, false);
    }

    return listener;
  }

  // TODO: support xlink:href and SVG strings
  function getListener(rootHref, callback) {
    var rootInfo = urlResolve(rootHref);

    return function listen(event) {
      var navInfo = getNavigationInfo(event, rootInfo);

      if (navInfo)
        callback(event, navInfo);
    };
  }

  function getNavigationInfo(event, rootInfo) {
    var anchorElem = getAnchorElement(event.target, event.currentTarget);

    if (!anchorElem || typeof anchorElem.getAttribute('href') !== 'string')
      return null;

    var navInfo = urlResolve(anchorElem.href),
        anchorTarget = anchorElem.getAttribute('target'),
        clickTargetedHere = isLocalNavigationEvent(event);

    // Convenience variables
    var path = navInfo.pathname,
        rootPath = rootInfo.pathname;

    var isRelative = (navInfo.protocol === rootInfo.protocol &&
                      navInfo.host.toLowerCase() === rootInfo.host.toLowerCase() &&
                      rootPath === path.substr(0, rootPath.length) &&
                      (path.length === rootPath.length ||
                       path.charAt(rootPath.length) === '/' ||
                       rootPath.charAt(rootPath.length - 1) === '/'));

    var relativePath, isLocalNavigation;

    if (isRelative) {
      isLocalNavigation = clickTargetedHere && !anchorTarget;
      relativePath = getRelativePath(rootPath, navInfo.urlUtils);
    } else {
      isLocalNavigation = false;
      relativePath = null;
    }

    var isFragmentNavigation;

    if (!clickTargetedHere || (anchorTarget && anchorTarget !== '_self')) {
      isFragmentNavigation = false;
    } else {
      isFragmentNavigation = isLocationFragment(navInfo.urlUtils);
    }

    extend(navInfo, {
      anchor: anchorElem,
      isRelative: isRelative,
      relativePath: relativePath,
      isLocalNavigation: isLocalNavigation,
      isFragmentNavigation: isFragmentNavigation
    });

    return navInfo;
  }

  function isLocationFragment(urlUtils) {
    // FIXME: do I really need to do URLUtils separately for those IE compat caveats?

    if (!urlUtils.hash)
        return false;

    var location = exports._location;

    return (location.protocol === urlUtils.protocol &&
            location.host === urlUtils.host && // FIXME: case normalization?
            location.pathname === urlUtils.pathname &&
            location.search === urlUtils.search);
  }

  function isLocalNavigationEvent(event) {
    var defaultPrevented = event.isDefaultPrevented ? event.isDefaultPrevented() : event.defaultPrevented;

    return !(defaultPrevented ||
             // Control/command key pressed
             event.ctrlKey || event.metaKey ||
             // Clicked with center mouse button
             event.which === 2);
  }

  function getRelativePath(base, urlUtils) {
    var path = urlUtils.pathname;
    var relativePath = path.substring(base.length);

    // Make relative URLs for paths starting with a slash
    if (relativePath.charAt(0) === '/') {
      // We need these conditions to handle some corner cases around URLs with multiple slashes

      // When building a relative URL for /foo//bar from a base URL like /foo/, we get a naive
      // relative path of /bar and we need to turn it into .//bar
      if (base.charAt(base.length - 1) === '/') {
        // Prepend a doubled slash
        relativePath = '/' + relativePath;
      } else if (relativePath.charAt(1) !== '/') {
        // In the simpler case where the base URL is /foo and we have /foo/bar, we can just
        // remove the leading slash
        relativePath = relativePath.substring(1);
      }

      // Prepend a dot to the path if necessary
      if (relativePath.charAt(0) === '/') {
        relativePath = '.' + relativePath;
      }
    }

    return relativePath + urlUtils.search + urlUtils.hash;
  }

  /**
   * Find the anchor element an element is within, if any
   *
   * @param {DOMElement} elm
   * @param {DOMElement=} guard an optional guard element to stop the search at
   * @returns {?DOMElement} the anchor element, if one exists
   */
  function getAnchorElement(elm, guard) {
    while (elm && elm !== guard) {
      if (elm.nodeName.toUpperCase() === 'A')
        return elm;

      elm = elm.parentElement;
    }

    return null;
  }

  /**
   * @private
   * Extend the properties of an object in-place with the properties of another
   */
  function extend(obj, more) {
    for (var prop in more) {
      if (more.hasOwnProperty(prop)) {
        obj[prop] = more[prop];
      }
    }
  }

  // The following code is adapted from Angular's location service

  /**
   * documentMode is an IE-only property
   * http://msdn.microsoft.com/en-us/library/ie/cc196988(v=vs.85).aspx
   */
  var msie = document.documentMode;
  var urlParsingNode = document.createElement("a");


  /**
   *
   * Implementation Notes for non-IE browsers
   * ----------------------------------------
   * Assigning a URL to the href property of an anchor DOM node, even one attached to the DOM,
   * results both in the normalizing and parsing of the URL.  Normalizing means that a relative
   * URL will be resolved into an absolute URL in the context of the application document.
   * Parsing means that the anchor node's host, hostname, protocol, port, pathname and related
   * properties are all populated to reflect the normalized URL.  This approach has wide
   * compatibility - Safari 1+, Mozilla 1+, Opera 7+,e etc.  See
   * http://www.aptana.com/reference/html/api/HTMLAnchorElement.html
   *
   * Implementation Notes for IE
   * ---------------------------
   * IE >= 8 and <= 10 normalizes the URL when assigned to the anchor node similar to the other
   * browsers.  However, the parsed components will not be set if the URL assigned did not specify
   * them.  (e.g. if you assign a.href = "foo", then a.protocol, a.host, etc. will be empty.)  We
   * work around that by performing the parsing in a 2nd step by taking a previously normalized
   * URL (e.g. by assigning to a.href) and assigning it a.href again.  This correctly populates the
   * properties such as protocol, hostname, port, etc.
   *
   * IE7 does not normalize the URL when assigned to an anchor node.  (Apparently, it does, if one
   * uses the inner HTML approach to assign the URL as part of an HTML snippet -
   * http://stackoverflow.com/a/472729)  However, setting img[src] does normalize the URL.
   * Unfortunately, setting img[src] to something like "javascript:foo" on IE throws an exception.
   * Since the primary usage for normalizing URLs is to sanitize such URLs, we can't use that
   * method and IE < 8 is unsupported.
   *
   * References:
   *   http://developer.mozilla.org/en-US/docs/Web/API/HTMLAnchorElement
   *   http://www.aptana.com/reference/html/api/HTMLAnchorElement.html
   *   http://url.spec.whatwg.org/#urlutils
   *   https://github.com/angular/angular.js/pull/2902
   *   http://james.padolsey.com/javascript/parsing-urls-with-the-dom/
   *
   * @kind function
   * @param {string} url The URL to be parsed.
   * @description Normalizes and parses a URL.
   * @returns {object} Returns the normalized URL as a dictionary.
   *
   *   | member name   | Description    |
   *   |---------------|----------------|
   *   | href          | A normalized version of the provided URL if it was not an absolute URL |
   *   | protocol      | The protocol including the trailing colon                              |
   *   | host          | The host and port (if the port is non-default) of the normalizedUrl    |
   *   | search        | The search params, minus the question mark                             |
   *   | hash          | The hash string, minus the hash symbol
   *   | hostname      | The hostname
   *   | port          | The port, without ":"
   *   | pathname      | The pathname, beginning with "/"
   *
   */
  function urlResolve(url) {
    // jshint -W014
    var href = url;

    if (msie) {
      // Normalize before parse.  Refer Implementation Notes on why this is
      // done in two steps on IE.
      urlParsingNode.setAttribute("href", href);
      href = urlParsingNode.href;
    }

    urlParsingNode.setAttribute('href', href);

    // urlParsingNode provides the UrlUtils interface - http://url.spec.whatwg.org/#urlutils

    return {
      urlUtils: {
        href: urlParsingNode.href,
        protocol: urlParsingNode.protocol,
        host: urlParsingNode.host,
        search: urlParsingNode.search,

        // Some browsers don't seem to prepend the #
        // TODO(wabain): Get a better idea of the compat picture here
        hash: urlParsingNode.getAttribute('href').indexOf('#') >= 0 && urlParsingNode.hash.charAt(0) !== '#'
            ? '#' + urlParsingNode.hash
            : urlParsingNode.hash,

        hostname: urlParsingNode.hostname,
        port: urlParsingNode.port,
        pathname: urlParsingNode.pathname
      },
      href: urlParsingNode.href,
      protocol: urlParsingNode.protocol ? urlParsingNode.protocol.replace(/:$/, '') : '',
      host: urlParsingNode.host,
      search: urlParsingNode.search ? urlParsingNode.search.replace(/^\?/, '') : '',
      hash: urlParsingNode.hash ? urlParsingNode.hash.replace(/^#/, '') : '',
      hostname: urlParsingNode.hostname,
      port: urlParsingNode.port,
      pathname: (urlParsingNode.pathname.charAt(0) === '/')
        ? urlParsingNode.pathname
        : '/' + urlParsingNode.pathname
    };
  }

  return exports;
}));
