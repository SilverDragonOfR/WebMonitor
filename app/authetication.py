# app/auth_simple.py
import secrets
from fastapi import Security, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

VALID_USERNAME = "pratik"
VALID_PASSWORD = "tripathy"

basic_auth = HTTPBasic()

async def verify_credentials(credentials: HTTPBasicCredentials = Security(basic_auth)):
    correct_username = secrets.compare_digest(credentials.username, VALID_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, VALID_PASSWORD)

    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return True