function addAlbumAccess(userId) {
  var albumName = $("#album_name_" + userId).val();
  $.ajax({
    url: "/add_album_access",
    type: "POST",
    data: JSON.stringify({
      user_id: userId,
      album_name: albumName,
    }),
    contentType: "application/json; charset=utf-8",
    dataType: "json",
    success: function (response) {
      alert("Accès à l'album ajouté avec succès.");
      // Optionnel: rafraîchir la liste ou mettre à jour l'UI ici
    },
    error: function (xhr, status, error) {
      alert("Une erreur est survenue.");
    },
  });
}

function removeAlbumAccess(userId, albumName) {
  $.ajax({
    url: "/remove_album_access",
    type: "POST",
    data: JSON.stringify({
      user_id: userId,
      album_name: albumName,
    }),
    contentType: "application/json; charset=utf-8",
    dataType: "json",
    success: function (response) {
      alert("Accès à l'album retiré avec succès.");
      // Optionnel: rafraîchir la liste ou mettre à jour l'UI ici
    },
    error: function (xhr, status, error) {
      alert(
        "Une erreur est survenue lors de la tentative de retrait de l'accès à l'album."
      );
    },
  });
}