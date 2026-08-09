from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.auth import RegisterRequest, LoginRequest, AuthResponse, UserResponse
from app.services.auth_service import AuthService
from app.db.session import get_db
from app.core.security import jwt, SECRET_KEY, ALGORITHM
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError

router = APIRouter(prefix="/auth", tags=["auth"])

bearer_scheme = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: AsyncSession = Depends(get_db)) -> UserResponse:
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

    from app.services.redis_service import get_session
    import logging

    try:
        session_data = await get_session(user_id, jti)
    except Exception as e:
        logging.error(f"Redis error during session validation: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked or session expired")

    if not session_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked or session expired")

    # Construct UserResponse from Redis session data without querying DB
    user_response = UserResponse(
        id=session_data.get("user_id"),
        email=session_data.get("email"),
        full_name=session_data.get("full_name"),
        is_active=session_data.get("is_active", True),
        is_admin=session_data.get("is_admin", False),
    )

    return user_response

@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register_user(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    existing_user = await auth_service.get_user_by_email(request.email)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    user = await auth_service.create_user(request.email, request.password, request.full_name)
    token = auth_service.create_token(user)
    return AuthResponse(access_token=token)

from app.services.rate_limit_dependency import rate_limit_dependency

from fastapi import Depends
from app.services.rate_limit_dependency import rate_limit_dependency

@router.post("/login", response_model=AuthResponse, dependencies=[Depends(rate_limit_dependency)])
async def login_user(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    user = await auth_service.authenticate_user(request.email, request.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = auth_service.create_token(user)

    from app.services.redis_service import store_session
    from jose import jwt as pyjwt
    decoded = pyjwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    jti = decoded.get("jti")
    await store_session(
        user_id=str(user.id),
        token_id=jti,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_admin=user.is_admin,
    )

    return AuthResponse(access_token=token)

@router.get("/me", response_model=UserResponse)
async def read_current_user(current_user: UserResponse = Depends(get_current_user)):
    return current_user