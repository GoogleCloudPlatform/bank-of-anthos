const defaultUser = Cypress.env('defaultUser')
const username = defaultUser.username
const password = defaultUser.password
const name = defaultUser.name
const externalAccount = {
    accountNum: '9099791699',
    routingNum: '808889588'
}
const randomNum = (max) => {
    return Math.floor(Math.random() * max)
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
        const depositAmount = randomNum(100)

        cy.deposit(externalAccount, depositAmount)
    })

    it('can see balance update', function () {
        const depositAmount = randomNum(100)
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
        const depositAmount = randomNum(100)

        cy.deposit(externalAccount, depositAmount)
        cy.get('.alert').contains('Deposit accepted')       

        cy.reload()

        cy.get('#transaction-table').find('tbody>tr').as('latest')

        cy.get('@latest').find('.transaction-account').contains(externalAccount.accountNum)
        cy.get('@latest').find('.transaction-type').contains('Debit')
        cy.get('@latest').find('.transaction-amount').contains(depositAmount)
    })

    it('see new contact show up', function () {
        // makes random 10 digit number
        const accountNum = Math.floor(100000000 + Math.random() * 10000000000);
        // makes random 9 digit number
        const routingNum= Math.floor(100000000 + Math.random() * 1000000000);
        const newExternalAccount = {
            accountNum: accountNum,
            routingNum: routingNum,
            contactLabel: `testcontact${accountNum}`
        }
        const paymentAmount = randomNum(100)

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
        const negativePayment = `-${randomNum(100)}`
        cy.deposit(externalAccount, negativePayment)
        cy.get('.invalid-feedback').should('be.visible')
    })

    it('cannot reference invalid account or routing number', function () {

    })
})
