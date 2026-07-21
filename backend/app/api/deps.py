from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from app.database.session import get_db
from app.models import User

DEMO_USER_EMAIL = "demo@local.dev"


async def get_current_user_id(db: AsyncSession = Depends(get_db)) -> int:
    result = await db.execute(select(User).where(User.email == DEMO_USER_EMAIL))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(email=DEMO_USER_EMAIL, hashed_password="stub")
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user.id
