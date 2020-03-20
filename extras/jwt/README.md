# JWT Key Pair Secret

Bank of Anthos uses [Json Web Tokens (JWTs)](https://jwt.io/introduction/) to handle user authentication.
JWTs use asymmetric key pairs to sign and verify tokens.
In this case, `userservice` creates and signs tokens with a RSA private key when a user logs in,
and the other services use the corresponding public key to validate the user.

This directory contains a pre-built [Secret](https://kubernetes.io/docs/concepts/configuration/secret/) 
containing an RSA key pair to make deployment easier.
**In practice, the secret should be generated manually and not checked in to version control**

## Creating Secret Manually

```
  openssl genrsa -out jwtRS256.key 4096
  openssl rsa -in jwtRS256.key -outform PEM -pubout -out jwtRS256.key.pub
  kubectl create secret generic jwt-key --from-file=./jwtRS256.key --from-file=./jwtRS256.key.pub
```

