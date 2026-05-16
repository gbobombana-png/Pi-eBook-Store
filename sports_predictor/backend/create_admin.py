"""Run once at startup: creates the admin user if none exists."""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))


async def main():
    from app.database import AsyncSessionLocal
    from app.models.user import User
    from app.utils.auth import hash_password
    from sqlalchemy import select

    username = os.getenv("ADMIN_USERNAME", "Gael Kkool")
    email = os.getenv("ADMIN_EMAIL", "bobombana99@gmail.com")
    password = os.getenv("ADMIN_PASSWORD", "Admin2026")

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.is_admin == True))
        if result.scalar_one_or_none():
            print("Admin already exists — skipping creation")
            return

        user = User(
            username=username.lower(),
            email=email.lower(),
            hashed_password=hash_password(password),
            is_admin=True,
            is_active=True,
        )
        session.add(user)
        await session.commit()
        print(f"Admin '{username}' created successfully")


if __name__ == "__main__":
    asyncio.run(main())
