"use strict";

function _typeof(obj) { "@babel/helpers - typeof"; return _typeof = "function" == typeof Symbol && "symbol" == typeof Symbol.iterator ? function (obj) { return typeof obj; } : function (obj) { return obj && "function" == typeof Symbol && obj.constructor === Symbol && obj !== Symbol.prototype ? "symbol" : typeof obj; }, _typeof(obj); }
/*! iFrame Resizer (iframeSizer.contentWindow.min.js) - v4.3.5 - 2023-03-08
 *  Desc: Include this file in any page being loaded into an iframe
 *        to force the iframe to resize to the content size.
 *  Requires: iframeResizer.min.js on host page.
 *  Copyright: (c) 2023 David J. Bradshaw - dave@bradshaw.net
 *  License: MIT
 */
!function (a) {
  if ("undefined" != typeof window) {
    var r = !0,
      P = "",
      u = 0,
      c = "",
      s = null,
      D = "",
      d = !1,
      j = {
        resize: 1,
        click: 1
      },
      l = 128,
      q = !0,
      f = 1,
      n = "bodyOffset",
      m = n,
      H = !0,
      W = "",
      h = {},
      g = 32,
      B = null,
      p = !1,
      v = !1,
      y = "[iFrameSizer]",
      J = y.length,
      w = "",
      U = {
        max: 1,
        min: 1,
        bodyScroll: 1,
        documentElementScroll: 1
      },
      b = "child",
      V = !0,
      X = window.parent,
      T = "*",
      E = 0,
      i = !1,
      Y = null,
      O = 16,
      S = 1,
      K = "scroll",
      M = K,
      Q = window,
      G = function G() {
        x("onMessage function not defined");
      },
      Z = function Z() {},
      $ = function $() {},
      _ = {
        height: function height() {
          return x("Custom height calculation function not defined"), document.documentElement.offsetHeight;
        },
        width: function width() {
          return x("Custom width calculation function not defined"), document.body.scrollWidth;
        }
      },
      ee = {},
      te = !1;
    try {
      var ne = Object.create({}, {
        passive: {
          get: function get() {
            te = !0;
          }
        }
      });
      window.addEventListener("test", ae, ne), window.removeEventListener("test", ae, ne);
    } catch (e) {}
    var oe,
      o,
      I,
      ie,
      N,
      A,
      C = {
        bodyOffset: function bodyOffset() {
          return document.body.offsetHeight + ye("marginTop") + ye("marginBottom");
        },
        offset: function offset() {
          return C.bodyOffset();
        },
        bodyScroll: function bodyScroll() {
          return document.body.scrollHeight;
        },
        custom: function custom() {
          return _.height();
        },
        documentElementOffset: function documentElementOffset() {
          return document.documentElement.offsetHeight;
        },
        documentElementScroll: function documentElementScroll() {
          return document.documentElement.scrollHeight;
        },
        max: function max() {
          return Math.max.apply(null, e(C));
        },
        min: function min() {
          return Math.min.apply(null, e(C));
        },
        grow: function grow() {
          return C.max();
        },
        lowestElement: function lowestElement() {
          return Math.max(C.bodyOffset() || C.documentElementOffset(), we("bottom", Te()));
        },
        taggedElement: function taggedElement() {
          return be("bottom", "data-iframe-height");
        }
      },
      z = {
        bodyScroll: function bodyScroll() {
          return document.body.scrollWidth;
        },
        bodyOffset: function bodyOffset() {
          return document.body.offsetWidth;
        },
        custom: function custom() {
          return _.width();
        },
        documentElementScroll: function documentElementScroll() {
          return document.documentElement.scrollWidth;
        },
        documentElementOffset: function documentElementOffset() {
          return document.documentElement.offsetWidth;
        },
        scroll: function scroll() {
          return Math.max(z.bodyScroll(), z.documentElementScroll());
        },
        max: function max() {
          return Math.max.apply(null, e(z));
        },
        min: function min() {
          return Math.min.apply(null, e(z));
        },
        rightMostElement: function rightMostElement() {
          return we("right", Te());
        },
        taggedElement: function taggedElement() {
          return be("right", "data-iframe-width");
        }
      },
      re = (oe = Ee, N = null, A = 0, function () {
        var e = Date.now(),
          t = O - (e - (A = A || e));
        return o = this, I = arguments, t <= 0 || O < t ? (N && (clearTimeout(N), N = null), A = e, ie = oe.apply(o, I), N || (o = I = null)) : N = N || setTimeout(Oe, t), ie;
      });
    k(window, "message", function (t) {
      var n = {
        init: function init() {
          W = t.data, X = t.source, se(), q = !1, setTimeout(function () {
            H = !1;
          }, l);
        },
        reset: function reset() {
          H ? R("Page reset ignored by init") : (R("Page size reset by host page"), Me("resetPage"));
        },
        resize: function resize() {
          L("resizeParent", "Parent window requested size check");
        },
        moveToAnchor: function moveToAnchor() {
          h.findTarget(i());
        },
        inPageLink: function inPageLink() {
          this.moveToAnchor();
        },
        pageInfo: function pageInfo() {
          var e = i();
          R("PageInfoFromParent called from parent: " + e), $(JSON.parse(e)), R(" --");
        },
        message: function message() {
          var e = i();
          R("onMessage called from parent: " + e), G(JSON.parse(e)), R(" --");
        }
      };
      function o() {
        return t.data.split("]")[1].split(":")[0];
      }
      function i() {
        return t.data.slice(t.data.indexOf(":") + 1);
      }
      function r() {
        return t.data.split(":")[2] in {
          "true": 1,
          "false": 1
        };
      }
      function e() {
        var e = o();
        e in n ? n[e]() : ("undefined" == typeof module || !module.exports) && "iFrameResize" in window || window.jQuery !== a && "iFrameResize" in window.jQuery.prototype || r() || x("Unexpected message (" + t.data + ")");
      }
      y === ("" + t.data).slice(0, J) && (!1 === q ? e() : r() ? n.init() : R('Ignored message of type "' + o() + '". Received before initialization.'));
    }), k(window, "readystatechange", Ne), Ne();
  }
  function ae() {}
  function k(e, t, n, o) {
    e.addEventListener(t, n, !!te && (o || {}));
  }
  function ue(e) {
    return e.charAt(0).toUpperCase() + e.slice(1);
  }
  function ce(e) {
    return y + "[" + w + "] " + e;
  }
  function R(e) {
    p && "object" == _typeof(window.console) && console.log(ce(e));
  }
  function x(e) {
    "object" == _typeof(window.console) && console.warn(ce(e));
  }
  function se() {
    function e(e) {
      return "true" === e;
    }
    function t(e, t) {
      return "function" == typeof e && (R("Setup custom " + t + "CalcMethod"), _[t] = e, e = "custom"), e;
    }
    {
      var n;
      n = W.slice(J).split(":"), w = n[0], u = a === n[1] ? u : Number(n[1]), d = a === n[2] ? d : e(n[2]), p = a === n[3] ? p : e(n[3]), g = a === n[4] ? g : Number(n[4]), r = a === n[6] ? r : e(n[6]), c = n[7], m = a === n[8] ? m : n[8], P = n[9], D = n[10], E = a === n[11] ? E : Number(n[11]), h.enable = a !== n[12] && e(n[12]), b = a === n[13] ? b : n[13], M = a === n[14] ? M : n[14], v = a === n[15] ? v : e(n[15]), R("Initialising iFrame (" + window.location.href + ")"), "iFrameResizer" in window && Object === window.iFrameResizer.constructor && (n = window.iFrameResizer, R("Reading data from page: " + JSON.stringify(n)), Object.keys(n).forEach(de, n), G = "onMessage" in n ? n.onMessage : G, Z = "onReady" in n ? n.onReady : Z, T = "targetOrigin" in n ? n.targetOrigin : T, m = "heightCalculationMethod" in n ? n.heightCalculationMethod : m, M = "widthCalculationMethod" in n ? n.widthCalculationMethod : M, m = t(m, "height"), M = t(M, "width"));
    }
    function o(e) {
      F(0, 0, e.type, e.screenY + ":" + e.screenX);
    }
    function i(e, t) {
      R("Add event listener: " + t), k(window.document, e, o);
    }
    R("TargetOrigin for parent set to: " + T), le("margin", function (e, t) {
      -1 !== t.indexOf("-") && (x("Negative CSS value ignored for " + e), t = "");
      return t;
    }("margin", c = a === c ? u + "px" : c)), le("background", P), le("padding", D), (n = document.createElement("div")).style.clear = "both", n.style.display = "block", n.style.height = "0", document.body.appendChild(n), he(), ge(), document.documentElement.style.height = "", document.body.style.height = "", R('HTML & body height set to "auto"'), R("Enable public methods"), Q.parentIFrame = {
      autoResize: function autoResize(e) {
        return !0 === e && !1 === r ? (r = !0, pe()) : !1 === e && !0 === r && (r = !1, fe("remove"), null !== s && s.disconnect(), clearInterval(B)), F(0, 0, "autoResize", JSON.stringify(r)), r;
      },
      close: function close() {
        F(0, 0, "close");
      },
      getId: function getId() {
        return w;
      },
      getPageInfo: function getPageInfo(e) {
        "function" == typeof e ? ($ = e, F(0, 0, "pageInfo")) : ($ = function $() {}, F(0, 0, "pageInfoStop"));
      },
      moveToAnchor: function moveToAnchor(e) {
        h.findTarget(e);
      },
      reset: function reset() {
        Ie("parentIFrame.reset");
      },
      scrollTo: function scrollTo(e, t) {
        F(t, e, "scrollTo");
      },
      scrollToOffset: function scrollToOffset(e, t) {
        F(t, e, "scrollToOffset");
      },
      sendMessage: function sendMessage(e, t) {
        F(0, 0, "message", JSON.stringify(e), t);
      },
      setHeightCalculationMethod: function setHeightCalculationMethod(e) {
        m = e, he();
      },
      setWidthCalculationMethod: function setWidthCalculationMethod(e) {
        M = e, ge();
      },
      setTargetOrigin: function setTargetOrigin(e) {
        R("Set targetOrigin: " + e), T = e;
      },
      size: function size(e, t) {
        L("size", "parentIFrame.size(" + ((e || "") + (t ? "," + t : "")) + ")", e, t);
      }
    }, !0 === v && (i("mouseenter", "Mouse Enter"), i("mouseleave", "Mouse Leave")), pe(), h = function () {
      function n(e) {
        var e = e.getBoundingClientRect(),
          t = {
            x: window.pageXOffset === a ? document.documentElement.scrollLeft : window.pageXOffset,
            y: window.pageYOffset === a ? document.documentElement.scrollTop : window.pageYOffset
          };
        return {
          x: parseInt(e.left, 10) + parseInt(t.x, 10),
          y: parseInt(e.top, 10) + parseInt(t.y, 10)
        };
      }
      function o(e) {
        var e = e.split("#")[1] || e,
          t = decodeURIComponent(e),
          t = document.getElementById(t) || document.getElementsByName(t)[0];
        a === t ? (R("In page link (#" + e + ") not found in iFrame, so sending to parent"), F(0, 0, "inPageLink", "#" + e)) : (t = n(t = t), R("Moving to in page link (#" + e + ") at x: " + t.x + " y: " + t.y), F(t.y, t.x, "scrollToOffset"));
      }
      function e() {
        var e = window.location.hash,
          t = window.location.href;
        "" !== e && "#" !== e && o(t);
      }
      function t() {
        Array.prototype.forEach.call(document.querySelectorAll('a[href^="#"]'), function (e) {
          "#" !== e.getAttribute("href") && k(e, "click", function (e) {
            e.preventDefault(), o(this.getAttribute("href"));
          });
        });
      }
      function i() {
        Array.prototype.forEach && document.querySelectorAll ? (R("Setting up location.hash handlers"), t(), k(window, "hashchange", e), setTimeout(e, l)) : x("In page linking not fully supported in this browser! (See README.md for IE8 workaround)");
      }
      h.enable ? i() : R("In page linking not enabled");
      return {
        findTarget: o
      };
    }(), L("init", "Init message from host page"), Z();
  }
  function de(e) {
    var t = e.split("Callback");
    2 === t.length && (this[t = "on" + t[0].charAt(0).toUpperCase() + t[0].slice(1)] = this[e], delete this[e], x("Deprecated: '" + e + "' has been renamed '" + t + "'. The old method will be removed in the next major version."));
  }
  function le(e, t) {
    a !== t && "" !== t && "null" !== t && R("Body " + e + ' set to "' + (document.body.style[e] = t) + '"');
  }
  function t(n) {
    var e = {
      add: function add(e) {
        function t() {
          L(n.eventName, n.eventType);
        }
        ee[e] = t, k(window, e, t, {
          passive: !0
        });
      },
      remove: function remove(e) {
        var t = ee[e];
        delete ee[e], window.removeEventListener(e, t, !1);
      }
    };
    n.eventNames && Array.prototype.map ? (n.eventName = n.eventNames[0], n.eventNames.map(e[n.method])) : e[n.method](n.eventName), R(ue(n.method) + " event listener: " + n.eventType);
  }
  function fe(e) {
    t({
      method: e,
      eventType: "Animation Start",
      eventNames: ["animationstart", "webkitAnimationStart"]
    }), t({
      method: e,
      eventType: "Animation Iteration",
      eventNames: ["animationiteration", "webkitAnimationIteration"]
    }), t({
      method: e,
      eventType: "Animation End",
      eventNames: ["animationend", "webkitAnimationEnd"]
    }), t({
      method: e,
      eventType: "Input",
      eventName: "input"
    }), t({
      method: e,
      eventType: "Mouse Up",
      eventName: "mouseup"
    }), t({
      method: e,
      eventType: "Mouse Down",
      eventName: "mousedown"
    }), t({
      method: e,
      eventType: "Orientation Change",
      eventName: "orientationchange"
    }), t({
      method: e,
      eventType: "Print",
      eventNames: ["afterprint", "beforeprint"]
    }), t({
      method: e,
      eventType: "Ready State Change",
      eventName: "readystatechange"
    }), t({
      method: e,
      eventType: "Touch Start",
      eventName: "touchstart"
    }), t({
      method: e,
      eventType: "Touch End",
      eventName: "touchend"
    }), t({
      method: e,
      eventType: "Touch Cancel",
      eventName: "touchcancel"
    }), t({
      method: e,
      eventType: "Transition Start",
      eventNames: ["transitionstart", "webkitTransitionStart", "MSTransitionStart", "oTransitionStart", "otransitionstart"]
    }), t({
      method: e,
      eventType: "Transition Iteration",
      eventNames: ["transitioniteration", "webkitTransitionIteration", "MSTransitionIteration", "oTransitionIteration", "otransitioniteration"]
    }), t({
      method: e,
      eventType: "Transition End",
      eventNames: ["transitionend", "webkitTransitionEnd", "MSTransitionEnd", "oTransitionEnd", "otransitionend"]
    }), "child" === b && t({
      method: e,
      eventType: "IFrame Resized",
      eventName: "resize"
    });
  }
  function me(e, t, n, o) {
    return t !== e && (e in n || (x(e + " is not a valid option for " + o + "CalculationMethod."), e = t), R(o + ' calculation method set to "' + e + '"')), e;
  }
  function he() {
    m = me(m, n, C, "height");
  }
  function ge() {
    M = me(M, K, z, "width");
  }
  function pe() {
    var e;
    !0 === r ? (fe("add"), e = g < 0, window.MutationObserver || window.WebKitMutationObserver ? e ? ve() : s = function () {
      function t(e) {
        function t(e) {
          !1 === e.complete && (R("Attach listeners to " + e.src), e.addEventListener("load", i, !1), e.addEventListener("error", r, !1), u.push(e));
        }
        "attributes" === e.type && "src" === e.attributeName ? t(e.target) : "childList" === e.type && Array.prototype.forEach.call(e.target.querySelectorAll("img"), t);
      }
      function o(e) {
        R("Remove listeners from " + e.src), e.removeEventListener("load", i, !1), e.removeEventListener("error", r, !1), u.splice(u.indexOf(e), 1);
      }
      function n(e, t, n) {
        o(e.target), L(t, n + ": " + e.target.src);
      }
      function i(e) {
        n(e, "imageLoad", "Image loaded");
      }
      function r(e) {
        n(e, "imageLoadFailed", "Image load failed");
      }
      function a(e) {
        L("mutationObserver", "mutationObserver: " + e[0].target + " " + e[0].type), e.forEach(t);
      }
      var u = [],
        c = window.MutationObserver || window.WebKitMutationObserver,
        s = function () {
          var e = document.querySelector("body");
          return s = new c(a), R("Create body MutationObserver"), s.observe(e, {
            attributes: !0,
            attributeOldValue: !1,
            characterData: !0,
            characterDataOldValue: !1,
            childList: !0,
            subtree: !0
          }), s;
        }();
      return {
        disconnect: function disconnect() {
          "disconnect" in s && (R("Disconnect body MutationObserver"), s.disconnect(), u.forEach(o));
        }
      };
    }() : (R("MutationObserver not supported in this browser!"), ve())) : R("Auto Resize disabled");
  }
  function ve() {
    0 !== g && (R("setInterval: " + g + "ms"), B = setInterval(function () {
      L("interval", "setInterval: " + g);
    }, Math.abs(g)));
  }
  function ye(e, t) {
    return t = t || document.body, t = null === (t = document.defaultView.getComputedStyle(t, null)) ? 0 : t[e], parseInt(t, 10);
  }
  function we(e, t) {
    for (var n, o = t.length, i = 0, r = ue(e), a = Date.now(), u = 0; u < o; u++) i < (n = t[u].getBoundingClientRect()[e] + ye("margin" + r, t[u])) && (i = n);
    return a = Date.now() - a, R("Parsed " + o + " HTML elements"), R("Element position calculated in " + a + "ms"), O / 2 < (a = a) && R("Event throttle increased to " + (O = 2 * a) + "ms"), i;
  }
  function e(e) {
    return [e.bodyOffset(), e.bodyScroll(), e.documentElementOffset(), e.documentElementScroll()];
  }
  function be(e, t) {
    var n = document.querySelectorAll("[" + t + "]");
    return 0 === n.length && (x("No tagged elements (" + t + ") found on page"), document.querySelectorAll("body *")), we(e, n);
  }
  function Te() {
    return document.querySelectorAll("body *");
  }
  function Ee(e, t, n, o) {
    function i() {
      e in {
        init: 1,
        interval: 1,
        size: 1
      } || !(m in U || d && M in U) ? e in {
        interval: 1
      } || R("No change in size detected") : Ie(t);
    }
    function r(e, t) {
      return !(Math.abs(e - t) <= E);
    }
    n = a === n ? C[m]() : n, o = a === o ? z[M]() : o, r(f, n) || d && r(S, o) || "init" === e ? (Se(), F(f = n, S = o, e)) : i();
  }
  function Oe() {
    A = Date.now(), N = null, ie = oe.apply(o, I), N || (o = I = null);
  }
  function L(e, t, n, o) {
    i && e in j ? R("Trigger event cancelled: " + e) : (e in {
      reset: 1,
      resetPage: 1,
      init: 1
    } || R("Trigger event: " + t), ("init" === e ? Ee : re)(e, t, n, o));
  }
  function Se() {
    i || (i = !0, R("Trigger event lock on")), clearTimeout(Y), Y = setTimeout(function () {
      i = !1, R("Trigger event lock off"), R("--");
    }, l);
  }
  function Me(e) {
    f = C[m](), S = z[M](), F(f, S, e);
  }
  function Ie(e) {
    var t = m;
    m = n, R("Reset trigger event: " + e), Se(), Me("reset"), m = t;
  }
  function F(e, t, n, o, i) {
    !0 === V && (a === i ? i = T : R("Message targetOrigin: " + i), R("Sending message to host page (" + (e = w + ":" + (e + ":" + t) + ":" + n + (a === o ? "" : ":" + o)) + ")"), X.postMessage(y + e, i));
  }
  function Ne() {
    "loading" !== document.readyState && window.parent.postMessage("[iFrameResizerChild]Ready", "*");
  }
}();
"use strict";

