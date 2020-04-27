describe('User can navigate to create account screen', function() {
    it('from login', function() {
        cy.visit('/login')
        cy.get('.btn-create-account').click()
        cy.url().should('contain', 'signup')

    })

    it('from url', function() {
      cy.visit('/signup')
      cy.get('.header-title').contains('Register a new account')
    })
})

describe('User can create account', function() {
    const uuid = () => Cypress._.random(0, 1e6)
    const password = 'bells'
    const firstName = 'Tom'
    const lastName = 'Nook'
    const expectedBalance = '$0.00'

    beforeEach(function() {
        const id = uuid()
        const user = {
            username: `user-${id}`,
            firstName: firstName,
            lastName: `${lastName}-${id}`,
            password: password
        }

        cy.createAccount(user)
    })

    it('redirected to home', function() {
        cy.url().should('include', '/home')
    })

    it('contain zero balance', function() {
        cy.get('#current-balance').contains(expectedBalance)
    })
    
    it('sees correct username', function() {
        cy.get('#accountDropdown').contains(`${firstName} ${lastName}`)
    })
})