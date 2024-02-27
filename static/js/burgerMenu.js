document.addEventListener("DOMContentLoaded", function () {
  let navWrapper = document.querySelector("#nav-wrapper"),
    navToogler = document.querySelector(".nav-toogler");

  navToogler.addEventListener("click", function () {
    navWrapper.classList.toggle("active");
  });
});
