# User Service

The user service manages user accounts and authentication. 
It creates and signs JWTs that are used by other services to authenticate users.

## Testing locally

1. Start the service locally:

    ```
    mvn spring-boot:run
    ```
   
2. Send a curl request to the `/users` endpoint

    ```
    curl --header "Content-Type: application/json" --request POST --data \
        '{"username": "jdoe","password": "pwd","password-repeat":
          "pwd","firstname": "John","lastname": "Doe","birthday": "2000-01-01",
          "timezone": "GMT+1","address": "1600 Amphitheatre Parkway","state": "CA",
          "zip": "94043","ssn": "123"}' \
        localhost:8080/users
    ```