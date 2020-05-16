const defaultUser = Cypress.env('defaultUser')
const username = defaultUser.username
const password = defaultUser.password
const name = defaultUser.name

describe('Default user can deposit funds', function() {
  beforeEach(function() {
    cy.login(username, password)
  })
  
  it('sees deposit button', function() {
    cy.get('.h5.mb-0').first().contains('Deposit Funds')
  })

  it('clicking deposit button makes modal visible', function() {
    cy.get('#depositFunds').should('not.be.visible')
    cy.get('.h5.mb-0').first().click() 
    cy.get('#depositFunds').should('be.visible')
  })
  it('shows expected external account', function() {
    // TODO: add id
    cy.get('.h5.mb-0').first().click() 
    cy.get('#depositFunds').should('be.visible') 
    // TODO: change to deposit accounts
    cy.get('#accounts').children().first().contains('External Bank')
    cy.get('#accounts').children().first().contains('9099791699')
    cy.get('#accounts').children().first().contains('808889588')
  })
  it('can deposit funds', function() {
    // cy.get('.h5.mb-0').first().click() 
    // cy.get('#depositFunds').should('be.visible') 
    // // select first account

    // cy.get('#accounts').select('{"account_num": "9099791699", "routing_num": "808889588" }')
    // cy.get('#deposit-amount').type('5.00')
    // cy.get('#deposit-form').submit()
    const externalAccount = {
        accountNum: '9099791699',
        routingNum: '808889588'
    }
    const depositAmount = 10

    cy.deposit(externalAccount, depositAmount)
  })

  it.only('can see balance update', function() {
    const externalAccount = {
        accountNum: '9099791699',
        routingNum: '808889588'
    }
    const depositAmount = 400
    let expectedBalance
    cy.get("#current-balance").then(($span) => {
        const currentBalanceSpan= $span.text()
        // regex: removes any characters that are not a digit [0-9] or a period [.]
        const currentBalance = parseFloat(currentBalanceSpan.replace(/[^\d.]/g, ''))
        expectedBalance = currentBalance + depositAmount
        cy.deposit(externalAccount, depositAmount)
        // Deposit accepted
    })
    cy.reload()
    cy.get('#current-balance').then(($span) => {
        const updatedBalanceSpan = $span.text()
        const updatedBalance = parseFloat(updatedBalanceSpan.replace(/[^\d.]/g, ''))
        cy.wrap(updatedBalance).should('eq', expectedBalance)
    })

  })

  it('can see transaction in history', function() {
    cy.get('#transaction-table').children().should('have.length.greaterThan', 1)
    
  })

  it('see new contact show up', function() {

  })
// See balance update
// See transaction in history
// See new contact show up



})