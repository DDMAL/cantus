describe('getNavigationInfo()', function () {
  function pathInfoFrom(root, relative, event) {
    var anchor = document.createElement('a');
    anchor.href = relative;

    // Since we just get the target and then check booleans for the event, a plain object is good enough
    if (!event)
      event = {};

    event.target = anchor;

    return LinkWatcher.getNavigationInfo(event, LinkWatcher.urlResolve(root));
  }

  describe('relative path detection', function () {
    function isRelative(base, url) {
      var info = pathInfoFrom(base, url);

      expect(info.isRelative === (info.relativePath !== null)).toBe(true, 'sanity check (isRelative and relativePath)');

      return info.isRelative;
    }

    it('should differentiate by scheme', function () {
      expect(isRelative('http://example.org', 'https://example.org/foo')).toBe(false);
    });

    it('should differentiate by host', function () {
      expect(isRelative('http://example.org', 'http://google.com/foo')).toBe(false);
    });

    it('should differentiate by port', function () {
      expect(isRelative('http://example.org', 'http://example.org:8080/foo')).toBe(false);
    });

    // ...
    it('should differentiate by path', function () {
      expect(isRelative('http://example.org/bar', 'http://example.org/foo/bar')).toBe(false);
      expect(isRelative('http://example.org/fo', 'http://example.org/foo')).toBe(false);
    });

    // Test the normalization concerns from RFC 3986 and RFC 7230

    // RFC 3986, sec. 6.2.2.1, Case normalization
    it('should use case-normalized protocols', function () {
      expect(isRelative('HTTP://example.org', 'http://example.org/foo')).toBe(true);
    });

    it('should use case-normalized hosts', function () {
      expect(isRelative('http://EXAMPLE.ORG', 'http://example.org/foo')).toBe(true);
    });

    it('should use case-normalized percent encoding', function () {
      expect(isRelative('http://example.org/%3A', 'http://example.org/%3a/foo')).toBe(true);
    });

    // RFC 3986, sec. 6.2.2.2, Percent encoding
    it('should decode unreserved percent-encoded characters', function () {
      expect(isRelative('http://example.org/%41', 'http://example.org/A/foo')).toBe(true);
    });

    // RFC 3986, sec. 6.2.2.3, Path segment normalization
    it('should have normalized path segments', function () {
      expect(isRelative('http://example.org/./%41/bar/..', 'http://example.org/A/foo')).toBe(true);
    });

    // RFC 3986, sec. 6.2.3, Scheme normalization
    // RFC 7230, sec. 2.7.3, http and https URI Normalization and Comparison
    it('should normalize an empty port to the scheme default', function () {
      expect(isRelative('http://example.org:/', 'http://example.org/foo')).toBe(true);
      expect(isRelative('https://example.org:/', 'https://example.org/foo')).toBe(true);
    });

    it('should treat the default port and no port as equivalent', function () {
      expect(isRelative('http://example.org:80/', 'http://example.org/foo')).toBe(true);
      expect(isRelative('https://example.org:443/', 'https://example.org/foo')).toBe(true);
    });

    it('should treat no path as an empty path', function () {
      expect(isRelative('http://example.org/', 'http://example.org')).toBe(true);
    });
  });

  describe('relativized path generation', function () {
    function expectRelative(root, full, rel) {
      expect(pathInfoFrom(root, full).relativePath).toBe(rel);

      var rebuilt = root + (root.charAt(root.length - 1) === '/' ? '' : '/') + rel;

      expect(pathInfoFrom(root, rebuilt).relativePath).toBe(rel, 'idempotency');
    }

    it('should generate paths relative to the root URL', function () {
      expectRelative('http://example.org/foo/', 'http://example.org/foo/bar', 'bar');
    });

    it('should strip a leading slash', function () {
      expectRelative('http://example.org/foo', 'http://example.org/foo/bar', 'bar');
    });

    it('should maintain query strings and hash fragments', function () {
      expectRelative('http://example.org/', 'http://example.org/?foo=bar#baz', '?foo=bar#baz');
    });

    it('should use a `.` segment when the relative path starts with an empty component', function () {
      expectRelative('http://example.org/foo/', 'http://example.org/foo//bar', './/bar');
      expectRelative('http://example.org/foo', 'http://example.org/foo//bar', './/bar');
      expectRelative('http://example.org/foo//', 'http://example.org/foo///bar', './/bar');
    });
  });

  describe('local navigation detection', function () {
    it('should treat clicks with the control and meta keys as non-local', function () {
      var info;

      info = pathInfoFrom('http://example.org/', 'http://example.org/foo', {ctrlKey: true});
      expect(info).toEqual(jasmine.objectContaining({isRelative: true, isLocalNavigation: false}), 'ctrl');

      info = pathInfoFrom('http://example.org/', 'http://example.org/foo', {metaKey: true});
      expect(info).toEqual(jasmine.objectContaining({isRelative: true, isLocalNavigation: false}), 'meta');
    });

    it('should treat clicks with the center mouse button as non-local', function () {
      var info = pathInfoFrom('http://example.org/', 'http://example.org/foo', {which: 2});
      expect(info).toEqual(jasmine.objectContaining({isRelative: true, isLocalNavigation: false}));
    });

    it('should treat clicks on anchors with targets as non-local', function () {
      var anchor = document.createElement('a');
      anchor.setAttribute('target', '_self');
      anchor.href = 'http://example.org/foo';

      var info = LinkWatcher.getNavigationInfo({target: anchor}, LinkWatcher.urlResolve('http://example.org/'));

      expect(info).toEqual(jasmine.objectContaining({isRelative: true, isLocalNavigation: false}));
    });
  });

  describe('fragment navigation', function () {
    function setLocation(urlUtilsValue) {
      LinkWatcher._location = {
        protocol: urlUtilsValue.protocol || 'http:',
        host: urlUtilsValue.host,
        port: urlUtilsValue.port || '',
        pathname: urlUtilsValue.pathname,
        search: urlUtilsValue.search || '',
        hash: urlUtilsValue.hash || ''
      };
    }

    function navigationFrom(currentUrlComponents, linkUrl, event) {
      setLocation(currentUrlComponents);

      return pathInfoFrom('', linkUrl, event);
    }

    afterEach(function () {
      LinkWatcher._location = window.location;
    });

    it('applies if the link is to the current location and there is a fragment in the href', function () {
      expect(navigationFrom({
        host: 'example.org',
        pathname: '/foo/'
      }, 'http://example.org/foo/#').isFragmentNavigation).toBe(true);

      expect(navigationFrom({
        host: 'example.org',
        pathname: '/foo/',
        hash: '#'
      }, 'http://example.org/foo/').isFragmentNavigation).toBe(false);

      expect(navigationFrom({
        host: 'example.org',
        pathname: '/foo/',
        hash: '#bar'
      }, 'http://example.org/foo/#baz').isFragmentNavigation).toBe(true);

      expect(navigationFrom({
        host: 'example.org',
        pathname: '/foo/',
        hash: '#bar'
      }, 'http://example.org/qux/../foo/#baz').isFragmentNavigation).toBe(true);
    });

    it('does not apply if the click event is not local', function () {
      expect(navigationFrom({
        host: 'example.org',
        pathname: '/foo/'
      }, 'http://example.org/foo/#', {ctrlKey: true}).isFragmentNavigation).toBe(false);
    });
  });
});
