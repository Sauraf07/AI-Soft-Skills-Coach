document.addEventListener("DOMContentLoaded", () => {
  const navLinks = document.querySelectorAll(".navbar .nav-link");

  navLinks.forEach((link) => {
    link.addEventListener("click", () => {
      const navbarCollapse = document.querySelector(".navbar-collapse.show");
      if (navbarCollapse) {
        const toggleButton = document.querySelector(".navbar-toggler");
        if (toggleButton) {
          toggleButton.click();
        }
      }
    });
  });
});
