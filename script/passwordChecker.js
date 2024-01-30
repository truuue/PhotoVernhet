function passwordChecker() {
  var password = prompt(
    "Veuillez entrer le mot de passe pour accéder à cette page :"
  );
  if (password == "motdepasse") {
  } else {
    alert("Mot de passe incorrect.");
    window.location = "index.html"; // Redirection si le mot de passe est incorrect
  }
}
passwordChecker();
