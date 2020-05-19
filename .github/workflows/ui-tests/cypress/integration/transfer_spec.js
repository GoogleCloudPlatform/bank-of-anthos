const defaultUser = Cypress.env('defaultUser')
const username = defaultUser.username
const password = defaultUser.password
const name = defaultUser.name

const receipient = {
    accountNum: '1044226144',
    name: 'Alice'
}
const randomNum = (max) => {
    return Math.floor(Math.random() * max)
}

describe('Default user can transfer funds', function () {
    beforeEach(function () {
        cy.loginRequest(username, password)
        cy.visit('/home')
    })

    it('sees transfer button', function () {
        cy.get('.h5.mb-0').last().contains('Send Payment')

    })

    it('clicking payments button makes modal visible', function () {
        cy.get('#sendPayment').should('not.be.visible')
        cy.get('.h5.mb-0').last().click()
        cy.get('#sendPayment').should('be.visible')

    })

    it('shows expected receipients', function () {
        cy.get('.h5.mb-0').last().click()
        cy.get('#payment-accounts').children().contains("1044226144")
        cy.get('#payment-accounts').children().contains("1055757655")
        cy.get('#payment-accounts').contains("Alice")
        cy.get('#payment-accounts').contains("Bob")

    })

    it('can transfer funds', function () {
        const paymentAmount = Math.floor(Math.random() * 10)

        cy.transfer(receipient, paymentAmount)
        cy.get('.alert').contains('Payment initiated')
    })

    it('can see balance update', function () {
        // const paymentAmount = Math.floor(Math.random() * 10)
        const paymentAmount = randomNum(100)
        let expectedBalance

        cy.get("#current-balance").then(($span) => {
            const currentBalanceSpan = $span.text()

            // regex: removes any characters that are not a digit [0-9] or a period [.]
            const currentBalance = parseFloat(currentBalanceSpan.replace(/[^\d.]/g, ''))
            expectedBalance = currentBalance - paymentAmount
            cy.transfer(receipient, paymentAmount)

            // Payment Initiated
            cy.get('.alert').contains('Payment initiated')
        })
        cy.reload()
        cy.get('#current-balance').then(($span) => {
            const updatedBalanceSpan = $span.text()
            const updatedBalance = parseFloat(updatedBalanceSpan.replace(/[^\d.]/g, ''))
            cy.wrap(updatedBalance).should('eq', expectedBalance)
        })

    })

    it('can see transaction in history', function () {
        const paymentAmount = randomNum(100)
        cy.transfer(receipient, paymentAmount)
        cy.get('.alert').contains('Payment initiated')
        cy.reload()

        cy.get('#transaction-table').find('tbody>tr').as('latest')

        cy.get('@latest').find('.transaction-account').contains(receipient.accountNum)
        cy.get('@latest').find('.transaction-type').contains('Credit')
        cy.get('@latest').find('.transaction-amount').contains(paymentAmount)


    })

    it('can see new contact show up', function () {
        // makes random 10 digit number
        const accountNum = Math.floor(100000000 + Math.random() * 10000000000);
        const newReceipient = {
            accountNum: accountNum,
            contactLabel: `testcontact${accountNum}`
        }
        const paymentAmount = randomNum(100)

        cy.transferToNewContact(newReceipient, paymentAmount)
        cy.get('.alert').contains('Payment initiated')
        cy.get('.h5.mb-0').last().click()
        cy.get('#payment-accounts').contains(newReceipient.contactLabel)
        cy.get('#payment-accounts').contains(newReceipient.accountNum)

    })

})

describe('Invalid data is disallowed for transfer', function () {
    beforeEach(function () {
        cy.login(username, password)
    })

    it('cannot be greater than balance', function () {
        let greaterThanBalance
        const paymentAmount = randomNum(100)
        cy.get("#current-balance").then(($span) => {
            const currentBalanceSpan = $span.text()

            // regex: removes any characters that are not a digit [0-9] or a period [.]
            const currentBalance = parseFloat(currentBalanceSpan.replace(/[^\d.]/g, ''))
            greaterThanBalance = currentBalance + paymentAmount
            cy.transfer(receipient, greaterThanBalance)

            cy.get('.invalid-feedback').should('be.visible')
        })
    })


    it('cannot be equal to zero', function () {
        // zero amount
        const zeroPayment = 0
        cy.transfer(receipient, zeroPayment)
        cy.get('.invalid-feedback').should('be.visible')

    })

    it('cannot be less than zero', function () {
        const negativePayment = `-${randomNum(100)}`
        cy.transfer(receipient, negativePayment)
        cy.get('.invalid-feedback').should('be.visible')
    })

    it.skip('cannot contain more than 2 decimal digits', function () {
        const invalidPayment = '5.02.35.459'

        cy.transfer(receipient, invalidPayment)
        cy.get('.invalid-feedback').should('be.visible')

    })

    it('cannot reference invalid account', function () {
        const invalidReceipient = {
            accountNum: randomNum(100),
            contactLabel: `testcontact invalid ${this.accountNum}`
        }
        const paymentAmount = randomNum(100)

        cy.transferToNewContact(invalidReceipient, paymentAmount)
        cy.get('.invalid-feedback').should('be.visible')
        cy.get('.invalid-feedback').first().contains('Please enter a valid 10 digit account number')

    })

})
