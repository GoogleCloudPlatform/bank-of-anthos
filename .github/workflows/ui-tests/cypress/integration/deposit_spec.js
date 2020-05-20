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
        cy.get('.h5.mb-0').first().contains('Deposit Funds')
    })

    it('clicking deposit button makes modal visible', function () {
        cy.get('#depositFunds').should('not.be.visible')
        cy.get('.h5.mb-0').first().click()
        cy.get('#depositFunds').should('be.visible')
    })

    it('sees expected external accounts', function () {
        // TODO: add id
        cy.get('.h5.mb-0').first().click()
        cy.get('#depositFunds').should('be.visible')
        // TODO: change to deposit accounts
        cy.get('#accounts').children().first().as('firstOption')
        cy.get('@firstOption').contains('External Bank')
        cy.get('@firstOption').contains('9099791699')
        cy.get('@firstOption').contains('808889588')
    })

    it('can deposit funds successfully', function () {
        const depositAmount = validPayment()

        cy.deposit(externalAccount, depositAmount)
        cy.get('.alert').contains(depositMsgs.success)
    })

    it('can see balance update after deposit', function () {
        const depositAmount = validPayment()
        let expectedBalance
        cy.get("#current-balance").then(($span) => {
            const currentBalanceSpan = $span.text()
            // regex: removes any characters that are not a digit [0-9] or a period [.]
            const currentBalance = parseFloat(currentBalanceSpan.replace(/[^\d.]/g, ''))

            expectedBalance = formatter.format(currentBalance + parseFloat(depositAmount))

            cy.deposit(externalAccount, depositAmount)
            cy.get('.alert').contains(depositMsgs.success)
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
        cy.get('.alert').contains(depositMsgs.success)

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
        cy.get('.alert').contains(depositMsgs.success)

        cy.reload()
        cy.get('.h5.mb-0').first().click()
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
    })

    it('cannot be less than zero', function () {
        const negativePayment = `-${validPayment()}`
        cy.deposit(externalAccount, negativePayment)
        cy.get('.invalid-feedback').should('be.visible')
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
        cy.get('.invalid-feedback').first().contains(invalidFeedback.accountNum)
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
})
