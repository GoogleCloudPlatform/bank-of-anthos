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

const defaultUser = Cypress.env('defaultUser')
const username = defaultUser.username
const password = defaultUser.password
const name = defaultUser.name
const externalAccount = defaultUser.externalAccounts[0]

const depositMsgs = Cypress.env('messages').deposit
const invalidFeedback = Cypress.env('messages').invalidFeedback
const formatter = new Intl.NumberFormat('en-US', {
    maximumFractionDigits: 2,
  });

const randomInt = (min, max) => {
    // max is exclusive and the min inclusive
    return Math.floor(Math.random() * (max-min)) + min
}

const validPayment = () => {
    const max = 100
    const min = 1
    const num = (Math.random() * max) + min
    return formatter.format(num)
}

const validAccountNum = () => {
    // 10 digit integer
    const max = 10000000000
    const min = 1000000000
    return randomInt(min, max)
}

const validRoutingNum = () => {
    // 9 digit integer
    const max = 1000000000
    const min = 100000000
    return randomInt(min, max)
}

describe('Authenticated default user', function () {
    beforeEach(function () {
        cy.loginRequest(username, password)
        cy.visit('/home')
    })

    it('sees deposit button', function () {
        cy.get('#depositSpan').contains('Deposit Funds')
    })

    it('clicking deposit button makes modal visible', function () {
        cy.get('#depositFunds').should('not.be.visible')
        cy.get('#depositSpan').click()
        cy.get('#depositFunds').should('be.visible')
    })

    it('sees expected external accounts', function () {
        cy.get('#depositSpan').click()
        cy.get('#depositFunds').should('be.visible')
        cy.get('#accounts').children().first().as('firstOption')
        cy.get('@firstOption').contains(externalAccount.accountNum)
        cy.get('@firstOption').contains(externalAccount.routingNum)
    })

    it('can deposit funds successfully', function () {
        const depositAmount = validPayment()

        cy.deposit(externalAccount, depositAmount)
        cy.get('#alert-message').contains(depositMsgs.success)
    })

    it('can see balance update after deposit', function () {
        const depositAmount = validPayment()
        let expectedBalance
        cy.get("#current-balance").then(($span) => {
            const currentBalanceSpan = $span.text()
            // regex: removes any characters that are not a digit [0-9] or a period [.]
            const currentBalance = parseFloat(currentBalanceSpan.replace(/[^\d.]/g, ''))
            // ignore cents to avoid float percision errors
            expectedBalance = formatter.format(currentBalance + parseFloat(depositAmount))
                                       .split('.')[0]

            cy.deposit(externalAccount, depositAmount)
            cy.get('#alert-message').contains(depositMsgs.success)
        })
        cy.visit('/home')
        cy.get('#current-balance').then(($span) => {
            const updatedBalanceSpan = $span.text()
            cy.wrap(updatedBalanceSpan).should('contain', expectedBalance)
        })

    })

    it('can see transaction in history after deposit', function () {
        const depositAmount = validPayment()

        cy.deposit(externalAccount, depositAmount)
        cy.get('#alert-message').contains(depositMsgs.success)

        cy.visit('/home')

        cy.get('#transaction-table').find('tbody>tr').as('latest')

        cy.get('@latest').find('.transaction-account').contains(externalAccount.accountNum)
        cy.get('@latest').find('.transaction-type').contains('Debit')
        cy.get('@latest').find('.transaction-amount').contains(depositAmount)
    })

    it('can deposit to new account and see new account', function () {
        const accountNum = validAccountNum()
        const routingNum = validRoutingNum()
        const newExternalAccount = {
            accountNum: accountNum,
            routingNum: routingNum,
            contactLabel: `testcontact${accountNum}`
        }
        const paymentAmount = validPayment()

        cy.depositToNewAccount(newExternalAccount, paymentAmount)
        cy.get('#alert-message').contains(depositMsgs.success)

        cy.reload()
        cy.get('#depositSpan').click()
        cy.get('#accounts').contains(newExternalAccount.contactLabel)
        cy.get('#accounts').contains(newExternalAccount.accountNum)
        cy.get('#accounts').contains(newExternalAccount.routingNum)
    })

})

describe('Deposit is unsuccessful with invalid data', function () {
    beforeEach(function () {
        cy.loginRequest(username, password)
        cy.visit('/home')
    })

    it('cannot be equal to zero', function () {
        const zeroPayment = 0
        cy.deposit(externalAccount, zeroPayment)
        cy.get('.invalid-feedback').should('be.visible')
        cy.get('.invalid-feedback').contains(invalidFeedback.payment)
    })

    it('cannot be less than zero', function () {
        const negativePayment = `-${validPayment()}`
        cy.deposit(externalAccount, negativePayment)
        cy.get('.invalid-feedback').should('be.visible')
        cy.get('.invalid-feedback').contains(invalidFeedback.payment)
    })

    it('cannot reference invalid account number', function () {
        const invalidExternalAccount = {
            accountNum: randomInt(100,100000),
            routingNum: validRoutingNum(),
            contactLabel: `testcontact invalid ${this.accountNum}`
        }

        const paymentAmount = validPayment()

        cy.depositToNewAccount(invalidExternalAccount, paymentAmount)
        cy.get('.invalid-feedback').should('be.visible')
        cy.get('.invalid-feedback').contains(invalidFeedback.accountNum)
    })

    it('cannot reference invalid routing number', function () {
        const invalidExternalAccount = {
            accountNum: validAccountNum(),
            routingNum: randomInt(100,100000),
            contactLabel: `testcontact invalid ${this.accountNum}`
        }

        const paymentAmount = validPayment()

        cy.depositToNewAccount(invalidExternalAccount, paymentAmount)
        cy.get('.invalid-feedback').should('be.visible')
        cy.get('.invalid-feedback').contains(invalidFeedback.routingNum)
    })

    it('cannot reference local routing number', function() {
        const invalidExternalAccount = {
            accountNum: validAccountNum(),
            routingNum: defaultUser.localRoutingNum,
            contactLabel: 'local routing num'
        }

        const paymentAmount = validPayment()

        cy.depositToNewAccount(invalidExternalAccount, paymentAmount)
        cy.get('#alert-message').contains(depositMsgs.error)
        cy.get('#alert-message').contains(depositMsgs.errRoutingNum)
    })
})
