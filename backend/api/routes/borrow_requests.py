# api/routes/borrow_requests.py
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from utils.jwt_utils import verify_jwt
from utils.response_utils import dict_keys_to_camel
from db.session import get_session
from repositories import BorrowRepository
from typing import List
from schemas import BorrowOut, BorrowRequest

router = APIRouter(prefix="/borrow-requests", tags=["borrows"])

@router.post("/")
async def request_book(borrow_request: BorrowRequest, user_id: int = Depends(verify_jwt), session: AsyncSession = Depends(get_session)):
    id = borrow_request.id
    repo = BorrowRepository(session)
    try:
        if await repo.is_book_already_requested(id, user_id):
            return JSONResponse(
                status_code=400,
                content={"userSafeErrorMessage": "This book has already been requested."}
            )

        if not await repo.is_book_available(id, user_id):
            return JSONResponse(
                status_code=400,
                content={"userSafeErrorMessage": "This book is not currently available."}
            )

        borrow = await repo.create_borrow_request(id, user_id)
        return JSONResponse(
            status_code=200,
            content={"status": borrow.status}
        )

    except Exception as e:
        print(f"Error: {e}")
        return JSONResponse(
            status_code=500,
            content={"userSafeErrorMessage": "An unknown error occurred"}
        )

@router.get("/sent")
async def get_sent_requests(
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(verify_jwt)
):
    repo = BorrowRepository(session)
    response = await repo.get_requests_sent_by(user_id)
    return dict_keys_to_camel([BorrowOut.model_validate(i, from_attributes=True).model_dump(by_alias=True) for i in response])


@router.get("/received", response_model=List[BorrowOut])
async def get_received_requests(
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(verify_jwt)
):
    repo = BorrowRepository(session)
    response = await repo.get_requests_received_by(user_id)
    return dict_keys_to_camel([BorrowOut.model_validate(i, from_attributes=True).model_dump(by_alias=True) for i in response])

