/* Progressive enhancement only: the application is fully usable without JS. */
(function () {
  "use strict";

  // Ask before destructive actions (revoke, deactivate).
  document.querySelectorAll("form[data-confirm]").forEach(function (form) {
    form.addEventListener("submit", function (event) {
      if (!window.confirm(form.getAttribute("data-confirm"))) {
        event.preventDefault();
      }
    });
  });

  // Toggle disclosure panels such as the revoke form.
  document.querySelectorAll("[data-toggle-target]").forEach(function (button) {
    button.addEventListener("click", function () {
      var target = document.getElementById(button.getAttribute("data-toggle-target"));
      if (!target) return;
      var isHidden = target.hasAttribute("hidden");
      if (isHidden) {
        target.removeAttribute("hidden");
      } else {
        target.setAttribute("hidden", "");
      }
      button.setAttribute("aria-expanded", String(isHidden));
    });
  });

  // Copy a credential ID to the clipboard.
  document.querySelectorAll("[data-copy]").forEach(function (button) {
    button.addEventListener("click", function () {
      var value = button.getAttribute("data-copy");
      if (!navigator.clipboard) return;
      navigator.clipboard.writeText(value).then(function () {
        var original = button.textContent;
        button.textContent = "Copied";
        setTimeout(function () {
          button.textContent = original;
        }, 1500);
      });
    });
  });

  // Live monitoring panel: refresh the counters from /metrics.
  var panel = document.getElementById("metrics-panel");
  if (panel) {
    var refresh = function () {
      fetch("/metrics", { headers: { Accept: "application/json" } })
        .then(function (response) {
          return response.ok ? response.json() : null;
        })
        .then(function (data) {
          if (!data) return;
          var map = {
            "metric-qualifications": data.qualifications.total,
            "metric-active": data.qualifications.active,
            "metric-verifications": data.verifications.total,
            "metric-valid": data.verifications.valid,
            "metric-audit": data.audit_entries,
          };
          Object.keys(map).forEach(function (id) {
            var el = document.getElementById(id);
            if (el && map[id] !== undefined) el.textContent = map[id];
          });
          var stamp = document.getElementById("metrics-updated");
          if (stamp) stamp.textContent = new Date().toLocaleTimeString();
        })
        .catch(function () {
          /* Monitoring is best-effort; a failed poll must not break the page. */
        });
    };
    refresh();
    setInterval(refresh, 15000);
  }
})();
