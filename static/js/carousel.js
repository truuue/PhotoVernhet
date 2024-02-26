document.addEventListener("DOMContentLoaded", () => {
  const carousels = document.querySelectorAll(".carousel");

  carousels.forEach((carousel) => {
    const images = carousel.querySelectorAll(".carousel-image");
    let currentImageIndex = 1;

    if (images.length > 1) {
      images[1].classList.add("active");
    }

    const nextButton = carousel.nextElementSibling;
    const prevButton = nextButton.nextElementSibling;

    nextButton.addEventListener("click", () => {
      currentImageIndex = (currentImageIndex + 1) % images.length;
      updateCarousel();
    });

    prevButton.addEventListener("click", () => {
      currentImageIndex =
        (currentImageIndex - 1 + images.length) % images.length;
      updateCarousel();
    });

    const updateCarousel = () => {
      images.forEach((img, index) => {
        img.classList.remove("active"); // Retirer la classe 'active' de toutes les images
        img.style.transform = `translateX(-${100 * currentImageIndex}%)`;
      });
      images[currentImageIndex].classList.add("active"); // Ajouter la classe 'active' à l'image courante
    };
  });
});
