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

describe('Login Page', function() {
  it('successfully loads', function() {
    cy.visit('/login')
  })
})

describe('Default Credentials on Form Submission', function() {
  const username = 'testuser'
  const password = 'password'
  const name = 'Eve'

  beforeEach(function() {
    cy.login(username, password)
  })

  it('redirects to home', function() {
    cy.url().should('include', '/home')
  })

  it('sees correct username', function() {
    cy.get('#account-user-name').contains(name)
  })

  it('sees correct balance', function() {
    cy.get("#current-balance").then(($span) => {
      const balanceStr= $span.text()
      const balance = parseFloat(balanceStr.replace(/[^\d.]/g, ''))
      cy.wrap(balance).should('greaterThan', 0)
     })
  })

  it('login and signup redirects back to home', function() {
    cy.visit('login')
    cy.url().should('include', '/home')

    cy.visit('signup')
    cy.url().should('include', '/home')
  })

})

describe('Bad Credentials on Form Submission', function() {
  const uuid = () => Cypress._.random(0, 1e6)
  const id = uuid()
  const username = `baduser-${id}`
  const password = `badpassword-${id}`

  beforeEach(function() {
    cy.login(username, password)
  })

  it('fails with alert banner', function() {
    cy.get('#alertBanner').contains('Login failed.')
  })

  it('cannot access home page', function() {
      cy.visit('home')
      // should be redirected to login
      cy.url().should('include', '/login')
  })

})

