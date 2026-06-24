(function () {
  if (window.__aiSkiftetAudioContinuity) return;

  var STORAGE_KEY = "ai-skiftet.audio-continuity.v1";
  var CSS_HREF = "/audio-continuity.css";
  var SCRIPT_SRC = "/audio-continuity.js";
  var root = null;
  var player = null;
  var playerTitle = null;
  var playerNote = null;
  var globalAudio = null;
  var activeSource = "";
  var activeTitle = "";
  var activeNote = "";
  var lastSaveAt = 0;
  var navigating = false;

  window.__aiSkiftetAudioContinuity = {
    save: saveState,
    sync: syncInlineAudioState,
  };

  function onReady(callback) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", callback, { once: true });
    } else {
      callback();
    }
  }

  function init() {
    ensureHeadAssets();
    ensurePageRoot();
    ensurePlayer();
    restoreState();
    bindDocumentEvents();
    syncInlineAudioState();
  }

  function ensureHeadAssets() {
    if (!document.querySelector('link[data-audio-continuity="css"]')) {
      var css = document.createElement("link");
      css.rel = "stylesheet";
      css.href = CSS_HREF;
      css.setAttribute("data-audio-continuity", "css");
      document.head.appendChild(css);
    }

    if (!document.querySelector('script[data-audio-continuity="js"]')) {
      var script = document.createElement("script");
      script.defer = true;
      script.src = SCRIPT_SRC;
      script.setAttribute("data-audio-continuity", "js");
      document.head.appendChild(script);
    }
  }

  function ensurePageRoot() {
    root = document.getElementById("audio-page-root");
    if (root) return root;

    root = document.createElement("div");
    root.id = "audio-page-root";

    while (document.body.firstChild) {
      root.appendChild(document.body.firstChild);
    }
    document.body.appendChild(root);
    return root;
  }

  function ensurePlayer() {
    player = document.getElementById("audio-continuity-player");
    if (!player) {
      player = document.createElement("div");
      player.id = "audio-continuity-player";
      player.className = "audio-continuity";
      player.setAttribute("role", "region");
      player.setAttribute("aria-label", "Audio player");
      player.innerHTML =
        '<div class="audio-continuity__inner">' +
        '<div class="audio-continuity__meta">' +
        '<div class="audio-continuity__eyebrow">AI-skiftet audio</div>' +
        '<div class="audio-continuity__title"></div>' +
        '<div class="audio-continuity__note"></div>' +
        "</div>" +
        '<audio class="audio-continuity__audio" controls preload="metadata" data-audio-continuity-ignore="true"></audio>' +
        '<button class="audio-continuity__close" type="button" aria-label="Close player">x</button>' +
        "</div>";
      document.body.appendChild(player);
    }

    playerTitle = player.querySelector(".audio-continuity__title");
    playerNote = player.querySelector(".audio-continuity__note");
    globalAudio = player.querySelector("audio");

    if (globalAudio.dataset.audioContinuityBound !== "true") {
      globalAudio.dataset.audioContinuityBound = "true";
      globalAudio.addEventListener("play", function () {
        showPlayer();
        saveState();
        updateMediaSession();
      });
      globalAudio.addEventListener("pause", saveState);
      globalAudio.addEventListener("ended", saveState);
      globalAudio.addEventListener("timeupdate", throttledSave);
    }

    var closeButton = player.querySelector(".audio-continuity__close");
    if (closeButton.dataset.audioContinuityBound !== "true") {
      closeButton.dataset.audioContinuityBound = "true";
      closeButton.addEventListener("click", function () {
        globalAudio.pause();
        activeSource = "";
        activeTitle = "";
        activeNote = "";
        try {
          sessionStorage.removeItem(STORAGE_KEY);
        } catch (error) {}
        hidePlayer();
      });
    }
  }

  function bindDocumentEvents() {
    if (document.documentElement.dataset.audioContinuityBound === "true") return;
    document.documentElement.dataset.audioContinuityBound = "true";

    document.addEventListener("play", onNativeAudioPlay, true);
    document.addEventListener("click", onDocumentClick, true);
    document.addEventListener("keydown", onDocumentKeyDown, true);
    window.addEventListener("beforeunload", saveState);
    window.addEventListener("popstate", function () {
      if (activeSource) {
        softNavigate(window.location.href, { replace: true });
      } else {
        window.location.reload();
      }
    });
  }

  function onNativeAudioPlay(event) {
    var nativeAudio = event.target;
    if (!nativeAudio || nativeAudio.tagName !== "AUDIO" || nativeAudio === globalAudio) return;
    if (nativeAudio.dataset.audioContinuityIgnore === "true") return;

    activateNativeAudio(nativeAudio);
  }

  function activateNativeAudio(nativeAudio) {
    var source = getAudioSource(nativeAudio);
    if (!source) return;

    var meta = getAudioMeta(nativeAudio);
    var startAt = nativeAudio.currentTime || 0;
    if (source === activeSource && globalAudio && globalAudio.currentTime > startAt) {
      startAt = globalAudio.currentTime;
    }

    nativeAudio.pause();
    setGlobalSource(source, meta, startAt);
    globalAudio.play().catch(function () {
      saveState();
    });
  }

  function onDocumentClick(event) {
    var nativeAudio = event.target.closest ? event.target.closest("audio") : null;
    if (nativeAudio && nativeAudio !== globalAudio && nativeAudio.dataset.audioContinuityIgnore !== "true") {
      event.preventDefault();
      event.stopPropagation();
      activateNativeAudio(nativeAudio);
      return;
    }

    if (!activeSource) return;
    if (event.defaultPrevented || event.button !== 0) return;
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;

    var link = event.target.closest ? event.target.closest("a[href]") : null;
    if (!link || !document.documentElement.contains(link)) return;
    if (link.target && link.target !== "_self") return;
    if (link.hasAttribute("download") || link.dataset.noAudioContinuity === "true") return;

    var targetUrl;
    try {
      targetUrl = new URL(link.getAttribute("href"), window.location.href);
    } catch (error) {
      return;
    }

    if (!shouldSoftNavigate(targetUrl)) return;
    event.preventDefault();
    softNavigate(targetUrl.href);
  }

  function onDocumentKeyDown(event) {
    if (event.key !== " " && event.key !== "Enter") return;
    var nativeAudio = event.target && event.target.closest ? event.target.closest("audio") : null;
    if (!nativeAudio || nativeAudio === globalAudio || nativeAudio.dataset.audioContinuityIgnore === "true") return;

    event.preventDefault();
    event.stopPropagation();
    activateNativeAudio(nativeAudio);
  }

  function shouldSoftNavigate(url) {
    if (url.origin !== window.location.origin) return false;
    if (url.protocol !== "http:" && url.protocol !== "https:") return false;

    var sameDocument =
      url.pathname === window.location.pathname &&
      url.search === window.location.search;
    if (sameDocument) return false;

    var filename = url.pathname.split("/").pop();
    if (!filename || filename.indexOf(".") === -1) return true;
    return /\.html?$/i.test(filename);
  }

  function softNavigate(href, options) {
    if (navigating) return Promise.resolve();
    navigating = true;
    saveState();

    var targetUrl = new URL(href, window.location.href);
    var fetchUrl = new URL(targetUrl.href);
    fetchUrl.hash = "";
    document.body.classList.add("audio-continuity-loading");

    return fetch(fetchUrl.href, {
      credentials: "same-origin",
      headers: { "X-Requested-With": "ai-skiftet-audio-continuity" },
    })
      .then(function (response) {
        var contentType = response.headers.get("content-type") || "";
        if (!response.ok || contentType.indexOf("text/html") === -1) {
          throw new Error("Not an HTML page");
        }
        return response.text();
      })
      .then(function (html) {
        var nextDocument = new DOMParser().parseFromString(html, "text/html");
        if (!nextDocument.body || !nextDocument.head) throw new Error("Invalid HTML");

        if (options && options.replace) {
          history.replaceState({ audioContinuity: true }, "", targetUrl.href);
        } else {
          history.pushState({ audioContinuity: true }, "", targetUrl.href);
        }

        document.documentElement.lang = nextDocument.documentElement.lang || document.documentElement.lang;
        document.head.innerHTML = nextDocument.head.innerHTML;
        ensureHeadAssets();
        document.title = nextDocument.title || document.title;

        ensurePageRoot();
        root.innerHTML = nextDocument.body.innerHTML;
        runInsertedScripts(root);
        ensurePlayer();
        showPlayer();
        syncInlineAudioState();
        scrollToTarget(targetUrl.hash);
      })
      .catch(function () {
        window.location.href = targetUrl.href;
      })
      .finally(function () {
        navigating = false;
        document.body.classList.remove("audio-continuity-loading");
      });
  }

  function runInsertedScripts(container) {
    Array.prototype.slice.call(container.querySelectorAll("script")).forEach(function (oldScript) {
      var script = document.createElement("script");
      Array.prototype.slice.call(oldScript.attributes).forEach(function (attr) {
        script.setAttribute(attr.name, attr.value);
      });
      script.textContent = oldScript.textContent;
      oldScript.replaceWith(script);
    });
  }

  function scrollToTarget(hash) {
    if (!hash) {
      window.scrollTo({ top: 0, left: 0, behavior: "auto" });
      return;
    }

    var id = decodeURIComponent(hash.slice(1));
    var target = document.getElementById(id) || document.querySelector('[name="' + cssEscape(id) + '"]');
    if (target) {
      target.scrollIntoView();
    } else {
      window.scrollTo({ top: 0, left: 0, behavior: "auto" });
    }
  }

  function cssEscape(value) {
    if (window.CSS && typeof window.CSS.escape === "function") return window.CSS.escape(value);
    return String(value).replace(/"/g, '\\"');
  }

  function getAudioSource(audio) {
    var source = audio.currentSrc || audio.getAttribute("src");
    if (!source) {
      var sourceNode = audio.querySelector("source[src]");
      if (sourceNode) source = sourceNode.getAttribute("src");
    }
    if (!source) return "";
    return new URL(source, document.baseURI).href;
  }

  function getAudioMeta(audio) {
    var region = audio.closest(".news-audio") || audio.parentElement;
    var titleNode = region ? region.querySelector(".news-audio__title") : null;
    var noteNode = region ? region.querySelector(".news-audio__note") : null;
    return {
      title: cleanText(titleNode ? titleNode.textContent : "") || audio.getAttribute("aria-label") || document.title || "AI-skiftet audio",
      note: cleanText(noteNode ? noteNode.textContent : ""),
    };
  }

  function cleanText(value) {
    return String(value || "").replace(/\s+/g, " ").trim();
  }

  function setGlobalSource(source, meta, startAt) {
    activeSource = source;
    activeTitle = meta && meta.title ? meta.title : document.title || "AI-skiftet audio";
    activeNote = meta && meta.note ? meta.note : "";

    if (globalAudio.src !== source) {
      globalAudio.src = source;
      globalAudio.load();
    }

    setGlobalTime(startAt || 0);
    updatePlayerText();
    showPlayer();
    updateMediaSession();
    saveState();
  }

  function setGlobalTime(seconds) {
    if (!seconds || !isFinite(seconds)) return;

    function applyTime() {
      try {
        if (Math.abs(globalAudio.currentTime - seconds) > 0.5) {
          globalAudio.currentTime = seconds;
        }
      } catch (error) {}
    }

    if (globalAudio.readyState >= 1) {
      applyTime();
    } else {
      globalAudio.addEventListener("loadedmetadata", applyTime, { once: true });
    }
  }

  function updatePlayerText() {
    if (playerTitle) playerTitle.textContent = activeTitle || "AI-skiftet audio";
    if (playerNote) playerNote.textContent = activeNote || "";
  }

  function showPlayer() {
    if (!player || !activeSource) return;
    player.classList.add("is-visible");
    document.body.classList.add("audio-continuity-active");
  }

  function hidePlayer() {
    if (player) player.classList.remove("is-visible");
    document.body.classList.remove("audio-continuity-active");
  }

  function saveState() {
    if (!globalAudio || !activeSource) return;
    try {
      sessionStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({
          src: activeSource,
          title: activeTitle,
          note: activeNote,
          currentTime: globalAudio.currentTime || 0,
          paused: globalAudio.paused,
          pageHref: window.location.href,
          updatedAt: Date.now(),
        }),
      );
    } catch (error) {}
  }

  function throttledSave() {
    var now = Date.now();
    if (now - lastSaveAt < 1000) return;
    lastSaveAt = now;
    saveState();
    syncInlineAudioState();
  }

  function restoreState() {
    if (activeSource || !globalAudio) return;

    var state;
    try {
      state = JSON.parse(sessionStorage.getItem(STORAGE_KEY) || "null");
    } catch (error) {
      state = null;
    }
    if (!state || !state.src) return;

    setGlobalSource(
      state.src,
      { title: state.title || "AI-skiftet audio", note: state.note || "" },
      state.currentTime || 0,
    );

    if (state.paused === false) {
      globalAudio.play().catch(function () {
        saveState();
      });
    }
  }

  function syncInlineAudioState() {
    if (!root || !globalAudio || !activeSource) return;
    Array.prototype.slice.call(root.querySelectorAll("audio")).forEach(function (audio) {
      if (audio === globalAudio || audio.dataset.audioContinuityIgnore === "true") return;
      if (getAudioSource(audio) !== activeSource) return;

      function syncTime() {
        try {
          if (Math.abs(audio.currentTime - globalAudio.currentTime) > 1) {
            audio.currentTime = globalAudio.currentTime || 0;
          }
        } catch (error) {}
      }

      if (audio.readyState >= 1) {
        syncTime();
      } else {
        audio.addEventListener("loadedmetadata", syncTime, { once: true });
      }
    });
  }

  function updateMediaSession() {
    if (!("mediaSession" in navigator) || !activeSource) return;

    try {
      navigator.mediaSession.metadata = new MediaMetadata({
        title: activeTitle || "AI-skiftet audio",
        artist: "AI-skiftet",
        album: activeNote || "ai-skiftet.se",
      });
    } catch (error) {}
  }

  onReady(init);
})();
