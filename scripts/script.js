document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("contact-form");

  form.addEventListener("submit", function (event) {
    event.preventDefault();

    // Récupérer les valeurs des champs
    const name = document.getElementById("name").value;
    const email = document.getElementById("email").value;
    const message = document.getElementById("message").value;

    // Construire l'objet de données à envoyer
    const formData = {
      name: name,
      email: email,
      message: message,
    };

    // Envoyer les données à Formspree
    fetch("https://formspree.io/f/meqbwelk", {
      method: "POST",
      headers: {
        Accept: "application/json",
      },
      body: JSON.stringify(formData),
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error("Erreur lors de l'envoi du formulaire.");
        }
        return response.json();
      })
      .then((data) => {
        // Succès : traiter la réponse si nécessaire
        console.log("Formulaire soumis avec succès :", data);
        alert("Votre message a été envoyé avec succès!");
        form.reset(); // Effacer le formulaire après l'envoi
      })
      .catch((error) => {
        // Erreur : traiter l'erreur si nécessaire
        console.error("Erreur lors de l'envoi du formulaire :", error);
        alert("Une erreur s'est produite lors de l'envoi du formulaire.");
      });
  });
});
