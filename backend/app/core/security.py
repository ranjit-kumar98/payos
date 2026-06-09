from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
import os

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

from app.core.config import settings

SECRET_KEY = getattr(settings, "JWT_SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    # bcrypt has a max password length of 72 bytes, truncate if longer
    max_length = 72
    if isinstance(password, str):
        password = password.encode('utf-8')
    if len(password) > max_length:
        password = password[:max_length]
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS))
    to_encode.update({"exp": expire})
    # Add a unique token identifier (jti)
    import uuid
    jti = str(uuid.uuid4())
    to_encode.update({"jti": jti})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
