from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import Borrow, UserEdition
from datetime import datetime

class BorrowRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def is_book_available(self, book_id: int, user_id: int) -> bool:
        result = await self.session.execute(
            select(UserEdition).where(
                UserEdition.id == book_id,
                UserEdition.is_available == True,
                UserEdition.user_id != user_id
            )
        )
        return result.scalar_one_or_none() is not None

    async def is_book_already_requested(self, book_id: int, user_id: int) -> bool:
        result = await self.session.execute(
            select(Borrow).where(
                Borrow.book_id == book_id,
                Borrow.borrower_id == user_id
            )
        )
        return result.scalar_one_or_none() is not None

    async def create_borrow_request(
        self, book_id: int, user_id: int
    ) -> Borrow:
        borrow = Borrow(
            book_id=book_id,
            borrower_id=user_id,
            status="requested",
            requested_at=datetime.utcnow()
        )
        self.session.add(borrow)
        await self.session.commit()
        await self.session.refresh(borrow)
        return borrow

    async def get_requests_sent_by(self, user_id: int):
        stmt = select(Borrow).where(Borrow.borrower_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_requests_received_by(self, user_id: int):
        stmt = select(Borrow).join(UserEdition).where(UserEdition.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()