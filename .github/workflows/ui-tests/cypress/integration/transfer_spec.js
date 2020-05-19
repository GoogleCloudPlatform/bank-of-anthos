const defaultUser = Cypress.env('defaultUser')
const username = defaultUser.username
const password = defaultUser.password
const name = defaultUser.name

const recipient = defaultUser.recipients[0]
const randomNum = (min, max) => {
    //The maximum is exclusive and the minimum is inclusive
    return Math.floor(Math.random() * (max-min)) + min
}

const validPayment = () => {
    const max = 1000
    const min = 1
    return randomNum(min, max)
}

const validAccountNum = () => {
    // 10 digit integer
    const max = 10000000000
    const min = 1000000000
    return randomNum(min, max)
}

const validRoutingNum = () => {
    // 9 digit integer
    const max = 1000000000
    const min = 100000000
    return randomNum(min, max)
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

    it('shows expected recipients', function () {
        cy.get('.h5.mb-0').last().click()
        cy.get('#payment-accounts').children().contains("1044226144")
        cy.get('#payment-accounts').children().contains("1055757655")
        cy.get('#payment-accounts').contains("Alice")
        cy.get('#payment-accounts').contains("Bob")

    })

    it('can transfer funds', function () {
        const paymentAmount = Math.floor(Math.random() * 10)

        cy.transfer(recipient, paymentAmount)
        cy.get('.alert').contains('Payment initiated')
    })

    it('can see balance update', function () {
        // const paymentAmount = Math.floor(Math.random() * 10)
        const paymentAmount = validPayment()
        let expectedBalance

        cy.get("#current-balance").then(($span) => {
            const currentBalanceSpan = $span.text()

            // regex: removes any characters that are not a digit [0-9] or a period [.]
            const currentBalance = parseFloat(currentBalanceSpan.replace(/[^\d.]/g, ''))
            expectedBalance = currentBalance - paymentAmount
            cy.transfer(recipient, paymentAmount)

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
        const paymentAmount = validPayment()
        cy.transfer(recipient, paymentAmount)
        cy.get('.alert').contains('Payment initiated')
        cy.reload()

        cy.get('#transaction-table').find('tbody>tr').as('latest')

        cy.get('@latest').find('.transaction-account').contains(recipient.accountNum)
        cy.get('@latest').find('.transaction-type').contains('Credit')
        cy.get('@latest').find('.transaction-amount').contains(paymentAmount)


    })

    it('can see new contact show up', function () {
        // makes random 10 digit number
        const accountNum = validAccountNum();
        const newRecipient = {
            accountNum: accountNum,
            contactLabel: `testcontact${accountNum}`
        }
        const paymentAmount = validPayment()

        cy.transferToNewContact(newRecipient, paymentAmount)
        cy.get('.alert').contains('Payment initiated')
        cy.get('.h5.mb-0').last().click()
        cy.get('#payment-accounts').contains(newRecipient.contactLabel)
        cy.get('#payment-accounts').contains(newRecipient.accountNum)

    })

})

describe('Invalid data is disallowed for transfer', function () {
    beforeEach(function () {
        cy.login(username, password)
    })

    it('cannot be greater than balance', function () {
        let greaterThanBalance
        const paymentAmount = validPayment()
        cy.get("#current-balance").then(($span) => {
            const currentBalanceSpan = $span.text()

            // regex: removes any characters that are not a digit [0-9] or a period [.]
            const currentBalance = parseFloat(currentBalanceSpan.replace(/[^\d.]/g, ''))
            greaterThanBalance = currentBalance + paymentAmount
            cy.transfer(recipient, greaterThanBalance)

            cy.get('.invalid-feedback').should('be.visible')
        })
    })


    it('cannot be equal to zero', function () {
        // zero amount
        const zeroPayment = 0
        cy.transfer(recipient, zeroPayment)
        cy.get('.invalid-feedback').should('be.visible')

    })

    it('cannot be less than zero', function () {
        const negativePayment = `-${validPayment()}`
        cy.transfer(recipient, negativePayment)
        cy.get('.invalid-feedback').should('be.visible')
    })

    it.skip('cannot contain more than 2 decimal digits', function () {
        const invalidPayment = '5.02.35.459'

        cy.transfer(recipient, invalidPayment)
        cy.get('.invalid-feedback').should('be.visible')

    })

    it('cannot reference invalid account', function () {
        const invalidRecipient = {
            accountNum: randomNum(100,10000000),
            contactLabel: `testcontact invalid ${this.accountNum}`
        }
        const paymentAmount = validPayment()

        cy.transferToNewContact(invalidRecipient, paymentAmount)
        cy.get('.invalid-feedback').should('be.visible')
        cy.get('.invalid-feedback').first().contains('Please enter a valid 10 digit account number')

    })

})
