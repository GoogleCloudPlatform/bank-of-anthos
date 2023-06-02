// Sign-up validation
document.addEventListener("DOMContentLoaded", function(e) {
  var form = document.querySelector("#signup-form");
  // Add max attribute to birthday input
  var today = new Date();
  var maxDate = today.toISOString().split("T")[0];
  document.querySelector("#signup-birthday").setAttribute("max", maxDate);
  // Add submit listener to signup form
  form.addEventListener("submit", function(event) {
    var passwordsMatch = document.querySelector("#signup-password").value == document.querySelector("#signup-password-repeat").value;
    if (!form.checkValidity() || !passwordsMatch) {
      event.preventDefault();
      event.stopPropagation();
      if (!passwordsMatch) document.querySelector("#alertBanner").classList.remove("hidden");
      window.scrollTo({ top: 0, behavior: "auto" });
    }
    form.classList.add("was-validated");
  });
});