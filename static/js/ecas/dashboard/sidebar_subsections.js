document.addEventListener("DOMContentLoaded", function () {
  document
    .querySelectorAll(".sidebar-subsection-link")
    .forEach(function (link) {
      link.addEventListener("click", function (e) {
        var anchor = this.getAttribute("data-anchor");
        var urlBase = this.getAttribute("href").split("#")[0];
        if (
          window.location.pathname === urlBase ||
          window.location.pathname === urlBase + "/"
        ) {
          e.preventDefault();
          setTimeout(function () {
            var section = document.querySelector(anchor);
            if (section) {
              if (!section.classList.contains("show")) {
                var header = document.querySelector(
                  '[data-bs-target="' + anchor + '"]',
                );
                if (header) header.click();
                setTimeout(function () {
                  section.scrollIntoView({
                    behavior: "smooth",
                    block: "center",
                  });
                }, 420);
              } else {
                section.scrollIntoView({ behavior: "smooth", block: "center" });
              }
            }
          }, 60);
        }
      });
    });
});
