from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
import aiosqlite
from typing import Optional

from app.schemas.user import UserCreate, UserResponse, Token, TokenData
from app.utils.config import settings
from app.utils.security import get_password_hash, verify_password, create_access_token
from app.storage.db import get_db_path

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

async def get_user(db: aiosqlite.Connection, username: str):
    async with db.execute("SELECT id, username, email, full_name, hashed_password, is_active FROM users WHERE username = ?", (username,)) as cursor:
        row = await cursor.fetchone()
        if row:
            return {
                "id": row[0],
                "username": row[1],
                "email": row[2],
                "full_name": row[3],
                "hashed_password": row[4],
                "is_active": bool(row[5])
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
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    async with aiosqlite.connect(get_db_path()) as db:
        user = await get_user(db, username=token_data.username)
        if user is None:
            raise credentials_exception
        return user

@router.post("/auth/register", response_model=UserResponse)
async def register_user(user: UserCreate):
    async with aiosqlite.connect(get_db_path()) as db:
        existing_user = await get_user(db, user.username)
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already registered")
        
        hashed_password = get_password_hash(user.password)
        try:
            cursor = await db.execute(
                "INSERT INTO users (username, email, hashed_password, full_name) VALUES (?, ?, ?, ?)",
                (user.username, user.email, hashed_password, user.full_name)
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
            "is_active": True
        }

@router.post("/auth/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    async with aiosqlite.connect(get_db_path()) as db:
        user = await get_user(db, form_data.username)
        if not user or not verify_password(form_data.password, user["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token = create_access_token(data={"sub": user["username"]})
        return {"access_token": access_token, "token_type": "bearer"}

@router.get("/auth/me", response_model=UserResponse)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    return current_user
