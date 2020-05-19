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
        url: '/login', // baseUrl will be prepended to this url
        form: true, // indicates the body should be form urlencoded and sets Content-Type: application/x-www-form-urlencoded headers
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

Cypress.Commands.add('deposit', (externalAccount, depositAmount) => {
    Cypress.log({
        name: 'deposit',
        message: `${externalAccount}` | `${depositAmount}`
    })

    const accountNum = externalAccount.accountNum
    const routingNum = externalAccount.routingNum

    // const template = '{"account_num": "${account_num}", "routing_num": "${routing_num}"}';
    // const makeVal = new Function("{account_num, routing_num}", "return `" + template + "`;")
    // const val = makeVal({account_num: accountNum, routing_num: routingNum})
// var makeUrl = new Function("{name, age}", "return `" + template + "`;");
// var url = makeUrl({name: "John", age: 30});
// console.log(url); //http://example.com/?name=John&age=30

    cy.get('.h5.mb-0').first().click() 
    cy.get('#depositFunds').should('be.visible') 
    // cy.get('#accounts').select(val)
    cy.get('#accounts').select('{"account_num": "9099791699", "routing_num": "808889588" }')
    cy.get('#deposit-amount').type(`${depositAmount}`)
    cy.get('#deposit-form').submit()
})

Cypress.Commands.add('depositToNewAccount', (externalAccount, depositAmount) => {
    Cypress.log({
        name: 'depositToNewAccount',
        message: `${externalAccount}` | `${depositAmount}`
    })
    cy.get('.h5.mb-0').first().click() 
    cy.get('#depositFunds').should('be.visible') 
    // cy.get('#accounts').select(val)
    cy.get('#accounts').select('add')
    cy.get('#external_account_num').type(externalAccount.accountNum)
    cy.get('#external_routing_num').type(externalAccount.routingNum)
    cy.get('#external_label').type(externalAccount.contactLabel)
    cy.get('#deposit-amount').type(depositAmount)
    cy.get('#deposit-form').submit()

})

Cypress.Commands.add('transfer', (recipient, paymentAmount) => {
    Cypress.log({
        name: 'transfer',
        message: `${recipient}` | `${paymentAmount}`
    })
    cy.get('.h5.mb-0').last().click() 
    cy.get('#payment-accounts').select(recipient.accountNum)
    cy.get('#payment-amount').type(paymentAmount)
    cy.get('#payment-form').submit()
})

Cypress.Commands.add('transferToNewContact', (recipient, paymentAmount) => {
    Cypress.log({
        name: 'transferToNewContact',
        message: `${recipient}` | `${paymentAmount}`
    }) 
    cy.get('.h5.mb-0').last().click() 
    cy.get('#payment-accounts').select("add")
    cy.get('#contact_account_num').type(recipient.accountNum)
    cy.get('#contact_label').type(recipient.contactLabel)
    cy.get('#payment-amount').type(paymentAmount)
    cy.get('#payment-form').submit()
})
