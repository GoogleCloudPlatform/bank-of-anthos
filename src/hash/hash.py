
import hashlib
import os
import sys

# Function to hash a password using PBKDF2
def hash_password_pbkdf2(password: str) -> str:
    # Generate a new salt
    salt = os.urandom(16)
    # Hash the password using PBKDF2 with SHA-256
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 10000)
    # Return the salt and hashed password as a combined string
    return salt.hex() + ":" + hashed.hex()

# Main function for the command-line interface
def main():
    if len(sys.argv) != 2:
        print("Usage: python hash.py <password>")
        sys.exit(1)

    password = sys.argv[1]

    # Hash the password using PBKDF2
    pbkdf2_hashed_password = hash_password_pbkdf2(password)
    print(f"PBKDF2 Hashed Password: {pbkdf2_hashed_password}")

if __name__ == "__main__":
    main()