function _wrapNativeSuper(Class) { var _cache = typeof Map === "function" ? new Map() : undefined; _wrapNativeSuper = function _wrapNativeSuper(Class) { if (Class === null || !_isNativeFunction(Class)) return Class; if (typeof Class !== "function") { throw new TypeError("Super expression must either be null or a function"); } if (typeof _cache !== "undefined") { if (_cache.has(Class)) return _cache.get(Class); _cache.set(Class, Wrapper); } function Wrapper() { return _construct(Class, arguments, _getPrototypeOf(this).constructor); } Wrapper.prototype = Object.create(Class.prototype, { constructor: { value: Wrapper, enumerable: false, writable: true, configurable: true } }); return _setPrototypeOf(Wrapper, Class); }; return _wrapNativeSuper(Class); }
function _construct(Parent, args, Class) { if (_isNativeReflectConstruct()) { _construct = Reflect.construct.bind(); } else { _construct = function _construct(Parent, args, Class) { var a = [null]; a.push.apply(a, args); var Constructor = Function.bind.apply(Parent, a); var instance = new Constructor(); if (Class) _setPrototypeOf(instance, Class.prototype); return instance; }; } return _construct.apply(null, arguments); }
function _isNativeFunction(fn) { return Function.toString.call(fn).indexOf("[native code]") !== -1; }
function _slicedToArray(arr, i) { return _arrayWithHoles(arr) || _iterableToArrayLimit(arr, i) || _unsupportedIterableToArray(arr, i) || _nonIterableRest(); }
function _nonIterableRest() { throw new TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method."); }
function _iterableToArrayLimit(arr, i) { var _i = null == arr ? null : "undefined" != typeof Symbol && arr[Symbol.iterator] || arr["@@iterator"]; if (null != _i) { var _s, _e, _x, _r, _arr = [], _n = !0, _d = !1; try { if (_x = (_i = _i.call(arr)).next, 0 === i) { if (Object(_i) !== _i) return; _n = !1; } else for (; !(_n = (_s = _x.call(_i)).done) && (_arr.push(_s.value), _arr.length !== i); _n = !0); } catch (err) { _d = !0, _e = err; } finally { try { if (!_n && null != _i["return"] && (_r = _i["return"](), Object(_r) !== _r)) return; } finally { if (_d) throw _e; } } return _arr; } }
function _arrayWithHoles(arr) { if (Array.isArray(arr)) return arr; }
function _inherits(subClass, superClass) { if (typeof superClass !== "function" && superClass !== null) { throw new TypeError("Super expression must either be null or a function"); } subClass.prototype = Object.create(superClass && superClass.prototype, { constructor: { value: subClass, writable: true, configurable: true } }); Object.defineProperty(subClass, "prototype", { writable: false }); if (superClass) _setPrototypeOf(subClass, superClass); }
function _setPrototypeOf(o, p) { _setPrototypeOf = Object.setPrototypeOf ? Object.setPrototypeOf.bind() : function _setPrototypeOf(o, p) { o.__proto__ = p; return o; }; return _setPrototypeOf(o, p); }
function _createSuper(Derived) { var hasNativeReflectConstruct = _isNativeReflectConstruct(); return function _createSuperInternal() { var Super = _getPrototypeOf(Derived), result; if (hasNativeReflectConstruct) { var NewTarget = _getPrototypeOf(this).constructor; result = Reflect.construct(Super, arguments, NewTarget); } else { result = Super.apply(this, arguments); } return _possibleConstructorReturn(this, result); }; }
function _possibleConstructorReturn(self, call) { if (call && (_typeof(call) === "object" || typeof call === "function")) { return call; } else if (call !== void 0) { throw new TypeError("Derived constructors may only return object or undefined"); } return _assertThisInitialized(self); }
function _assertThisInitialized(self) { if (self === void 0) { throw new ReferenceError("this hasn't been initialised - super() hasn't been called"); } return self; }
function _isNativeReflectConstruct() { if (typeof Reflect === "undefined" || !Reflect.construct) return false; if (Reflect.construct.sham) return false; if (typeof Proxy === "function") return true; try { Boolean.prototype.valueOf.call(Reflect.construct(Boolean, [], function () {})); return true; } catch (e) { return false; } }
function _getPrototypeOf(o) { _getPrototypeOf = Object.setPrototypeOf ? Object.getPrototypeOf.bind() : function _getPrototypeOf(o) { return o.__proto__ || Object.getPrototypeOf(o); }; return _getPrototypeOf(o); }
function _toConsumableArray(arr) { return _arrayWithoutHoles(arr) || _iterableToArray(arr) || _unsupportedIterableToArray(arr) || _nonIterableSpread(); }
function _nonIterableSpread() { throw new TypeError("Invalid attempt to spread non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method."); }
function _unsupportedIterableToArray(o, minLen) { if (!o) return; if (typeof o === "string") return _arrayLikeToArray(o, minLen); var n = Object.prototype.toString.call(o).slice(8, -1); if (n === "Object" && o.constructor) n = o.constructor.name; if (n === "Map" || n === "Set") return Array.from(o); if (n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n)) return _arrayLikeToArray(o, minLen); }
function _iterableToArray(iter) { if (typeof Symbol !== "undefined" && iter[Symbol.iterator] != null || iter["@@iterator"] != null) return Array.from(iter); }
function _arrayWithoutHoles(arr) { if (Array.isArray(arr)) return _arrayLikeToArray(arr); }
function _arrayLikeToArray(arr, len) { if (len == null || len > arr.length) len = arr.length; for (var i = 0, arr2 = new Array(len); i < len; i++) arr2[i] = arr[i]; return arr2; }
function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }
function _defineProperties(target, props) { for (var i = 0; i < props.length; i++) { var descriptor = props[i]; descriptor.enumerable = descriptor.enumerable || false; descriptor.configurable = true; if ("value" in descriptor) descriptor.writable = true; Object.defineProperty(target, _toPropertyKey(descriptor.key), descriptor); } }
function _createClass(Constructor, protoProps, staticProps) { if (protoProps) _defineProperties(Constructor.prototype, protoProps); if (staticProps) _defineProperties(Constructor, staticProps); Object.defineProperty(Constructor, "prototype", { writable: false }); return Constructor; }
function _toPropertyKey(arg) { var key = _toPrimitive(arg, "string"); return _typeof(key) === "symbol" ? key : String(key); }
function _toPrimitive(input, hint) { if (_typeof(input) !== "object" || input === null) return input; var prim = input[Symbol.toPrimitive]; if (prim !== undefined) { var res = prim.call(input, hint || "default"); if (_typeof(res) !== "object") return res; throw new TypeError("@@toPrimitive must return a primitive value."); } return (hint === "string" ? String : Number)(input); }
function _typeof(obj) { "@babel/helpers - typeof"; return _typeof = "function" == typeof Symbol && "symbol" == typeof Symbol.iterator ? function (obj) { return typeof obj; } : function (obj) { return obj && "function" == typeof Symbol && obj.constructor === Symbol && obj !== Symbol.prototype ? "symbol" : typeof obj; }, _typeof(obj); }
/*!
  Highlight.js v11.7.0 (git: 82688fad18)
  (c) 2006-2022 undefined and other contributors
  License: BSD-3-Clause
 */
