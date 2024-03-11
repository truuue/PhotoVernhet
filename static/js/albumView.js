function showImage(src) {
  const modal = document.getElementById("modal");
  const fullImage = document.getElementById("fullImage");
  fullImage.src = src.replace("/thumb/", "/full/"); // Remplacement si nécessaire
  modal.style.display = "block";
}

function closeImage() {
  document.getElementById("modal").style.display = "none";
}
