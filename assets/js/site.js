// Phone menu: the button opens and closes the panel; Escape, a link or a wider window closes it.
(function () {
  var header = document.querySelector(".site");
  var button = document.querySelector(".menu-btn");
  if (!header || !button) return;
  function set(open) {
    header.classList.toggle("open", open);
    button.setAttribute("aria-expanded", open ? "true" : "false");
  }
  button.addEventListener("click", function () {
    var open = !header.classList.contains("open");
    set(open);
    // The links come before the button in the page, so focus moves into the opened menu.
    if (open) { var first = header.querySelector(".menu a"); if (first) first.focus(); }
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && header.classList.contains("open")) { set(false); button.focus(); }
  });
  document.addEventListener("click", function (e) {
    if (header.classList.contains("open") && !header.contains(e.target)) set(false);
  });
  header.querySelectorAll(".menu a").forEach(function (a) { a.addEventListener("click", function () { set(false); }); });
  window.matchMedia("(min-width: 44rem)").addEventListener("change", function (m) { if (m.matches) set(false); });
})();

// Products: workflow areas start closed on phones so the list scans, and open on wide screens; each can be toggled.
(function () {
  var groups = document.querySelectorAll(".groups details.group");
  if (!groups.length) return;
  var narrow = window.matchMedia("(max-width: 52rem)");
  function apply() { groups.forEach(function (d) { d.open = !narrow.matches; }); }
  apply();
  narrow.addEventListener("change", apply);
})();

// Theme: one button flips light and dark. A choice that matches the device is not saved,
// so the site goes back to following the device; any other choice is saved in this browser
// and applied by the head script on every page.
(function () {
  var button = document.querySelector(".theme-toggle");
  if (!button) return;
  var root = document.documentElement;
  var system = window.matchMedia("(prefers-color-scheme: dark)");
  function current() {
    var t = root.getAttribute("data-theme");
    return t === "light" || t === "dark" ? t : (system.matches ? "dark" : "light");
  }
  function show() { button.setAttribute("aria-pressed", current() === "dark" ? "true" : "false"); }
  button.addEventListener("click", function () {
    var next = current() === "dark" ? "light" : "dark";
    var follow = next === (system.matches ? "dark" : "light");
    if (follow) root.removeAttribute("data-theme"); else root.setAttribute("data-theme", next);
    var meta = document.querySelector('meta[name="color-scheme"]');
    if (meta) meta.setAttribute("content", follow ? "light dark" : next);
    try { if (follow) localStorage.removeItem("theme"); else localStorage.setItem("theme", next); } catch (e) {}
    show();
  });
  // The device changed while the page is open: a saved choice it now matches is dropped.
  system.addEventListener("change", function () {
    var t = root.getAttribute("data-theme");
    if (t && t === (system.matches ? "dark" : "light")) {
      root.removeAttribute("data-theme");
      var meta = document.querySelector('meta[name="color-scheme"]');
      if (meta) meta.setAttribute("content", "light dark");
      try { localStorage.removeItem("theme"); } catch (e) {}
    }
    show();
  });
  show();
  button.hidden = false;
})();
