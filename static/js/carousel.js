document.addEventListener("DOMContentLoaded", function () {
  // Sélectionner tous les conteneurs de carrousel
  const carousels = document.querySelectorAll(".carousel-container");

  carousels.forEach((carousel) => {
    // Initialiser chaque carrousel avec une image par défaut au centre
    setDefaultImagePosition(carousel);

    // Écouter les clics sur les images de chaque carrousel
    const pics = carousel.querySelectorAll(".carousel-pic");
    pics.forEach((pic, index) => {
      pic.addEventListener("click", function () {
        if (pic.classList.contains("center")) return; // Ignorer si déjà au centre

        // Réinitialiser les classes pour tous les pics
        pics.forEach((p) => p.classList.remove("left", "center", "right"));

        // Image cliquée au centre
        pic.classList.add("center");

        // Calculer et ajuster les positions des images restantes
        const leftIndex = (index + pics.length - 1) % pics.length;
        const rightIndex = (index + 1) % pics.length;

        pics[leftIndex].classList.add("left");
        pics[rightIndex].classList.add("right");
      });
    });
  });
});

function setDefaultImagePosition(carousel) {
  const pics = carousel.querySelectorAll(".carousel-pic");
  const randomIndex = Math.floor(Math.random() * pics.length);

  pics.forEach((pic, index) => {
    pic.classList.remove("left", "center", "right");
    if (index === randomIndex) {
      pic.classList.add("center");
    } else if ((randomIndex + 1) % pics.length === index) {
      pic.classList.add("right");
    } else {
      pic.classList.add("left");
    }
  });
}
