"""Run once at startup: creates the admin user if none exists, normalizes username to lowercase."""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))


async def main():
    from app.database import AsyncSessionLocal
    from app.models.user import User
    from app.utils.auth import hash_password
    from sqlalchemy import select

    username = os.getenv("ADMIN_USERNAME", "Gael Kkool").lower()
    email = os.getenv("ADMIN_EMAIL", "bobombana99@gmail.com").lower()
    password = os.getenv("ADMIN_PASSWORD", "Admin2026")

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.is_admin == True))
        existing = result.scalar_one_or_none()

        if existing:
            # Normalize username to lowercase if needed
            if existing.username != existing.username.lower():
                old = existing.username
                existing.username = existing.username.lower()
                existing.email = existing.email.lower()
                await session.commit()
                print(f"Admin username normalized: '{old}' → '{existing.username}'")
            else:
                print(f"Admin '{existing.username}' already exists — skipping")
            return

        user = User(
            username=username,
            email=email,
            hashed_password=hash_password(password),
            is_admin=True,
            is_active=True,
        )
        session.add(user)
        await session.commit()
        print(f"Admin '{username}' created successfully")


if __name__ == "__main__":
    asyncio.run(main())
