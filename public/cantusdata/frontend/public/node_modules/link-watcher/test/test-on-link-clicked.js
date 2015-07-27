describe('onClick()', function () {
  function callbackWith(elemHtml, targetSelector) {
    var listener = document.createElement('div'),
        guard = document.createElement('div'),
        expectedCb = jasmine.createSpy(),
        clickEvent;

    try {
      clickEvent = new MouseEvent('click', {
        view: window,
        bubbles: true,
        cancelable: true
      });
    } catch (e) {
      clickEvent = document.createEvent('Event');
      clickEvent.initEvent('click', true, true);
    }

    listener.innerHTML = elemHtml;
    guard.appendChild(listener);

    guard.addEventListener('click', function (e) {e.preventDefault();});
    LinkWatcher.onLinkClicked(listener, expectedCb, {rootHref: '/'});

    // PhantomJS only allows canceling the event if the guard is in the DOM
    document.body.appendChild(guard);

    var target = targetSelector ? listener.querySelector(targetSelector) : listener.firstChild;

    // This is synchronous for some reason
    target.dispatchEvent(clickEvent);

    document.body.removeChild(guard);

    return expectedCb;
  }

  it('should work with plain links', function () {
    expect(callbackWith('<a href="relative">link</a>')).toHaveBeenCalled();
  });

  it('should work with elements within links', function () {
    expect(callbackWith('<a href="relative"><em id="nested">link</em></a>', '#nested')).toHaveBeenCalled();
  });

  it('should not be triggered for non-anchor clicks', function () {
    expect(callbackWith('<button type="button">I am not a link</button>')).not.toHaveBeenCalled();
  });

  it('should not be triggered for anchors without href', function () {
    expect(callbackWith('<a>I am also not a link!</a>')).not.toHaveBeenCalled();
  });
});
