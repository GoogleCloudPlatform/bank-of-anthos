const defaultUser = Cypress.env('defaultUser')
const username = defaultUser.username
const password = defaultUser.password
const name = defaultUser.name

describe('Default user can transfer funds', function() {
    beforeEach(function() {
        cy.login(username, password)
      })

  it('sees transfer button', function() {
    cy.get('.h5.mb-0').last().contains('Send Payment')

  })

  it('clicking payments button makes modal visible', function() {
    cy.get('#sendPayment').should('not.be.visible')
    cy.get('.h5.mb-0').last().click()   
    cy.get('#sendPayment').should('be.visible')

  })

  it('shows expected receipients', function() {
    cy.get('.h5.mb-0').last().click() 
    cy.get('#payment-accounts').children().contains("1044226144")
    cy.get('#payment-accounts').children().contains("1055757655")
    cy.get('#payment-accounts').contains("Alice")
    cy.get('#payment-accounts').contains("Bob")

  })

  it('can transfer funds', function() {
    const receipient = {
        acccountNum: '1044226144',
        name: 'Alice'
    }
    const paymentAmount = Math.floor(Math.random() * 10)

    cy.transfer(receipient, paymentAmount)

  })

  it('can see balance update', function() {
    const receipient = {
        acccountNum: '1044226144',
        name: 'Alice'
    }
    const paymentAmount = Math.floor(Math.random() * 10)
    let expectedBalance

    cy.get("#current-balance").then(($span) => {
        const currentBalanceSpan= $span.text()
        // regex: removes any characters that are not a digit [0-9] or a period [.]
        const currentBalance = parseFloat(currentBalanceSpan.replace(/[^\d.]/g, ''))
        expectedBalance = currentBalance - paymentAmount
        cy.transfer(receipient, paymentAmount)
        // Payment Initiated
        // cy.get('.alert').contains('Payment initiated')
    })
    cy.reload()
    cy.get('#current-balance').then(($span) => {
        const updatedBalanceSpan = $span.text()
        const updatedBalance = parseFloat(updatedBalanceSpan.replace(/[^\d.]/g, ''))
        cy.wrap(updatedBalance).should('eq', expectedBalance)
    })

  })

  it.only('can see transaction in history', function() {
    const receipient = {
        acccountNum: '1044226144',
        name: 'Alice'
    }
    const paymentAmount = Math.floor(Math.random() * 10)
    cy.transfer(receipient, paymentAmount)
    cy.reload() 

    cy.get('#transaction-table').find('tbody>tr').as('latest')

    cy.get('@latest').find('.transaction-account').contains(receipient.acccountNum)
    cy.get('@latest').find('.transaction-type').contains('Credit')
    cy.get('@latest').find('.transaction-amount').contains(paymentAmount)


  })

  it('can see new contact show up', function() {

  })

})

describe('Invalid data is disallowed for transfer', function() {
    it('cannot be greater than balance', function() {

    })


    it('cannot be less than or greater than zero', function() {


    })

    it('cannot contain more than 2 decimal digits', function() {

    })

    it('cannot reference invalid account or routing number', function() {

    })
})
