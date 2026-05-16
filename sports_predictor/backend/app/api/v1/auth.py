from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.utils.auth import hash_password, verify_password, create_access_token, require_auth
from app.schemas.auth import UserCreate, Token, UserOut, LoginForm

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.username == data.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Nom d'utilisateur déjà utilisé")

    existing_email = await db.execute(select(User).where(User.email == data.email))
    if existing_email.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email déjà utilisé")

    user = User(
        username=data.username,
        email=data.email,
        hashed_password=hash_password(data.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=Token)
async def login(data: LoginForm, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == data.username.lower()))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants incorrects",
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Compte désactivé")

    token = create_access_token({"sub": user.username, "is_admin": user.is_admin})
    return Token(access_token=token, username=user.username, is_admin=user.is_admin)


@router.post("/login/form", response_model=Token, include_in_schema=False)
async def login_form(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == form.username.lower()))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identifiants incorrects")
    token = create_access_token({"sub": user.username, "is_admin": user.is_admin})
    return Token(access_token=token, username=user.username, is_admin=user.is_admin)


@router.get("/me", response_model=dict)
async def me(user: dict = Depends(require_auth)):
    return user


@router.post("/init-admin", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def init_admin(data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Create first admin — blocked once any admin exists."""
    existing_admin = await db.execute(select(User).where(User.is_admin == True))
    if existing_admin.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Un administrateur existe déjà")

    existing = await db.execute(select(User).where(User.username == data.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Nom d'utilisateur déjà utilisé")

    user = User(
        username=data.username,
        email=data.email,
        hashed_password=hash_password(data.password),
        is_admin=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
