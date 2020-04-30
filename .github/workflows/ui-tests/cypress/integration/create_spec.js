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

describe('User can navigate to create account screen', function() {
    it('from login', function() {
        cy.visit('/login')
        cy.get('#create-account-btn').click()
        cy.url().should('contain', 'signup')

    })

    it('from url', function() {
      cy.visit('/signup')
      cy.get('#signup-title').contains('Register a new account')
    })
})

describe('User can create account', function() {
    const uuid = () => Cypress._.random(0, 1e6)
    const password = 'bells'
    const firstName = 'Tom'
    const lastName = 'Nook'
    const expectedBalance = '$0.00'

    beforeEach(function() {
        const id = uuid()
        const user = {
            username: `user-${id}`,
            firstName: firstName,
            lastName: `${lastName}-${id}`,
            password: password
        }

        cy.createAccount(user)
    })

    it('redirected to home', function() {
        cy.url().should('include', '/home')
    })

    it('contain zero balance', function() {
        cy.get('#current-balance').contains(expectedBalance)
    })
    
    it('sees correct username', function() {
        cy.get('#accountDropdown').contains(`${firstName} ${lastName}`)
    })

    it('sees empty transaction history message', function() {
        const transactionMsgs = Cypress.env('messages').transaction
        // sees empty transaction history message
        cy.get('#transaction-table').children('.card-table-header').contains(transactionMsgs.empty)
        // does not see error message
        cy.get('#transaction-table').children().should('not.contain', transactionMsgs.error)

    })


    it('sees no transactions', function() {
        // new accounts only see empty history message
        // new accounts should not see a table
        cy.get('#transaction-table').children().should('have.length', 1)
        cy.get('#transaction-table').children().should('have.class', 'card-table-header')
        cy.get('#transaction-table').children().should('not.have.class', 'table')        
    })
})