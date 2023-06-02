document.addEventListener("DOMContentLoaded", function(event) {
  // Login client-side validation
  var login = document.querySelector("#login-form");
  login.addEventListener("submit", function(e) {
    if(!login.checkValidity()){
      e.preventDefault();
      e.stopPropagation();
    }
    login.classList.add('was-validated');
  });

  var showAlert = (window.location.search == "?msg=Login+Failed");
  if (showAlert){
      document.querySelector("#alertBanner").classList.remove("hidden");
  }
});