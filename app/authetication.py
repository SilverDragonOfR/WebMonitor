# app/auth_simple.py
import os
import secrets
from fastapi import Security, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

VALID_USERNAME = os.getenv("VALID_USERNAME")
VALID_PASSWORD = os.getenv("VALID_PASSWORD")

basic_auth = HTTPBasic() # Create an instance of HTTPBasic authentication scheme from FastAPI

# Asynchronous function to verify HTTP Basic Authentication credentials
# For every request we need only an username and password in the header
async def verify_credentials(credentials: HTTPBasicCredentials = Security(basic_auth)):
    correct_username = secrets.compare_digest(credentials.username, VALID_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, VALID_PASSWORD)

    # Check if both username and password are correct
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return True