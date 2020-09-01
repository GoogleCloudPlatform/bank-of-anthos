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
const uuid = () => Cypress._.random(0, 1e6)
Cypress.Commands.add('login', (username, password) => {
    Cypress.log({
        name: 'login',
        message: `${username} | ${password}`,
    })

    cy.visit('login')

    cy.get('#login-username').clear().type(username)
    cy.get('#login-password').clear().type(password)
    cy.get('#login-form').submit()

})

Cypress.Commands.add('loginRequest', (username, password) => {
    Cypress.log({
        name: 'loginRequest',
        message: `${username} | ${password}`,
    })
    
    return cy.request({
        method: 'POST',
        url: '/login', 
        form: true, 
        body: {
          username,
          password,
        },
      })
})

Cypress.Commands.add('createAccount', (user) => {
    Cypress.log({
        name: 'createAccount',
        message: user,
    })

    cy.visit('/signup')
    cy.get('#signup-username').type(user.username)
    cy.get('#signup-password').type(user.password)
    cy.get('#signup-password-repeat').type(user.password)
    cy.get('#signup-firstname').type(user.firstName)
    cy.get('#signup-lastname').type(user.lastName)
    cy.get('#signup-birthday').type('1981-01-01')
    cy.get('#signup-form').submit()
})

// deposit through UI
Cypress.Commands.add('deposit', (externalAccount, depositAmount) => {
    Cypress.log({
        name: 'deposit',
        message: `${externalAccount}` | `${depositAmount}`
    })

    const accountNum = externalAccount.accountNum
    const routingNum = externalAccount.routingNum


    cy.get('#depositSpan').click() 
    cy.get('#depositFunds').should('be.visible')
    cy.get('#accounts').contains(accountNum).and('contain', routingNum).click({force:true})
    cy.get('#deposit-amount').clear().type(`${depositAmount}`)
    cy.get('#deposit-form').submit()
})

// deposits to a new external account through UI
Cypress.Commands.add('depositToNewAccount', (externalAccount, depositAmount) => {
    Cypress.log({
        name: 'depositToNewAccount',
        message: `${externalAccount}` | `${depositAmount}`
    })
    cy.get('#depositSpan').click() 
    cy.get('#depositFunds').should('be.visible') 
    cy.get('#accounts').select('add')
    cy.get('#external_account_num').clear().type(externalAccount.accountNum)
    cy.get('#external_routing_num').clear().type(externalAccount.routingNum)
    cy.get('#external_label').clear().type(externalAccount.contactLabel)
    cy.get('#deposit-amount').clear().type(depositAmount)
    cy.get('#deposit-form').submit()

})

// transfers through UI
Cypress.Commands.add('transfer', (recipient, paymentAmount) => {
    Cypress.log({
        name: 'transfer',
        message: `${recipient}` | `${paymentAmount}`
    })
    cy.get('#paymentSpan').click() 
    cy.get('#payment-accounts').select(recipient.accountNum)
    cy.get('#payment-amount').clear().type(paymentAmount)
    cy.get('#payment-form').submit()
})

// transfers through request
Cypress.Commands.add('transferRequest', (recipientAccount, paymentAmount) => {
    Cypress.log({
        name: 'transferRequest',
        message: `${recipientAccount}` | `${paymentAmount}`,
    })

    const id = uuid()

    const contact_account_num = ''
    const contact_label = ''

      return cy.request({
        method: 'POST',
        url: '/payment', 
        form: true, 
        body: {
            account_num: recipientAccount,
            contact_account_num: contact_account_num,
            contact_label: contact_label,
            amount: paymentAmount,
            uuid: id
        },
      })

})

// transfers to a new account through UI
Cypress.Commands.add('transferToNewContact', (recipient, paymentAmount) => {
    Cypress.log({
        name: 'transferToNewContact',
        message: `${recipient}` | `${paymentAmount}`
    }) 
    cy.get('#paymentSpan').click() 
    cy.get('#payment-accounts').select("add")
    cy.get('#contact_account_num').clear().type(recipient.accountNum)
    cy.get('#contact_label').clear().type(recipient.contactLabel)
    cy.get('#payment-amount').clear().type(paymentAmount)
    cy.get('#payment-form').submit()
})