var hljs = function () {
  "use strict";

  var e = {
    exports: {}
  };
  function t(e) {
    return e instanceof Map ? e.clear = e["delete"] = e.set = function () {
      throw Error("map is read-only");
    } : e instanceof Set && (e.add = e.clear = e["delete"] = function () {
      throw Error("set is read-only");
    }), Object.freeze(e), Object.getOwnPropertyNames(e).forEach(function (n) {
      var i = e[n];
      "object" != _typeof(i) || Object.isFrozen(i) || t(i);
    }), e;
  }
  e.exports = t, e.exports["default"] = t;
  var n = /*#__PURE__*/function () {
    function n(e) {
      _classCallCheck(this, n);
      void 0 === e.data && (e.data = {}), this.data = e.data, this.isMatchIgnored = !1;
    }
    _createClass(n, [{
      key: "ignoreMatch",
      value: function ignoreMatch() {
        this.isMatchIgnored = !0;
      }
    }]);
    return n;
  }();
  function i(e) {
    return e.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#x27;");
  }
  function r(e) {
    var n = Object.create(null);
    for (var _t in e) n[_t] = e[_t];
    for (var _len = arguments.length, t = new Array(_len > 1 ? _len - 1 : 0), _key = 1; _key < _len; _key++) {
      t[_key - 1] = arguments[_key];
    }
    return t.forEach(function (e) {
      for (var _t2 in e) n[_t2] = e[_t2];
    }), n;
  }
  var s = function s(e) {
    return !!e.scope || e.sublanguage && e.language;
  };
  var o = /*#__PURE__*/function () {
    function o(e, t) {
      _classCallCheck(this, o);
      this.buffer = "", this.classPrefix = t.classPrefix, e.walk(this);
    }
    _createClass(o, [{
      key: "addText",
      value: function addText(e) {
        this.buffer += i(e);
      }
    }, {
      key: "openNode",
      value: function openNode(e) {
        if (!s(e)) return;
        var t = "";
        t = e.sublanguage ? "language-" + e.language : function (e, _ref) {
          var t = _ref.prefix;
          if (e.includes(".")) {
            var _n = e.split(".");
            return ["".concat(t).concat(_n.shift())].concat(_toConsumableArray(_n.map(function (e, t) {
              return "".concat(e).concat("_".repeat(t + 1));
            }))).join(" ");
          }
          return "".concat(t).concat(e);
        }(e.scope, {
          prefix: this.classPrefix
        }), this.span(t);
      }
    }, {
      key: "closeNode",
      value: function closeNode(e) {
        s(e) && (this.buffer += "</span>");
      }
    }, {
      key: "value",
      value: function value() {
        return this.buffer;
      }
    }, {
      key: "span",
      value: function span(e) {
        this.buffer += "<span class=\"".concat(e, "\">");
      }
    }]);
    return o;
  }();
  var a = function a() {
    var e = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : {};
    var t = {
      children: []
    };
    return Object.assign(t, e), t;
  };
  var c = /*#__PURE__*/function () {
    function c() {
      _classCallCheck(this, c);
      this.rootNode = a(), this.stack = [this.rootNode];
    }
    _createClass(c, [{
      key: "top",
      get: function get() {
        return this.stack[this.stack.length - 1];
      }
    }, {
      key: "root",
      get: function get() {
        return this.rootNode;
      }
    }, {
      key: "add",
      value: function add(e) {
        this.top.children.push(e);
      }
    }, {
      key: "openNode",
      value: function openNode(e) {
        var t = a({
          scope: e
        });
        this.add(t), this.stack.push(t);
      }
    }, {
      key: "closeNode",
      value: function closeNode() {
        if (this.stack.length > 1) return this.stack.pop();
      }
    }, {
      key: "closeAllNodes",
      value: function closeAllNodes() {
        for (; this.closeNode(););
      }
    }, {
      key: "toJSON",
      value: function toJSON() {
        return JSON.stringify(this.rootNode, null, 4);
      }
    }, {
      key: "walk",
      value: function walk(e) {
        return this.constructor._walk(e, this.rootNode);
      }
    }], [{
      key: "_walk",
      value: function _walk(e, t) {
        var _this = this;
        return "string" == typeof t ? e.addText(t) : t.children && (e.openNode(t), t.children.forEach(function (t) {
          return _this._walk(e, t);
        }), e.closeNode(t)), e;
      }
    }, {
      key: "_collapse",
      value: function _collapse(e) {
        "string" != typeof e && e.children && (e.children.every(function (e) {
          return "string" == typeof e;
        }) ? e.children = [e.children.join("")] : e.children.forEach(function (e) {
          c._collapse(e);
        }));
      }
    }]);
    return c;
  }();
  var l = /*#__PURE__*/function (_c) {
    _inherits(l, _c);
    var _super = _createSuper(l);
    function l(e) {
      var _this2;
      _classCallCheck(this, l);
      _this2 = _super.call(this), _this2.options = e;
      return _this2;
    }
    _createClass(l, [{
      key: "addKeyword",
      value: function addKeyword(e, t) {
        "" !== e && (this.openNode(t), this.addText(e), this.closeNode());
      }
    }, {
      key: "addText",
      value: function addText(e) {
        "" !== e && this.add(e);
      }
    }, {
      key: "addSublanguage",
      value: function addSublanguage(e, t) {
        var n = e.root;
        n.sublanguage = !0, n.language = t, this.add(n);
      }
    }, {
      key: "toHTML",
      value: function toHTML() {
        return new o(this, this.options).value();
      }
    }, {
      key: "finalize",
      value: function finalize() {
        return !0;
      }
    }]);
    return l;
  }(c);
  function g(e) {
    return e ? "string" == typeof e ? e : e.source : null;
  }
  function d(e) {
    return p("(?=", e, ")");
  }
  function u(e) {
    return p("(?:", e, ")*");
  }
  function h(e) {
    return p("(?:", e, ")?");
  }
  function p() {
    for (var _len2 = arguments.length, e = new Array(_len2), _key2 = 0; _key2 < _len2; _key2++) {
      e[_key2] = arguments[_key2];
    }
    return e.map(function (e) {
      return g(e);
    }).join("");
  }
  function f() {
    for (var _len3 = arguments.length, e = new Array(_len3), _key3 = 0; _key3 < _len3; _key3++) {
      e[_key3] = arguments[_key3];
    }
    var t = function (e) {
      var t = e[e.length - 1];
      return "object" == _typeof(t) && t.constructor === Object ? (e.splice(e.length - 1, 1), t) : {};
    }(e);
    return "(" + (t.capture ? "" : "?:") + e.map(function (e) {
      return g(e);
    }).join("|") + ")";
  }
  function b(e) {
    return RegExp(e.toString() + "|").exec("").length - 1;
  }
  var m = /\[(?:[^\\\]]|\\.)*\]|\(\??|\\([1-9][0-9]*)|\\./;
  function E(e, _ref2) {
    var t = _ref2.joinWith;
    var n = 0;
    return e.map(function (e) {
      n += 1;
      var t = n;
      var i = g(e),
        r = "";
      for (; i.length > 0;) {
        var _e = m.exec(i);
        if (!_e) {
          r += i;
          break;
        }
        r += i.substring(0, _e.index), i = i.substring(_e.index + _e[0].length), "\\" === _e[0][0] && _e[1] ? r += "\\" + (Number(_e[1]) + t) : (r += _e[0], "(" === _e[0] && n++);
      }
      return r;
    }).map(function (e) {
      return "(".concat(e, ")");
    }).join(t);
  }
  var x = "[a-zA-Z]\\w*",
    w = "[a-zA-Z_]\\w*",
    y = "\\b\\d+(\\.\\d+)?",
    _ = "(-?)(\\b0[xX][a-fA-F0-9]+|(\\b\\d+(\\.\\d*)?|\\.\\d+)([eE][-+]?\\d+)?)",
    O = "\\b(0b[01]+)",
    v = {
      begin: "\\\\[\\s\\S]",
      relevance: 0
    },
    N = {
      scope: "string",
      begin: "'",
      end: "'",
      illegal: "\\n",
      contains: [v]
    },
    k = {
      scope: "string",
      begin: '"',
      end: '"',
      illegal: "\\n",
      contains: [v]
    },
    M = function M(e, t) {
      var n = arguments.length > 2 && arguments[2] !== undefined ? arguments[2] : {};
      var i = r({
        scope: "comment",
        begin: e,
        end: t,
        contains: []
      }, n);
      i.contains.push({
        scope: "doctag",
        begin: "[ ]*(?=(TODO|FIXME|NOTE|BUG|OPTIMIZE|HACK|XXX):)",
        end: /(TODO|FIXME|NOTE|BUG|OPTIMIZE|HACK|XXX):/,
        excludeBegin: !0,
        relevance: 0
      });
      var s = f("I", "a", "is", "so", "us", "to", "at", "if", "in", "it", "on", /[A-Za-z]+['](d|ve|re|ll|t|s|n)/, /[A-Za-z]+[-][a-z]+/, /[A-Za-z][a-z]{2,}/);
      return i.contains.push({
        begin: p(/[ ]+/, "(", s, /[.]?[:]?([.][ ]|[ ])/, "){3}")
      }), i;
    },
    S = M("//", "$"),
    R = M("/\\*", "\\*/"),
    j = M("#", "$");
  var A = Object.freeze({
    __proto__: null,
    MATCH_NOTHING_RE: /\b\B/,
    IDENT_RE: x,
    UNDERSCORE_IDENT_RE: w,
    NUMBER_RE: y,
    C_NUMBER_RE: _,
    BINARY_NUMBER_RE: O,
    RE_STARTERS_RE: "!|!=|!==|%|%=|&|&&|&=|\\*|\\*=|\\+|\\+=|,|-|-=|/=|/|:|;|<<|<<=|<=|<|===|==|=|>>>=|>>=|>=|>>>|>>|>|\\?|\\[|\\{|\\(|\\^|\\^=|\\||\\|=|\\|\\||~",
    SHEBANG: function SHEBANG() {
      var e = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : {};
      var t = /^#![ ]*\//;
      return e.binary && (e.begin = p(t, /.*\b/, e.binary, /\b.*/)), r({
        scope: "meta",
        begin: t,
        end: /$/,
        relevance: 0,
        "on:begin": function onBegin(e, t) {
          0 !== e.index && t.ignoreMatch();
        }
      }, e);
    },
    BACKSLASH_ESCAPE: v,
    APOS_STRING_MODE: N,
    QUOTE_STRING_MODE: k,
    PHRASAL_WORDS_MODE: {
      begin: /\b(a|an|the|are|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|they|like|more)\b/
    },
    COMMENT: M,
    C_LINE_COMMENT_MODE: S,
    C_BLOCK_COMMENT_MODE: R,
    HASH_COMMENT_MODE: j,
    NUMBER_MODE: {
      scope: "number",
      begin: y,
      relevance: 0
    },
    C_NUMBER_MODE: {
      scope: "number",
      begin: _,
      relevance: 0
    },
    BINARY_NUMBER_MODE: {
      scope: "number",
      begin: O,
      relevance: 0
    },
    REGEXP_MODE: {
      begin: /(?=\/[^/\n]*\/)/,
      contains: [{
        scope: "regexp",
        begin: /\//,
        end: /\/[gimuy]*/,
        illegal: /\n/,
        contains: [v, {
          begin: /\[/,
          end: /\]/,
          relevance: 0,
          contains: [v]
        }]
      }]
    },
    TITLE_MODE: {
      scope: "title",
      begin: x,
      relevance: 0
    },
    UNDERSCORE_TITLE_MODE: {
      scope: "title",
      begin: w,
      relevance: 0
    },
    METHOD_GUARD: {
      begin: "\\.\\s*[a-zA-Z_]\\w*",
      relevance: 0
    },
    END_SAME_AS_BEGIN: function END_SAME_AS_BEGIN(e) {
      return Object.assign(e, {
        "on:begin": function onBegin(e, t) {
          t.data._beginMatch = e[1];
        },
        "on:end": function onEnd(e, t) {
          t.data._beginMatch !== e[1] && t.ignoreMatch();
        }
      });
    }
  });
  function I(e, t) {
    "." === e.input[e.index - 1] && t.ignoreMatch();
  }
  function T(e, t) {
    void 0 !== e.className && (e.scope = e.className, delete e.className);
  }
  function L(e, t) {
    t && e.beginKeywords && (e.begin = "\\b(" + e.beginKeywords.split(" ").join("|") + ")(?!\\.)(?=\\b|\\s)", e.__beforeBegin = I, e.keywords = e.keywords || e.beginKeywords, delete e.beginKeywords, void 0 === e.relevance && (e.relevance = 0));
  }
  function B(e, t) {
    Array.isArray(e.illegal) && (e.illegal = f.apply(void 0, _toConsumableArray(e.illegal)));
  }
  function D(e, t) {
    if (e.match) {
      if (e.begin || e.end) throw Error("begin & end are not supported with match");
      e.begin = e.match, delete e.match;
    }
  }
  function H(e, t) {
    void 0 === e.relevance && (e.relevance = 1);
  }
  var P = function P(e, t) {
      if (!e.beforeMatch) return;
      if (e.starts) throw Error("beforeMatch cannot be used with starts");
      var n = Object.assign({}, e);
      Object.keys(e).forEach(function (t) {
        delete e[t];
      }), e.keywords = n.keywords, e.begin = p(n.beforeMatch, d(n.begin)), e.starts = {
        relevance: 0,
        contains: [Object.assign(n, {
          endsParent: !0
        })]
      }, e.relevance = 0, delete n.beforeMatch;
    },
    C = ["of", "and", "for", "in", "not", "or", "if", "then", "parent", "list", "value"];
  function $(e, t) {
    var n = arguments.length > 2 && arguments[2] !== undefined ? arguments[2] : "keyword";
    var i = Object.create(null);
    return "string" == typeof e ? r(n, e.split(" ")) : Array.isArray(e) ? r(n, e) : Object.keys(e).forEach(function (n) {
      Object.assign(i, $(e[n], t, n));
    }), i;
    function r(e, n) {
      t && (n = n.map(function (e) {
        return e.toLowerCase();
      })), n.forEach(function (t) {
        var n = t.split("|");
        i[n[0]] = [e, U(n[0], n[1])];
      });
    }
  }
  function U(e, t) {
    return t ? Number(t) : function (e) {
      return C.includes(e.toLowerCase());
    }(e) ? 0 : 1;
  }
  var z = {},
    K = function K(e) {
      console.error(e);
    },
    W = function W(e) {
      var _console;
      for (var _len4 = arguments.length, t = new Array(_len4 > 1 ? _len4 - 1 : 0), _key4 = 1; _key4 < _len4; _key4++) {
        t[_key4 - 1] = arguments[_key4];
      }
      (_console = console).log.apply(_console, ["WARN: " + e].concat(t));
    },
    X = function X(e, t) {
      z["".concat(e, "/").concat(t)] || (console.log("Deprecated as of ".concat(e, ". ").concat(t)), z["".concat(e, "/").concat(t)] = !0);
    },
    G = Error();
  function Z(e, t, _ref3) {
    var n = _ref3.key;
    var i = 0;
    var r = e[n],
      s = {},
      o = {};
    for (var _e2 = 1; _e2 <= t.length; _e2++) o[_e2 + i] = r[_e2], s[_e2 + i] = !0, i += b(t[_e2 - 1]);
    e[n] = o, e[n]._emit = s, e[n]._multi = !0;
  }
  function F(e) {
    (function (e) {
      e.scope && "object" == _typeof(e.scope) && null !== e.scope && (e.beginScope = e.scope, delete e.scope);
    })(e), "string" == typeof e.beginScope && (e.beginScope = {
      _wrap: e.beginScope
    }), "string" == typeof e.endScope && (e.endScope = {
      _wrap: e.endScope
    }), function (e) {
      if (Array.isArray(e.begin)) {
        if (e.skip || e.excludeBegin || e.returnBegin) throw K("skip, excludeBegin, returnBegin not compatible with beginScope: {}"), G;
        if ("object" != _typeof(e.beginScope) || null === e.beginScope) throw K("beginScope must be object"), G;
        Z(e, e.begin, {
          key: "beginScope"
        }), e.begin = E(e.begin, {
          joinWith: ""
        });
      }
    }(e), function (e) {
      if (Array.isArray(e.end)) {
        if (e.skip || e.excludeEnd || e.returnEnd) throw K("skip, excludeEnd, returnEnd not compatible with endScope: {}"), G;
        if ("object" != _typeof(e.endScope) || null === e.endScope) throw K("endScope must be object"), G;
        Z(e, e.end, {
          key: "endScope"
        }), e.end = E(e.end, {
          joinWith: ""
        });
      }
    }(e);
  }
  function V(e) {
    function t(t, n) {
      return RegExp(g(t), "m" + (e.case_insensitive ? "i" : "") + (e.unicodeRegex ? "u" : "") + (n ? "g" : ""));
    }
    var n = /*#__PURE__*/function () {
      function n() {
        _classCallCheck(this, n);
        this.matchIndexes = {}, this.regexes = [], this.matchAt = 1, this.position = 0;
      }
      _createClass(n, [{
        key: "addRule",
        value: function addRule(e, t) {
          t.position = this.position++, this.matchIndexes[this.matchAt] = t, this.regexes.push([t, e]), this.matchAt += b(e) + 1;
        }
      }, {
        key: "compile",
        value: function compile() {
          0 === this.regexes.length && (this.exec = function () {
            return null;
          });
          var e = this.regexes.map(function (e) {
            return e[1];
          });
          this.matcherRe = t(E(e, {
            joinWith: "|"
          }), !0), this.lastIndex = 0;
        }
      }, {
        key: "exec",
        value: function exec(e) {
          this.matcherRe.lastIndex = this.lastIndex;
          var t = this.matcherRe.exec(e);
          if (!t) return null;
          var _n2 = t.findIndex(function (e, t) {
              return t > 0 && void 0 !== e;
            }),
            i = this.matchIndexes[_n2];
          return t.splice(0, _n2), Object.assign(t, i);
        }
      }]);
      return n;
    }();
    var i = /*#__PURE__*/function () {
      function i() {
        _classCallCheck(this, i);
        this.rules = [], this.multiRegexes = [], this.count = 0, this.lastIndex = 0, this.regexIndex = 0;
      }
      _createClass(i, [{
        key: "getMatcher",
        value: function getMatcher(e) {
          if (this.multiRegexes[e]) return this.multiRegexes[e];
          var t = new n();
          return this.rules.slice(e).forEach(function (_ref4) {
            var _ref5 = _slicedToArray(_ref4, 2),
              e = _ref5[0],
              n = _ref5[1];
            return t.addRule(e, n);
          }), t.compile(), this.multiRegexes[e] = t, t;
        }
      }, {
        key: "resumingScanAtSamePosition",
        value: function resumingScanAtSamePosition() {
          return 0 !== this.regexIndex;
        }
      }, {
        key: "considerAll",
        value: function considerAll() {
          this.regexIndex = 0;
        }
      }, {
        key: "addRule",
        value: function addRule(e, t) {
          this.rules.push([e, t]), "begin" === t.type && this.count++;
        }
      }, {
        key: "exec",
        value: function exec(e) {
          var t = this.getMatcher(this.regexIndex);
          t.lastIndex = this.lastIndex;
          var n = t.exec(e);
          if (this.resumingScanAtSamePosition()) if (n && n.index === this.lastIndex) ;else {
            var _t3 = this.getMatcher(0);
            _t3.lastIndex = this.lastIndex + 1, n = _t3.exec(e);
          }
          return n && (this.regexIndex += n.position + 1, this.regexIndex === this.count && this.considerAll()), n;
        }
      }]);
      return i;
    }();
    if (e.compilerExtensions || (e.compilerExtensions = []), e.contains && e.contains.includes("self")) throw Error("ERR: contains `self` is not supported at the top-level of a language.  See documentation.");
    return e.classNameAliases = r(e.classNameAliases || {}), function n(s, o) {
      var _ref6;
      var a = s;
      if (s.isCompiled) return a;
      [T, D, F, P].forEach(function (e) {
        return e(s, o);
      }), e.compilerExtensions.forEach(function (e) {
        return e(s, o);
      }), s.__beforeBegin = null, [L, B, H].forEach(function (e) {
        return e(s, o);
      }), s.isCompiled = !0;
      var c = null;
      return "object" == _typeof(s.keywords) && s.keywords.$pattern && (s.keywords = Object.assign({}, s.keywords), c = s.keywords.$pattern, delete s.keywords.$pattern), c = c || /\w+/, s.keywords && (s.keywords = $(s.keywords, e.case_insensitive)), a.keywordPatternRe = t(c, !0), o && (s.begin || (s.begin = /\B|\b/), a.beginRe = t(a.begin), s.end || s.endsWithParent || (s.end = /\B|\b/), s.end && (a.endRe = t(a.end)), a.terminatorEnd = g(a.end) || "", s.endsWithParent && o.terminatorEnd && (a.terminatorEnd += (s.end ? "|" : "") + o.terminatorEnd)), s.illegal && (a.illegalRe = t(s.illegal)), s.contains || (s.contains = []), s.contains = (_ref6 = []).concat.apply(_ref6, _toConsumableArray(s.contains.map(function (e) {
        return function (e) {
          return e.variants && !e.cachedVariants && (e.cachedVariants = e.variants.map(function (t) {
            return r(e, {
              variants: null
            }, t);
          })), e.cachedVariants ? e.cachedVariants : q(e) ? r(e, {
            starts: e.starts ? r(e.starts) : null
          }) : Object.isFrozen(e) ? r(e) : e;
        }("self" === e ? s : e);
      }))), s.contains.forEach(function (e) {
        n(e, a);
      }), s.starts && n(s.starts, o), a.matcher = function (e) {
        var t = new i();
        return e.contains.forEach(function (e) {
          return t.addRule(e.begin, {
            rule: e,
            type: "begin"
          });
        }), e.terminatorEnd && t.addRule(e.terminatorEnd, {
          type: "end"
        }), e.illegal && t.addRule(e.illegal, {
          type: "illegal"
        }), t;
      }(a), a;
    }(e);
  }
  function q(e) {
    return !!e && (e.endsWithParent || q(e.starts));
  }
  var J = /*#__PURE__*/function (_Error) {
    _inherits(J, _Error);
    var _super2 = _createSuper(J);
    function J(e, t) {
      var _this3;
      _classCallCheck(this, J);
      _this3 = _super2.call(this, e), _this3.name = "HTMLInjectionError", _this3.html = t;
      return _this3;
    }
    return _createClass(J);
  }( /*#__PURE__*/_wrapNativeSuper(Error));
  var Y = i,
    Q = r,
    ee = Symbol("nomatch");
  var te = function (t) {
    var i = Object.create(null),
      r = Object.create(null),
      s = [];
    var o = !0;
    var a = "Could not find the language '{}', did you forget to load/include a language module?",
      c = {
        disableAutodetect: !0,
        name: "Plain text",
        contains: []
      };
    var g = {
      ignoreUnescapedHTML: !1,
      throwUnescapedHTML: !1,
      noHighlightRe: /^(no-?highlight)$/i,
      languageDetectRe: /\blang(?:uage)?-([\w-]+)\b/i,
      classPrefix: "hljs-",
      cssSelector: "pre code",
      languages: null,
      __emitter: l
    };
    function b(e) {
      return g.noHighlightRe.test(e);
    }
    function m(e, t, n) {
      var i = "",
        r = "";
      "object" == _typeof(t) ? (i = e, n = t.ignoreIllegals, r = t.language) : (X("10.7.0", "highlight(lang, code, ...args) has been deprecated."), X("10.7.0", "Please use highlight(code, options) instead.\nhttps://github.com/highlightjs/highlight.js/issues/2277"), r = e, i = t), void 0 === n && (n = !0);
      var s = {
        code: i,
        language: r
      };
      k("before:highlight", s);
      var o = s.result ? s.result : E(s.language, s.code, n);
      return o.code = s.code, k("after:highlight", o), o;
    }
    function E(e, t, r, s) {
      var c = Object.create(null);
      function l() {
        if (!N.keywords) return void M.addText(S);
        var e = 0;
        N.keywordPatternRe.lastIndex = 0;
        var t = N.keywordPatternRe.exec(S),
          n = "";
        for (; t;) {
          n += S.substring(e, t.index);
          var _r2 = y.case_insensitive ? t[0].toLowerCase() : t[0],
            _s2 = (i = _r2, N.keywords[i]);
          if (_s2) {
            var _s3 = _slicedToArray(_s2, 2),
              _e3 = _s3[0],
              _i2 = _s3[1];
            if (M.addText(n), n = "", c[_r2] = (c[_r2] || 0) + 1, c[_r2] <= 7 && (R += _i2), _e3.startsWith("_")) n += t[0];else {
              var _n3 = y.classNameAliases[_e3] || _e3;
              M.addKeyword(t[0], _n3);
            }
          } else n += t[0];
          e = N.keywordPatternRe.lastIndex, t = N.keywordPatternRe.exec(S);
        }
        var i;
        n += S.substring(e), M.addText(n);
      }
      function d() {
        null != N.subLanguage ? function () {
          if ("" === S) return;
          var e = null;
          if ("string" == typeof N.subLanguage) {
            if (!i[N.subLanguage]) return void M.addText(S);
            e = E(N.subLanguage, S, !0, k[N.subLanguage]), k[N.subLanguage] = e._top;
          } else e = x(S, N.subLanguage.length ? N.subLanguage : null);
          N.relevance > 0 && (R += e.relevance), M.addSublanguage(e._emitter, e.language);
        }() : l(), S = "";
      }
      function u(e, t) {
        var n = 1;
        var i = t.length - 1;
        for (; n <= i;) {
          if (!e._emit[n]) {
            n++;
            continue;
          }
          var _i3 = y.classNameAliases[e[n]] || e[n],
            _r3 = t[n];
          _i3 ? M.addKeyword(_r3, _i3) : (S = _r3, l(), S = ""), n++;
        }
      }
      function h(e, t) {
        return e.scope && "string" == typeof e.scope && M.openNode(y.classNameAliases[e.scope] || e.scope), e.beginScope && (e.beginScope._wrap ? (M.addKeyword(S, y.classNameAliases[e.beginScope._wrap] || e.beginScope._wrap), S = "") : e.beginScope._multi && (u(e.beginScope, t), S = "")), N = Object.create(e, {
          parent: {
            value: N
          }
        }), N;
      }
      function p(e, t, i) {
        var r = function (e, t) {
          var n = e && e.exec(t);
          return n && 0 === n.index;
        }(e.endRe, i);
        if (r) {
          if (e["on:end"]) {
            var _i4 = new n(e);
            e["on:end"](t, _i4), _i4.isMatchIgnored && (r = !1);
          }
          if (r) {
            for (; e.endsParent && e.parent;) e = e.parent;
            return e;
          }
        }
        if (e.endsWithParent) return p(e.parent, t, i);
      }
      function f(e) {
        return 0 === N.matcher.regexIndex ? (S += e[0], 1) : (I = !0, 0);
      }
      function b(e) {
        var n = e[0],
          i = t.substring(e.index),
          r = p(N, e, i);
        if (!r) return ee;
        var s = N;
        N.endScope && N.endScope._wrap ? (d(), M.addKeyword(n, N.endScope._wrap)) : N.endScope && N.endScope._multi ? (d(), u(N.endScope, e)) : s.skip ? S += n : (s.returnEnd || s.excludeEnd || (S += n), d(), s.excludeEnd && (S = n));
        do {
          N.scope && M.closeNode(), N.skip || N.subLanguage || (R += N.relevance), N = N.parent;
        } while (N !== r.parent);
        return r.starts && h(r.starts, e), s.returnEnd ? 0 : n.length;
      }
      var m = {};
      function w(i, s) {
        var a = s && s[0];
        if (S += i, null == a) return d(), 0;
        if ("begin" === m.type && "end" === s.type && m.index === s.index && "" === a) {
          if (S += t.slice(s.index, s.index + 1), !o) {
            var _t4 = Error("0 width match regex (".concat(e, ")"));
            throw _t4.languageName = e, _t4.badRule = m.rule, _t4;
          }
          return 1;
        }
        if (m = s, "begin" === s.type) return function (e) {
          var t = e[0],
            i = e.rule,
            r = new n(i),
            s = [i.__beforeBegin, i["on:begin"]];
          for (var _i5 = 0, _s4 = s; _i5 < _s4.length; _i5++) {
            var _n4 = _s4[_i5];
            if (_n4 && (_n4(e, r), r.isMatchIgnored)) return f(t);
          }
          return i.skip ? S += t : (i.excludeBegin && (S += t), d(), i.returnBegin || i.excludeBegin || (S = t)), h(i, e), i.returnBegin ? 0 : t.length;
        }(s);
        if ("illegal" === s.type && !r) {
          var _e4 = Error('Illegal lexeme "' + a + '" for mode "' + (N.scope || "<unnamed>") + '"');
          throw _e4.mode = N, _e4;
        }
        if ("end" === s.type) {
          var _e5 = b(s);
          if (_e5 !== ee) return _e5;
        }
        if ("illegal" === s.type && "" === a) return 1;
        if (A > 1e5 && A > 3 * s.index) throw Error("potential infinite loop, way more iterations than matches");
        return S += a, a.length;
      }
      var y = O(e);
      if (!y) throw K(a.replace("{}", e)), Error('Unknown language: "' + e + '"');
      var _ = V(y);
      var v = "",
        N = s || _;
      var k = {},
        M = new g.__emitter(g);
      (function () {
        var e = [];
        for (var _t5 = N; _t5 !== y; _t5 = _t5.parent) _t5.scope && e.unshift(_t5.scope);
        e.forEach(function (e) {
          return M.openNode(e);
        });
      })();
      var S = "",
        R = 0,
        j = 0,
        A = 0,
        I = !1;
      try {
        for (N.matcher.considerAll();;) {
          A++, I ? I = !1 : N.matcher.considerAll(), N.matcher.lastIndex = j;
          var _e6 = N.matcher.exec(t);
          if (!_e6) break;
          var _n5 = w(t.substring(j, _e6.index), _e6);
          j = _e6.index + _n5;
        }
        return w(t.substring(j)), M.closeAllNodes(), M.finalize(), v = M.toHTML(), {
          language: e,
          value: v,
          relevance: R,
          illegal: !1,
          _emitter: M,
          _top: N
        };
      } catch (n) {
        if (n.message && n.message.includes("Illegal")) return {
          language: e,
          value: Y(t),
          illegal: !0,
          relevance: 0,
          _illegalBy: {
            message: n.message,
            index: j,
            context: t.slice(j - 100, j + 100),
            mode: n.mode,
            resultSoFar: v
          },
          _emitter: M
        };
        if (o) return {
          language: e,
          value: Y(t),
          illegal: !1,
          relevance: 0,
          errorRaised: n,
          _emitter: M,
          _top: N
        };
        throw n;
      }
    }
    function x(e, t) {
      t = t || g.languages || Object.keys(i);
      var n = function (e) {
          var t = {
            value: Y(e),
            illegal: !1,
            relevance: 0,
            _top: c,
            _emitter: new g.__emitter(g)
          };
          return t._emitter.addText(e), t;
        }(e),
        r = t.filter(O).filter(N).map(function (t) {
          return E(t, e, !1);
        });
      r.unshift(n);
      var s = r.sort(function (e, t) {
          if (e.relevance !== t.relevance) return t.relevance - e.relevance;
          if (e.language && t.language) {
            if (O(e.language).supersetOf === t.language) return 1;
            if (O(t.language).supersetOf === e.language) return -1;
          }
          return 0;
        }),
        _s5 = _slicedToArray(s, 2),
        o = _s5[0],
        a = _s5[1],
        l = o;
      return l.secondBest = a, l;
    }
    function w(e) {
      var t = null;
      var n = function (e) {
        var t = e.className + " ";
        t += e.parentNode ? e.parentNode.className : "";
        var n = g.languageDetectRe.exec(t);
        if (n) {
          var _t6 = O(n[1]);
          return _t6 || (W(a.replace("{}", n[1])), W("Falling back to no-highlight mode for this block.", e)), _t6 ? n[1] : "no-highlight";
        }
        return t.split(/\s+/).find(function (e) {
          return b(e) || O(e);
        });
      }(e);
      if (b(n)) return;
      if (k("before:highlightElement", {
        el: e,
        language: n
      }), e.children.length > 0 && (g.ignoreUnescapedHTML || (console.warn("One of your code blocks includes unescaped HTML. This is a potentially serious security risk."), console.warn("https://github.com/highlightjs/highlight.js/wiki/security"), console.warn("The element with unescaped HTML:"), console.warn(e)), g.throwUnescapedHTML)) throw new J("One of your code blocks includes unescaped HTML.", e.innerHTML);
      t = e;
      var i = t.textContent,
        s = n ? m(i, {
          language: n,
          ignoreIllegals: !0
        }) : x(i);
      e.innerHTML = s.value, function (e, t, n) {
        var i = t && r[t] || n;
        e.classList.add("hljs"), e.classList.add("language-" + i);
      }(e, n, s.language), e.result = {
        language: s.language,
        re: s.relevance,
        relevance: s.relevance
      }, s.secondBest && (e.secondBest = {
        language: s.secondBest.language,
        relevance: s.secondBest.relevance
      }), k("after:highlightElement", {
        el: e,
        result: s,
        text: i
      });
    }
    var y = !1;
    function _() {
      "loading" !== document.readyState ? document.querySelectorAll(g.cssSelector).forEach(w) : y = !0;
    }
    function O(e) {
      return e = (e || "").toLowerCase(), i[e] || i[r[e]];
    }
    function v(e, _ref7) {
      var t = _ref7.languageName;
      "string" == typeof e && (e = [e]), e.forEach(function (e) {
        r[e.toLowerCase()] = t;
      });
    }
    function N(e) {
      var t = O(e);
      return t && !t.disableAutodetect;
    }
    function k(e, t) {
      var n = e;
      s.forEach(function (e) {
        e[n] && e[n](t);
      });
    }
    "undefined" != typeof window && window.addEventListener && window.addEventListener("DOMContentLoaded", function () {
      y && _();
    }, !1), Object.assign(t, {
      highlight: m,
      highlightAuto: x,
      highlightAll: _,
      highlightElement: w,
      highlightBlock: function highlightBlock(e) {
        return X("10.7.0", "highlightBlock will be removed entirely in v12.0"), X("10.7.0", "Please use highlightElement now."), w(e);
      },
      configure: function configure(e) {
        g = Q(g, e);
      },
      initHighlighting: function initHighlighting() {
        _(), X("10.6.0", "initHighlighting() deprecated.  Use highlightAll() now.");
      },
      initHighlightingOnLoad: function initHighlightingOnLoad() {
        _(), X("10.6.0", "initHighlightingOnLoad() deprecated.  Use highlightAll() now.");
      },
      registerLanguage: function registerLanguage(e, n) {
        var r = null;
        try {
          r = n(t);
        } catch (t) {
          if (K("Language definition for '{}' could not be registered.".replace("{}", e)), !o) throw t;
          K(t), r = c;
        }
        r.name || (r.name = e), i[e] = r, r.rawDefinition = n.bind(null, t), r.aliases && v(r.aliases, {
          languageName: e
        });
      },
      unregisterLanguage: function unregisterLanguage(e) {
        delete i[e];
        for (var _i6 = 0, _Object$keys = Object.keys(r); _i6 < _Object$keys.length; _i6++) {
          var _t7 = _Object$keys[_i6];
          r[_t7] === e && delete r[_t7];
        }
      },
      listLanguages: function listLanguages() {
        return Object.keys(i);
      },
      getLanguage: O,
      registerAliases: v,
      autoDetection: N,
      inherit: Q,
      addPlugin: function addPlugin(e) {
        (function (e) {
          e["before:highlightBlock"] && !e["before:highlightElement"] && (e["before:highlightElement"] = function (t) {
            e["before:highlightBlock"](Object.assign({
              block: t.el
            }, t));
          }), e["after:highlightBlock"] && !e["after:highlightElement"] && (e["after:highlightElement"] = function (t) {
            e["after:highlightBlock"](Object.assign({
              block: t.el
            }, t));
          });
        })(e), s.push(e);
      }
    }), t.debugMode = function () {
      o = !1;
    }, t.safeMode = function () {
      o = !0;
    }, t.versionString = "11.7.0", t.regex = {
      concat: p,
      lookahead: d,
      either: f,
      optional: h,
      anyNumberOfTimes: u
    };
    for (var _t8 in A) "object" == _typeof(A[_t8]) && e.exports(A[_t8]);
    return Object.assign(t, A), t;
  }({});
  return te;
}();
"object" == (typeof exports === "undefined" ? "undefined" : _typeof(exports)) && "undefined" != typeof module && (module.exports = hljs); /*! `python` grammar compiled for Highlight.js 11.7.0 */
(function () {
  var e = function () {
    "use strict";

    return function (e) {
      var n = e.regex,
        a = /(?:[A-Z_a-z\xAA\xB5\xBA\xC0-\xD6\xD8-\xF6\xF8-\u02C1\u02C6-\u02D1\u02E0-\u02E4\u02EC\u02EE\u0370-\u0374\u0376\u0377\u037B-\u037D\u037F\u0386\u0388-\u038A\u038C\u038E-\u03A1\u03A3-\u03F5\u03F7-\u0481\u048A-\u052F\u0531-\u0556\u0559\u0560-\u0588\u05D0-\u05EA\u05EF-\u05F2\u0620-\u064A\u066E\u066F\u0671-\u06D3\u06D5\u06E5\u06E6\u06EE\u06EF\u06FA-\u06FC\u06FF\u0710\u0712-\u072F\u074D-\u07A5\u07B1\u07CA-\u07EA\u07F4\u07F5\u07FA\u0800-\u0815\u081A\u0824\u0828\u0840-\u0858\u0860-\u086A\u0870-\u0887\u0889-\u088E\u08A0-\u08C9\u0904-\u0939\u093D\u0950\u0958-\u0961\u0971-\u0980\u0985-\u098C\u098F\u0990\u0993-\u09A8\u09AA-\u09B0\u09B2\u09B6-\u09B9\u09BD\u09CE\u09DC\u09DD\u09DF-\u09E1\u09F0\u09F1\u09FC\u0A05-\u0A0A\u0A0F\u0A10\u0A13-\u0A28\u0A2A-\u0A30\u0A32\u0A33\u0A35\u0A36\u0A38\u0A39\u0A59-\u0A5C\u0A5E\u0A72-\u0A74\u0A85-\u0A8D\u0A8F-\u0A91\u0A93-\u0AA8\u0AAA-\u0AB0\u0AB2\u0AB3\u0AB5-\u0AB9\u0ABD\u0AD0\u0AE0\u0AE1\u0AF9\u0B05-\u0B0C\u0B0F\u0B10\u0B13-\u0B28\u0B2A-\u0B30\u0B32\u0B33\u0B35-\u0B39\u0B3D\u0B5C\u0B5D\u0B5F-\u0B61\u0B71\u0B83\u0B85-\u0B8A\u0B8E-\u0B90\u0B92-\u0B95\u0B99\u0B9A\u0B9C\u0B9E\u0B9F\u0BA3\u0BA4\u0BA8-\u0BAA\u0BAE-\u0BB9\u0BD0\u0C05-\u0C0C\u0C0E-\u0C10\u0C12-\u0C28\u0C2A-\u0C39\u0C3D\u0C58-\u0C5A\u0C5D\u0C60\u0C61\u0C80\u0C85-\u0C8C\u0C8E-\u0C90\u0C92-\u0CA8\u0CAA-\u0CB3\u0CB5-\u0CB9\u0CBD\u0CDD\u0CDE\u0CE0\u0CE1\u0CF1\u0CF2\u0D04-\u0D0C\u0D0E-\u0D10\u0D12-\u0D3A\u0D3D\u0D4E\u0D54-\u0D56\u0D5F-\u0D61\u0D7A-\u0D7F\u0D85-\u0D96\u0D9A-\u0DB1\u0DB3-\u0DBB\u0DBD\u0DC0-\u0DC6\u0E01-\u0E30\u0E32\u0E40-\u0E46\u0E81\u0E82\u0E84\u0E86-\u0E8A\u0E8C-\u0EA3\u0EA5\u0EA7-\u0EB0\u0EB2\u0EBD\u0EC0-\u0EC4\u0EC6\u0EDC-\u0EDF\u0F00\u0F40-\u0F47\u0F49-\u0F6C\u0F88-\u0F8C\u1000-\u102A\u103F\u1050-\u1055\u105A-\u105D\u1061\u1065\u1066\u106E-\u1070\u1075-\u1081\u108E\u10A0-\u10C5\u10C7\u10CD\u10D0-\u10FA\u10FC-\u1248\u124A-\u124D\u1250-\u1256\u1258\u125A-\u125D\u1260-\u1288\u128A-\u128D\u1290-\u12B0\u12B2-\u12B5\u12B8-\u12BE\u12C0\u12C2-\u12C5\u12C8-\u12D6\u12D8-\u1310\u1312-\u1315\u1318-\u135A\u1380-\u138F\u13A0-\u13F5\u13F8-\u13FD\u1401-\u166C\u166F-\u167F\u1681-\u169A\u16A0-\u16EA\u16EE-\u16F8\u1700-\u1711\u171F-\u1731\u1740-\u1751\u1760-\u176C\u176E-\u1770\u1780-\u17B3\u17D7\u17DC\u1820-\u1878\u1880-\u18A8\u18AA\u18B0-\u18F5\u1900-\u191E\u1950-\u196D\u1970-\u1974\u1980-\u19AB\u19B0-\u19C9\u1A00-\u1A16\u1A20-\u1A54\u1AA7\u1B05-\u1B33\u1B45-\u1B4C\u1B83-\u1BA0\u1BAE\u1BAF\u1BBA-\u1BE5\u1C00-\u1C23\u1C4D-\u1C4F\u1C5A-\u1C7D\u1C80-\u1C88\u1C90-\u1CBA\u1CBD-\u1CBF\u1CE9-\u1CEC\u1CEE-\u1CF3\u1CF5\u1CF6\u1CFA\u1D00-\u1DBF\u1E00-\u1F15\u1F18-\u1F1D\u1F20-\u1F45\u1F48-\u1F4D\u1F50-\u1F57\u1F59\u1F5B\u1F5D\u1F5F-\u1F7D\u1F80-\u1FB4\u1FB6-\u1FBC\u1FBE\u1FC2-\u1FC4\u1FC6-\u1FCC\u1FD0-\u1FD3\u1FD6-\u1FDB\u1FE0-\u1FEC\u1FF2-\u1FF4\u1FF6-\u1FFC\u2071\u207F\u2090-\u209C\u2102\u2107\u210A-\u2113\u2115\u2118-\u211D\u2124\u2126\u2128\u212A-\u2139\u213C-\u213F\u2145-\u2149\u214E\u2160-\u2188\u2C00-\u2CE4\u2CEB-\u2CEE\u2CF2\u2CF3\u2D00-\u2D25\u2D27\u2D2D\u2D30-\u2D67\u2D6F\u2D80-\u2D96\u2DA0-\u2DA6\u2DA8-\u2DAE\u2DB0-\u2DB6\u2DB8-\u2DBE\u2DC0-\u2DC6\u2DC8-\u2DCE\u2DD0-\u2DD6\u2DD8-\u2DDE\u3005-\u3007\u3021-\u3029\u3031-\u3035\u3038-\u303C\u3041-\u3096\u309D-\u309F\u30A1-\u30FA\u30FC-\u30FF\u3105-\u312F\u3131-\u318E\u31A0-\u31BF\u31F0-\u31FF\u3400-\u4DBF\u4E00-\uA48C\uA4D0-\uA4FD\uA500-\uA60C\uA610-\uA61F\uA62A\uA62B\uA640-\uA66E\uA67F-\uA69D\uA6A0-\uA6EF\uA717-\uA71F\uA722-\uA788\uA78B-\uA7CA\uA7D0\uA7D1\uA7D3\uA7D5-\uA7D9\uA7F2-\uA801\uA803-\uA805\uA807-\uA80A\uA80C-\uA822\uA840-\uA873\uA882-\uA8B3\uA8F2-\uA8F7\uA8FB\uA8FD\uA8FE\uA90A-\uA925\uA930-\uA946\uA960-\uA97C\uA984-\uA9B2\uA9CF\uA9E0-\uA9E4\uA9E6-\uA9EF\uA9FA-\uA9FE\uAA00-\uAA28\uAA40-\uAA42\uAA44-\uAA4B\uAA60-\uAA76\uAA7A\uAA7E-\uAAAF\uAAB1\uAAB5\uAAB6\uAAB9-\uAABD\uAAC0\uAAC2\uAADB-\uAADD\uAAE0-\uAAEA\uAAF2-\uAAF4\uAB01-\uAB06\uAB09-\uAB0E\uAB11-\uAB16\uAB20-\uAB26\uAB28-\uAB2E\uAB30-\uAB5A\uAB5C-\uAB69\uAB70-\uABE2\uAC00-\uD7A3\uD7B0-\uD7C6\uD7CB-\uD7FB\uF900-\uFA6D\uFA70-\uFAD9\uFB00-\uFB06\uFB13-\uFB17\uFB1D\uFB1F-\uFB28\uFB2A-\uFB36\uFB38-\uFB3C\uFB3E\uFB40\uFB41\uFB43\uFB44\uFB46-\uFBB1\uFBD3-\uFC5D\uFC64-\uFD3D\uFD50-\uFD8F\uFD92-\uFDC7\uFDF0-\uFDF9\uFE71\uFE73\uFE77\uFE79\uFE7B\uFE7D\uFE7F-\uFEFC\uFF21-\uFF3A\uFF41-\uFF5A\uFF66-\uFF9D\uFFA0-\uFFBE\uFFC2-\uFFC7\uFFCA-\uFFCF\uFFD2-\uFFD7\uFFDA-\uFFDC]|\uD800[\uDC00-\uDC0B\uDC0D-\uDC26\uDC28-\uDC3A\uDC3C\uDC3D\uDC3F-\uDC4D\uDC50-\uDC5D\uDC80-\uDCFA\uDD40-\uDD74\uDE80-\uDE9C\uDEA0-\uDED0\uDF00-\uDF1F\uDF2D-\uDF4A\uDF50-\uDF75\uDF80-\uDF9D\uDFA0-\uDFC3\uDFC8-\uDFCF\uDFD1-\uDFD5]|\uD801[\uDC00-\uDC9D\uDCB0-\uDCD3\uDCD8-\uDCFB\uDD00-\uDD27\uDD30-\uDD63\uDD70-\uDD7A\uDD7C-\uDD8A\uDD8C-\uDD92\uDD94\uDD95\uDD97-\uDDA1\uDDA3-\uDDB1\uDDB3-\uDDB9\uDDBB\uDDBC\uDE00-\uDF36\uDF40-\uDF55\uDF60-\uDF67\uDF80-\uDF85\uDF87-\uDFB0\uDFB2-\uDFBA]|\uD802[\uDC00-\uDC05\uDC08\uDC0A-\uDC35\uDC37\uDC38\uDC3C\uDC3F-\uDC55\uDC60-\uDC76\uDC80-\uDC9E\uDCE0-\uDCF2\uDCF4\uDCF5\uDD00-\uDD15\uDD20-\uDD39\uDD80-\uDDB7\uDDBE\uDDBF\uDE00\uDE10-\uDE13\uDE15-\uDE17\uDE19-\uDE35\uDE60-\uDE7C\uDE80-\uDE9C\uDEC0-\uDEC7\uDEC9-\uDEE4\uDF00-\uDF35\uDF40-\uDF55\uDF60-\uDF72\uDF80-\uDF91]|\uD803[\uDC00-\uDC48\uDC80-\uDCB2\uDCC0-\uDCF2\uDD00-\uDD23\uDE80-\uDEA9\uDEB0\uDEB1\uDF00-\uDF1C\uDF27\uDF30-\uDF45\uDF70-\uDF81\uDFB0-\uDFC4\uDFE0-\uDFF6]|\uD804[\uDC03-\uDC37\uDC71\uDC72\uDC75\uDC83-\uDCAF\uDCD0-\uDCE8\uDD03-\uDD26\uDD44\uDD47\uDD50-\uDD72\uDD76\uDD83-\uDDB2\uDDC1-\uDDC4\uDDDA\uDDDC\uDE00-\uDE11\uDE13-\uDE2B\uDE3F\uDE40\uDE80-\uDE86\uDE88\uDE8A-\uDE8D\uDE8F-\uDE9D\uDE9F-\uDEA8\uDEB0-\uDEDE\uDF05-\uDF0C\uDF0F\uDF10\uDF13-\uDF28\uDF2A-\uDF30\uDF32\uDF33\uDF35-\uDF39\uDF3D\uDF50\uDF5D-\uDF61]|\uD805[\uDC00-\uDC34\uDC47-\uDC4A\uDC5F-\uDC61\uDC80-\uDCAF\uDCC4\uDCC5\uDCC7\uDD80-\uDDAE\uDDD8-\uDDDB\uDE00-\uDE2F\uDE44\uDE80-\uDEAA\uDEB8\uDF00-\uDF1A\uDF40-\uDF46]|\uD806[\uDC00-\uDC2B\uDCA0-\uDCDF\uDCFF-\uDD06\uDD09\uDD0C-\uDD13\uDD15\uDD16\uDD18-\uDD2F\uDD3F\uDD41\uDDA0-\uDDA7\uDDAA-\uDDD0\uDDE1\uDDE3\uDE00\uDE0B-\uDE32\uDE3A\uDE50\uDE5C-\uDE89\uDE9D\uDEB0-\uDEF8]|\uD807[\uDC00-\uDC08\uDC0A-\uDC2E\uDC40\uDC72-\uDC8F\uDD00-\uDD06\uDD08\uDD09\uDD0B-\uDD30\uDD46\uDD60-\uDD65\uDD67\uDD68\uDD6A-\uDD89\uDD98\uDEE0-\uDEF2\uDF02\uDF04-\uDF10\uDF12-\uDF33\uDFB0]|\uD808[\uDC00-\uDF99]|\uD809[\uDC00-\uDC6E\uDC80-\uDD43]|\uD80B[\uDF90-\uDFF0]|[\uD80C\uD81C-\uD820\uD822\uD840-\uD868\uD86A-\uD86C\uD86F-\uD872\uD874-\uD879\uD880-\uD883\uD885-\uD887][\uDC00-\uDFFF]|\uD80D[\uDC00-\uDC2F\uDC41-\uDC46]|\uD811[\uDC00-\uDE46]|\uD81A[\uDC00-\uDE38\uDE40-\uDE5E\uDE70-\uDEBE\uDED0-\uDEED\uDF00-\uDF2F\uDF40-\uDF43\uDF63-\uDF77\uDF7D-\uDF8F]|\uD81B[\uDE40-\uDE7F\uDF00-\uDF4A\uDF50\uDF93-\uDF9F\uDFE0\uDFE1\uDFE3]|\uD821[\uDC00-\uDFF7]|\uD823[\uDC00-\uDCD5\uDD00-\uDD08]|\uD82B[\uDFF0-\uDFF3\uDFF5-\uDFFB\uDFFD\uDFFE]|\uD82C[\uDC00-\uDD22\uDD32\uDD50-\uDD52\uDD55\uDD64-\uDD67\uDD70-\uDEFB]|\uD82F[\uDC00-\uDC6A\uDC70-\uDC7C\uDC80-\uDC88\uDC90-\uDC99]|\uD835[\uDC00-\uDC54\uDC56-\uDC9C\uDC9E\uDC9F\uDCA2\uDCA5\uDCA6\uDCA9-\uDCAC\uDCAE-\uDCB9\uDCBB\uDCBD-\uDCC3\uDCC5-\uDD05\uDD07-\uDD0A\uDD0D-\uDD14\uDD16-\uDD1C\uDD1E-\uDD39\uDD3B-\uDD3E\uDD40-\uDD44\uDD46\uDD4A-\uDD50\uDD52-\uDEA5\uDEA8-\uDEC0\uDEC2-\uDEDA\uDEDC-\uDEFA\uDEFC-\uDF14\uDF16-\uDF34\uDF36-\uDF4E\uDF50-\uDF6E\uDF70-\uDF88\uDF8A-\uDFA8\uDFAA-\uDFC2\uDFC4-\uDFCB]|\uD837[\uDF00-\uDF1E\uDF25-\uDF2A]|\uD838[\uDC30-\uDC6D\uDD00-\uDD2C\uDD37-\uDD3D\uDD4E\uDE90-\uDEAD\uDEC0-\uDEEB]|\uD839[\uDCD0-\uDCEB\uDFE0-\uDFE6\uDFE8-\uDFEB\uDFED\uDFEE\uDFF0-\uDFFE]|\uD83A[\uDC00-\uDCC4\uDD00-\uDD43\uDD4B]|\uD83B[\uDE00-\uDE03\uDE05-\uDE1F\uDE21\uDE22\uDE24\uDE27\uDE29-\uDE32\uDE34-\uDE37\uDE39\uDE3B\uDE42\uDE47\uDE49\uDE4B\uDE4D-\uDE4F\uDE51\uDE52\uDE54\uDE57\uDE59\uDE5B\uDE5D\uDE5F\uDE61\uDE62\uDE64\uDE67-\uDE6A\uDE6C-\uDE72\uDE74-\uDE77\uDE79-\uDE7C\uDE7E\uDE80-\uDE89\uDE8B-\uDE9B\uDEA1-\uDEA3\uDEA5-\uDEA9\uDEAB-\uDEBB]|\uD869[\uDC00-\uDEDF\uDF00-\uDFFF]|\uD86D[\uDC00-\uDF39\uDF40-\uDFFF]|\uD86E[\uDC00-\uDC1D\uDC20-\uDFFF]|\uD873[\uDC00-\uDEA1\uDEB0-\uDFFF]|\uD87A[\uDC00-\uDFE0]|\uD87E[\uDC00-\uDE1D]|\uD884[\uDC00-\uDF4A\uDF50-\uDFFF]|\uD888[\uDC00-\uDFAF])(?:[0-9A-Z_a-z\xAA\xB5\xB7\xBA\xC0-\xD6\xD8-\xF6\xF8-\u02C1\u02C6-\u02D1\u02E0-\u02E4\u02EC\u02EE\u0300-\u0374\u0376\u0377\u037B-\u037D\u037F\u0386-\u038A\u038C\u038E-\u03A1\u03A3-\u03F5\u03F7-\u0481\u0483-\u0487\u048A-\u052F\u0531-\u0556\u0559\u0560-\u0588\u0591-\u05BD\u05BF\u05C1\u05C2\u05C4\u05C5\u05C7\u05D0-\u05EA\u05EF-\u05F2\u0610-\u061A\u0620-\u0669\u066E-\u06D3\u06D5-\u06DC\u06DF-\u06E8\u06EA-\u06FC\u06FF\u0710-\u074A\u074D-\u07B1\u07C0-\u07F5\u07FA\u07FD\u0800-\u082D\u0840-\u085B\u0860-\u086A\u0870-\u0887\u0889-\u088E\u0898-\u08E1\u08E3-\u0963\u0966-\u096F\u0971-\u0983\u0985-\u098C\u098F\u0990\u0993-\u09A8\u09AA-\u09B0\u09B2\u09B6-\u09B9\u09BC-\u09C4\u09C7\u09C8\u09CB-\u09CE\u09D7\u09DC\u09DD\u09DF-\u09E3\u09E6-\u09F1\u09FC\u09FE\u0A01-\u0A03\u0A05-\u0A0A\u0A0F\u0A10\u0A13-\u0A28\u0A2A-\u0A30\u0A32\u0A33\u0A35\u0A36\u0A38\u0A39\u0A3C\u0A3E-\u0A42\u0A47\u0A48\u0A4B-\u0A4D\u0A51\u0A59-\u0A5C\u0A5E\u0A66-\u0A75\u0A81-\u0A83\u0A85-\u0A8D\u0A8F-\u0A91\u0A93-\u0AA8\u0AAA-\u0AB0\u0AB2\u0AB3\u0AB5-\u0AB9\u0ABC-\u0AC5\u0AC7-\u0AC9\u0ACB-\u0ACD\u0AD0\u0AE0-\u0AE3\u0AE6-\u0AEF\u0AF9-\u0AFF\u0B01-\u0B03\u0B05-\u0B0C\u0B0F\u0B10\u0B13-\u0B28\u0B2A-\u0B30\u0B32\u0B33\u0B35-\u0B39\u0B3C-\u0B44\u0B47\u0B48\u0B4B-\u0B4D\u0B55-\u0B57\u0B5C\u0B5D\u0B5F-\u0B63\u0B66-\u0B6F\u0B71\u0B82\u0B83\u0B85-\u0B8A\u0B8E-\u0B90\u0B92-\u0B95\u0B99\u0B9A\u0B9C\u0B9E\u0B9F\u0BA3\u0BA4\u0BA8-\u0BAA\u0BAE-\u0BB9\u0BBE-\u0BC2\u0BC6-\u0BC8\u0BCA-\u0BCD\u0BD0\u0BD7\u0BE6-\u0BEF\u0C00-\u0C0C\u0C0E-\u0C10\u0C12-\u0C28\u0C2A-\u0C39\u0C3C-\u0C44\u0C46-\u0C48\u0C4A-\u0C4D\u0C55\u0C56\u0C58-\u0C5A\u0C5D\u0C60-\u0C63\u0C66-\u0C6F\u0C80-\u0C83\u0C85-\u0C8C\u0C8E-\u0C90\u0C92-\u0CA8\u0CAA-\u0CB3\u0CB5-\u0CB9\u0CBC-\u0CC4\u0CC6-\u0CC8\u0CCA-\u0CCD\u0CD5\u0CD6\u0CDD\u0CDE\u0CE0-\u0CE3\u0CE6-\u0CEF\u0CF1-\u0CF3\u0D00-\u0D0C\u0D0E-\u0D10\u0D12-\u0D44\u0D46-\u0D48\u0D4A-\u0D4E\u0D54-\u0D57\u0D5F-\u0D63\u0D66-\u0D6F\u0D7A-\u0D7F\u0D81-\u0D83\u0D85-\u0D96\u0D9A-\u0DB1\u0DB3-\u0DBB\u0DBD\u0DC0-\u0DC6\u0DCA\u0DCF-\u0DD4\u0DD6\u0DD8-\u0DDF\u0DE6-\u0DEF\u0DF2\u0DF3\u0E01-\u0E3A\u0E40-\u0E4E\u0E50-\u0E59\u0E81\u0E82\u0E84\u0E86-\u0E8A\u0E8C-\u0EA3\u0EA5\u0EA7-\u0EBD\u0EC0-\u0EC4\u0EC6\u0EC8-\u0ECE\u0ED0-\u0ED9\u0EDC-\u0EDF\u0F00\u0F18\u0F19\u0F20-\u0F29\u0F35\u0F37\u0F39\u0F3E-\u0F47\u0F49-\u0F6C\u0F71-\u0F84\u0F86-\u0F97\u0F99-\u0FBC\u0FC6\u1000-\u1049\u1050-\u109D\u10A0-\u10C5\u10C7\u10CD\u10D0-\u10FA\u10FC-\u1248\u124A-\u124D\u1250-\u1256\u1258\u125A-\u125D\u1260-\u1288\u128A-\u128D\u1290-\u12B0\u12B2-\u12B5\u12B8-\u12BE\u12C0\u12C2-\u12C5\u12C8-\u12D6\u12D8-\u1310\u1312-\u1315\u1318-\u135A\u135D-\u135F\u1369-\u1371\u1380-\u138F\u13A0-\u13F5\u13F8-\u13FD\u1401-\u166C\u166F-\u167F\u1681-\u169A\u16A0-\u16EA\u16EE-\u16F8\u1700-\u1715\u171F-\u1734\u1740-\u1753\u1760-\u176C\u176E-\u1770\u1772\u1773\u1780-\u17D3\u17D7\u17DC\u17DD\u17E0-\u17E9\u180B-\u180D\u180F-\u1819\u1820-\u1878\u1880-\u18AA\u18B0-\u18F5\u1900-\u191E\u1920-\u192B\u1930-\u193B\u1946-\u196D\u1970-\u1974\u1980-\u19AB\u19B0-\u19C9\u19D0-\u19DA\u1A00-\u1A1B\u1A20-\u1A5E\u1A60-\u1A7C\u1A7F-\u1A89\u1A90-\u1A99\u1AA7\u1AB0-\u1ABD\u1ABF-\u1ACE\u1B00-\u1B4C\u1B50-\u1B59\u1B6B-\u1B73\u1B80-\u1BF3\u1C00-\u1C37\u1C40-\u1C49\u1C4D-\u1C7D\u1C80-\u1C88\u1C90-\u1CBA\u1CBD-\u1CBF\u1CD0-\u1CD2\u1CD4-\u1CFA\u1D00-\u1F15\u1F18-\u1F1D\u1F20-\u1F45\u1F48-\u1F4D\u1F50-\u1F57\u1F59\u1F5B\u1F5D\u1F5F-\u1F7D\u1F80-\u1FB4\u1FB6-\u1FBC\u1FBE\u1FC2-\u1FC4\u1FC6-\u1FCC\u1FD0-\u1FD3\u1FD6-\u1FDB\u1FE0-\u1FEC\u1FF2-\u1FF4\u1FF6-\u1FFC\u203F\u2040\u2054\u2071\u207F\u2090-\u209C\u20D0-\u20DC\u20E1\u20E5-\u20F0\u2102\u2107\u210A-\u2113\u2115\u2118-\u211D\u2124\u2126\u2128\u212A-\u2139\u213C-\u213F\u2145-\u2149\u214E\u2160-\u2188\u2C00-\u2CE4\u2CEB-\u2CF3\u2D00-\u2D25\u2D27\u2D2D\u2D30-\u2D67\u2D6F\u2D7F-\u2D96\u2DA0-\u2DA6\u2DA8-\u2DAE\u2DB0-\u2DB6\u2DB8-\u2DBE\u2DC0-\u2DC6\u2DC8-\u2DCE\u2DD0-\u2DD6\u2DD8-\u2DDE\u2DE0-\u2DFF\u3005-\u3007\u3021-\u302F\u3031-\u3035\u3038-\u303C\u3041-\u3096\u3099\u309A\u309D-\u309F\u30A1-\u30FA\u30FC-\u30FF\u3105-\u312F\u3131-\u318E\u31A0-\u31BF\u31F0-\u31FF\u3400-\u4DBF\u4E00-\uA48C\uA4D0-\uA4FD\uA500-\uA60C\uA610-\uA62B\uA640-\uA66F\uA674-\uA67D\uA67F-\uA6F1\uA717-\uA71F\uA722-\uA788\uA78B-\uA7CA\uA7D0\uA7D1\uA7D3\uA7D5-\uA7D9\uA7F2-\uA827\uA82C\uA840-\uA873\uA880-\uA8C5\uA8D0-\uA8D9\uA8E0-\uA8F7\uA8FB\uA8FD-\uA92D\uA930-\uA953\uA960-\uA97C\uA980-\uA9C0\uA9CF-\uA9D9\uA9E0-\uA9FE\uAA00-\uAA36\uAA40-\uAA4D\uAA50-\uAA59\uAA60-\uAA76\uAA7A-\uAAC2\uAADB-\uAADD\uAAE0-\uAAEF\uAAF2-\uAAF6\uAB01-\uAB06\uAB09-\uAB0E\uAB11-\uAB16\uAB20-\uAB26\uAB28-\uAB2E\uAB30-\uAB5A\uAB5C-\uAB69\uAB70-\uABEA\uABEC\uABED\uABF0-\uABF9\uAC00-\uD7A3\uD7B0-\uD7C6\uD7CB-\uD7FB\uF900-\uFA6D\uFA70-\uFAD9\uFB00-\uFB06\uFB13-\uFB17\uFB1D-\uFB28\uFB2A-\uFB36\uFB38-\uFB3C\uFB3E\uFB40\uFB41\uFB43\uFB44\uFB46-\uFBB1\uFBD3-\uFC5D\uFC64-\uFD3D\uFD50-\uFD8F\uFD92-\uFDC7\uFDF0-\uFDF9\uFE00-\uFE0F\uFE20-\uFE2F\uFE33\uFE34\uFE4D-\uFE4F\uFE71\uFE73\uFE77\uFE79\uFE7B\uFE7D\uFE7F-\uFEFC\uFF10-\uFF19\uFF21-\uFF3A\uFF3F\uFF41-\uFF5A\uFF66-\uFFBE\uFFC2-\uFFC7\uFFCA-\uFFCF\uFFD2-\uFFD7\uFFDA-\uFFDC]|\uD800[\uDC00-\uDC0B\uDC0D-\uDC26\uDC28-\uDC3A\uDC3C\uDC3D\uDC3F-\uDC4D\uDC50-\uDC5D\uDC80-\uDCFA\uDD40-\uDD74\uDDFD\uDE80-\uDE9C\uDEA0-\uDED0\uDEE0\uDF00-\uDF1F\uDF2D-\uDF4A\uDF50-\uDF7A\uDF80-\uDF9D\uDFA0-\uDFC3\uDFC8-\uDFCF\uDFD1-\uDFD5]|\uD801[\uDC00-\uDC9D\uDCA0-\uDCA9\uDCB0-\uDCD3\uDCD8-\uDCFB\uDD00-\uDD27\uDD30-\uDD63\uDD70-\uDD7A\uDD7C-\uDD8A\uDD8C-\uDD92\uDD94\uDD95\uDD97-\uDDA1\uDDA3-\uDDB1\uDDB3-\uDDB9\uDDBB\uDDBC\uDE00-\uDF36\uDF40-\uDF55\uDF60-\uDF67\uDF80-\uDF85\uDF87-\uDFB0\uDFB2-\uDFBA]|\uD802[\uDC00-\uDC05\uDC08\uDC0A-\uDC35\uDC37\uDC38\uDC3C\uDC3F-\uDC55\uDC60-\uDC76\uDC80-\uDC9E\uDCE0-\uDCF2\uDCF4\uDCF5\uDD00-\uDD15\uDD20-\uDD39\uDD80-\uDDB7\uDDBE\uDDBF\uDE00-\uDE03\uDE05\uDE06\uDE0C-\uDE13\uDE15-\uDE17\uDE19-\uDE35\uDE38-\uDE3A\uDE3F\uDE60-\uDE7C\uDE80-\uDE9C\uDEC0-\uDEC7\uDEC9-\uDEE6\uDF00-\uDF35\uDF40-\uDF55\uDF60-\uDF72\uDF80-\uDF91]|\uD803[\uDC00-\uDC48\uDC80-\uDCB2\uDCC0-\uDCF2\uDD00-\uDD27\uDD30-\uDD39\uDE80-\uDEA9\uDEAB\uDEAC\uDEB0\uDEB1\uDEFD-\uDF1C\uDF27\uDF30-\uDF50\uDF70-\uDF85\uDFB0-\uDFC4\uDFE0-\uDFF6]|\uD804[\uDC00-\uDC46\uDC66-\uDC75\uDC7F-\uDCBA\uDCC2\uDCD0-\uDCE8\uDCF0-\uDCF9\uDD00-\uDD34\uDD36-\uDD3F\uDD44-\uDD47\uDD50-\uDD73\uDD76\uDD80-\uDDC4\uDDC9-\uDDCC\uDDCE-\uDDDA\uDDDC\uDE00-\uDE11\uDE13-\uDE37\uDE3E-\uDE41\uDE80-\uDE86\uDE88\uDE8A-\uDE8D\uDE8F-\uDE9D\uDE9F-\uDEA8\uDEB0-\uDEEA\uDEF0-\uDEF9\uDF00-\uDF03\uDF05-\uDF0C\uDF0F\uDF10\uDF13-\uDF28\uDF2A-\uDF30\uDF32\uDF33\uDF35-\uDF39\uDF3B-\uDF44\uDF47\uDF48\uDF4B-\uDF4D\uDF50\uDF57\uDF5D-\uDF63\uDF66-\uDF6C\uDF70-\uDF74]|\uD805[\uDC00-\uDC4A\uDC50-\uDC59\uDC5E-\uDC61\uDC80-\uDCC5\uDCC7\uDCD0-\uDCD9\uDD80-\uDDB5\uDDB8-\uDDC0\uDDD8-\uDDDD\uDE00-\uDE40\uDE44\uDE50-\uDE59\uDE80-\uDEB8\uDEC0-\uDEC9\uDF00-\uDF1A\uDF1D-\uDF2B\uDF30-\uDF39\uDF40-\uDF46]|\uD806[\uDC00-\uDC3A\uDCA0-\uDCE9\uDCFF-\uDD06\uDD09\uDD0C-\uDD13\uDD15\uDD16\uDD18-\uDD35\uDD37\uDD38\uDD3B-\uDD43\uDD50-\uDD59\uDDA0-\uDDA7\uDDAA-\uDDD7\uDDDA-\uDDE1\uDDE3\uDDE4\uDE00-\uDE3E\uDE47\uDE50-\uDE99\uDE9D\uDEB0-\uDEF8]|\uD807[\uDC00-\uDC08\uDC0A-\uDC36\uDC38-\uDC40\uDC50-\uDC59\uDC72-\uDC8F\uDC92-\uDCA7\uDCA9-\uDCB6\uDD00-\uDD06\uDD08\uDD09\uDD0B-\uDD36\uDD3A\uDD3C\uDD3D\uDD3F-\uDD47\uDD50-\uDD59\uDD60-\uDD65\uDD67\uDD68\uDD6A-\uDD8E\uDD90\uDD91\uDD93-\uDD98\uDDA0-\uDDA9\uDEE0-\uDEF6\uDF00-\uDF10\uDF12-\uDF3A\uDF3E-\uDF42\uDF50-\uDF59\uDFB0]|\uD808[\uDC00-\uDF99]|\uD809[\uDC00-\uDC6E\uDC80-\uDD43]|\uD80B[\uDF90-\uDFF0]|[\uD80C\uD81C-\uD820\uD822\uD840-\uD868\uD86A-\uD86C\uD86F-\uD872\uD874-\uD879\uD880-\uD883\uD885-\uD887][\uDC00-\uDFFF]|\uD80D[\uDC00-\uDC2F\uDC40-\uDC55]|\uD811[\uDC00-\uDE46]|\uD81A[\uDC00-\uDE38\uDE40-\uDE5E\uDE60-\uDE69\uDE70-\uDEBE\uDEC0-\uDEC9\uDED0-\uDEED\uDEF0-\uDEF4\uDF00-\uDF36\uDF40-\uDF43\uDF50-\uDF59\uDF63-\uDF77\uDF7D-\uDF8F]|\uD81B[\uDE40-\uDE7F\uDF00-\uDF4A\uDF4F-\uDF87\uDF8F-\uDF9F\uDFE0\uDFE1\uDFE3\uDFE4\uDFF0\uDFF1]|\uD821[\uDC00-\uDFF7]|\uD823[\uDC00-\uDCD5\uDD00-\uDD08]|\uD82B[\uDFF0-\uDFF3\uDFF5-\uDFFB\uDFFD\uDFFE]|\uD82C[\uDC00-\uDD22\uDD32\uDD50-\uDD52\uDD55\uDD64-\uDD67\uDD70-\uDEFB]|\uD82F[\uDC00-\uDC6A\uDC70-\uDC7C\uDC80-\uDC88\uDC90-\uDC99\uDC9D\uDC9E]|\uD833[\uDF00-\uDF2D\uDF30-\uDF46]|\uD834[\uDD65-\uDD69\uDD6D-\uDD72\uDD7B-\uDD82\uDD85-\uDD8B\uDDAA-\uDDAD\uDE42-\uDE44]|\uD835[\uDC00-\uDC54\uDC56-\uDC9C\uDC9E\uDC9F\uDCA2\uDCA5\uDCA6\uDCA9-\uDCAC\uDCAE-\uDCB9\uDCBB\uDCBD-\uDCC3\uDCC5-\uDD05\uDD07-\uDD0A\uDD0D-\uDD14\uDD16-\uDD1C\uDD1E-\uDD39\uDD3B-\uDD3E\uDD40-\uDD44\uDD46\uDD4A-\uDD50\uDD52-\uDEA5\uDEA8-\uDEC0\uDEC2-\uDEDA\uDEDC-\uDEFA\uDEFC-\uDF14\uDF16-\uDF34\uDF36-\uDF4E\uDF50-\uDF6E\uDF70-\uDF88\uDF8A-\uDFA8\uDFAA-\uDFC2\uDFC4-\uDFCB\uDFCE-\uDFFF]|\uD836[\uDE00-\uDE36\uDE3B-\uDE6C\uDE75\uDE84\uDE9B-\uDE9F\uDEA1-\uDEAF]|\uD837[\uDF00-\uDF1E\uDF25-\uDF2A]|\uD838[\uDC00-\uDC06\uDC08-\uDC18\uDC1B-\uDC21\uDC23\uDC24\uDC26-\uDC2A\uDC30-\uDC6D\uDC8F\uDD00-\uDD2C\uDD30-\uDD3D\uDD40-\uDD49\uDD4E\uDE90-\uDEAE\uDEC0-\uDEF9]|\uD839[\uDCD0-\uDCF9\uDFE0-\uDFE6\uDFE8-\uDFEB\uDFED\uDFEE\uDFF0-\uDFFE]|\uD83A[\uDC00-\uDCC4\uDCD0-\uDCD6\uDD00-\uDD4B\uDD50-\uDD59]|\uD83B[\uDE00-\uDE03\uDE05-\uDE1F\uDE21\uDE22\uDE24\uDE27\uDE29-\uDE32\uDE34-\uDE37\uDE39\uDE3B\uDE42\uDE47\uDE49\uDE4B\uDE4D-\uDE4F\uDE51\uDE52\uDE54\uDE57\uDE59\uDE5B\uDE5D\uDE5F\uDE61\uDE62\uDE64\uDE67-\uDE6A\uDE6C-\uDE72\uDE74-\uDE77\uDE79-\uDE7C\uDE7E\uDE80-\uDE89\uDE8B-\uDE9B\uDEA1-\uDEA3\uDEA5-\uDEA9\uDEAB-\uDEBB]|\uD83E[\uDFF0-\uDFF9]|\uD869[\uDC00-\uDEDF\uDF00-\uDFFF]|\uD86D[\uDC00-\uDF39\uDF40-\uDFFF]|\uD86E[\uDC00-\uDC1D\uDC20-\uDFFF]|\uD873[\uDC00-\uDEA1\uDEB0-\uDFFF]|\uD87A[\uDC00-\uDFE0]|\uD87E[\uDC00-\uDE1D]|\uD884[\uDC00-\uDF4A\uDF50-\uDFFF]|\uD888[\uDC00-\uDFAF]|\uDB40[\uDD00-\uDDEF])*/,
        i = ["and", "as", "assert", "async", "await", "break", "case", "class", "continue", "def", "del", "elif", "else", "except", "finally", "for", "from", "global", "if", "import", "in", "is", "lambda", "match", "nonlocal|10", "not", "or", "pass", "raise", "return", "try", "while", "with", "yield"],
        s = {
          $pattern: /[A-Za-z]\w+|__\w+__/,
          keyword: i,
          built_in: ["__import__", "abs", "all", "any", "ascii", "bin", "bool", "breakpoint", "bytearray", "bytes", "callable", "chr", "classmethod", "compile", "complex", "delattr", "dict", "dir", "divmod", "enumerate", "eval", "exec", "filter", "float", "format", "frozenset", "getattr", "globals", "hasattr", "hash", "help", "hex", "id", "input", "int", "isinstance", "issubclass", "iter", "len", "list", "locals", "map", "max", "memoryview", "min", "next", "object", "oct", "open", "ord", "pow", "print", "property", "range", "repr", "reversed", "round", "set", "setattr", "slice", "sorted", "staticmethod", "str", "sum", "super", "tuple", "type", "vars", "zip"],
          literal: ["__debug__", "Ellipsis", "False", "None", "NotImplemented", "True"],
          type: ["Any", "Callable", "Coroutine", "Dict", "List", "Literal", "Generic", "Optional", "Sequence", "Set", "Tuple", "Type", "Union"]
        },
        t = {
          className: "meta",
          begin: /^(>>>|\.\.\.) /
        },
        r = {
          className: "subst",
          begin: /\{/,
          end: /\}/,
          keywords: s,
          illegal: /#/
        },
        l = {
          begin: /\{\{/,
          relevance: 0
        },
        b = {
          className: "string",
          contains: [e.BACKSLASH_ESCAPE],
          variants: [{
            begin: /([uU]|[bB]|[rR]|[bB][rR]|[rR][bB])?'''/,
            end: /'''/,
            contains: [e.BACKSLASH_ESCAPE, t],
            relevance: 10
          }, {
            begin: /([uU]|[bB]|[rR]|[bB][rR]|[rR][bB])?"""/,
            end: /"""/,
            contains: [e.BACKSLASH_ESCAPE, t],
            relevance: 10
          }, {
            begin: /([fF][rR]|[rR][fF]|[fF])'''/,
            end: /'''/,
            contains: [e.BACKSLASH_ESCAPE, t, l, r]
          }, {
            begin: /([fF][rR]|[rR][fF]|[fF])"""/,
            end: /"""/,
            contains: [e.BACKSLASH_ESCAPE, t, l, r]
          }, {
            begin: /([uU]|[rR])'/,
            end: /'/,
            relevance: 10
          }, {
            begin: /([uU]|[rR])"/,
            end: /"/,
            relevance: 10
          }, {
            begin: /([bB]|[bB][rR]|[rR][bB])'/,
            end: /'/
          }, {
            begin: /([bB]|[bB][rR]|[rR][bB])"/,
            end: /"/
          }, {
            begin: /([fF][rR]|[rR][fF]|[fF])'/,
            end: /'/,
            contains: [e.BACKSLASH_ESCAPE, l, r]
          }, {
            begin: /([fF][rR]|[rR][fF]|[fF])"/,
            end: /"/,
            contains: [e.BACKSLASH_ESCAPE, l, r]
          }, e.APOS_STRING_MODE, e.QUOTE_STRING_MODE]
        },
        o = "[0-9](_?[0-9])*",
        c = "(\\b(".concat(o, "))?\\.(").concat(o, ")|\\b(").concat(o, ")\\."),
        d = "\\b|" + i.join("|"),
        g = {
          className: "number",
          relevance: 0,
          variants: [{
            begin: "(\\b(".concat(o, ")|(").concat(c, "))[eE][+-]?(").concat(o, ")[jJ]?(?=").concat(d, ")")
          }, {
            begin: "(".concat(c, ")[jJ]?")
          }, {
            begin: "\\b([1-9](_?[0-9])*|0+(_?0)*)[lLjJ]?(?=".concat(d, ")")
          }, {
            begin: "\\b0[bB](_?[01])+[lL]?(?=".concat(d, ")")
          }, {
            begin: "\\b0[oO](_?[0-7])+[lL]?(?=".concat(d, ")")
          }, {
            begin: "\\b0[xX](_?[0-9a-fA-F])+[lL]?(?=".concat(d, ")")
          }, {
            begin: "\\b(".concat(o, ")[jJ](?=").concat(d, ")")
          }]
        },
        p = {
          className: "comment",
          begin: n.lookahead(/# type:/),
          end: /$/,
          keywords: s,
          contains: [{
            begin: /# type:/
          }, {
            begin: /#/,
            end: /\b\B/,
            endsWithParent: !0
          }]
        },
        m = {
          className: "params",
          variants: [{
            className: "",
            begin: /\(\s*\)/,
            skip: !0
          }, {
            begin: /\(/,
            end: /\)/,
            excludeBegin: !0,
            excludeEnd: !0,
            keywords: s,
            contains: ["self", t, g, b, e.HASH_COMMENT_MODE]
          }]
        };
      return r.contains = [b, g, t], {
        name: "Python",
        aliases: ["py", "gyp", "ipython"],
        unicodeRegex: !0,
        keywords: s,
        illegal: /(<\/|->|\?)|=>/,
        contains: [t, g, {
          begin: /\bself\b/
        }, {
          beginKeywords: "if",
          relevance: 0
        }, b, p, e.HASH_COMMENT_MODE, {
          match: [/\bdef/, /\s+/, a],
          scope: {
            1: "keyword",
            3: "title.function"
          },
          contains: [m]
        }, {
          variants: [{
            match: [/\bclass/, /\s+/, a, /\s*/, /\(\s*/, a, /\s*\)/]
          }, {
            match: [/\bclass/, /\s+/, a]
          }],
          scope: {
            1: "keyword",
            3: "title.class",
            6: "title.class.inherited"
          }
        }, {
          className: "meta",
          begin: /^[\t ]*@/,
          end: /(?=#)|$/,
          contains: [g, m, b]
        }]
      };
    };
  }();
  hljs.registerLanguage("python", e);
})();
"use strict";

(function () {
  // HighlightJS
  hljs.addPlugin(new CopyButtonPlugin());
  hljs.highlightAll();

  // Tabs
  var rows = document.querySelectorAll("#gsk-scan .gsk-issue");
  rows.forEach(function (rowEl) {
    {
      rowEl.addEventListener("click", function (event) {
        {
          event.preventDefault();
          if (event.target.classList.contains("gsk-debug")) {
            {
              alert("Not implemented yet");
              return;
            }
          }
          rowEl.classList.toggle("open");
          rowEl.classList.toggle("bg-zinc-700");
        }
      });
    }
  });
  var tabs = document.querySelectorAll("#gsk-scan [role='tabpanel']");
  var tabHeaders = document.querySelectorAll("#gsk-scan [data-tab-target]");
  tabHeaders.forEach(function (tabHeader) {
    tabHeader.addEventListener("click", function (event) {
      event.preventDefault();
      var tabId = tabHeader.getAttribute("data-tab-target");
      tabs.forEach(function (tab) {
        tab.classList.add("hidden");
      });
      tabHeaders.forEach(function (tabh) {
        tabh.classList.remove("active");
      });
      tabHeader.classList.add("active");
      document.getElementById(tabId).classList.remove("hidden");
    });
  });
})();