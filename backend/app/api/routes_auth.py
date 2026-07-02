from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from typing import Optional, Any

from app.schemas.user import UserCreate, UserResponse, Token, TokenData
from app.utils.config import settings
from app.utils.rate_limit import limiter
from app.utils.security import get_password_hash, verify_password, create_access_token
from app.storage.db import db_connect

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

async def get_user(db: Any, username: str):
    async with db.execute("SELECT id, username, email, full_name, hashed_password, is_active, role FROM users WHERE username = ?", (username,)) as cursor:
        row = await cursor.fetchone()
        if row:
            return {
                "id": row[0],
                "username": row[1],
                "email": row[2],
                "full_name": row[3],
                "hashed_password": row[4],
                "is_active": bool(row[5]),
                "role": row[6] if row[6] else "doctor",
            }
        return None

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        jti: str = payload.get("jti")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    async with db_connect() as db:
        # Check jti blacklist (logout revocation)
        if jti:
            async with db.execute(
                "SELECT 1 FROM token_jti_blacklist WHERE jti = ?", (jti,)
            ) as cur:
                if await cur.fetchone():
                    raise credentials_exception
        user = await get_user(db, username=token_data.username)
        if user is None:
            raise credentials_exception
        if not user.get("is_active"):
            raise credentials_exception
        return user

@router.post("/auth/register", response_model=UserResponse)
@limiter.limit("5/minute")
async def register_user(request: Request, user: UserCreate):
    async with db_connect() as db:
        existing_user = await get_user(db, user.username)
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already registered")
        
        hashed_password = get_password_hash(user.password)
        role = user.role if user.role in ("doctor", "assistant") else "doctor"
        try:
            cursor = await db.execute(
                "INSERT INTO users (username, email, hashed_password, full_name, role) VALUES (?, ?, ?, ?, ?)",
                (user.username, user.email, hashed_password, user.full_name, role)
            )
            await db.commit()
            user_id = cursor.lastrowid
        except Exception as e:
            raise HTTPException(status_code=400, detail="Error creating user: " + str(e))

        return {
            "id": user_id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "is_active": True,
            "role": role,
        }

@router.post("/auth/token", response_model=Token)
@limiter.limit("10/minute")
async def login_for_access_token(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    async with db_connect() as db:
        user = await get_user(db, form_data.username)
        if not user or not verify_password(form_data.password, user["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        role = user.get("role", "doctor")
        access_token = create_access_token(data={"sub": user["username"], "role": role})
        return {"access_token": access_token, "token_type": "bearer", "role": role}

@router.get("/auth/me", response_model=UserResponse)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    return current_user


@router.post("/auth/refresh", response_model=Token)
@limiter.limit("20/minute")
async def refresh_access_token(request: Request, current_user: dict = Depends(get_current_user)):
    """Issue a fresh 60-minute token; the old token remains valid until its own expiry."""
    access_token = create_access_token(data={"sub": current_user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/auth/logout")
@limiter.limit("20/minute")
async def logout(request: Request, token: str = Depends(oauth2_scheme)):
    """Revoke the current token by adding its jti to the blacklist."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        jti: str = payload.get("jti")
        username: str = payload.get("sub")
        exp = payload.get("exp")
        if not jti or not username:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    expires_at = (
        datetime.fromtimestamp(exp, tz=timezone.utc).isoformat() if exp else ""
    )
    now = datetime.now(timezone.utc).isoformat()
    async with db_connect() as db:
        await db.execute(
            "INSERT INTO token_jti_blacklist (jti, user_id, expires_at, blacklisted_at) VALUES (?, ?, ?, ?) ON CONFLICT (jti) DO NOTHING",
            (jti, username, expires_at, now),
        )
        await db.commit()
    return {"message": "Logged out successfully"}
