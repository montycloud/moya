/* MOYA site — tiny vanilla helpers. No dependencies, no build. */
(function () {
  "use strict";

  // ── Mobile nav ────────────────────────────────────────────────────────────
  var toggle = document.querySelector(".nav-toggle");
  var links = document.querySelector(".nav-links");
  if (toggle && links) {
    toggle.addEventListener("click", function () {
      links.classList.toggle("open");
    });
    links.addEventListener("click", function (e) {
      if (e.target.tagName === "A") links.classList.remove("open");
    });
  }

  // ── Copy to clipboard ─────────────────────────────────────────────────────
  function copyText(text, btn) {
    var done = function () {
      var label = btn.textContent;
      btn.textContent = "Copied";
      btn.classList.add("copied");
      setTimeout(function () {
        btn.textContent = label;
        btn.classList.remove("copied");
      }, 1400);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done, function () {});
    } else {
      var ta = document.createElement("textarea");
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      try { document.execCommand("copy"); done(); } catch (e) {}
      document.body.removeChild(ta);
    }
  }

  document.querySelectorAll(".copy-btn").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var text = btn.getAttribute("data-copy");
      if (!text) {
        var card = btn.closest(".code") || btn.closest(".install");
        var el = card && (card.querySelector("pre") || card.querySelector("code"));
        text = el ? el.textContent : "";
      }
      copyText(text.trim(), btn);
    });
  });

  // ── Minimal Python syntax highlighter ─────────────────────────────────────
  var KEYWORDS = /^(?:from|import|def|return|for|in|if|elif|else|class|with|as|lambda|None|True|False|and|or|not|while|try|except|finally|raise|pass|yield|await|async|is|global|assert)\b/;
  var PATTERNS = [
    ["com", /^#[^\n]*/],
    ["str", /^(?:"""[\s\S]*?"""|'''[\s\S]*?'''|"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')/],
    ["num", /^\b\d+(?:\.\d+)?\b/],
    ["kw", KEYWORDS],
    ["fn", /^[A-Za-z_]\w*(?=\s*\()/],
    ["cls", /^[A-Z][A-Za-z0-9_]*\b/],
    ["word", /^[A-Za-z_]\w*/]
  ];
  function esc(s) {
    return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }
  function highlight(src) {
    var out = "", i = 0;
    while (i < src.length) {
      var rest = src.slice(i), matched = false;
      for (var p = 0; p < PATTERNS.length; p++) {
        var cls = PATTERNS[p][0], m = PATTERNS[p][1].exec(rest);
        if (m) {
          if (cls === "word") out += esc(m[0]);
          else out += '<span class="tok-' + cls + '">' + esc(m[0]) + "</span>";
          i += m[0].length; matched = true; break;
        }
      }
      if (!matched) { out += esc(src[i]); i++; }
    }
    return out;
  }
  document.querySelectorAll('code[data-lang="python"]').forEach(function (code) {
    code.innerHTML = highlight(code.textContent);
  });

  // ── Learn page: TOC scroll-spy ────────────────────────────────────────────
  var tocLinks = Array.prototype.slice.call(document.querySelectorAll(".toc a"));
  if (tocLinks.length && "IntersectionObserver" in window) {
    var map = {};
    tocLinks.forEach(function (a) {
      var id = a.getAttribute("href").slice(1);
      var sec = document.getElementById(id);
      if (sec) map[id] = a;
    });
    var current = null;
    var obs = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) {
          if (current) current.classList.remove("active");
          current = map[en.target.id];
          if (current) current.classList.add("active");
        }
      });
    }, { rootMargin: "-80px 0px -70% 0px", threshold: 0 });
    Object.keys(map).forEach(function (id) {
      obs.observe(document.getElementById(id));
    });
  }
})();
