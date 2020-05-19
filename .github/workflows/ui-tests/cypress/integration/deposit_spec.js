const defaultUser = Cypress.env('defaultUser')
const username = defaultUser.username
const password = defaultUser.password
const name = defaultUser.name
const externalAccount = defaultUser.externalAccounts[0]

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
    const max = 10000000000
    const min = 1000000000
    return randomNum(min, max)
}

const validRoutingNum = () => {
    const max = 1000000000
    const min = 100000000
    return randomNum(min, max)
}



describe('Default user can deposit funds', function () {
    beforeEach(function () {
        cy.loginRequest(username, password)
        cy.visit('/home')
    })

    it('sees deposit button', function () {
        cy.get('.h5.mb-0').first().contains('Deposit Funds')
    })

    it('clicking deposit button makes modal visible', function () {
        cy.get('#depositFunds').should('not.be.visible')
        cy.get('.h5.mb-0').first().click()
        cy.get('#depositFunds').should('be.visible')
    })
    it('shows expected external account', function () {
        // TODO: add id
        cy.get('.h5.mb-0').first().click()
        cy.get('#depositFunds').should('be.visible')
        // TODO: change to deposit accounts
        cy.get('#accounts').children().first().as('firstOption')
        cy.get('@firstOption').contains('External Bank')
        cy.get('@firstOption').contains('9099791699')
        cy.get('@firstOption').contains('808889588')
    })
    it('can deposit funds', function () {
        const depositAmount = validPayment()

        cy.deposit(externalAccount, depositAmount)
    })

    it('can see balance update', function () {
        const depositAmount = validPayment()
        let expectedBalance
        cy.get("#current-balance").then(($span) => {
            const currentBalanceSpan = $span.text()
            // regex: removes any characters that are not a digit [0-9] or a period [.]
            const currentBalance = parseFloat(currentBalanceSpan.replace(/[^\d.]/g, ''))
            expectedBalance = currentBalance + depositAmount
            cy.deposit(externalAccount, depositAmount)
            cy.get('.alert').contains('Deposit accepted')
        })
        cy.reload()
        cy.get('#current-balance').then(($span) => {
            const updatedBalanceSpan = $span.text()
            const updatedBalance = parseFloat(updatedBalanceSpan.replace(/[^\d.]/g, ''))
            cy.wrap(updatedBalance).should('eq', expectedBalance)
        })

    })

    it('can see transaction in history', function () {
        const depositAmount = validPayment()

        cy.deposit(externalAccount, depositAmount)
        cy.get('.alert').contains('Deposit accepted')

        cy.reload()

        cy.get('#transaction-table').find('tbody>tr').as('latest')

        cy.get('@latest').find('.transaction-account').contains(externalAccount.accountNum)
        cy.get('@latest').find('.transaction-type').contains('Debit')
        cy.get('@latest').find('.transaction-amount').contains(depositAmount)
    })

    it('see new contact show up', function () {
        const accountNum = validAccountNum()
        const routingNum = validRoutingNum()
        const newExternalAccount = {
            accountNum: accountNum,
            routingNum: routingNum,
            contactLabel: `testcontact${accountNum}`
        }
        const paymentAmount = validPayment()

        cy.depositToNewAccount(newExternalAccount, paymentAmount)
        cy.get('.alert').contains('Deposit accepted')

        cy.reload()
        cy.get('.h5.mb-0').first().click()
        cy.get('#accounts').contains(newExternalAccount.contactLabel)
        cy.get('#accounts').contains(newExternalAccount.accountNum)
        cy.get('#accounts').contains(newExternalAccount.routingNum)
    })

})

describe('Invalid data is disallowed for deposit', function () {
    beforeEach(function () {
        cy.login(username, password)
    })

    it('cannot be less than or greater than zero', function () {
        const zeroPayment = 0
        cy.deposit(externalAccount, zeroPayment)
        cy.get('.invalid-feedback').should('be.visible')
    })

    it('cannot contain more than 2 decimal digits', function () {
        const negativePayment = `-${validPayment()}`
        cy.deposit(externalAccount, negativePayment)
        cy.get('.invalid-feedback').should('be.visible')
    })

    it('cannot reference invalid account or routing number', function () {

    })
})
