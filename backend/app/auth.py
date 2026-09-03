from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from .config import settings
from .db import get_db
from .models import User, Membership

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/login")

def hash_password(password: str) -> str:
    if len(password.encode("utf-8")) > 72:
        raise HTTPException(400, "La contraseña es demasiado larga")
    return pwd.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    if len(password.encode("utf-8")) > 72:
        return False
    return pwd.verify(password, hashed)

def create_token(user_id: int) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_minutes)
    return jwt.encode({"sub": str(user_id), "exp": exp}, settings.jwt_secret, algorithm=settings.jwt_algorithm)

def current_user(token: str = Depends(oauth2), db: Session = Depends(get_db)) -> User:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        uid = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sesión inválida")
    user = db.get(User, uid)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Usuario no disponible")
    return user

def require_platform_admin(user: User):
    if not user.is_platform_admin:
        raise HTTPException(403, "Solo el administrador general puede realizar esta acción")

def require_company_access(company_id: int, user: User, db: Session):
    if user.is_platform_admin:
        return
    membership = db.query(Membership).filter(
        Membership.user_id==user.id,
        Membership.company_id==company_id
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Sin acceso a esta empresa")
