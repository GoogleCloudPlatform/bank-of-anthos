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