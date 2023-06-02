/*
 * Copyright 2023 Google Inc. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
 
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