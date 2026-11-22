// Phone menu: the button opens and closes the panel; Escape, a link or a wider window closes it.
(function () {
  var header = document.querySelector(".site");
  var button = document.querySelector(".menu-btn");
  if (!header || !button) return;
  function set(open) {
    header.classList.toggle("open", open);
    button.setAttribute("aria-expanded", open ? "true" : "false");
  }
  button.addEventListener("click", function () { set(!header.classList.contains("open")); });
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

// Theme: System follows the device; Light or Dark is saved in this browser and applied by the head script on every page.
(function () {
  var group = document.querySelector(".theme-switch");
  if (!group) return;
  var root = document.documentElement;
  var buttons = group.querySelectorAll("button");
  function show(choice) {
    buttons.forEach(function (b) { b.setAttribute("aria-pressed", b.getAttribute("data-theme-choice") === choice ? "true" : "false"); });
  }
  buttons.forEach(function (b) {
    b.addEventListener("click", function () {
      var choice = b.getAttribute("data-theme-choice");
      if (choice === "system") root.removeAttribute("data-theme"); else root.setAttribute("data-theme", choice);
      try { if (choice === "system") localStorage.removeItem("theme"); else localStorage.setItem("theme", choice); } catch (e) {}
      show(choice);
    });
  });
  var saved = root.getAttribute("data-theme");
  show(saved === "light" || saved === "dark" ? saved : "system");
  group.hidden = false;
})();
