/* BloodLink progressive enhancements */
document.addEventListener("DOMContentLoaded", function () {
  // Mobile navigation
  var toggle = document.querySelector("[data-nav-toggle]");
  var nav = document.getElementById("primary-nav");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

  // Dismiss flash messages
  document.querySelectorAll("[data-dismiss]").forEach(function (button) {
    button.addEventListener("click", function () {
      var flash = button.closest(".flash");
      if (flash) flash.remove();
    });
  });

  // Auto-dismiss info/success flashes
  window.setTimeout(function () {
    document.querySelectorAll(".flash-success, .flash-info").forEach(function (flash) {
      flash.style.transition = "opacity .35s ease";
      flash.style.opacity = "0";
      window.setTimeout(function () { flash.remove(); }, 400);
    });
  }, 7000);

  // Confirmation for destructive actions
  document.querySelectorAll("form[data-confirm]").forEach(function (form) {
    form.addEventListener("submit", function (event) {
      if (!window.confirm(form.getAttribute("data-confirm"))) event.preventDefault();
    });
  });

  // Show / hide password controls
  document.querySelectorAll('input[type="password"]').forEach(function (input) {
    if (input.closest(".password-wrap")) return;
    var wrap = document.createElement("div");
    wrap.className = "password-wrap";
    input.parentNode.insertBefore(wrap, input);
    wrap.appendChild(input);

    var button = document.createElement("button");
    button.type = "button";
    button.className = "password-toggle";
    button.textContent = "Show";
    button.setAttribute("aria-label", "Show password");
    wrap.appendChild(button);

    button.addEventListener("click", function () {
      var showing = input.getAttribute("type") === "text";
      input.setAttribute("type", showing ? "password" : "text");
      button.textContent = showing ? "Show" : "Hide";
      button.setAttribute("aria-label", showing ? "Show password" : "Hide password");
    });
  });

  // Auto-submit filter forms
  document.querySelectorAll("form[data-auto-submit]").forEach(function (form) {
    form.querySelectorAll("select, input[type='checkbox']").forEach(function (element) {
      element.addEventListener("change", function () { form.requestSubmit(); });
    });
  });

  // Countdown labels for request cards
  document.querySelectorAll("[data-needed-by]").forEach(function (element) {
    var target = new Date(element.getAttribute("data-needed-by"));
    if (isNaN(target.getTime())) return;
    var diff = target.getTime() - Date.now();
    if (diff <= 0) {
      element.textContent = "Needed by has passed";
      return;
    }
    var hours = Math.floor(diff / 3600000);
    var days = Math.floor(hours / 24);
    element.textContent = days > 0 ? "in " + days + "d " + (hours % 24) + "h" : "in " + hours + "h";
  });
});
