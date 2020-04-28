/**
 * Copyright 2020 Google LLC
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

Cypress.Commands.add('login', (username, password) => {
    Cypress.log({
        name: 'login',
        message: `${username} | ${password}`,
    })

    cy.visit('login')

    cy.get('input[name=username]').clear().type(username)
    cy.get('input[name=password]').clear().type(password)
    cy.get('form').submit()

})

Cypress.Commands.add('createAccount', (user) => {
    Cypress.log({
        name: 'createAccount',
        message: user,
    })

    cy.visit('/signup')
    cy.get('input[name=username]').type(user.username)
    cy.get('input[name=password]').type(user.password)
    cy.get('input[name=password-repeat]').type(user.password)
    cy.get('input[name=firstname]').type(user.firstName)
    cy.get('input[name=lastname]').type(user.lastName)
    cy.get('input[name=birthday]').type('1981-01-01')
    cy.get('form').submit()
})
