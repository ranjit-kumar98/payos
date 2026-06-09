from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.security import jwt, SECRET_KEY, ALGORITHM
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from app.services.auth_service import AuthService
from app.schemas.auth import UserResponse
from fastapi import HTTPException
from app.services.redis_service import remove_session
from fastapi import status

router = APIRouter(prefix="/auth", tags=["auth"])

bearer_scheme = HTTPBearer()

async def get_current_user_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        jti: str = payload.get("jti")
        if user_id is None or jti is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return user_id, jti

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(user_token: tuple = Depends(get_current_user_token), db: AsyncSession = Depends(get_db)):
    user_id, jti = user_token
    await remove_session(user_id, jti)
    return