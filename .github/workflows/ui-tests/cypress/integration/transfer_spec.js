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
const recipient = defaultUser.recipients[0]

const transferMsgs = Cypress.env('messages').transfer
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
    const num = Math.random() * max + min
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
    before(function () {
        // deposit $10,000 at beginning to ensure there is money in account
        const externalAccount = defaultUser.externalAccounts[0]
        cy.loginRequest(username, password)
        cy.visit('/home')
        cy.deposit(externalAccount, 10000)
    })
    beforeEach(function () {
        cy.loginRequest(username, password)
        cy.visit('/home')
    })

    it('sees transfer button', function () {
        cy.get('#paymentSpan').contains('Send Payment')

    })

    it('clicking payments button makes modal visible', function () {
        cy.get('#sendPayment').should('not.be.visible')
        cy.get('#paymentSpan').click()
        cy.get('#sendPayment').should('be.visible')

    })

    it('sees expected recipients', function () {
        cy.get('#paymentSpan').click()
        cy.get('#payment-accounts').children().contains("1033623433")
        cy.get('#payment-accounts').children().contains("1055757655")
        cy.get('#payment-accounts').children().contains("1077441377")
        cy.get('#payment-accounts').contains("Alice")
        cy.get('#payment-accounts').contains("Bob")
        cy.get('#payment-accounts').contains("Eve")

    })

    it('can transfer funds successfully', function () {
        const paymentAmount = validPayment()

        cy.transfer(recipient, paymentAmount)
        cy.get('#alert-message').contains(transferMsgs.success)
    })

    it('see balance update after transfer', function () {
        const paymentAmount = validPayment()
        let expectedBalance

        cy.get("#current-balance").then(($span) => {
            const currentBalanceSpan = $span.text()
            // regex: removes any characters that are not a digit [0-9] or a period [.]
            const currentBalance = parseFloat(currentBalanceSpan.replace(/[^\d.]/g, '')).toFixed(2)

            // ignore cents to avoid float percision errors
            expectedBalance = formatter.format(currentBalance - parseFloat(paymentAmount).toFixed(2))
                                       .split('.')[0]

            cy.transfer(recipient, paymentAmount)
            cy.get('#alert-message').contains(transferMsgs.success)
        })
        cy.visit('/home')
        cy.get('#current-balance').then(($span) => {
            const updatedBalanceSpan = $span.text()
            cy.wrap(updatedBalanceSpan).should('contain', expectedBalance)
        })

    })

    // TODO: [issue-300]
    it('see transaction in history after transfer', function () {
        const paymentAmount = validPayment()
        cy.transferRequest(recipient.accountNum, paymentAmount)
        cy.visit('/home')

        cy.get('#transaction-table').find('tbody>tr').as('latest')

        cy.get('@latest').find('.transaction-account').contains(recipient.accountNum)
        cy.get('@latest').find('.transaction-type').contains('Credit')
        cy.get('@latest').find('.transaction-amount').contains(paymentAmount)

    })

    it('can transfer to a new recipient and see its contact', function () {
        // makes random 10 digit number
        const accountNum = validAccountNum();
        const newRecipient = {
            accountNum: accountNum,
            contactLabel: `testcontact${accountNum}`
        }
        const paymentAmount = validPayment()

        cy.transferToNewContact(newRecipient, paymentAmount)
        cy.get('#alert-message').contains(transferMsgs.success)
        cy.get('#paymentSpan').click()
        cy.get('#payment-accounts').contains(newRecipient.contactLabel)
        cy.get('#payment-accounts').contains(newRecipient.accountNum)

    })

})

describe('Transfer is unsuccessful with invalid data', function () {
    beforeEach(function () {
        cy.loginRequest(username, password)
        cy.visit('/home')
    })

    it('cannot be greater than balance', function () {
        let greaterThanBalance
        const paymentAmount = validPayment()
        cy.get("#current-balance").then(($span) => {
            const currentBalanceSpan = $span.text()

            // regex: removes any characters that are not a digit [0-9] or a period [.]
            const currentBalance = parseFloat(currentBalanceSpan.replace(/[^\d.]/g, '')).toFixed(2)
            greaterThanBalance = formatter.format(currentBalance + parseFloat(paymentAmount).toFixed(2))
            cy.transfer(recipient, greaterThanBalance)

            cy.get('.invalid-feedback').should('be.visible')
            cy.get('.invalid-feedback').contains(invalidFeedback.payment)
        })
    })


    it('cannot be equal to zero', function () {
        const zeroPayment = 0
        cy.transfer(recipient, zeroPayment)
        cy.get('.invalid-feedback').should('be.visible')
        cy.get('.invalid-feedback').contains(invalidFeedback.payment)

    })

    it('cannot be less than zero', function () {
        const negativePayment = `-${validPayment()}`
        cy.transfer(recipient, negativePayment)
        cy.get('.invalid-feedback').should('be.visible')
        cy.get('.invalid-feedback').contains(invalidFeedback.payment)
    })

    it('cannot reference invalid account', function () {
        const invalidRecipient = {
            accountNum: randomInt(100,10000000),
            contactLabel: `testcontact invalid ${this.accountNum}`
        }
        const paymentAmount = validPayment()

        cy.transferToNewContact(invalidRecipient, paymentAmount)
        cy.get('.invalid-feedback').should('be.visible')
        cy.get('.invalid-feedback').first().contains(invalidFeedback.accountNum)

    })

    it('cannot transfer to self', function() {
        const self = {
            accountNum: defaultUser.accountNum,
            contactLabel: 'self'
        }

        const paymentAmount = validPayment()

        cy.transferToNewContact(self, paymentAmount)
        cy.get('#alert-message').contains(transferMsgs.error)
        cy.get('#alert-message').contains(transferMsgs.errSelf)
    })

})
